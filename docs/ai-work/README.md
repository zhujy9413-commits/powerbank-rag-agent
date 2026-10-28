# AI Work｜整机测试报告评审

面向硬件产品经理，在研发评审前检查最新一版充电宝整机保护功能 PDF 测试报告，减少遗漏并缩短包含人工复核在内的总耗时。

- [MVP 范围](MVP.md)
- [完整 PRD](PRD.md)
- [完整知识库与 RAG 方案](RAG-and-knowledge-base.md)
- [首批模拟报告、规格与逐项参考标注](sample-pack.md)
- [工作流与验证方法补充](../shared/workflow-verification-notes.md)

状态：需求设计 v1.0，未开发、未实测。

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
