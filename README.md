# 充电宝研发评审与知识助手

面向公司内部，聚焦中国大陆充电宝整机保护功能。目标是减少资料核对遗漏、缩短取得正确依据和完成测试报告评审的时间。

## AI Work｜整机测试报告评审

2026-10-29 页面v0.4.3：已修复依据停用后历史访问被一并阻断的问题。当前权限保留时可查历史任务、PDF与导出，停用依据不能用于新检查，撤权仍拒绝访问。141个自动测试、35项专项HTTP及51项既有流程检查通过。见[停用依据历史访问修复与回归](docs/ai-work/basis-history-access-v0.4.3.md)。

此前页面v0.4.2：三类报告完整流程技术验收通过，正常r3完成12项代理走查并核对实际Excel；修复无未决时仍提示含未决的显示问题，133项回归通过。人工可用性、专业复核与真实业务收益待验证。见[完整流程验收与试用记录](docs/ai-work/workflow-acceptance-v0.4.1.md)。

- [模块入口](docs/ai-work/README.md)
- [MVP 范围](docs/ai-work/MVP.md)
- [完整 PRD](docs/ai-work/PRD.md)
- [需求实现与验收对照](docs/ai-work/prd-implementation-audit-v0.1.md)
- [RAG 增益验证方案](docs/ai-work/rag-gain-validation-plan-v0.1.md)与[评测清单](docs/ai-work/rag-gain-evaluation-checklist-v0.1.md)已更新为v0.2：[R02修订核验](docs/ai-work/rag-gain-r02-revision-v0.2.md)的26个评分测试和2397项材料/口径核验通过；16个开发场景材料已核验，32个留出场景待制作，RAG实验尚未执行。
- [开发样本包](docs/ai-work/rag-gain-dev-sample-pack-v0.1.md)、[完整参考标注](docs/ai-work/rag-gain-dev-reference-v0.1.md)及[材料核验报告](docs/ai-work/rag-gain-dev-material-audit-v0.1.md)：12份PDF、4份离线夹具，1693项材料校验通过；[下载ZIP](output/packages/ai-work-rag-gain-dev-v0.1.zip)。
- [知识库与 RAG 方案](docs/ai-work/RAG-and-knowledge-base.md)

2026-10-28 已接通同模板模拟PDF的解析、输入确认、逐项核对、人工复核与Excel导出。固定范围为A1/C1的5 V输出短路保护已有记录，共10个单元及2项一致性检查。当前仍是模拟原型，真实规则与任意PDF布局尚未启用。

- [逐项评审原型与测试报告](docs/ai-work/prototype-and-validation-v0.1.md)
- [三次模拟报告运行原始结果](eval-results/ai-work-review-final-v0.2.json)
- [模拟评审Excel](outputs/ai-work-v0.1/report-review.xlsx)

在原有本机应用左侧点击“报告逐项评审”。AI Work需先安装PDF依赖 `python3 -m pip install -r requirements-ai-work.txt`。当前62项回归通过；1份报告的12项草拟参考对照在3次运行中一致，专业验收待完成。

2026-10-28 追加 v0.2：已补24份受控PDF变体与异常样本，新增候选记录覆盖审计和逐条测试条件核对。80项回归通过；最终构造开发集24个场景满足预期，仍不代表任意PDF或真实业务效果。

- [PDF模板变体与条件冲突回归](docs/ai-work/pdf-variants-and-conditions-v0.2.md)
- [变体样本包](data/pdf-variants-v0.1/README.md)
- [最终同输入修复前对照](eval-results/pdf-variants-final-input-baseline-v0.4.json) / [修复后结果](eval-results/pdf-variants-final-v0.5.json)

旧解析快照需重新导入PDF才能使用新引擎，历史结果可继续查看。运行全部开发测试需Python 3.10及以上（本机验证3.12），并安装 `python3 -m pip install -r requirements-dev.txt`；日常AI Work仍仅需PDF解析依赖，支持Python 3.9及以上。

### 新样本留出评测

