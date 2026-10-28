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

## 2026-10-28 新样本留出评测 v0.1

20份新模拟PDF、40页完成核验后，在提交`2b08f788fd3600374357440628a4bfeab25e58e2`冻结；被测应用固定为`cde690ee6fbf6b60a3ef3c7444eeacba3c28cafb`。首次满足12/20个冻结场景期望，文字记录匹配181/193条，58项行为断言满足36项，指定35项停止断言满足16项。86项回归通过（原有80项加6项评分器自检），不是新样本全通过。应用、标签和首次结果没有据此调整。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [新样本留出评测与问题清单](ai-work/holdout-evaluation-v0.1.md) | [07-新样本留出评测与问题清单](https://my.feishu.cn/wiki/IApXw3nDkiNhwTkl4QYcauv6n9g) |
| 样本与首次结果 | [冻结协议与样本包](../data/review-holdout-v0.1/README.md)、[首次完整结果](../eval-results/review-holdout-first-run-v0.1.json)、[问题分析及标注复核](../eval-results/review-holdout-analysis-v0.1.json) | 07保留完整口径、20个场景结果、P0/P1清单及复现步骤；机器结果、PDF原件与测试日志通过私有GitHub链接提供 |

07采用Markdown原生导入，目录位置`6,4,0,7`，属于AI Work分组。正文源SHA-256：`1937033232543a9c7aaa742132af1005440c31dce77a3ab8b4fa3728c6fcbc57`。已核对开头、结果原生表格、问题优先级、HO-17标注复核、末尾复现与原始结果链接；重新加载确认持久保存。

首次结果SHA-256：`183e730d8d436d54614b873faf527ff90f2096531e61babe49cba3984fe94e7d`。冻结协议SHA-256：`54229c70a7a10e04ad3d88939936d7a10c6c912594e88a213473b698d9936fd9`。当前知识语料与应用源码均保持原冻结版本，模型请求为0。沙箱端口限制导致的回归失败与允许本机绑定后的86项通过日志分别保留。

4个场景中的8个核对单元在应停止时显示未发现问题；另有条件维度和样机对象未支持。HO-17既有评分断言过窄，也有摘要单位诊断误绑定，单独说明，不事后改标签重算分数。该轮由同作者构造并知晓实现，是时间留出评测，不是外部独立测试、盲测或专业验收。若用于后续修复，本包即转为开发/回归集。

AI Work入口与01-MVP、02-PRD、03-RAG在原页面补充本轮分数、已发现风险和07入口，保留需求基线及原有80项开发回归历史。入口和三份原文均经重新加载或重访确认保存。浏览器中断的一次状态更新已用新只读会话核对，原写入实际保存，未重复提交。在线状态段位置与Markdown维护版可不同，并非自动双向同步。

## 2026-10-28 三个P0修复与第二批新样本 v0.3

未知或缺失编号进入候选审计；实际绘制图片尚未核验时停检；未绑定脚注、局部条件不能继承全局条件。102项回归通过，旧24份模板满足24/24原期望，旧5个P0失败场景满足5/5，原报告三次36项结果及来源一致。旧HO样本已转为开发/回归集，原始首次12/20保持不变；复测19/20，HO-17仍为P1及标注待复核项。

修复应用先冻结于`3b610efd128689e4a7fdca52ced14c3809091545`，之后另建20份新PDF、40页，在`91f96a7fca3402ab53fe12a24bee3569eece7878`冻结标签与评分。新批首次20/20满足场景期望，124/124行为、88/88停检断言满足；文字记录190/205，15条未知编号未自动映射但均提示并停检。图内3条记录未OCR；装饰图也会整体停检，未绘制资源控制正常。样本为同作者、知晓实现的时间留出，非外部独立或专业验收。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [P0修复回归与第二批留出评测](ai-work/p0-fix-and-holdout-v0.3.md) | [08-P0修复回归与第二批留出评测](https://my.feishu.cn/wiki/LLVlwPzloiS4xMkgvmvcT3QAnfe) |
| 新样本及原始结果 | [冻结样本与预设口径](../data/p0-holdout-v0.1/README.md)、[第二批首次结果](../eval-results/p0-holdout-first-run-v0.1.json)、[102项日志](../eval-results/p0-regression-final-v0.3.txt) | 08保留完整口径、修复、回归、首次分数、剩余P1与复现步骤；原件及机器结果链接到私有GitHub |

08在AI Work分组下，目录位置`6,4,0,8`，Markdown原生导入源SHA-256：`6916f1e43990150de73aa8fd60e1f02f04626cd66f66ac2773c157e65a98198d`。新批首次结果SHA-256：`cdcad47f6201d0cef5d0db34df18cc477159568ab6cf112c596c0f8d78fcea65`，冻结协议SHA-256：`0845e20db8ce30ab2363ea8f7f209f9ccec6a8a5fca49ff65b43a06cbb1b5b60`。

本机53754已重启加载v0.3；回归任务AW-86b05223194e、RUN-261337be1564的图片警告、10项停检、导出成功与刷新保留已核对，证据摘要见`eval-results/p0-ui-validation-v0.1.json`。现有任务、设置、密钥及数据库均保留，未纳入GitHub或飞书；旧解析快照须重新导入。新批首次结果后应用及标签未调整，模型请求为0。

08的开头、原生回归/新批结果表、末尾边界及复现链接已核对，重新加载确认保存。01-MVP、02-PRD、03-RAG在原页面追加v0.3状态及08链接，均逐份重新加载确认，保留设计基线和旧首次分数。在线说明段位置与Markdown源可能不同，不是自动双向同步。

AI Work入口的v0.3说明、08链接及03—08导航也已更新并刷新核对保存。导入菜单改用原生键盘展开后仅上传一次；父页导航和暂存占位节点导致的定位超时均先读状态后核对，没有重复创建08或覆盖其他文档。

## 2026-10-28 跨行摘要与单位归属P1修复 v0.4

摘要提取和逐行审计共用片段归属，同页连续两三行的ms/s摘要不再重复报孤立单位；摘要相邻条件绑定摘要，跨页与多候选单位不猜测。129项自动测试通过，旧24份模板24/24、上一轮P0样本20/20、HO-17单列5/5修复断言及原报告36次参考对照均满足。旧HO原标签复测仍19/20，HO-17标签过窄单列说明，旧首次12/20未改。

应用冻结于`48c4893643fe6a1eb30f540005a14d9ac30ce52a`，新20份PDF、40页及标签评分冻结于`78758ded94fa522fa34eb8e9d481c02d10dafcd9`。新批首次20/20满足预期，文字200/200、行为166/166、指定停检46/46、P1六组每场景检查120/120满足；17个独占单位行的完整归属多重集一致，552条评审引用及54条摘要/单位片段核对有效。模型请求0。同作者时间留出，20份变体共享10条基础记录，不是外部独立、盲测或专业验收。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [P1修复回归及新样本评测](ai-work/p1-fix-and-holdout-v0.4.md) | [09-P1跨行摘要与单位归属修复评测](https://my.feishu.cn/wiki/RcHjw5fjai8eiEkJdHmci8Qmnje) |
| 新样本及结果 | [冻结样本包](../data/p1-holdout-v0.1/README.md)、[首次完整结果](../eval-results/p1-holdout-first-run-v0.1.json)、[129项日志](../eval-results/p1-regression-final-v0.2.txt) | 09保留结果口径、修复、回归、首次评测、边界及复现步骤，原件和机器结果链接私有GitHub |

09导入在AI Work分组下，目录位置`6,4,0,9`。Markdown导入源SHA-256：`49c0f5cec4d091bd93406e995e2eda38c56e1a638fe9efdc04ed8cff84ba1021`。首次结果SHA-256：`bf90db16d90178544cc39febe59b23f8468b085c37919103c844c38741417c5b`。冻结协议SHA-256：`516a6061d94445f68b85f7e6dcf446d2b61fa0cedbe3fd50e3d28dcef8ab82de`。三批冻结资产哈希和前两批首次结果均核对未变。

本机53754加载v0.4，旧HO-17重导后的任务AW-a0ef3c9df573、运行RUN-6325dda2f6e3验证摘要137ms、A1恢复方式不被误拦截、准确跨行原文、Excel导出及刷新持久性。摘要见`eval-results/p1-ui-validation-v0.1.json`。任务、密钥、模型设置和数据库未同步；旧解析快照须重导。

09的开头、原生修复/结果表、末尾复现命令和原始结果链接已核对，刷新确认持久保存。AI Work入口及01-MVP、02-PRD、03-RAG均在原页更新v0.4说明和09入口，并经刷新或重访核对；历史段落保留。PRD保存提示超时及RAG加载/核验中断均先只读核对，确认写入已保存，没有重复追加。侧栏新增按钮自动滚动导致遮挡，查明实际命中位置后成功打开菜单，仅上传一次09。在线状态段位置与Markdown维护版可以不同，不是自动双向同步。

## 2026-10-28 完整流程技术验收 v0.4.1

使用三份已消耗的正常、摘要冲突及资料缺失模拟报告，完成上传、依据确认、运行、证据查看、复核、导出、恢复及版本修订流程。页面修复条件性结果筛选遗漏、固定RevA说明、索引摘要/原文混淆和保存期间操作问题。133项回归通过，3场景51/51项HTTP检查通过；页面保存36项明确标为流程验收模拟的处置。复核后原冲突和缺证保留，三任务刷新恢复与新旧运行隔离已核对。

受控模拟流程技术验收通过，使用者可用性、专业规则和业务效果验收待完成。未记录人工总耗时，不计算省时率；未启用真实标准或企业部署。页面v0.4.1，解析器及规则继续v0.4，原三批冻结资产、知识语料及旧首次分数核对未变。本轮0模型请求。源代码、最终HTTP与页面结果及原生Excel同步私有GitHub，临时库和本机任务/模型配置未同步。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [完整流程验收与试用记录](ai-work/workflow-acceptance-v0.4.1.md) | [10-完整流程验收与试用记录](https://my.feishu.cn/wiki/PYsWwxwn2iQIxZkZ6yPcnwjinyc) |
| 实测证据 | [最终HTTP结果](../eval-results/workflow-http-v0.4.json)、[页面与恢复记录](../eval-results/workflow-ui-v0.1.json)、[133项回归](../eval-results/workflow-regression-v0.3.txt) | 10保留验收结果、4个问题及修复、MVP分层判断、人工试用记录表和复现步骤 |

10通过Markdown原生导入，位于AI Work下`6,4,0,10`。导入源SHA-256：`b5f3421097cbb630053738705084fe44b7a4681ecf4c3060657d3487719ac7e4`。最终HTTP结果SHA-256：`f9e051af4f845580ddd3a45ec45a7cc4bcc3bb34d20c0a9987c2da38097389fe`。最终页面记录SHA-256：`5fd841e9abe3ecb30bb83400cf49bb067a2a82eb3eecd4cade8c59e33b4a4392`，含最终8份应用源码摘要。此前失败日志与中间结果保留，以v0.4 HTTP、v0.3回归日志为准。

10的开头、原生技术结果表、人工试用待填写表、末尾复现与原始结果链接已核对，刷新确认保存。AI Work入口及01-MVP、02-PRD、03-RAG已局部补充v0.4.1和10入口，逐份重访确认，保留设计正文及历轮首次分数。导入菜单未打开时先核对无10节点，再按实际命中位置开启，仅上传一次；长文按视窗加载，屏外结果通过滚动核对。在线状态段位置可与Markdown维护版不同，不是自动双向同步。

## 2026-10-28 正常r3代理代操作走查 v0.4.2

按用户授权代做正常FLOW-01的r3身份、范围、依据、逐项证据、保存、恢复和导出核对。12项当前处置均明确标为代理代操作走查；旧r2结果与历史保持。发现无未决项仍提示含未决的P2显示问题，页面v0.4.2按实际未决数展示。正常r3和含11项未决的冲突运行在浏览器核对通过，133项回归通过。解析器、规则、语料与旧首次分数保持，三批冻结包88个资产哈希匹配；模型请求0。

代理曾将5条C1理由页码写错，已通过版本2更正为第2页，17条历史完整保留；应用原有引用页码正确。实际应用Excel四张表的结果、最新理由、引用和历史核对一致；只读渲染查看5个范围，未在原生Excel中做人工阅读验收。宽表及条件JSON记录为后续体验改进项。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [10正文末节代理走查补充](ai-work/workflow-acceptance-v0.4.1.md) | [10-完整流程验收与试用记录](https://my.feishu.cn/wiki/PYsWwxwn2iQIxZkZ6yPcnwjinyc)原页补充 |
| 本轮证据 | [完整机器结果](../eval-results/delegated-walkthrough-v0.1.json)、[133项日志](../eval-results/delegated-walkthrough-regression-v0.1.txt)、[实际应用Excel](../outputs/delegated-walkthrough-v0.1/FLOW-01-r3.xlsx) | 10末节列出上述私有GitHub链接，保留原有技术验收和人工试用表 |

飞书10的r3状态及人工试用说明已局部更新，末尾追加代理身份、12项核对、P2修复、回归、页码文字更正、阅读观察与原始结果链接。刷新后分段读回确认持久保存，21个待填写单元及3个未测量耗时单元保持；未代填实际使用者体验，不声称专业通过或省时收益。屏外编辑焦点导致的一次段落拼接已先只读核对再修正，验证阶段对已卸载段落的读取超时后改为按视窗取值，没有重复追加正文。在线排版与Markdown维护源不完全相同。

当前10维护正文 SHA-256：`f0348fb83958e56b29b089199e03426dd545d56f6620ae23e181381687c336b3`。

本轮机器结果 SHA-256：`14f5acc8798edf8da9d9b889716cb3bdc2263df90b63c484395da4924e9f7018`。

实际应用Excel SHA-256：`9bdc51c6404b1859759ef53214116ef9c4e3dfb1701b2fbbb15fcb9530b2ce21`。

本机任务、数据库、模型配置及密钥未同步。原生Excel保持应用导出的原始字节；没有以另行制作的表格替代产品导出。

## 2026-10-29 AI Work需求实现与验收对照

以页面v0.4.2、代码73abf7a为基线，核对完整PRD的15节、11个AW用例和10个KB用例。36个核对单元为14项已实现、14项部分实现、8项未实现，数量不换算完成率。列出10组缺口，区分当前阶段的P1/P2、真实试点前置条件和范围外候选。下一轮优先处理停用依据后历史任务/结果/PDF也被拦截的问题；AI Work目前是固定依据映射、任务内BM25及字段扫描、确定性规则说明，未将客服的向量/生成能力计为本模块已实现。

本轮新增7项临时模拟库观察，另以144项文档结构、来源哈希、符号与映射一致性校验核对成果。144项不计作应用功能测试；原133项回归及51项HTTP结果作为既有证据引用，应用未改且未重跑全量回归。本轮模型请求0，真实业务与专业验收仍待完成。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [需求实现与验收对照](ai-work/prd-implementation-audit-v0.1.md) | [11-需求实现与验收对照](https://my.feishu.cn/wiki/HHpMw4259ihzjlkH1XrcAZgRn6c) |
| 本轮证据 | [结构化对照](../eval-results/prd-implementation-audit-v0.1.json)、[7项隔离观察](../eval-results/prd-implementation-audit-probes-v0.1.json)、[文档一致性检查](../eval-results/prd-implementation-audit-validation-v0.1.json) | 11含完整逐项表、21个用例映射、缺口排序及23条证据；机器结果链接私有GitHub |
| 同步核对 | [飞书原生表格读回记录](../eval-results/prd-implementation-audit-feishu-v0.1.json) | 原生导入在AI Work下6,4,0,11，刷新后逐段核对36项、21个用例、10组缺口、23条证据及8张表格完整；已查看表格换行，宽表可收起大纲或横向查看 |

11维护正文 SHA-256：`4fd1c9c1fa22474c85e62c91c189e16d3efba3ef3e118afc00d478083f193c73`。

11原生导入源 SHA-256：`6852c98897e53b62a73f04525e154493b117f5533ef8a68fdb52856148eb7a10`。

结构化对照 SHA-256：`572a251662c4725fed07e38cc9fc7a16a9a88daabe14f6c7d84c8674686d4981`。

本轮隔离观察 SHA-256：`0c66b97f56c55ddea16bcd333a3eafc74b67b4921ff0c24495b3a4f47227a786`。

本轮不改PRD v1.0设计正文、应用、知识包、冻结样本或旧首次成绩；本机任务库、模型配置、密钥与临时库未同步。飞书未提供专用连接器，使用原生Markdown导入；菜单展开和任务中断均先读当前状态，没有重复上传或重复创建11。

AI Work入口及01-MVP、02-PRD、03-RAG均在原页补充11链接并逐份重访确认，原设计正文与旧首次12/20仍保留。MVP连续切页后新注释未保存，已先读回确认缺失，再等待“保存中...”结束后原页刷新核对；PRD刷新超时和一次浏览器任务中断均先核对实际状态，最终四页持久读取通过，没有重复追加正文或重建11。线上说明位置与Markdown维护源可不同。

## 2026-10-29 停用依据历史访问修复 v0.4.3

G01已在受控模拟范围内修复。当前权限保留时可读取历史任务、PDF、运行与导出，依据当前状态独立显示；停用/归档/格式或模拟身份改变均阻止新检查。当前来源权限撤销或来源记录缺失时仍拒绝访问，403后页面清空旧结果。原任务快照、数值结果、复核历史及旧运行哈希保留。

最终源码141个自动测试方法、35项专项HTTP、三类报告51项既有流程检查全部通过；页面走查有效、停用、撤权与恢复，并补测无整页刷新时的状态更新及导出403清理。三批88份冻结资产哈希一致，旧首次分数与原审查JSON未改。模型请求0，专业和业务验收待完成。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| AI Work | [修复与回归报告](ai-work/basis-history-access-v0.4.3.md) | [12-停用依据历史访问修复与回归](https://my.feishu.cn/wiki/POLxwDj3ci8DHJkVjGYcmCOLndg) |
| 原始结果 | [专项HTTP](../eval-results/basis-history-access-v0.4.3.json)、[完整流程回归](../eval-results/workflow-http-v0.4.3.json)、[141个测试日志](../eval-results/basis-history-access-regression-v0.4.3.txt)、[校验摘要](../eval-results/basis-history-access-validation-v0.4.3.json) | 12中说明固定范围及证据链接 |
| 页面与同步 | [页面记录](../eval-results/basis-history-access-ui-v0.4.3.json)、[飞书读回记录](../eval-results/basis-history-access-feishu-v0.4.3.json) | 12已原生导入AI Work子目录6,4,0,12，读到末尾、核对2张原生表格、刷新确认保存，并检查表格换行 |
| 实际导出 | [停用依据历史Excel](../output/xlsx/basis-history-access-v0.4.3/disabled-basis-history.xlsx) | 12链接私有GitHub原文件，未另行重制电子表格 |

原11、AI Work入口、MVP、PRD和RAG均补充v0.4.3状态与12入口，并逐页等待保存、刷新核对。原11的14/14/8保留为v0.4.2基线，没有重算或覆盖审查结果。批量更新因PRD没有符合条件的无链接长段落而停止，先只读确认MVP已保存、PRD未改，再分别在PRD和RAG的独立说明段落补齐；未覆盖含旧首次成绩及链接的历史段落。在线说明位置与Markdown维护源可以不同。

本机服务已加载最终引擎，原正常报告r3仍有12项、0项待复核、17条追加历史；临时测试页和服务已关闭，原应用与飞书结果页保留。GitHub仓库已重新核实PRIVATE。本机数据库、模型配置和密钥未同步；未提供企业登录或管理者发布界面。

本轮关键产物SHA-256：

- 12维护正文：`60e93e87f64f4babe17c545056167116a6bb10dcdfd4dbe1f569df4338f2ab63`。
- 12原生导入源：`b61c037bf96805a081ac42e60df6558c7d59ca7ba2e91e6861a31c64790ceca0`。
- 最终专项HTTP：`fad7b138046af24d037a5482f87329282039d4f4567b94f54dc504d86df145b4`。
- 最终验证摘要：`f7b36be7abdfd3e45fd2f38b5268dbef977a798099922872e4d4793f5cbc6a84`。
- 实际历史Excel：`1b5557526e48f1210a86001b29ca29b506c88a6035d8d6e44ca2d52b465810c9`。

## 2026-10-29 AI Work RAG增益验证方案 v0.1

完成实验范围、五组对照、48项待制作场景和验收门槛。基线固定为页面v0.4.3、提交2a582e2，保留固定依据映射、全页扫描及原规则；A1/A2分别增加关键词/混合补证据，A3/A4在各自证据上增加模型说明，分别识别贡献。范围仍为PB-DEMO-01、A1/C1、5 V输出、单口短路保护。

场景为36个内容报告及12个离线权限/异常场景，开发16、留出32；尚未制作新PDF、冻结新样本或执行实验。九项验收分安全、原结果/引用保护、证据召回、配对净增、说明、时延与成本。无真实阅读者时不能宣布人工可用性增益。现有PRD/RAG设计正文保持。

| 分类 | GitHub维护源 | 飞书在线文档 |
| --- | --- | --- |
| 验证方案 | [实验范围与验收](ai-work/rag-gain-validation-plan-v0.1.md) | [13-AI Work RAG 增益验证方案](https://my.feishu.cn/wiki/NSMiwHelFiIY7ykVys4cJbL0nze) |
| 评测清单 | [48项待制作场景及执行登记](ai-work/rag-gain-evaluation-checklist-v0.1.md) | [14-AI Work RAG 增益评测清单](https://my.feishu.cn/wiki/Q5ZpwTcSTi485jkpDwkc2STsnLb) |
| 机器协议 | [protocol.json](../data/ai-work-rag-gain-v0.1/protocol.json)、[cases.json](../data/ai-work-rag-gain-v0.1/cases.json) | 13/14链接私有GitHub维护源；所有场景observed_result仍为空 |
| 核对证据 | [193项方案一致性校验](../eval-results/rag-gain-plan-validation-v0.1.json)、[飞书读回](../eval-results/rag-gain-plan-feishu-v0.1.json) | 13的4张表、5组及9指标；14的8张表及48个场景均读到末尾并刷新核对 |

两份文档通过原生Markdown导入，位于AI Work下6,4,0,13及6,4,0,14；标题使用文件名，正文不重复开篇H1。13导入后在原段落补清三轮冷/热安排，刷新读回确认：首轮测新任务，后两轮复用任务索引，不额外增加调用轮次。14直接链接飞书13；其余机器产物链接私有GitHub。原生表格已视觉检查，入口页补充13/14导航并刷新确认。线上链接与维护版可不同。

方案一致性校验193项通过，仅检查计数、分组、对照、门槛、来源哈希及清单映射，不是193项应用测试，也不是RAG实验成绩。主计划435次内容组运行加60次离线组运行共495次；生成最多348次加预检上限4次，均为未来计划。100元/2500次外部请求是方案止损上限，不代表当前支出授权或已产生费用；本轮模型调用0。

三批既有冻结资产88份校验值一致，旧首次成绩未改；本机应用代码、数据库、配置和密钥未同步或修改。应用仍为v0.4.3，未将设计写成已接通RAG。GitHub仓库已核实PRIVATE。导航的自动批准审核曾超时，按工具允许重试一次后完成；编辑段落虚拟卸载时先读当前状态再定位可见段落，未重复导入或覆盖旧文档。

本轮关键源SHA-256：

- 13维护正文：`da3c06f1bc9f341381df4686e616affecce6d89257202f58e8e88b57a5253440`。
- 14维护正文：`688c65bb6e2dd6512e162e544e021850d0e5a0f1801b935b3133c2e8c2e14d1e`。
- 机器协议：`717d0e74760c99c311ddd4c84d323d09d62ac09b4c5d5301d51f3e398f56217c`。
- 48项机器清单：`1840cdf07f9cc62abe7dcc14787db10fb3c8d51256f8cbdd0709deef78c5a646`。
- 方案一致性校验：`73e75c809afcb546cce643823f0377e6f7cbbe4fc6e4af9720d3067f3c33cff4`。

## 2026-10-29 AI Work RAG开发材料 v0.1

按既定范围完成16个开发场景：12份两页模拟报告、4份离线权限/异常夹具，参考标注覆盖120个固定检查单元及4个一致性查询。每份报告含20个有权限的任务附件干扰块，共240块；单份索引39至41块，总计481块。117个核心单元有记录，3个缺原始记录，缺证没有伪造引文。32个留出场景尚未制作，候选链路未冻结，应用行为测试、RAG组运行与模型请求均为0。

| 交付物 | GitHub维护源 | 飞书AI Work目录 |
| --- | --- | --- |
| 开发样本包说明 | [开发场景及使用边界](ai-work/rag-gain-dev-sample-pack-v0.1.md) | [15 AI Work RAG 开发样本包](https://my.feishu.cn/wiki/Qv6twselVij87akhUquc3ODhnCd) |
| 完整参考标注 | [要求与报告必要组、逐字引文及缺证状态](ai-work/rag-gain-dev-reference-v0.1.md) | [16 AI Work RAG 开发参考标注](https://my.feishu.cn/wiki/P2WpwS5eTiuo1LkAJc3c3w0BnZe) |
| 材料核验报告 | [核验范围、修正与R02口径问题](ai-work/rag-gain-dev-material-audit-v0.1.md) | [17 AI Work RAG 开发材料核验报告](https://my.feishu.cn/wiki/SGC1wDubRi8CCDktyFYcL4MVn0c) |
| 完整ZIP | [118文件开发包](../output/packages/ai-work-rag-gain-dev-v0.1.zip) | [AI Work下完整ZIP](https://my.feishu.cn/wiki/QTrAwLDt9iAmUokXwJEcTYVbnib) |

15至17均原生Markdown导入并刷新读回，位置6,4,0,15至17。共18张原生表格；16的14张表及147条去重后的预期原文/场景标记全部读回，三份均读到正文结束标记，并查看了实际排版。ZIP上传面板确认2.32 MB / 2.32 MB，随后原生移动至AI Work，刷新确认位置6,4,0,18。云端未再下载逐字节验哈希；源包哈希与封包校验另列。AI Work入口在原空白段落追加三份文档、ZIP和R02状态，等待保存后刷新读回。13/14在线正文及原48项机器清单保留方案制定时快照，当前开发状态以15至17和开发内容清单为准。

最终材料核验[1693/1693项通过](../eval-results/rag-gain-dev-material-validation-v0.2.json)，两种PDF提取引擎对账145个报告片段、96个要求实例，24页全部渲染查看。原索引部分要求为摘要，开发补充语料改取原文章节，不修改旧应用索引；单位表头初稿的两行范围已修正并新增顺序断言。仅核验材料完整性与对应关系，不是检索、生成或专业验收。4份离线夹具仅完成契约核验，构造种子不冒充实际A0输出。

对R02做[静态可达性预检](../eval-results/rag-gain-dev-metric-readiness-v0.1.json)：按当前必要组作为相关性标签，245个正例查询与来源组合的精度上限20%至60%，原固定5槽分母使80%门槛不可达。报告提出冻结独立种子相关性标签、按实际返回不同种子数计精度、继续用R01/R03约束完整性的建议。建议尚未应用，原验收标准不改，正式效果计分前需先明确口径。

最终包[216/216项校验通过](../eval-results/rag-gain-dev-package-validation-v0.3.json)，118个文件含原文、样本、附件、JSON标注、夹具、核验记录、联系图及离线验包脚本。最终ZIP SHA-256为`34220560d3fcd9b1f8299308204703e91a0a9c4b96c992639259eee1f6726245`，大小2435451字节。早期材料v0.1和封包v0.1/v0.2记录保留为本地制作中间证据，当前分别以材料v0.2及封包v0.3为准；它们不属于应用首次效果成绩。

88份既有冻结资产、72份已有结果文件及7个锁定来源文件哈希一致。应用、用户任务、数据库、模型配置与密钥未改动。GitHub再次核实PRIVATE。完整状态见[交付摘要](../eval-results/rag-gain-dev-delivery-v0.1.json)、[飞书同步读回](../eval-results/rag-gain-dev-feishu-v0.1.json)与[开发内容清单](../data/ai-work-rag-gain-dev-v0.1/material-manifest.json)。

## 2026-10-29 AI Work R02口径修订 v0.2

按用户授权修订R02，并在任何候选检索实测之前明确公式。R02现称“前5条实际返回精度”：正例取评分校验前原始补充种子顺序，m=min(5,实际返回条数)，相关且身份/原文有效的槽位数除以m；m=0记0。重复和错误继续占槽记0，缺日志或争议记未完成。无证据负例不进入精度宏平均，另验100%正确收敛。80%数值门槛保留，完整性仍须通过R01/R03；其余八项指标及实验范围未变。新旧R02定义不得混算。

| 交付 | 本地维护源 | 飞书 |
| --- | --- | --- |
| 验证方案内容v0.2 | [验证方案](ai-work/rag-gain-validation-plan-v0.1.md)，保留原文件路径 | [13原位更新](https://my.feishu.cn/wiki/NSMiwHelFiIY7ykVys4cJbL0nze) |
| 评测清单内容v0.2 | [48项清单](ai-work/rag-gain-evaluation-checklist-v0.1.md)，保留所有场景定义 | [14原位更新](https://my.feishu.cn/wiki/Q5ZpwTcSTi485jkpDwkc2STsnLb) |
| 修订与核验报告 | [公式、边界例子及结果](ai-work/rag-gain-r02-revision-v0.2.md) | [18 AI Work R02 评分口径修订与核验](https://my.feishu.cn/wiki/J0GdwHG0tijIdEkSJ0Dcvqabnth) |
| 机器协议及标注 | [协议](../data/ai-work-rag-gain-v0.2/protocol.json)、[台账](../data/ai-work-rag-gain-v0.2/cases.json)、[开发qrels](../data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json)、[参考评分函数](../scripts/rag_gain_scoring_v0_2.py) | 13/14/18链接私有GitHub维护源 |
| 核验结果 | [26个评分契约测试](../eval-results/rag-gain-r02-scoring-tests-v0.2.txt)、[2397项核验记录](../eval-results/rag-gain-r02-validation-v0.2.json)、[飞书读回](../eval-results/rag-gain-r02-feishu-v0.2.json) | 18展示结果及原始文件链接 |

开发种子相关性标注单独保存，共248个查询/来源组合、245个正例、3个报告缺证负例及4971个候选标签。标签绑定当前语料快照、来源文件及原完整性必要组，不向应用提供；同作者保守标注，专业及外部独立复核仍待完成。26个边界测试和2397/2397项口径/材料绑定核验通过。245个正例按金标构造的理想排序只验证新算术可达，不是检索实测100%。

13/14分别7处和9处修订均经刷新后逐项正文匹配，13保留4张原生表、全部九指标，14保留8张原生表、完整48个场景。14新增九项R02执行核对以分行政策文字呈现，本地Markdown使用额外表格，两种结构不声称逐字节一致。18仅导入一次，原生移动到AI Work，刷新位置6,4,0,19；3张表、核验计数、公式及正文结束标记均读回，并查看评分表实际排版。AI Work原入口更新状态并保留15/16/17/原ZIP链接，刷新确认保存。内部智能客服分组未修改。

一次只读多文档刷新任务被中断，诊断确认原任务已结束，按恢复流程接管原飞书标签并读取持久内容，确认先前写入已保存；没有据中断状态重做导入。最终浏览器任务正常结束、保留原标签。云端入口和正文位置可与Markdown不同，不是自动双向同步。

开发包93项内容资产、88份既有冻结材料、原开发ZIP、旧协议及历史结果、7个锁定来源保持原字节。原17及ZIP内的R02待明确说明保留为问题发现时快照，当前以18和v0.2为准。应用仍为v0.4.3；本轮候选检索、应用评测、Embedding及模型请求均为0，32个留出场景尚未制作。下一阶段仅用16个开发场景实现和调试候选链路。GitHub已再次核实PRIVATE。

本轮复现命令为`python3 -m unittest discover -s tests -p 'test_rag_gain_scoring_v0_2.py' -v`及`python3 scripts/validate_rag_gain_revision_v0_2.py --output tmp/r02-validation-recheck.json`。核验脚本拒绝覆盖已有结果；复查时选用新的输出路径，保留首次记录。当前交付文件摘要见[本轮交付清单](../eval-results/rag-gain-r02-delivery-v0.2.json)。

飞书悬停菜单多次未展开时均先读取状态，没有重复上传；参考标注上传成功但侧栏未更新，刷新核对了原文档，未重建。ZIP通过稳定的文档库入口上传一次，再移动一次。最后的只读导航被浏览器任务中断，核对原任务已结束及页面实际落点后，在新任务中读取并保存入口；未重放未知写入。最终浏览器任务正常结束，保留原标签，closedTabIds为空。
