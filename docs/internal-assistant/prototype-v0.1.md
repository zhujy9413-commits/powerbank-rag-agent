# 单轮知识问答原型 v0.1 与模型接入说明

日期：2026-10-27。当前是本机可运行原型，使用公开摘要及模拟样本。百炼生成与Embedding接口已真实调用，已建立26块向量索引并完成24题开发集多轮验证。存在引用与语义问题，尚未通过业务验收；详见[真实接口验证与问题记录](live-validation-v0.1.md)。

## 1. 这次实际实现了什么

| 环节 | 本版实现 | 当前验证状态 |
| --- | --- | --- |
| 资料导入 | 只加载样本包中两份指定的JSONL；保留来源、版本、章节与页码 | 已检查，不读取评测题目及答案 |
| 关键词检索 | 中文二元词、英文及数值保留，BM25排序；标准号和记录ID保留 | 已运行开发集检索基线 |
| 向量检索 | 百炼兼容Embedding接口、分批请求、向量归一化、本机索引、与关键词检索做RRF融合 | 真实26块索引建立及24题混合检索已运行 |
| 范围与权限 | 默认当前版本；归档需显式启用；显式RevA历史要求不串入当前RevB规范；任务附件独立授权 | 已做功能及HTTP接口测试 |
| 单轮生成 | 百炼和DeepSeek兼容Chat接口；只发送当前请求的授权证据，使用JSON输出 | 百炼已真实验证，DeepSeek未实测；语义质量未验收 |
| 引用校验 | 每个结论必须有本次证据ID及相符短引文；不相符时不展示为成功回答 | 已测试伪造ID、伪造摘录及不完整输出 |
| 原文查看 | 再次校验角色和任务权限，显示证据片段与资料正文；报告定位到PDF物理页码 | 页面交互已检查 |
| 异常及反馈 | 无依据、缺范围、模型未配置、生成失败分别显示；可提交有用或错误类型反馈 | 已检查保存与回放 |

没有接入模型时，页面提供真实检索结果，不伪装成模型生成答案。本轮没有实现完整AI Work逐项报告评审、企业登录、知识管理后台或对外部署。

## 2. 如何启动

应用本身只使用Python标准库，要求Python 3.9及以上，不需要安装Web框架。

在项目根目录执行：

```bash
python3 -m app.knowledge_assistant.server --open
```

程序自动选择空闲本机端口并打印实际地址。macOS也可双击项目根目录的`start-assistant.command`。关闭终端服务后页面接口会停止；重新启动时地址可能变化。

开发者可固定端口或测试普通员工身份：

```bash
python3 -m app.knowledge_assistant.server --port 8766 --profile employee
```

当前身份在服务端启动时确定，网页不能通过传入`role=engineer`升级权限。这只是本机演示身份，不能替代企业SSO。服务强制绑定127.0.0.1，不能直接向外网或公司局域网发布。

## 3. 为什么先选百炼

