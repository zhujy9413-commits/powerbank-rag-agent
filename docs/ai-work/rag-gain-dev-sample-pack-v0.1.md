# AI Work RAG 开发样本包 v0.1

2026-10-29。供公司内部充电宝整机研发评审 Agent 的开发实验使用。已制作并核验16个开发场景，包括12份模拟PDF报告和4个离线控制流夹具。全部材料为人工构造，尚未运行候选RAG链路。

## 获取材料

[下载完整开发样本包 ZIP](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/packages/ai-work-rag-gain-dev-v0.1.zip)，需要该私有仓库访问权限。解压后保留根目录结构；PDF、任务附件、要求原文、参考标注、材料核验记录与文件校验清单均在包内。

[16项机器台账](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/data/ai-work-rag-gain-dev-v0.1/cases.json) · [完整参考标注](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/docs/ai-work/rag-gain-dev-reference-v0.1.md) · [材料核验报告](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/docs/ai-work/rag-gain-dev-material-audit-v0.1.md)

## 实验范围

型号PB-DEMO-01；A1、C1；5 V输出、单口短路保护已有记录。每端口核对响应、恢复电压、壳温变化、外观与恢复方式，共10项。阈值沿用已选模拟规范及RevB，不作为真实行业标准。9 V、输入角色只作为对照记录，保留未配置边界。

## 开发场景清单

| 场景 | 材料与用途 | 核验状态 |
| --- | --- | --- |
| RG-TERM-DEV-01 | [SYND-801.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-801.pdf)；保护动作的叙述与字段名称不同 | 材料核验通过；应用行为待执行 |
| RG-TERM-DEV-02 | [SYND-802.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-802.pdf)；恢复输出与恢复电压的表达不同 | 材料核验通过；应用行为待执行 |
| RG-CONTEXT-DEV-01 | [SYND-803.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-803.pdf)；测试条件在记录表前的说明段 | 材料核验通过；应用行为待执行 |
| RG-CONTEXT-DEV-02 | [SYND-804.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-804.pdf)；表头单位与数值分行 | 材料核验通过；应用行为待执行 |
| RG-PORT-DEV-01 | [SYND-805.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-805.pdf)；A1与C1出现相同数值 | 材料核验通过；应用行为待执行 |
| RG-PORT-DEV-02 | [SYND-806.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-806.pdf)；不同字段出现相同数字 | 材料核验通过；应用行为待执行 |
| RG-CONDITION-DEV-01 | [SYND-807.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-807.pdf)；相同端口同时出现5 V及其他电压 | 材料核验通过；应用行为待执行 |
| RG-CONDITION-DEV-02 | [SYND-808.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-808.pdf)；输入与输出角色字面相似 | 材料核验通过；应用行为待执行 |
| RG-GAP-DEV-01 | [SYND-809.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-809.pdf)；C1外观观察记录缺失 | 材料核验通过；应用行为待执行 |
| RG-GAP-DEV-02 | [SYND-810.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-810.pdf)；报告填写RevA但本次确认RevB | 材料核验通过；应用行为待执行 |
| RG-NOISE-DEV-01 | [SYND-811.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-811.pdf)；当前任务含大量不相关但有权限片段 | 材料核验通过；应用行为待执行 |
| RG-NOISE-DEV-02 | [SYND-812.pdf](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/output/pdf/rag-gain-dev-v0.1/SYND-812.pdf)；背景说明复述合格结论但缺原始记录 | 材料核验通过；应用行为待执行 |
| RG-OPS-DEV-01 | [RG-OPS-DEV-01.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/data/ai-work-rag-gain-dev-v0.1/offline-fixtures/RG-OPS-DEV-01.json)；普通员工请求研发专属来源 | 材料核验通过；应用行为待执行 |
| RG-OPS-DEV-02 | [RG-OPS-DEV-02.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/data/ai-work-rag-gain-dev-v0.1/offline-fixtures/RG-OPS-DEV-02.json)；依据已停用后尝试新检查 | 材料核验通过；应用行为待执行 |
| RG-OPS-DEV-03 | [RG-OPS-DEV-03.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/data/ai-work-rag-gain-dev-v0.1/offline-fixtures/RG-OPS-DEV-03.json)；模型返回不存在的引用编号 | 材料核验通过；应用行为待执行 |
| RG-OPS-DEV-04 | [RG-OPS-DEV-04.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/data/ai-work-rag-gain-dev-v0.1/offline-fixtures/RG-OPS-DEV-04.json)；模型调用超时的离线注入 | 材料核验通过；应用行为待执行 |

## 包内目录与隔离

| 目录 | 内容 | 使用边界 |
| --- | --- | --- |
| output/pdf/rag-gain-dev-v0.1 | 12份PDF，共24页 | 可供当前任务解析 |
| data/ai-work-rag-gain-dev-v0.1/application-inputs | 每份报告的任务事实、通用字段查询、双来源语料及任务附件 | 只向应用提供当前任务目录与对应PDF；不传外层台账 |
| selected-basis | 已选依据的两份原文及8个逐字章节片段 | 与bootstrap原文内容相同；旧摘要索引保持原样 |
| author-source / reference-annotations | 作者意图与124个查询的必要组、条件、引文、保守处理 | 仅供评测器，不进入检索、Embedding或模型Prompt |
| offline-fixtures | 4份权限、停用、伪造引用及超时注入JSON | 虚拟时钟、禁止网络；待候选适配器执行 |
| render-bounds / eval-results | 排版边界、逐页观察与1693项材料校验 | 不计为应用测试或效果成绩 |

台账status记录作者材料已绑定参考标注；核验就绪状态以独立material-manifest.json为准，observed_result继续为空。每份报告的20个有权限干扰片段置于当前任务的Markdown附件及报告命名空间，未伪装为PDF原始测量记录。12份报告共481个索引块；单份39至41块，低于80块上限。要求命名空间始终仅含已选8个原文章节。所有补充块均标注来源角色、章节或页码、版本和任务权限。

每个种子最多预关联1个上下文块。单位跨行样本关联表头，其余普通记录关联全局条件。扩展不等于原始top-5，未来评分必须分开登记。

## 运行前约束

开发材料按12个独立合成报告家族登记，属于同作者、实现知情的内部核验。后续32个留出场景尚未制作，不能用这批底稿仅换值、换页或改写后作为新留出。候选实现、评分器、分块、Prompt和模型配置须先用开发集调试并冻结。

A0现有完整基线保留。A1至A4尚未实现；本次没有生成模型或Embedding请求，没有改动应用、本机任务、数据库或模型配置。4份离线夹具仅完成输入和预期契约核验，执行结果均为空。

## 下一阶段入口

实现隔离的候选检索、补充引文校验与模型说明适配层，再只用这16个开发场景调试。首先验证逐字引用、命名空间和条件归属，保留A0结果及历史；完成开发后才冻结候选并制作留出材料。

开发样本包正文结束。
