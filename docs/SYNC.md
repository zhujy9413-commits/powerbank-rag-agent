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