本项目需要同时处理问答和资料检索。百炼提供生成、Embedding及重排序接口，可减少多平台接入与维护环节；因此首版优先接百炼。DeepSeek保留为生成模型对照，并不预设哪个模型在硬件问答上更准确。[百炼向量与重排序文档](https://help.aliyun.com/zh/model-studio/embedding-rerank-model)、[DeepSeek Chat接口](https://api-docs.deepseek.com/api/create-chat-completion/)

本版默认填写`qwen-flash`和`text-embedding-v4`作为初始配置，已完成连接和开发集实测。模型ID、开放权限、服务地域和Base URL都以用户控制台实际可用项为准；不声称该组合已被本项目验证最优。生成适配器采用非思考JSON模式；更换为其他思考模型需另外验证兼容性。[百炼结构化输出](https://help.aliyun.com/zh/model-studio/qwen-structured-output)

## 4. 在本机配置百炼

1. 打开页面右上角“连接模型”。
2. 选择“阿里云百炼”。从控制台复制当前地域、业务空间对应的兼容接口Base URL；不要附加`/chat/completions`。文档中的`{WorkspaceId}`必须替换为真实业务空间ID。
3. 填写账号中可用的回答模型ID、Embedding模型ID及API密钥。
4. 点击“保存本机配置”。保存成功只说明配置已存储，尚未证明接口可调用。
5. 在主页面选择“基于资料回答”，先用“演示任务选用的RevB恢复电压范围是什么？”验证一次真实生成及引用。
6. 需要语义检索时，在模型设置中点击“建立向量索引”。这会调用百炼Embedding接口；之后查询结合关键词与向量排序。

Base URL和密钥需匹配地域及业务空间。接口形式参见[百炼OpenAI兼容接入](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)和[Embedding接口](https://help.aliyun.com/en/model-studio/text-embedding-synchronous-api)。

本包有20个知识证据块和6个任务证据块。向量缓存会保存它们各自的ID；检索前仍按资料角色、发布状态及任务命名空间筛选，报告不会因此变成全局可检索知识。语料或Embedding配置变化后需要重建索引。

生成和向量调用会产生服务方费用。本机设置不会购买额度、开通付费产品或自动反复重试。建立索引及提问均由明确动作触发。

## 5. 密钥与运行记录在哪里

- 模型配置保存在`.local/assistant/model.json`，目录权限0700、文件权限0600。密钥不回显，不放入模型提示词、运行记录或仓库。
- 向量缓存保存在`.local/assistant/vectors.json`；Embedding配置或语料摘要不匹配时不使用旧向量。
- 请求结果、检索证据、状态和反馈保存在`.local/assistant/requests.sqlite3`。启动时清理7天前的记录；这是原型保留策略，企业部署前需重新确认。
- `.local/`已加入Git忽略规则。后续接入真实公司资料时，需要重新评审云端数据流向与访问控制。

也支持环境变量。百炼需要`DASHSCOPE_API_KEY`与`RAG_API_BASE_URL`，可选`RAG_CHAT_MODEL`和`RAG_EMBEDDING_MODEL`。DeepSeek使用`DEEPSEEK_API_KEY`及可选`RAG_CHAT_MODEL`。本机已保存配置优先于环境变量。

## 6. 本轮验证结果

25项自动测试通过，覆盖版本隔离、显式双版本比较、角色与任务权限、无状态请求、原文访问、引用ID与摘录、模型失败处理、配置不回显密钥、Embedding分批顺序、HTTP会话与跨站请求边界，以及单位换算、部分回答和关联依据检索。自动测试使用模拟模型返回；另外保留独立的真实接口运行结果，不混同两类验证。

页面已检查搜索、原文及证据片段、反馈、缺依据停止生成、历史版本开关和模型设置；桌面与390像素移动端版式已查看，移动端无横向溢出。

### 关键词检索开发集基线

只运行BM25检索，top-k为6；不调用外部模型或Embedding。共24道作者草拟的开发用例、41个必要证据组，命中37组；20道题命中全部必要证据组。

| 用例 | 未进入前6的预期证据 | 影响 |
| --- | --- | --- |
| QA-15 | POL-EVIDENCE | 权限拒答仍由程序边界处理，但对应流程依据未召回 |
| QA-18 | SYN-NORM-CONFLICT | 缺少冲突处理规范上下文 |
| QA-21 | SYN-NORM-APPEARANCE | 缺少外观观察完整要求 |
| QA-22 | SYN-NORM-ACCESS | 缺少资料指令与权限规范上下文 |

这是检索证据覆盖结果，不是回答准确率。语料极小，全部为开发集；标签专业复核未完成，没有独立测试集、真实报告代表性或业务收益验证。报告任务问答的检索也不能代替完整AI Work流程验收。

### 复现方式

```bash
python3 -m unittest discover -s tests -v
python3 scripts/evaluate_retrieval.py --output /tmp/powerbank-keyword-check.json
```

检索结果保存在[retrieval-baseline-v0.1.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/retrieval-baseline-v0.1.json)。评测脚本可以读取答案标签，应用运行代码不会读取。

## 7. 引用校验的实际边界

程序检查引用ID属于本次授权证据、短引文确实出现在该证据块中。它尚不能自动证明自然语言结论必然由引用推出；`semantic_review`仍标为pending，需要人工复核。不得把“引用校验通过”表述为专业技术结论已验收。

标准资料目前只有题录与公告摘要；请求真实条款或限值时，程序直接说明缺依据。任何模拟阈值都不能作为真实实验操作、国家标准限值或认证结论。

## 8. 真实接口验证与下一步

已使用`qwen-flash`及`text-embedding-v4`完成真实问答、26块向量索引建立及24题多轮运行。当前混合检索命中41个预期证据组，同版关键词检索命中39组；数据仅为作者草拟开发集。最后一轮20个生成请求中1个错误引用被程序拦截，另有输入输出角色混淆等未被引用校验识别的语义问题。完整条件、失败、耗时及结果链接见[真实接口验证与问题记录](live-validation-v0.1.md)。

本轮补充任务内关联规格和记录要求，并提供明确数字的秒到毫秒换算辅助。后续先解决角色、时点、数值及引用语义的一致性。只有在确有检索排序瓶颈时再接远程Rerank；尚未调用百炼Rerank。DeepSeek对照需固定相同题目与证据，不能把检索配置差异误认为生成模型差异。

正式质量目标、延迟与成本门槛需结合真实试点另行确定。当前阶段止于本机原型，不自动发起认证、量产放行或企业部署。


## 方法补充

结合用户提供的既有任务表更新原型，本轮补充了实际生成请求的提示词和规范化请求体SHA-256，便于后续固定条件比较。格式校验与语义判断仍分开；原始观察和后续验收关注点见[工作流与验证方法补充](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/docs/shared/workflow-verification-notes.md)。本轮不复制其业务数据或认证配置。
