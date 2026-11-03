# 内部智能客服｜知识检索与问答

面向内部产品、研发和测试人员，帮助查找并理解充电宝整机保护功能相关规格、适用标准和公司规范，缩短取得正确依据的时间。

- [完整 PRD v0.1.3](PRD.md)：当前主交付，包含用户任务、优先级、页面、知识库/RAG、引用与验收，补清单轮澄清和部分回答。
- [PRD HTML阅读版](../../产品需求文档/internal-assistant-prd.html)：与维护源正文对应，含流程图和章节目录。
- [MVP 范围](MVP.md)
- [完整知识库与 RAG 方案](RAG-and-knowledge-base.md)
- [首批知识样本与问答评测集](sample-pack.md)
- [单轮知识问答原型与模型接入说明](prototype-v0.1.md)
- [百炼真实接口验证与问题记录](live-validation-v0.1.md)
- [角色范围与引用修复回归](role-citation-regression-v0.1.md)

需求范围沿用v0.1.1确认基线，当前PRD v0.1.3补充受控原型v0.5.0的实现状态、真实资料技术接入及试用执行条件，设计目标与已有单轮原型能力分开。以下原型、接口和修复记录作为实现支撑；语义质量、企业部署和实际业务收益仍待相应验证。

## 本轮实现状态

受控原型v0.5.0已完成本轮P0关键流程补齐，本次发布范围256项隔离回归通过；页面操作与四表导出已在隔离模拟资料中核对。具体新增功能、运行方式及真实试用进入条件见[项目当前进度](../../README.md)，原始结果见[发布范围回归日志](../../eval-results/mvp-p0-published-regression-v0.5.0.txt)。本地完整385项回归含未发布的A1实验，见[原记录](../../eval-results/mvp-p0-regression-v0.5.0.txt)，不作为公开仓库测试数量。下方旧版本记录按原验证时点保留。

当前可先用现有模拟资料，按PRD第12.3节开展实际使用者的可用性试用，无需先提供公司资料。真实业务试用尚未启动；授权材料就绪后先完成对应模板/知识、规则或身份的技术接入，再按准备表与对照步骤验证。

本地页面的「演示数据与验证」提供8个开发演示问题。每个问题展示具体数值或报告记录、原文入口和核对要点，支持填入明确的资料版本及任务范围。提交搜索后，对照预期证据组显示实际命中与遗漏；条款未收录的场景同时核对缺依据提示。原始样本沿用bootstrap-v0.1，未改动已有24题及冻结材料。预期对照独立于检索和生成，命中来源不直接代表回答语义正确；演示结果不作为独立评测或真实业务效果。权限不足、样本原件或版本状态变化时，不显示受影响的固定示例。

2026-11-03，D01正常问答、D05报告冲突和D08缺依据的页面流程核对通过，同版原文及D05四处引用可打开，反馈重复提交只保存一条且刷新后仍可查看。本轮使用关键词检索；D01实际调用一次百炼模型，D05由记录模板处理，D08停止生成并说明缺少条款。操作与反馈均标为助手代操作的模拟技术验收，未作为实际使用者体验或专业业务验收，见[原始结果](../../eval-results/internal-assistant-workflow-2026-11-03.json)。

本次演示功能发布范围在只包含仓库文件的隔离目录中独立通过[264项Python回归](../../eval-results/demo-sync-published-regression-2026-11-03.txt)，另通过[页面检索对照的遗漏、失败与快照变化检查](../../eval-results/demo-view-checks-2026-11-03.txt)。演示数据与预期定义见[场景文件](../../app/knowledge_assistant/demo.py)，与[检索及生成实现](../../app/knowledge_assistant/core.py)分别维护。

## 飞书在线文档

飞书与GitHub当前完整PRD均为v0.1.3，保留已确认需求范围并补清技术适配、试用进入条件和执行口径；GitHub同时提供受控原型v0.5.0对应代码和发布范围回归记录。以下保留各类文档入口，历史材料沿用其编制时版本。

- [MVP 范围](https://my.feishu.cn/wiki/BXA1weYkFiBxJkkLlxwc5MaFnWf)
- [完整 PRD](https://my.feishu.cn/wiki/YTAXwN0qBirjsKkTiMfcWe56nPc)
- [知识库与 RAG 方案](https://my.feishu.cn/wiki/KHnnwa5J8i9yZzkI4gfcvDEQntf)
- [知识样本与问答评测集](https://my.feishu.cn/wiki/AATmwtAHsiJ8c3kvQIpcUGv6n7c)
- [单轮知识问答原型与模型接入说明](https://my.feishu.cn/wiki/JjGuwIRVziJB9nkzAlgcoUj9nQc)
- [百炼真实接口验证与问题记录](https://my.feishu.cn/wiki/PPdkwtH45iFHsakhbJ3cYxVPnyh)
- [角色范围与引用修复回归](https://my.feishu.cn/wiki/BCwkw8ya7iuBATk4B4ncdGmen9c)
