# 角色范围与引用修复回归

日期：2026-10-27。本轮修复已识别的输入输出角色混淆、摘要端口错配和引用编号问题。39项本地回归通过；最终24题开发集运行无生成失败，另有6次重点重复测试通过引用校验。此结论仅针对当前公开摘要与模拟样本，尚未完成专业业务验收。

## 1. 修复前后

| 问题 | 修复前的实际表现 | 当前处理 |
| --- | --- | --- |
| 测试角色 | 把“C1的5 V输出角色”写成“C1充电输入的5 V输出角色” | 从授权规格的明确范围句提取端口、角色与电压，由程序呈现，不交给模型改写角色 |
| 摘要归属 | 因A1明细与C1摘要都出现80 ms，把C1摘要归到A1 | 按报告、端口、测试字段关联；同数值不能决定归属。C1摘要80 ms与C1明细680 ms保留为冲突 |
| 虚构引用 | 将换算字段或题设当作证据编号 | 模型只能选择本次来源目录中的编号；真实证据ID与原文由程序解析填入 |
| 有编号但缺支撑 | 讲R04实测值时只引用规格，未引用R04记录 | 仅从同一次授权目录补齐唯一对应的记录或摘要，并记录补充；仍校验记录号及摘要原文 |
| 校验失败 | 生成失败时难以比较校正前后 | 校验失败最多校正一次；保留每次原始候选、错误、请求摘要和用量，不覆盖失败 |

范围说明显示“规格范围 · 按原文生成”；响应记录核对显示“记录核对 · 按原文计算”。这两条路径不调用生成模型，仍先执行授权、版本及检索范围筛选。标准实施日期的既有程序提取也继续保留。

## 2. 关键样例

QA-12当前说明：模拟RevB只配置A1、C1的5 V输出角色；其他角色、电压等未配置，不能认定输入角色或全部快充档已覆盖。依据为`SYN-SPEC-PB01-RevB-SCOPE`。

QA-17当前说明：R02属于C1端口，明细为0.68 s；摘要S01也属于C1，记载80 ms。程序换算0.68 s为680 ms，确认同端口摘要与明细不一致。仅按R02作条件性比较时，680 ms超过模拟上限500 ms；冲突继续保留未决。引用同时包含原始记录、摘要、模拟规则及冲突处理约定。

上述限值均为模拟数值，不是国家标准限值或真实测试结论。记录核对只覆盖当前明确的模拟响应记录格式，不等于完整AI Work报告评审已经实现。

## 3. 最终实测

模型仍使用百炼`qwen-flash`及`text-embedding-v4`，语料快照仍为`BOOTSTRAP-20261026-01`，top-k为6。24题及参考标签未修改；运行代码不读取评测题目、参考答案或标注。检索算法与上轮相同，本次未重建或更换向量模型。

| 指标 | 最终完整运行 | 重点重复运行 |
| --- | --- | --- |
| 测试范围 | 24题，各1次 | QA-10与QA-18各3次，共6次 |
| 必要证据组命中 | 41/41 | 15/15，按6次请求计 |
| 进入生成的请求 | 18题 | 6次 |
| 实际生成接口调用 | 19次，含1次校正 | 8次，含2次校正 |
| 校正后通过结构与引文校验 | 18/18个生成请求 | 6/6次 |
| 校正前被拒绝的候选 | 1个，保留原返回 | 2个，保留原返回 |
| 必要来源补充 | 2处 | 6处 |
| 最终生成失败 | 0 | 0 |
| 检索到越权证据 | 0 | 0 |

完整运行另外有3题由程序回答：标准日期、范围说明、响应记录核对；另有3题因缺条款、无内部权限或未选任务而停止生成。这些情况没有伪装成模型回答，也没有把拒答当作技术通过。

完整运行耗时中位数1.99秒，P95为3.60秒，最长4.82秒，包含程序路径和未生成请求。记录的生成用量为27,045 tokens；重复运行为11,393 tokens。均不含Embedding、网页请求或中间运行，实际费用以服务方账单为准，不作为生产性能或成本承诺。

## 4. 回归与页面检查

39项测试包含原有版本、权限、会话、配置及引用边界，以及新增的范围改写、输入输出复合错误、换端口与换数值、参数问题不被范围说明接管、记录号支撑、摘要来源、未知引用、一次校正上限、失败保留和必要来源补充。测试中接口使用模拟返回；上表另为独立真实调用。

实际网页已检查QA-12和QA-17：范围说明及冲突状态、按原文生成的标签、单位比较和引用按钮均能呈现。模型配置、密钥和本机数据库未纳入同步。

## 5. 边界与待复核项

范围与响应记录解析目前支持本样本包的明确句式。未识别的格式、多版本或不完整来源不会被程序猜成已覆盖；参数和硬件能力问题继续走正常问答。真实PDF解析与完整技术规则引擎仍需后续实现。

来源目录保证引用来自当前授权证据，并原样填入引文；记录与摘要检查补充了局部语义约束。它仍不能证明所有自然语言结论都由引用推出。例如QA-21的外观和恢复方式复合结论，其规范来源分配仍需复核；QA-18的版本冲突及条件性措辞也不能替代负责人最终判断。

当前不发布回答准确率、评审工时收益或专业验收通过率。开发集标签待专业复核，`final_human_decision`仍为空。通用语义判断与独立测试集仍是后续工作。

## 6. 运行材料与复现

- [最终24题全部输出](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/live-role-citation-final-v0.9.json)
- [两题各重复3次的输出](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/live-citation-repeat-v0.9.json)
- [初次来源目录验证](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/live-role-citation-v0.5.json)
- [中间运行v0.6](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/live-role-citation-intermediate-v0.6.json)、[v0.7](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/live-role-citation-intermediate-v0.7.json)、[v0.8](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/live-role-citation-intermediate-v0.8.json)

中间运行保留了“引用合法但端口归属错误”及“R04缺少记录来源导致两次校验均失败”的实际结果。最终结果以v0.9为准，没有删除或覆盖中间失败。输出记录代码、题集、语料和实际请求摘要；模型别名对应的服务端具体版本未锁定。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/evaluate_live.py --keyword-baseline eval-results/retrieval-keyword-v0.4.json --output /tmp/powerbank-role-check.json
python3 scripts/evaluate_live.py --keyword-baseline eval-results/retrieval-keyword-v0.4.json --case QA-10 --case QA-18 --repeat 3 --output /tmp/powerbank-citation-repeat.json
```

输出路径须使用新的文件名。真实评测会产生服务方用量。原始模型候选在`provider_attempts`中，必要来源补充在`source_anchor_additions`中；这两者与最终可展示结果分开保留。
