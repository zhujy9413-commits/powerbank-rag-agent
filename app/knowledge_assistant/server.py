"""Local-only prototype. Run: python3 -m app.knowledge_assistant.server"""
import argparse
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import sqlite3
import threading
from urllib.parse import urlparse, unquote

from .core import Assistant, Corpus, Principal, ROOT, card
from .providers import Settings, ProviderError
from .maintenance import KnowledgeMaintenance
from app.ai_work.review import ReviewService, ConflictError
from app.ai_work.export import export_xlsx

STATIC = Path(__file__).parent / "static"


class Store:
    def __init__(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.lock=threading.RLock()
        self.db.executescript("""CREATE TABLE IF NOT EXISTS requests(id TEXT PRIMARY KEY, owner TEXT, created_at TEXT, response TEXT);
        CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY, request_id TEXT, owner TEXT, created_at TEXT, kind TEXT, note TEXT);""")
        columns={r[1] for r in self.db.execute('PRAGMA table_info(feedback)')}
        for name, definition in [('operation_key','TEXT'),('state',"TEXT DEFAULT 'pending'"),('handling_note',"TEXT DEFAULT ''")]:
            if name not in columns:self.db.execute(f'ALTER TABLE feedback ADD COLUMN {name} {definition}')
        self.db.execute('CREATE UNIQUE INDEX IF NOT EXISTS feedback_retry ON feedback(owner,request_id,operation_key)')
        self.db.execute("DELETE FROM requests WHERE created_at < datetime('now','-7 days')")
        self.db.execute("DELETE FROM feedback WHERE created_at < datetime('now','-7 days')")
        self.db.commit()

    def add(self,principal,result):
        with self.lock:
            self.db.execute("INSERT INTO requests VALUES(?,?,datetime('now'),?)",(result["request_id"],principal.user_id,json.dumps(result,ensure_ascii=False)))
            self.db.commit()

    def get(self,principal,request_id,corpus):
        with self.lock:
            row=self.db.execute("SELECT response FROM requests WHERE id=? AND owner=?",(request_id,principal.user_id)).fetchone()
        if not row:
            raise PermissionError("记录不存在或当前身份无权访问。")
        result=json.loads(row[0])
        for cid in result["trace"]["retrieved_chunk_ids"]:
            if cid not in corpus.by_id or not corpus.accessible(corpus.by_id[cid],principal):
                raise PermissionError("资料权限已变化，请重新检索。")
        return result

    def feedback(self,principal,request_id,kind,note,corpus,operation_key=None):
        self.get(principal,request_id,corpus)
        if kind not in {"useful","wrong_answer","wrong_citation","missing_retrieval","missing_material"} or not isinstance(note,str) or len(note)>1000:
            raise ValueError("反馈类型或备注无效。")
        import hashlib
        if operation_key is None:
            operation_key=hashlib.sha256(json.dumps([kind,note],ensure_ascii=False).encode()).hexdigest()
        if not isinstance(operation_key,str) or not 8<=len(operation_key)<=100:
            raise ValueError('反馈重试标识无效。')
        with self.lock,self.db:
            row=self.db.execute('SELECT id,kind,note FROM feedback WHERE owner=? AND request_id=? AND operation_key=?',(principal.user_id,request_id,operation_key)).fetchone()
            if row:
                if (row[1],row[2])!=(kind,note):raise ConflictError('同一反馈标识不能用于不同内容。')
                return dict(saved=True,feedback_id=row[0])
            cursor=self.db.execute("INSERT INTO feedback(request_id,owner,created_at,kind,note,operation_key) VALUES(?,?,datetime('now'),?,?,?)",(request_id,principal.user_id,kind,note,operation_key))
            return dict(saved=True,feedback_id=cursor.lastrowid)

    def maintenance_feedback(self,principal,corpus,identity=None,data=None):
        if principal.role!='engineer':raise PermissionError('当前身份没有反馈维护权限。')
        with self.lock,self.db:
            rows=self.db.execute('SELECT id,request_id,owner,kind,note,state,handling_note FROM feedback ORDER BY id DESC').fetchall()
            accessible=[]
            for row in rows:
                try:request=self.get(principal,row[1],corpus)
                except PermissionError:continue
                record=dict(id=row[0],request_id=row[1],kind=row[3],note=row[4],state=row[5],handling_note=row[6],query=request['query'],snapshot=request['snapshot'])
                if identity is not None and str(row[0])==str(identity):
                    if not isinstance(data,dict) or set(data)!={'state','note'} or data['state'] not in {'pending','handled','deferred'} or not isinstance(data['note'],str) or not 0<len(data['note'].strip())<=1000:
                        raise ValueError('请选择处理状态并填写理由。')
                    self.db.execute('UPDATE feedback SET state=?,handling_note=? WHERE id=?',(data['state'],data['note'].strip(),row[0]))
                    return dict(saved=True)
                accessible.append(record)
            if identity is not None:raise PermissionError('反馈不存在或无权处理。')
            return accessible


class LocalServer(ThreadingHTTPServer):
    daemon_threads=True

    def __init__(self,address,principal,local_dir):
        if address[0] not in {"127.0.0.1","localhost"}:
            raise ValueError("本原型仅绑定本机地址；企业登录未接入，不能对外部署。")
        self.principal=principal
        self.secret=secrets.token_urlsafe(32)
        self.settings=Settings(Path(local_dir)/"model.json")
        self.corpus=Corpus()
        self.knowledge=KnowledgeMaintenance(Path(local_dir)/"knowledge.sqlite3",self.corpus)
        self.assistant=Assistant(self.corpus,self.settings,Path(local_dir)/"vectors.json")
        self.store=Store(Path(local_dir)/"requests.sqlite3")
        self.review_service=ReviewService(Path(local_dir)/"reviews.sqlite3",self.corpus)
        super().__init__(address,Handler)


class Handler(BaseHTTPRequestHandler):
    server_version="KnowledgePrototype/0.1"

    def log_message(self,*args):
        # Queries, API keys, and provider error bodies never enter terminal logs.
        pass

    def send_data(self,status,body,content_type="application/json; charset=utf-8",cookie=False):
        if isinstance(body,(dict,list)):
            body=json.dumps(body,ensure_ascii=False).encode()
        elif isinstance(body,str):
            body=body.encode()
        self.send_response(status)
        self.send_header("Content-Type",content_type)
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store")
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Referrer-Policy","no-referrer")
        if cookie:
            self.send_header("Set-Cookie",f"local_session={self.server.secret}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(body)

    def host_ok(self):
        port=self.server.server_address[1]
        return self.headers.get("Host") in {f"127.0.0.1:{port}",f"localhost:{port}"}

    def session_ok(self):
        try:
            cookies=SimpleCookie(self.headers.get("Cookie",""))
            value=cookies.get("local_session")
            return value is not None and secrets.compare_digest(value.value,self.server.secret)
        except Exception:
            return False

    def get_json(self):
        if self.headers.get("Content-Type","").split(";")[0] != "application/json":
            raise ValueError("请求需使用JSON格式。")
        try:
            length=int(self.headers.get("Content-Length","0"))
        except ValueError:
            raise ValueError("请求长度无效。") from None
        limit=3*1024*1024 if self.path=="/api/ai-work/tasks" else 256*1024 if self.path.startswith(("/api/knowledge", "/api/ai-work/tasks/")) else 16384
        if not 0<length<=limit:
            raise ValueError("请求为空或超过大小限制。")
        try:
            data=json.loads(self.rfile.read(length))
        except ValueError:
            raise ValueError("JSON格式无效。") from None
        if not isinstance(data,dict):
            raise ValueError("请求必须为JSON对象。")
        return data

    def do_GET(self):
        with self.server.corpus.lock:
            return self._do_GET()

    def _do_GET(self):
        if not self.host_ok():
            return self.send_data(403,{"error":"仅允许本机访问。"})
        route=unquote(urlparse(self.path).path)
        assets={"/":("index.html","text/html; charset=utf-8"),"/app.js":("app.js","text/javascript; charset=utf-8"),"/work.js":("work.js","text/javascript; charset=utf-8"),"/maintenance.js":("maintenance.js","text/javascript; charset=utf-8"),"/style.css":("style.css","text/css; charset=utf-8")}
        if route in assets:
            name,mime=assets[route]
            return self.send_data(200,(STATIC/name).read_bytes(),mime)
        principal=self.server.principal
        if route=="/api/config":
            docs={c["document_id"] for c in self.server.corpus.candidates(principal)}
            return self.send_data(200,dict(profile=dict(name="研发工程师" if principal.role=="engineer" else "普通员工",role=principal.role,local_demo=True),
                task_ids=list(principal.task_ids),model=self.server.settings.public(),vector_ready=self.server.assistant.vector_ready(),
                snapshot=self.server.corpus.snapshot,document_count=len(docs),csrf_token=self.server.secret),cookie=True)
        if not self.session_ok():
            return self.send_data(401,{"error":"请刷新页面以建立本机演示会话。"})
        try:
            if route=="/api/knowledge":
                return self.send_data(200,self.server.knowledge.listing(principal))
            if route=="/api/maintenance-feedback":
                return self.send_data(200,self.server.store.maintenance_feedback(principal,self.server.corpus))
            if route=="/api/query-options":
                permitted=self.server.corpus.candidates(principal,True)
                docs={c.get('knowledge_version_id',c['document_id']):dict(version_id=c.get('knowledge_version_id',c['document_id']),document_id=c['document_id'],title=c['title'],version=c['version'],publication_status=c['publication_status']) for c in permitted if c['scope']=='knowledge'}
                return self.send_data(200,list(docs.values()))
            if route=="/api/ai-work/catalog":
                return self.send_data(200,self.server.review_service.catalog(principal))
            if route=="/api/ai-work/tasks":
                return self.send_data(200,self.server.review_service.list_tasks(principal))
            if route.startswith("/api/ai-work/tasks/"):
                parts=route.split("/")
                if len(parts)==7 and parts[5]=='sources':
                    return self.send_data(200,self.server.review_service.source(principal,parts[4],parts[6]))
                if len(parts)==6 and parts[5]=="pdf":
                    return self.send_data(200,self.server.review_service.pdf(principal,parts[4]),"application/pdf")
                if len(parts)==5:
                    return self.send_data(200,self.server.review_service.task(principal,parts[4]))
            if route.startswith("/api/ai-work/runs/"):
                parts=route.split("/")
                result=self.server.review_service.result(principal,parts[4])
                if len(parts)==6 and parts[5]=="export":
                    return self.send_data(200,export_xlsx(result),"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                if len(parts)==5:
                    return self.send_data(200,result)
            if route=="/api/catalog":
                return self.send_data(200,{"sources":[card(c) for c in self.server.corpus.candidates(principal)]})
            if route.startswith("/api/source/"):
                return self.send_data(200,self.server.corpus.source(route.removeprefix("/api/source/"),principal))
            if route.startswith("/api/requests/"):
                return self.send_data(200,self.server.store.get(principal,route.removeprefix("/api/requests/"),self.server.corpus))
            if route=="/api/pdf/SYN-TR-001-R1":
                self.server.corpus.source("TR-P2-RESPONSE",principal)
                return self.send_data(200,(ROOT/"output/pdf/SYN-TR-001-R1.pdf").read_bytes(),"application/pdf")
            return self.send_data(404,{"error":"页面或接口不存在。"})
        except PermissionError as exc:
            return self.send_data(403,{"error":str(exc)})
        except ValueError as exc:
            return self.send_data(400,{"error":str(exc)})
        except Exception:
            return self.send_data(500,{"error":"读取资料失败，请重试。"})

    def do_POST(self):
        with self.server.corpus.lock:
            return self._do_POST()

    def _do_POST(self):
        if not self.host_ok() or not self.session_ok() or not secrets.compare_digest(self.headers.get("X-Local-Token",""),self.server.secret):
            return self.send_data(403,{"error":"本机请求校验失败，请刷新页面。"})
        origin=self.headers.get("Origin")
        if origin and origin!=f"http://{self.headers.get('Host')}":
            return self.send_data(403,{"error":"不接受跨站请求。"})
        route=urlparse(self.path).path
        principal=self.server.principal
        try:
            data=self.get_json()
            if route=="/api/knowledge":
                return self.send_data(200,self.server.knowledge.submit(principal,data))
            if route.startswith('/api/knowledge/'):
                return self.send_data(200,self.server.knowledge.transition(principal,route.removeprefix('/api/knowledge/'),data))
            if route.startswith('/api/maintenance-feedback/'):
                return self.send_data(200,self.server.store.maintenance_feedback(principal,self.server.corpus,route.removeprefix('/api/maintenance-feedback/'),data))
            if route=="/api/ai-work/tasks":
                return self.send_data(200,self.server.review_service.create(principal,data))
            if route.startswith("/api/ai-work/tasks/"):
                parts=route.split("/")
                if len(parts)==6 and parts[5] in {"confirm","run"}:
                    operation=self.server.review_service.confirm if parts[5]=="confirm" else self.server.review_service.run
                    return self.send_data(200,operation(principal,parts[4],data))
            if route.startswith("/api/ai-work/runs/"):
                parts=route.split("/")
                if len(parts)==6 and parts[5]=="review":
                    return self.send_data(200,self.server.review_service.review(principal,parts[4],data))
            if route=="/api/query":
                if set(data)-{"query","mode","include_archived","task_id","document_ids","version_ids","model"}:
                    raise ValueError("请求包含不支持的字段。身份与权限由服务端提供。")
                result=self.server.assistant.ask(data.get("query"),principal,mode=data.get("mode","search"),include_archived=data.get("include_archived",False),task_id=data.get("task_id"),document_ids=data.get("document_ids"),version_ids=data.get("version_ids"),model=data.get("model"))
                self.server.store.add(principal,result)
                return self.send_data(200,result)
            if route=="/api/feedback":
                if set(data)-{"request_id","kind","note","operation_key"}:
                    raise ValueError("反馈字段无效。")
                return self.send_data(200,self.server.store.feedback(principal,data.get("request_id"),data.get("kind"),data.get("note",""),self.server.corpus,data.get('operation_key')))
            if route=="/api/model-config":
                if principal.role!="engineer":
                    raise PermissionError("当前本机演示身份不能更改模型设置。")
                return self.send_data(200,self.server.settings.save(data))
            if route=="/api/build-index":
                if principal.role!="engineer":
                    raise PermissionError("当前本机演示身份不能建立索引。")
                if data:
                    raise ValueError("索引建立不接受客户端自定义路径或语料。")
                return self.send_data(200,self.server.assistant.build_vectors(principal))
            return self.send_data(404,{"error":"接口不存在。"})
        except PermissionError as exc:
            return self.send_data(403,{"error":str(exc)})
        except ConflictError as exc:
            return self.send_data(409,{"error":str(exc)})
        except ValueError as exc:
            return self.send_data(400,{"error":str(exc)})
        except ProviderError as exc:
            return self.send_data(502,{"error":str(exc)})
        except (BrokenPipeError,ConnectionResetError):
            return
        except Exception:
            return self.send_data(500,{"error":"请求未完成；请检查本机服务后重试。"})


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=0,help="0自动选择空闲本机端口")
    parser.add_argument("--profile",choices=["engineer","employee"],default="engineer")
    parser.add_argument("--open",action="store_true",help="启动后在本机浏览器打开页面")
    parser.add_argument("--local-dir",type=Path,default=ROOT/".local/assistant",help="本机资料与运行记录目录；可为隔离演示指定独立目录")
    args=parser.parse_args()
    principal=Principal("local-"+args.profile,args.profile,("DEMO-TASK-001",) if args.profile=="engineer" else ())
    server=LocalServer(("127.0.0.1",args.port),principal,args.local_dir)
    url=f"http://127.0.0.1:{server.server_address[1]}"
    print(f"知识助手本机原型：{url}  / 身份：{args.profile}",flush=True)
    if args.open:
        import webbrowser
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__=="__main__":
    main()
