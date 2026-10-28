# AI Work｜整机测试报告评审

面向硬件产品经理，在研发评审前检查最新一版充电宝整机保护功能 PDF 测试报告，减少遗漏并缩短包含人工复核在内的总耗时。

- [MVP 范围](MVP.md)
- [完整 PRD](PRD.md)
- [完整知识库与 RAG 方案](RAG-and-knowledge-base.md)
- [首批模拟报告、规格与逐项参考标注](sample-pack.md)
- [工作流与验证方法补充](../shared/workflow-verification-notes.md)

状态：需求设计v1.0；模拟原型v0.2可运行。新样本评测发现扩展输入仍有遗漏与条件误判，未完成真实业务验收。

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