2026-10-28：核验并冻结20份新模拟PDF后，以固定v0.2代码首次评测，12/20个场景满足期望，文字记录匹配181/193条；发现静默遗漏与局部条件处理缺口。86项自动回归通过不等于新样本全部通过，本轮未修改应用。

- [新样本留出评测、问题优先级和标注局限](docs/ai-work/holdout-evaluation-v0.1.md)
- [冻结协议及样本包](data/review-holdout-v0.1/README.md)
- [首次完整结果](eval-results/review-holdout-first-run-v0.1.json)

## 内部智能客服｜知识检索与问答

- [模块入口](docs/internal-assistant/README.md)
- [MVP 范围](docs/internal-assistant/MVP.md)
- [完整 PRD](docs/internal-assistant/PRD.md)
- [知识库与 RAG 方案](docs/internal-assistant/RAG-and-knowledge-base.md)

## 共用基线与原始阅读版

- [产品总览与整体 MVP](docs/shared/product-overview-mvp.md)
- [知识库与 RAG 共用规范](docs/shared/knowledge-base-rag.md)
- [原始 HTML 阅读入口](产品需求文档-v1.0/index.html)（下载后本地打开）

## 首批知识样本与评测包

v0.1 · 2026-10-26 准备，2026-10-27 校验。使用官方资料摘要和明确标注的模拟材料，没有使用公司历史资料。

- [样本包入口与使用顺序](data/bootstrap-v0.1/README.md)
- [资料清单与公开来源](docs/shared/bootstrap-materials.md)
- [AI Work 模拟报告、规格与12项参考标注](docs/ai-work/sample-pack.md)
- [内部智能客服知识样本与24题问答开发集](docs/internal-assistant/sample-pack.md)
- [四页模拟测试报告 PDF](output/pdf/SYN-TR-001-R1.pdf)

已完成数据结构、引用与PDF检查，并完成首批真实模型开发集验证。真实标准条款判定未启用，专业复核待完成。

## 文档状态

v1.0 · 2026-10-26。业务范围、优先级和页面交互已梳理，当前为需求设计成果。真实规则白名单、标准使用权限、代表性语料、定量性能目标与部署条件仍待落实。模拟材料单独标注；不将设计方案当成已完成开发或已验证业务收益。

## 本机单轮知识问答原型

2026-10-27 新增 v0.1。已实现关键词与向量混合检索、版本与权限筛选、关联依据补充、证据片段及原文查看、反馈、本机模型设置；百炼生成与Embedding接口已真实验证，DeepSeek接口保留适配。

```bash
python3 -m app.knowledge_assistant.server --open
```

Python 3.9及以上，无Web框架依赖。macOS也可双击`start-assistant.command`。本机地址由程序启动时打印；不对外部署。

- [使用说明、接入步骤及验证结果](docs/internal-assistant/prototype-v0.1.md)
- [关键词检索开发集结果](eval-results/retrieval-baseline-v0.1.json)
- [工作流与验证方法补充](docs/shared/workflow-verification-notes.md)
- [百炼真实接口验证与问题记录](docs/internal-assistant/live-validation-v0.1.md)
- [角色范围与引用修复回归](docs/internal-assistant/role-citation-regression-v0.1.md)

39项自动测试通过。已修复已识别的输入输出混淆、摘要端口错配和引用编号问题；最后24题混合检索命中41个必要证据组，18个生成请求均通过结构和引文校验，其中1个经过一次校正。另有3题由程序回答，3题因缺依据或范围停止生成。结果来自作者草拟开发集，不代表回答准确率或专业业务验收通过。

## 飞书分类入口

- [项目根页面](https://my.feishu.cn/wiki/NKZ4wE0T4iFHTLkTcfrcKR10nAe)
- [AI Work｜整机测试报告评审](https://my.feishu.cn/wiki/UlodwHIzJidrjDkQXVvcApD1nbe)
- [内部智能客服｜知识检索与问答](https://my.feishu.cn/wiki/G5ErwipsTiq0lxkZpbvcSj8snQb)

- [飞书整体总览与 MVP](https://my.feishu.cn/wiki/GrUkwdeLfi1Orgkrpn9cUupznid)
- [同步记录与逐份文档对应关系](docs/SYNC.md)
