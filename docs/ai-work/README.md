# AI Work｜整机测试报告评审

面向硬件产品经理，在研发评审前检查最新一版充电宝整机保护功能 PDF 测试报告，减少遗漏并缩短包含人工复核在内的总耗时。

- [MVP 范围](MVP.md)
- [完整 PRD](PRD.md)
- [完整知识库与 RAG 方案](RAG-and-knowledge-base.md)
- [首批模拟报告、规格与逐项参考标注](sample-pack.md)
- [工作流与验证方法补充](../shared/workflow-verification-notes.md)

状态：需求设计v1.0；模拟原型v0.4可运行。三个P0及跨行摘要与单位归属P1已修复并验证，真实业务验收仍待完成。

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
