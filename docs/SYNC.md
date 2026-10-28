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
