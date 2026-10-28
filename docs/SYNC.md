# 飞书与 GitHub 同步记录

同步日期：2026-10-26。文档版本：v1.0。

## 飞书目录

项目根页面已整理为 [充电宝研发评审与知识助手](https://my.feishu.cn/wiki/NKZ4wE0T4iFHTLkTcfrcKR10nAe)。

- [AI Work｜整机测试报告评审](https://my.feishu.cn/wiki/UlodwHIzJidrjDkQXVvcApD1nbe)

- [内部智能客服｜知识检索与问答](https://my.feishu.cn/wiki/G5ErwipsTiq0lxkZpbvcSj8snQb)

两个分组各有 MVP、完整 PRD、知识库与 RAG 方案三份在线子文档；共用的整体总览放在项目根页面下。

## 文档对应关系

| 分类 | GitHub 维护文件 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [docs/ai-work/MVP.md](ai-work/MVP.md) | [MVP 范围](https://my.feishu.cn/wiki/Q2GnwQhJDiXzjWkmqLRccBfbneW) |
| AI Work | [docs/ai-work/PRD.md](ai-work/PRD.md) | [完整 PRD](https://my.feishu.cn/wiki/K71fwnJo8iDBy9kgkRBchCvcn0g) |
| AI Work | [docs/ai-work/RAG-and-knowledge-base.md](ai-work/RAG-and-knowledge-base.md) | [知识库与 RAG 方案](https://my.feishu.cn/wiki/Gs9Xw9YpHiVB6wknPDVcsMw7nUf) |
| 内部智能客服 | [docs/internal-assistant/MVP.md](internal-assistant/MVP.md) | [MVP 范围](https://my.feishu.cn/wiki/BXA1weYkFiBxJkkLlxwc5MaFnWf) |
| 内部智能客服 | [docs/internal-assistant/PRD.md](internal-assistant/PRD.md) | [完整 PRD](https://my.feishu.cn/wiki/YTAXwN0qBirjsKkTiMfcWe56nPc) |
| 内部智能客服 | [docs/internal-assistant/RAG-and-knowledge-base.md](internal-assistant/RAG-and-knowledge-base.md) | [知识库与 RAG 方案](https://my.feishu.cn/wiki/KHnnwa5J8i9yZzkI4gfcvDEQntf) |
| 共用 | [整体总览与 MVP](shared/product-overview-mvp.md) | [00-项目总览与整体MVP](https://my.feishu.cn/wiki/GrUkwdeLfi1Orgkrpn9cUupznid) |

## 核对记录

- GitHub 仓库 `zhujy9413-commits/powerbank-rag-agent` 已确认是 PRIVATE，文档已推送到 main。
- 飞书导入界面分别确认两批三份模块文档及一份总览上传成功。
- 飞书目录已核对：两个模块位于项目根页面下，每个模块的三份文档位于各自模块下。
- 两份 PRD 和 AI Work RAG 的正文开头、原生表格及最后章节已抽查，长文按视窗加载。
- 项目根页及两个模块入口页已补充导航和对应 GitHub 链接。
- 仓库保留原始 HTML 阅读版、Markdown 维护版和在线文档对应关系。

## 本次正文快照校验值

下表为本次导入的 Markdown 正文源文件 SHA-256。后续两端独立编辑后，应重新对齐内容并更新同步记录。

| 文件 | SHA-256 |
| --- | --- |
| `docs/ai-work/MVP.md` | `e3385d55f580ddd744f86988d8b678bbdfec044f3b1df2a8273df6457546fc3e` |
| `docs/ai-work/PRD.md` | `11aa018a3e16423d8610f72dee3d35944bca2d3ae9c87dda0091272fd3aa5088` |
| `docs/ai-work/RAG-and-knowledge-base.md` | `2e4e6c116b91db1925373b10511120128ec22f72110eaaefbf372edfb7aef3de` |
| `docs/internal-assistant/MVP.md` | `802eaeef8b73633741601ed02c090d9907878cb1a0d79bdee14d37a38168c175` |
| `docs/internal-assistant/PRD.md` | `87460ae658ff6750df64cb1a59eb125314abe33cb0e32caef58350376db32661` |
| `docs/internal-assistant/RAG-and-knowledge-base.md` | `2e859a9b8317221f667e88dbbf6ed237bd0d2de875acb8bd31d5dc1dbeeffc2d` |
| `docs/shared/product-overview-mvp.md` | `ace14564d0bb3e6770c0af7c5645daea156508fb0ddb6b30c3215d4ef7c037f6` |

## 2026-10-27 首批样本包 v0.1

新增内容使用5份官方资料摘要和明确标注的模拟资料。未使用公司原始资料；公开资料不含标准全文。24题问答开发集与12项报告参考标注均由作者拟定，专业复核待完成，未运行模型评测。

| 分类 | GitHub 维护文件 | 飞书在线文档或原件 |
| --- | --- | --- |
| 共用资料 | [资料清单与公开来源](shared/bootstrap-materials.md) | [01-首批知识样本与资料清单](https://my.feishu.cn/wiki/RGJWwDAjji4laIkaBNUcroAlndd) |
| AI Work | [模拟规格、报告与参考标注](ai-work/sample-pack.md) | [04-模拟报告与逐项标注](https://my.feishu.cn/wiki/KqKQwhIzsi2KQukyfh2czZAvnZd) |
| AI Work | [四页模拟PDF](../output/pdf/SYN-TR-001-R1.pdf) | [SYN-TR-001-R1.pdf](https://my.feishu.cn/wiki/CdWGwp7NviGQQgkiJCgc5YOhnab) |
| 内部智能客服 | [知识样本与问答开发集](internal-assistant/sample-pack.md) | [04-知识样本与问答评测集](https://my.feishu.cn/wiki/AATmwtAHsiJ8c3kvQIpcUGv6n7c) |

可导入的JSON/JSONL及完整来源登记保存在[样本包](../data/bootstrap-v0.1/README.md)。飞书在线阅读版保留对应GitHub维护源，导入文档与维护源的正文一致；并非自动双向同步。

| 在线阅读版维护源 | 本次导入正文 SHA-256 |
| --- | --- |
| `docs/shared/bootstrap-materials.md` | `5487a4ed45a04548ebc8cc6b54b35256d67499794398625beea0e9b9bb868990` |
| `docs/ai-work/sample-pack.md` | `87e719c20db4f3da1627ff339158a29dfd1fcb37ac350c08dc47de40765b6629` |
| `docs/internal-assistant/sample-pack.md` | `1a90d83bb5deb1843f086ccedb349e21b772d5fdc931e73b370f9bb4320d43cc` |

本地数据校验已通过，检查范围包括24份样本文件校验值、证据引用、角色与任务范围、版本状态、10项检查覆盖、数值换算、4页PDF文字及本地阅读链接；四页PDF已逐页渲染检查。校验不代表RAG效果或专业验收。

## 2026-10-27 单轮问答原型 v0.1

应用代码、运行入口、功能测试和关键词检索基线同步到私有GitHub仓库。19项自动测试通过；页面搜索、引用查看、反馈、缺依据与归档版本行为已检查。真实百炼/DeepSeek生成和Embedding调用仍待本机配置后验证，未对外部署。

| 分类 | GitHub 维护源 | 飞书文档 |
| --- | --- | --- |
| 内部智能客服 | [原型与模型接入说明](internal-assistant/prototype-v0.1.md) | [05-单轮知识问答原型与接入说明](https://my.feishu.cn/wiki/JjGuwIRVziJB9nkzAlgcoUj9nQc) |
| 共用方法 | [工作流与验证方法补充](shared/workflow-verification-notes.md) | [02-工作流与验证方法补充](https://my.feishu.cn/wiki/S6z8wBu7Ai19fHkhWXKcYtxOnDc) |

原型说明导入后在原页面更新至19项测试，并追加提示词及规范化请求摘要方法；保留原有文档位置和格式。方法补充仅吸收用户既有项目的工作流与验证经验，没有复制其业务数据、认证配置或改变当前产品范围。

本机密钥、向量缓存和运行记录均位于忽略的`.local/`目录，不纳入仓库或飞书正文。开发集检索结果保存在`eval-results/retrieval-baseline-v0.1.json`，不能当成回答准确率或业务收益证明。

## 2026-10-27 百炼真实接口验证

接入`qwen-flash`及`text-embedding-v4`，建立26块向量索引，保留24题开发集的初测与全部复测。25项功能及边界测试通过；最后一轮检索命中41个必要证据组，但有1次错误引用被拦截及角色、时点等语义问题，未宣布业务验收通过。

| 分类 | GitHub维护源 | 飞书文档 |
| --- | --- | --- |
| 内部智能客服 | [真实接口验证与问题记录](internal-assistant/live-validation-v0.1.md) | [06-百炼真实接口验证与问题记录](https://my.feishu.cn/wiki/PPdkwtH45iFHsakhbJ3cYxVPnyh) |

新报告通过Markdown导入为在线文档，已核对内部智能客服下的目录位置、正文开头、原生表格及末尾复现命令。报告导入正文SHA-256：`e5266fb92316c2cb4a2d8f70e67d5a945a26019053ed9724394a4604ff08d0b6`。

原05接入说明在原页面更新了接入状态、接口验证表、25项测试、复现命令和下一步，并链接新报告；共用02方法补充也更新了历史与当前验证状态。在线链接使用飞书地址，GitHub维护版使用仓库内链接，未宣称这两份局部更新后的页面是字节相同的Markdown快照。

实际输出与中间失败保存在`eval-results/live-*.json`，当前同版关键词对照为`retrieval-keyword-v0.4.json`。本机密钥、业务空间接入地址和运行数据库均未同步。

## 2026-10-27 角色与引用修复回归

本轮修复输入输出角色混淆、同数值导致的摘要端口错配，并采用请求内来源目录、必要记录来源补充和一次校正。39项本地回归通过；最终24题命中41个必要证据组，18个生成请求均通过结构和引文校验，其中1个经校正。6次重点重复运行也通过，2次经校正。没有把这些结果表述为专业回答准确率。

| 分类 | GitHub维护源 | 飞书文档 |
| --- | --- | --- |
| 内部智能客服 | [角色范围与引用修复回归](internal-assistant/role-citation-regression-v0.1.md) | [07-角色范围与引用修复回归](https://my.feishu.cn/wiki/BCwkw8ya7iuBATk4B4ncdGmen9c) |

导入正文SHA-256：`e7115cac1a01b7c601263890f2f9ba46bc739c322b5352bd2026632a19a38843`。07位于内部智能客服目录下。实际输出、校正前候选、来源补充和中间失败保留在`eval-results/live-role-citation-*.json`及`live-citation-repeat-v0.9.json`；最终代码与实测的三份应用源码摘要已核对一致。

已核对07的开头、原生表格、末尾说明与复现命令；05原接入说明更新39项回归、最终结果和引用处理方式，06首次验证记录保留历史数据并添加07入口。在线文档使用飞书链接，仓库版使用对应维护文件链接。

## 2026-10-28 AI Work逐项评审原型

固定模拟PDF模板内已实现上传与解析、输入与依据确认、10个预期单元逐项核对、摘要及依据一致性检查、人工复核和Excel导出。62个自动测试方法通过（AI Work新增23个，另有边界子用例）。1份报告的12项草拟参考标注在3次运行中共36次结果、必要来源及记录对照均一致；专业核实与独立业务测试尚未完成。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [原型与测试报告](ai-work/prototype-and-validation-v0.1.md) | [05-逐项评审原型与测试报告](https://my.feishu.cn/wiki/PKLtwf0CFiPC2GkafY5cvWFIn7e) |
| AI Work运行产物 | [三次最终运行](../eval-results/ai-work-review-final-v0.2.json)、[完整回归记录](../eval-results/ai-work-tests-v0.1.txt) | 测试口径、结果与复现步骤保留在05正文，原始机器结果链接至私有GitHub |
| AI Work导出 | [模拟评审Excel](../outputs/ai-work-v0.1/report-review.xlsx) | 05提供私有GitHub下载链接，未另建飞书电子表格 |

05采用Markdown原生导入，位于AI Work分组（目录位置6,4,0,5）。已核对开头、原生表格、62项回归和36次参考对照、末尾运行命令及边界说明。AI Work入口与原01—03文档在原页面补充当前实现状态和05入口，保留设计正文。在线状态说明与仓库版位置、链接格式可不同，并非自动双向同步。

正文导入SHA-256：`a9308f00f5fcb4cca35eda9db1a1584a57274820493073bd6e1a3f51e53c4c22`。
Excel SHA-256：`33f4783672a5356aed56f463b20e9c80908d2ccf49059a77dfa8840ee4c9fece`。

最终运行记录保留执行引擎、导出器、接口、界面、测试与评测脚本摘要，已与最终源码核对一致。中间开发运行保存在`ai-work-review-intermediate-v0.1.json`；其导出摘要属于当时的临时导出，当前基线Excel以final-v0.2为准。本机任务数据库、真实密钥和模型接入地址未同步。

## 2026-10-28 PDF模板变体与条件冲突回归 v0.2

新增24份受控模拟PDF、51页，补充换列、换行、跨页、未映射和条件异常，并修复解析遗漏诊断与条件不匹配时仍比较的问题。最终同一批PDF上旧引擎满足4/24个场景期望，新引擎满足24/24个；可支持文字记录按固定180条对照，145条增至180条一致。指定阻塞行为从1/16变为16/16。80项自动测试通过，新增18个测试方法；原四页控制报告三次12项参考及必要来源一致。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [PDF模板变体与条件冲突回归](ai-work/pdf-variants-and-conditions-v0.2.md) | [06-PDF模板变体与条件冲突回归](https://my.feishu.cn/wiki/LgWKwZP2fiD27NkBnXicNEDZni8) |
| 样本与原始结果 | [24份PDF样本清单](../data/pdf-variants-v0.1/cases.json)、[最终对照结果](../eval-results/pdf-variants-final-v0.5.json) | 06说明样本、固定分母、失败及阻塞口径，并链接私有GitHub原始产物 |

06通过Markdown原生导入，位于AI Work分组，目录位置6,4,0,6。正文源SHA-256：`31decd05ca483adbf0966e4a872ec6cc082955486bcfd9094e36af0fd63ad084`。已核对开头、原生表格、80项回归与修复前后数字、末尾复现及范围说明。AI Work入口、原01—03和05在原页面补充v0.2状态及06入口，保留需求与历史记录；在线状态段和仓库格式可不同，不是自动双向同步。

初批字体未嵌入的样本经渲染发现后重建；内容与期望不变。最终比较使用相同的最终PDF清单，基线为既有提交acd883a中的引擎。早期运行保留为中间记录，最终以v0.4/v0.5为准。180条不包含图片文字或无法映射内容；24/24包含应阻塞、应拒绝场景，不能称为报告通过率或真实业务准确率。

任务数据库、密钥及模型接入地址未同步。原始PDF、参考期望、实际输出、开发测试日志和控制样本Excel均为明确的模拟材料。未完成真实标准、OCR、任意PDF或专业验收。
