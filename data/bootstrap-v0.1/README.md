# 首批知识样本与评测包 v0.1

准备日期2026-10-26。用于充电宝研发评审与内部知识问答原型的数据准备。没有使用公司历史资料。

## 从这里开始

1. 先读[资料清单与入库说明](资料清单与入库说明.md)，明确哪些能回答标准元数据、哪些只能用于演示。
2. 阅读[模拟RevB规格](knowledge/synthetic/SYN-SPEC-PB01-RevB.md)和[模拟评审规范](knowledge/synthetic/SYN-QA-SC-1.0.md)。
3. 打开[四页模拟测试报告](../../output/pdf/SYN-TR-001-R1.pdf)，对照[12项标注](evaluation/报告逐项标注表.md)。
4. 用[24题问答集](evaluation/问答评测集.md)与[执行及评分说明](evaluation/执行及评分说明.md)设计第一轮验证。

## 已准备与未验证

已准备5份官方资料摘要、模拟规格RevA/RevB、1份模拟评审规范、1份4页模拟报告、24道问答用例、12项报告参考标注以及可导入JSONL。

公开材料仅收原创元数据摘要与官方链接，不含国家标准全文和真实认证判定规则。模拟阈值用于检验软件行为，不能用于真实检测。所有答案与标注由样本作者拟定，专业复核仍待完成。

这批材料全部属于开发集。没有训练/测试独立性、真实PDF代表性或业务收益证据。当前未接入模型，未运行RAG评测，不能报告召回率、准确率或节省时间。

## 机器可用文件

- `index/knowledge-chunks.jsonl`：共用知识候选块，带来源、版本、角色与状态。归档材料默认不得进入当前依据召回。
- `index/task-chunks.jsonl`：单任务报告块；只在该任务授权范围内检索，不能自动发布到共用知识库。
- `rules/demo-rules.json`：5条演示规则。`real_compliance_enabled=false`。
- `task-reports/task-input.json`：本次模拟任务的显式输入快照。
- `evaluation/questions.jsonl`：问答开发集，含证据、要点、禁止结果与空白人工复核字段。
- `evaluation/review-annotations.jsonl`：逐项检查预期与空白人工复核字段。

## 维护方式

`scripts/build_bootstrap_pack.py`维护这一版构造样本，变更后重新生成并运行`python3 scripts/validate_bootstrap_pack.py`。公开源的核验日期由维护者人工更新；运行构建不会重新查网。
后续拿到有权使用的资料时，复制为新版本，重新做来源、适用性与专业标注审核，保留本版用于回归。不要在模拟文件上涂掉“模拟”后当真实资料使用。
