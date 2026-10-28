"""Small application XLSX exporter: all external strings use inlineStr, never formulas."""
from io import BytesIO
import math
import re
import json
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED

from .review import RESULTS, DISPOSITIONS

NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def workbook_rows(run):
    snapshot = run["snapshot"]
    report = snapshot["report"]
    scope = [["项目", "本次范围与状态"], ["数据性质", "全部为软件流程模拟材料，不作为真实标准或认证结论"],
             ["任务 / 运行", run["task_id"]+" / "+run["run_id"]], ["输入版本", run["revision"]],
             ["报告", report["filename"]], ["报告SHA-256", run["report_sha256"]],
             ["确认快照SHA-256", run["input_sha256"]], ["生成时间UTC", run["created_at"]],
             ["任务状态", "处理失败" if run["state"] == "failed" else "复核完成" if run["state"] == "review_complete" else "待人工复核"],
             ["待复核项目", run["pending_reviews"]], ["历史运行", "是" if run["historical"] else "否"],
             ["产品与范围", "PB-DEMO-01；A1、C1；5 V输出角色；端口短路保护已有记录"],
             ["采用依据", "SYN-SPEC-PB01-RevB / SYN-QA-SC-1.0"], ["规则版本", snapshot["rule_version"]],
             ["知识发布", snapshot["publication"]], ["配置内单元", run["configured_units"]],
             ["一致性项", run["consistency_items"]], ["未配置", "、".join(run["unconfigured"])],
             ["结果解释", "未发现问题不等于人工通过；冲突、缺证、失败、未配置不得计为通过。"],
             ["复核解释", "复核完成表示每项已记录处置，可包含暂无法确认；不表示整改关闭或产品放行。"]]
    if run.get("error"):
        scope.append(["失败原因", run["error"]])
    audit=report.get("parse_audit",{})
    scope.append(["解析覆盖", f"候选记录{audit.get('candidate_count','未记录')}；已映射{audit.get('captured_count','未记录')}；未映射{audit.get('unresolved_count','未记录')}；诊断项{len(audit.get('issues',[]))}。映射成功不表示数值及条件已核实。"])
    scope.append(["报告测试条件",json.dumps(report.get("global_conditions",{}),ensure_ascii=False)])
    items = [["检查项", "端口", "项目", "执行状态", "系统结果", "要求（模拟）", "比较与发现", "条件性", "人工复核", "复核理由"]]
    evidence = [["检查项", "来源类型", "来源身份", "版本 / 页码", "原文证据或解析修正", "报告SHA-256 / 来源块ID"]]
    for item in run["items"]:
        rev = item["review"]
        explanation=item["explanation"]
        if item.get("record_conditions"):
            explanation+="\n记录条件："+json.dumps(item["record_conditions"],ensure_ascii=False)
        items.append([item["item_id"], item["port"], item["title"], {"completed":"已检查","not_checked":"未检查","failed":"失败"}.get(item["execution"],item["execution"]), RESULTS[item["result"]],
                      item["requirement"], explanation, "是" if item["conditional"] else "否",
                      DISPOSITIONS[rev["disposition"]], rev["reason"]])
        for c in item["basis"]:
            evidence.append([item["item_id"], "模拟依据", c["document_id"], "版本"+c["version"]+" / "+c["section"], c["text"], c["chunk_id"]])
        for ref in item["report_evidence"]:
            evidence.append([item["item_id"], "报告提取原文", report["filename"], "PDF第"+str(ref["page"])+"页", ref["quote"], ref["sha256"]])
        if item.get("correction"):
            c = item["correction"]
            evidence.append([item["item_id"], "人工解析修正", c["actor"], c["at"], c["value"]+"；原因："+c["reason"], run["input_sha256"]])
    history = [["检查项", "版本", "处置", "理由", "操作者", "时间UTC"]]
    history += [[r["item_id"], r["version"], DISPOSITIONS[r["disposition"]], r["reason"], r["actor"], r["at"]] for r in run["review_history"]]
    if len(history) == 1:
        history.append(["尚无人工复核记录", "", "", "", "", ""])
    return [("任务与范围", scope, [27, 112]), ("逐项检查", items, [20, 9, 18, 15, 23, 40, 64, 11, 23, 45]),
            ("依据与原文", evidence, [20, 20, 36, 30, 95, 72]), ("复核记录", history, [20, 9, 23, 70, 24, 37])]


def col(n):
    value = ""
    while n:
        n, r = divmod(n-1, 26)
        value = chr(65+r)+value
    return value


def safe_text(value):
    return escape(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(value)))


def export_xlsx(run):
    sheets = workbook_rows(run)
    out = BytesIO()
    with ZipFile(out, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'+''.join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1,len(sheets)+1))+'</Types>')
        z.writestr("_rels/.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", f'<workbook xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>' for i,(name,_,_) in enumerate(sheets,1))+'</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))+f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr("xl/styles.xml", f'<styleSheet xmlns="{NS}"><fonts count="2"><font><sz val="11"/><name val="Arial"/><color rgb="FF203831"/></font><font><b/><sz val="11"/><name val="Arial"/><color rgb="FFFFFFFF"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF274C40"/><bgColor indexed="64"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="center" horizontal="center" wrapText="1"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
        for i, (name, rows, widths) in enumerate(sheets,1):
            xml = f'<worksheet xmlns="{NS}"><dimension ref="A1:{col(len(widths))}{len(rows)}"/><sheetViews><sheetView workbookViewId="0" showGridLines="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>'+''.join(f'<col min="{n}" max="{n}" width="{w}" customWidth="1"/>' for n,w in enumerate(widths,1))+'</cols><sheetData>'
            for r, row in enumerate(rows,1):
                # Count CJK approximately as two Latin characters; accommodate explicit PDF line breaks.
                line_counts = []
                for value, width in zip(row, widths):
                    lines = str(value).splitlines() or [""]
                    line_counts.append(sum(max(1, math.ceil(sum(2 if ord(ch)>255 else 1 for ch in line)/max(1,width-3))) for line in lines))
                height = max(30, max(line_counts)*16+10)
                xml += f'<row r="{r}" ht="{min(409,height)}" customHeight="1">'
                for c, value in enumerate(row,1):
                    addr = f'{col(c)}{r}'
                    if type(value) in {int,float}:
                        xml += f'<c r="{addr}" s="{1 if r==1 else 0}"><v>{value}</v></c>'
                    else:
                        xml += f'<c r="{addr}" s="{1 if r==1 else 0}" t="inlineStr"><is><t xml:space="preserve">{safe_text(value)}</t></is></c>'
                xml += '</row>'
            xml += f'</sheetData><autoFilter ref="A1:{col(len(widths))}{len(rows)}"/></worksheet>'
            z.writestr(f"xl/worksheets/sheet{i}.xml", xml)
    return out.getvalue()
