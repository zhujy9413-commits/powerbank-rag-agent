# AI Work｜整机测试报告评审

面向硬件产品经理，在研发评审前检查最新一版充电宝整机保护功能 PDF 测试报告，减少遗漏并缩短包含人工复核在内的总耗时。

- [MVP 范围](MVP.md)
- [完整 PRD](PRD.md)
- [完整知识库与 RAG 方案](RAG-and-knowledge-base.md)
- [首批模拟报告、规格与逐项参考标注](sample-pack.md)
- [工作流与验证方法补充](../shared/workflow-verification-notes.md)

状态：需求设计v1.0；模拟原型页面v0.4.3可运行。三个P0及跨行摘要与单位归属P1已修复并验证，真实业务验收仍待完成。

## 飞书在线文档

- [MVP 范围](https://my.feishu.cn/wiki/Q2GnwQhJDiXzjWkmqLRccBfbneW)
- [完整 PRD](https://my.feishu.cn/wiki/K71fwnJo8iDBy9kgkRBchCvcn0g)
- [知识库与 RAG 方案](https://my.feishu.cn/wiki/Gs9Xw9YpHiVB6wknPDVcsMw7nUf)
- [模拟报告与逐项标注](https://my.feishu.cn/wiki/KqKQwhIzsi2KQukyfh2czZAvnZd)
- [模拟PDF原件](https://my.feishu.cn/wiki/CdWGwp7NviGQQgkiJCgc5YOhnab)

## 可运行原型与验证

2026-10-28：同模板模拟PDF已可完成解析确认、逐项核对、复核与Excel导出。支持固定模拟规则，不代表完整MVP或真实业务验收已完成。

- [05-逐项评审原型与测试报告](prototype-and-validation-v0.1.md)
- [原始运行与参考对照](../../eval-results/ai-work-review-final-v0.2.json)
- [模拟评审Excel](../../outputs/ai-work-v0.1/report-review.xlsx)

[飞书05-逐项评审原型与测试报告](https://my.feishu.cn/wiki/PKLtwf0CFiPC2GkafY5cvWFIn7e)

## PDF模板与异常回归 v0.2

2026-10-28：新增24份构造PDF，覆盖换列、换行、跨页、未映射字段、缺页和条件冲突。新增解析覆盖提示及逐条条件核对；80项自动回归通过。

- [06-PDF模板变体与条件冲突回归](pdf-variants-and-conditions-v0.2.md)
- [样本清单](../../data/pdf-variants-v0.1/cases.json)
- [最终实测结果](../../eval-results/pdf-variants-final-v0.5.json)

[飞书06-PDF模板变体与条件冲突回归](https://my.feishu.cn/wiki/LgWKwZP2fiD27NkBnXicNEDZni8)

## 新样本留出评测 v0.1

2026-10-28：20份新PDF、40页在运行前冻结，固定v0.2代码首次满足12/20个场景期望；文字记录181/193匹配。4个场景中8个应停止的单元仍显示未发现问题。本轮只评测，不修改应用或事后改标签。

- [07-新样本留出评测与问题清单](holdout-evaluation-v0.1.md)
- [冻结样本、标注与口径](../../data/review-holdout-v0.1/README.md)
- [首次完整结果](../../eval-results/review-holdout-first-run-v0.1.json)
- [问题分析及标注复核](../../eval-results/review-holdout-analysis-v0.1.json)

86项回归通过，其中6项是新增评分器自检。这是同作者、实现知情的新样本留出评测，不是外部独立测试或专业验收。

[飞书07-新样本留出评测与问题清单](https://my.feishu.cn/wiki/IApXw3nDkiNhwTkl4QYcauv6n9g)

## P0修复与第二批留出评测 v0.3

102项回归通过；旧5个P0失败场景全部满足期望。新20份、40页PDF先冻结后首次满足20/20个场景，88项停检断言均满足；文字匹配190/205，15条未知编号明确提示并停止，不代表全部内容已解析。

- [08-P0修复回归与第二批留出评测](p0-fix-and-holdout-v0.3.md)
- [第二批冻结样本](../../data/p0-holdout-v0.1/README.md)
- [第二批首次结果](../../eval-results/p0-holdout-first-run-v0.1.json)

当前有实际绘制图片即停检10项，尚未OCR；旧快照须重新导入，历史结果保留。

[飞书08-P0修复回归与第二批留出评测](https://my.feishu.cn/wiki/LLVlwPzloiS4xMkgvmvcT3QAnfe)

## 跨行摘要与单位归属修复 v0.4

2026-10-28 P1修复v0.4：跨行摘要与单位采用一致归属，129项回归通过。代码先冻结后另建20份新PDF，首次20/20满足期望，200/200文字记录、166/166行为及46/46指定停检断言满足；属于同作者时间留出。旧首次分数保留，真实业务验收待完成。详见[跨行摘要与单位归属修复回归及新样本评测](p1-fix-and-holdout-v0.4.md)。

- [09-修复回归及新样本评测](p1-fix-and-holdout-v0.4.md)
- [新样本与冻结协议](../../data/p1-holdout-v0.1/README.md)
- [首次完整结果](../../eval-results/p1-holdout-first-run-v0.1.json)

[飞书09-P1跨行摘要与单位归属修复评测](https://my.feishu.cn/wiki/RcHjw5fjai8eiEkJdHmci8Qmnje)

## 完整流程技术验收 v0.4.1

2026-10-28 完整流程验收v0.4.1：修复条件性结果筛选、报告版本展示、索引摘要/原文区分及保存期间操作问题。133项回归、3场景51项HTTP检查通过；三类页面任务保存36项模拟处置，导出及恢复核对通过。受控模拟流程技术验收通过，人工可用性、专业复核和业务收益待验证。见[完整流程技术验收与试用记录](workflow-acceptance-v0.4.1.md)。

- [10-完整流程验收与试用记录](workflow-acceptance-v0.4.1.md)
- [场景清单和复现](../../data/workflow-acceptance-v0.1/README.md)
- [HTTP完整结果](../../eval-results/workflow-http-v0.4.json)
- [页面及持久性记录](../../eval-results/workflow-ui-v0.1.json)

[飞书10-完整流程验收与试用记录](https://my.feishu.cn/wiki/PYsWwxwn2iQIxZkZ6yPcnwjinyc)

2026-10-28 页面v0.4.2：按用户授权完成正常报告r3的12项代理代操作走查，核对原PDF、依据、保存恢复及实际Excel四张表，133项回归通过。修复无未决时仍显示含未决的P2提示问题；人工试用表保留待填写。细节、代理页码文字更正及17条历史见10的补充记录。

## 需求实现与验收对照

2026-10-29，以页面v0.4.2逐项核对PRD设计：36个单元中14项已实现、14项部分实现、8项未实现，状态数量不代表完成率。核对11个AW和10个KB用例，新增7项临时库观察。下一轮优先补历史依据停用后的核验路径；检索/模型、知识发布与试点条件分别跟踪。

- [11-需求实现与验收对照](prd-implementation-audit-v0.1.md)
- [结构化对照及来源](../../eval-results/prd-implementation-audit-v0.1.json)
- [本轮隔离观察](../../eval-results/prd-implementation-audit-probes-v0.1.json)

[飞书11-需求实现与验收对照](https://my.feishu.cn/wiki/HHpMw4259ihzjlkH1XrcAZgRn6c)

## 停用依据历史访问修复

2026-10-29 页面v0.4.3：已修复依据停用后历史访问被一并阻断的问题。当前权限保留时可查历史任务、PDF与导出，停用依据不能用于新检查，撤权仍拒绝访问。141个自动测试、35项专项HTTP及51项既有流程检查通过。见[停用依据历史访问修复与回归](basis-history-access-v0.4.3.md)。

- [专项HTTP原始结果](../../eval-results/basis-history-access-v0.4.3.json)
- [页面状态与恢复记录](../../eval-results/basis-history-access-ui-v0.4.3.json)

[飞书12-停用依据历史访问修复与回归](https://my.feishu.cn/wiki/POLxwDj3ci8DHJkVjGYcmCOLndg)

## RAG增益验证方案

2026-10-29 RAG实验方案口径基线为v0.2：保留现有完整基线、五组对照、48个计划场景与分层验收。R02采用“前5条实际返回精度”，80%门槛保留，仍须联合满足R01/R03完整性及安全等门禁。16个开发场景已完成查询修复回归，32个留出场景待制作，正式五组留出未执行。当前状态见[真实向量对照报告](live-vector-comparison-v0.1.md)；[验证方案](rag-gain-validation-plan-v0.1.md)、[评测清单](rag-gain-evaluation-checklist-v0.1.md)及[R02报告](rag-gain-r02-revision-v0.2.md)保留各自交付时快照。

- [当前机器协议v0.2](../../data/ai-work-rag-gain-v0.2/protocol.json)与[48项状态台账](../../data/ai-work-rag-gain-v0.2/cases.json)
- [开发种子相关性qrels](../../data/ai-work-rag-gain-v0.2/qrels-dev-v0.1.json)：248个查询/来源组合，245正例、3负例，4971个标签。
- [参考评分函数](../../scripts/rag_gain_scoring_v0_2.py)、[26个评分契约测试](../../eval-results/rag-gain-r02-scoring-tests-v0.2.txt)及[2397项核验记录](../../eval-results/rag-gain-r02-validation-v0.2.json)；仅验证口径及绑定，不是实际检索分数。
- [原v0.1协议](../../data/ai-work-rag-gain-v0.1/protocol.json)与[193项方案一致性校验](../../eval-results/rag-gain-plan-validation-v0.1.json)保留历史快照。

- [飞书13 AI Work RAG 增益验证方案](https://my.feishu.cn/wiki/NSMiwHelFiIY7ykVys4cJbL0nze)
- [飞书14 AI Work RAG 增益评测清单](https://my.feishu.cn/wiki/Q5ZpwTcSTi485jkpDwkc2STsnLb)
- [飞书18 AI Work R02 评分口径修订与核验](https://my.feishu.cn/wiki/J0GdwHG0tijIdEkSJ0Dcvqabnth)
- [本轮飞书刷新读回记录](../../eval-results/rag-gain-r02-feishu-v0.2.json)

## RAG开发材料

2026-10-29完成12份模拟报告、4份离线夹具及完整参考标注。1693项材料断言和24页页面核验通过；原ZIP含118个文件，216项封包校验通过。原材料报告及ZIP保留问题发现时快照，其中R02原分母问题已在v0.2解决，旧材料未被回写。当前12份PDF已执行候选开发实验、4个夹具已执行离线适配器契约；最新结果见下方候选开发章节。

- [开发样本包](rag-gain-dev-sample-pack-v0.1.md)与[完整ZIP](../../output/packages/ai-work-rag-gain-dev-v0.1.zip)
- [参考标注](rag-gain-dev-reference-v0.1.md)
- [材料核验报告](rag-gain-dev-material-audit-v0.1.md)及[1693项最终记录](../../eval-results/rag-gain-dev-material-validation-v0.2.json)
- [开发内容哈希清单](../../data/ai-work-rag-gain-dev-v0.1/material-manifest.json)
- [飞书15 开发样本包](https://my.feishu.cn/wiki/Qv6twselVij87akhUquc3ODhnCd)
- [飞书16 开发参考标注](https://my.feishu.cn/wiki/P2WpwS5eTiuo1LkAJc3c3w0BnZe)
- [飞书17 材料核验报告](https://my.feishu.cn/wiki/SGC1wDubRi8CCDktyFYcL4MVn0c)
- [飞书完整ZIP](https://my.feishu.cn/wiki/QTrAwLDt9iAmUokXwJEcTYVbnib)

## 候选检索开发验证

2026-10-29候选模块v0.5已补齐版本核对和背景完整性两个要求侧查询；独立A1检索、混合接口、上下文扩展及引用门禁仍通过CLI运行，普通页面与原规则保持v0.4.3。12份PDF原规则载荷均未改变，4个离线异常夹具通过。完整212项回归包含45项候选及26项评分测试，另有2099项执行/历史不变性核验通过。

A1开发R01要求、报告均100%；R02要求99.19%、报告98.35%，3个缺证负例正确收敛。两个查询均覆盖2/2组，其余492条候选输出与v0.4一致。候选未冻结；A2内容运行仍为显式关键词降级，真实向量、生成、正式留出和业务收益待验。

- [本轮查询修复与回归](candidate-consistency-fix-v0.5.md)、[16项运行清单](../../data/ai-work-candidate-dev-v0.5/run-manifest.json)
- [本轮原始结果](../../eval-results/candidate-query-fix-dev-v0.5.json)、[212项回归](../../eval-results/candidate-query-fix-regression-v0.5.txt)、[2099项核验](../../eval-results/candidate-query-fix-validation-v0.5.json)
- [原v0.4实现与开发结果](candidate-retrieval-dev-v0.4.md)，保留修复前两个查询缺口与各轮分数。
- [飞书19 候选检索链路与开发验证](https://my.feishu.cn/wiki/WKQAwmuA7iyqQZk1wv5cuQIpndx)
- [飞书20 一致性查询修复与回归](https://my.feishu.cn/wiki/K07BwHd4jiCXS9kQwY1cyMUfnbg)

## 首轮百炼真实向量开发验证

2026-10-29 原16个开发场景完成A1/A2真实向量对照。固定百炼北京text-embedding-v4、1024维及原v0.5路由，433次请求，按接口用量与标价核算0.0129435元，非账户实扣。225项完整回归、3456/3456项执行/计量/历史核验通过。当前保留A1，A2暂不接入页面；具体覆盖、精度、逐条变化与耗时见[验证报告](live-vector-comparison-v0.1.md)。

- [原始执行及逐次费用账本](../../eval-results/candidate-live-dev-v0.1.json)
- [配对变化、耗时和完整性核验](../../eval-results/candidate-live-validation-v0.2.json)
- [16项执行台账](../../data/ai-work-candidate-live-v0.1/run-manifest.json)
- [飞书21 百炼真实向量检索验证与对比](https://my.feishu.cn/wiki/CxOIws1oDiPyBJkFeE2ckWDonpa)

原v0.5及更早A2降级记录保留。本轮无意外降级，四个异常夹具仍零联网，生成请求0；普通页面与原规则流程保持v0.4.3，正式留出、专业复核及R03业务净增益未验收。
