# AI Work 需求实现与验收对照

2026-10-29 页面v0.4.3：已修复依据停用后历史访问被一并阻断的问题。当前权限保留时可查历史任务、PDF与导出，停用依据不能用于新检查，撤权仍拒绝访问。141个自动测试、35项专项HTTP及51项既有流程检查通过。见[停用依据历史访问修复与回归](basis-history-access-v0.4.3.md)。

2026-10-29整理，核对应用基线为此前已完成的页面v0.4.2。

本轮以 PRD v1.0 的15节需求、11个AW验收用例及10个共用KB验收用例核对页面v0.4.2。受控模拟报告的上传、规则核对、引用、复核、导出和恢复已具备；完整PRD中的动态依据与适用性、知识发布维护、AI Work语义/模型链路和企业试点条件仍有缺口。当前可交付受控模拟演示，尚不满足完整需求或真实业务验收。

核对代码基线为 [73abf7a](https://github.com/zhujy9413-commits/powerbank-rag-agent/commit/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d)；规则/解析仍v0.4。范围为PB-DEMO-01、A1/C1、5 V输出、单口短路保护已有记录。智能客服能力只作共用实现参考，未在AI Work执行的能力不计完成。

## 状态与优先级口径

“已实现”指明确支持范围内有可执行实现和现有验证；“部分实现”指只完成一部分或采用简化方案；“未实现”指AI Work缺少对应可执行能力，或业务验收尚未发生。功能状态与业务验收分别记录，状态数量不换算完成率。

本次拆分36个核对单元，统计为已实现14项、部分实现14项、未实现8项；覆盖PRD全部15节。数量取决于拆分粒度，不能解释成需求权重或产品成熟度。

原PRD的P0核心价值范围保持。下文缺口按当前阶段排序：P0指已支持流程中导致错误确定判断、越权泄露或核心操作无法完成的阻断；P1指扩大范围或试点前需补齐；P2为非阻断的体验与管理改善。“试点前置条件”和“范围外候选”单列。本轮7项临时库观察没有新增P0判定；历史停用行为列P1，下一轮优先处理。

## 逐项对照

### 输入 解析与适用范围

| 编号及PRD节 | 需求与状态 | 当前实现 | 缺口或限制 | 证据 |
| --- | --- | --- | --- | --- |
| AW-R01 / 03,04,05 | 受控PDF上传与文件身份 · 已实现 | ≤2 MB、1至12页、≤80000字符；保存文件名、页数及SHA-256，拒绝不支持模板。 | 仅适用于PB-DEMO-01模拟模板；限制为原型固定值。 | E01, E07, E12 |
| AW-R02 / 04,05 | 型号及报告业务身份提取 · 部分实现 | 检查模拟模板标识并固定model=PB-DEMO-01；提取报告填写的规格版本。 | 未通用提取并核对型号；报告编号、报告自身版本/日期未作为字段保存。规格版本不等于报告版本。 关联G05 | E01, E22 |
| AW-R03 / 03,04 | 任务列表与可编辑任务名 · 部分实现 | 按所有者恢复任务，显示文件名、任务ID及输入修订；最多返回最近50项。 | 无自定义任务名或改名接口；列表分页和完整状态/创建时间展示未实现。 关联G09 | E05, E08, E19 |
| AW-R04 / 05,10 | 关键解析值修正及原始值保留 · 部分实现 | 唯一定位的已有记录可修正value并填原因，保存原值、操作者与时间。 | 缺失、多条对应记录不能在界面补齐/重映射；条件与适用项不可编辑确认。 关联G05 | E03, E08, E12 |
| AW-R05 / 05,07 | 解析覆盖与遗漏可见 · 已实现 | 候选/已映射/未映射、缺页声明、未知编号、孤立单位和局部条件诊断进入结果。 | 保守检测只覆盖已验证模板；映射成功不代表全文无遗漏。 | E02, E14, E15 |
| AW-R06 / 05 | 图片与扫描页处理 · 部分实现 | 实际绘图图片或无文字页明确提示未验证，并使相关单元停检。 | 未执行OCR或视觉核验；装饰图片也可导致10项整体停检。通用扫描件处理在当前支持范围外。 关联G10 | E02, E14 |
| AW-R07 / 03,04,07 | 依据选择及任务内依据附件 · 部分实现 | 确认固定RevB模拟依据快照，保存来源、版本及知识发布标识。 | 无依据版本选择器、任务内规格/规范附件上传；confirm拒绝selected_basis。 关联G05 | E03, E05, E08, E19 |
| AW-R08 / 04,07 | 预期清单及适用性确认 · 部分实现 | 固定5项×2端口及一致性项；确认框展示范围，未配置内容单列。 | 无逐项适用/不适用/待确认、排除理由和自定义清单；confirm拒绝excluded_items。 关联G05 | E04, E08, E19 |

### 比较与报告处理

| 编号及PRD节 | 需求与状态 | 当前实现 | 缺口或限制 | 证据 |
| --- | --- | --- | --- | --- |
| AW-R09 / 08 | 测试条件匹配 · 已实现 | 核对5 V、输出、单口；摘要对齐同时考虑已声明环境；局部未绑定条件阻塞。 | 其他电压/角色/组合不受自动判断支持。 | E02, E04, E13, E14, E15 |
| AW-R10 / 08 | 数值和单位比较 · 已实现 | 依据文字提取模拟阈值，使用Decimal计算响应、恢复电压和温差；显示原值与式子。 | 限已配置单位与表达格式。 | E04, E12 |
| AW-R11 / 08 | 记录完整性与缺证处理 · 已实现 | 各端口检查所需记录及外观/恢复方式文字；找不到记录标缺证，不推断未测试。 | 完整性只相对固定清单成立。 | E04, E12 |
| AW-R12 / 08 | 摘要和资料一致性 · 部分实现 | 保护响应摘要与明细保留双方；检查报告填写的规格版本与选用RevB差异。 | 不覆盖任意字段/跨文档一致性；不同条件不直接当数值矛盾。 关联G05 | E04, E13, E15 |
| AW-R13 / 08 | 报告自然语言结论与数据核对 · 未实现 | 当前仅抽取支持格式的响应摘要及记录。 | 尚无通用“通过/合格”等自然语言结论与支撑数据对照。 关联G06 | E01, E02, E04 |
| AW-R14 / 06,08,10 | 结果 执行状态与未配置区分 · 已实现 | 未发现问题/不符合/冲突/缺证与未检查/失败分别保存；条件性明细可筛选。 | 固定清单外的适用性状态见AW-R08。 | E04, E05, E08, E16 |
| AW-R15 / 03,06,12 | 处理阶段及持久失败记录 · 部分实现 | 界面显示解析/检查提示，确认后可运行，结果待复核/完成/失败可恢复。 | 调用同步完成；没有持久parsing/running任务状态；解析拒绝不生成失败任务事件。 关联G07 | E05, E07, E08, E19 |

### 检索 证据 复核与导出

| 编号及PRD节 | 需求与状态 | 当前实现 | 缺口或限制 | 证据 |
| --- | --- | --- | --- | --- |
| AW-R16 / 09 | 按检查项定位报告及要求证据 · 已实现 | 每项执行任务内BM25页排序及全页字段扫描；依据通过固定RULE_SOURCES绑定。 | 依据绑定属于固定映射；语料规模及真实检索效果待验证。 | E04, E09, E16 |
| AW-R17 / 09 | AI Work语义召回与排序 · 未实现 | AI Work使用BM25+字段扫描；共享Assistant具备混合检索实现。 | AI Work没有调用向量召回或融合排序；客服能力不能算成此链路已接通。共用规范允许经验证的简化配置。 关联G03 | E04, E10, E21 |
| AW-R18 / 09 | AI Work模型辅助对齐与说明 · 未实现 | generator=deterministic_rules_no_llm，说明由规则模板生成。 | 未接模型协助字段对齐、解释和支持性校验。应先验证其增益，再决定接入；明确数值继续由规则执行。 关联G03 | E04, E17 |
| AW-R19 / 03,09,10 | 引用身份及原文查看 · 已实现 | 区分模拟依据与报告，校验报告quote属于本页；来源弹窗分开索引摘要、原文章节及全文。 | 原文章节定位限当前Markdown结构；语义支持的专业正确性未验收。 | E04, E08, E09, E17 |
| AW-R20 / 10,12 | 复核处置与追加历史 · 已实现 | 确认/排除/暂无法确认必须填理由；乐观版本检查，原系统结果保持。 | 代理处置不等于专业复核通过。 | E05, E08, E12, E17 |
| AW-R21 / 06,12 | 输入与运行版本隔离 · 已实现 | 新修订保存快照与依据，run锁定输入哈希；旧结果标历史，源码版本不兼容时要求重新导入。 | 规则更换不是自助操作；原型采用重新导入而非通用迁移。 | E03, E05, E12, E13, E16 |
| AW-R22 / 11,12 | Excel导出与结果一致 · 已实现 | 原生四表含范围、逐项结果、依据/原文与复核历史；失败及未复核内容保留，外部文字按文本写入。 | 较宽十列表与条件JSON影响阅读；本机原文不是可跨环境共享的永久链接。 关联G08 | E06, E07, E12, E17 |
| AW-R23 / 02,12 | 任务所有者及资料访问校验 · 部分实现 | 服务层按principal/owner隔离任务，PDF/结果/导出同样校验；本机服务固定一个演示身份。 | 企业登录、实际多用户身份来源、授权任务协作和权限变更未接入。 关联G02 | E05, E07, E09, E12 |
| AW-R24 / 12,13 | 本机会话与输入边界 · 已实现 | 本机绑定、会话、Origin、请求大小及允许字段检查，拒绝客户端身份覆盖。 | 验证边界为本机原型，不等同企业认证。 | E07, E12 |

### 知识维护 异常和业务验收

| 编号及PRD节 | 需求与状态 | 当前实现 | 缺口或限制 | 证据 |
| --- | --- | --- | --- | --- |
| AW-R25 / 01,09 | 知识元数据与人工入库维护 · 部分实现 | 静态manifest及知识/任务块带版本、scope、来源身份；校验脚本验证样本包。 | 元数据未构成完整审核责任/权限登记；缺增量导入、去重、审批记录和运行时维护工具。 关联G04 | E09, E20, E21 |
| AW-R26 / 01,09,13 | 知识发布与原子切换 · 未实现 | 启动时一次载入静态manifest和两份JSONL；可校验既有包。 | 无待核验→待索引→发布/停用操作链；无索引失败不切换、发布幂等和缓存撤销验收。 关联G04 | E09, E20, E21 |
| AW-R27 / 07,08 | 规则注册与专业发布门禁 · 部分实现 | 有demo-rules.json结构样例及固定RULE_SOURCES，运行从已选模拟来源提阈值。 | 运行未加载通用注册表；无draft/verified/active/suspended门禁与专业复核记录。 关联G01,G04 | E04, E05, E11 |
| AW-R28 / 06,13 | 依据停用后的历史核验 · 部分实现 | 原运行存完整snapshot及引用身份；新运行对当前依据校验。 | 仅停用依据且用户权限未变时，历史任务/结果/PDF也被auth拦截；尚无资料停用变化提示与可核对历史路径。 关联G01 | E05, E12, E19 |
| AW-R29 / 12,13 | 失败记录 重试 幂等与并发 · 已实现 | 规则运行失败保存10个失败单元，可导出；幂等请求复用，旧确认/复核版本拒绝。 | 上传失败事件见AW-R15；结果项级故障隔离见AW-R30。 | E05, E12, E16 |
| AW-R30 / 06,13 | 单项失败保留其他已完成结果 · 部分实现 | 解析/条件诊断可只停检受影响项，其他项继续展示。 | 未隔离每条规则执行异常；evaluate抛异常时整次run改为10项失败，已完成部分不保存。 关联G07 | E04, E05, E12 |
| AW-R31 / 09,15 | 运行追踪和关键事件 · 部分实现 | 有输入/报告/引擎哈希、来源、检索trace、部分耗时、修改/复核时间与操作者。 | 没有统一事件表及证据查看/导出事件；解析、等待、失败总耗时和人工成本不全。 关联G07 | E03, E04, E05, E08 |
| AW-R32 / 14,15 | 真实质量 效率与成本验收 · 未实现 | 已有模拟开发/时间留出、HTTP和代理走查记录。 | 独立专业参考、实际使用者体验、真实对照总耗时和维护成本尚未就绪。 关联G02 | E17, E18, E21 |
| AW-R33 / 01,08,15 | 真实标准与规则授权 · 未实现 | 原型显式使用模拟规则，real_compliance_enabled=false。 | 真实条款使用授权、适用白名单和专业标注未落实，不能开启真实合规判断。 关联G02 | E11, E21, E22 |
| AW-R34 / 15 | 企业部署及数据保留 · 未实现 | 本机SQLite与原文保存，配置目录不入版本库；代码拒绝非本机绑定。 | 部署身份、备份/保留/删除策略、并发及预算门槛待试点核定。 关联G02 | E05, E07, E21 |
| AW-R35 / 13 | AI Work模型失败及校正 · 未实现 | AI Work未发模型请求；客服的适配与校验属于另一链路。 | 仅当启用AI Work模型时，才需要验证格式/引文失败、有限重试和超时处理。 关联G03 | E04, E07, E10 |
| AW-R36 / 01,15 | 模拟与支持范围说明 · 已实现 | 上传及结果页明示模拟、固定范围和未配置内容；未检/失败不转为通过，无认证放行输出。 | 保持声明；本次对照不提高真实验收等级。 | E04, E06, E22 |

## PRD验收用例对照

以下为用例要求与现有证据的映射，未重新将其计算为11项或10项全通过。受控范围已覆盖仍受本页输入边界限制。

| 用例 | 当前覆盖 | 对照单元 | 判断 |
| --- | --- | --- | --- |
| AW-A01 | 部分覆盖 | AW-R02,AW-R07,AW-R08,AW-R21 | 固定型号/依据/清单可确认并锁快照；选择依据和适用性未完成。 |
| AW-A02 | 受控范围已覆盖 | AW-R09 | 当前电压/角色/组合及摘要环境差异不直接判等价。 |
| AW-A03 | 受控范围已覆盖 | AW-R10 | 支持格式内单位换算、闭区间与温差可复现。 |
| AW-A04 | 受控范围已覆盖 | AW-R11 | 缺记录标缺证，不等同实际未测。 |
| AW-A05 | 部分覆盖 | AW-R12,AW-R13 | 响应摘要矛盾保留双方；通用自然语言结论未覆盖。 |
| AW-A06 | 部分覆盖 | AW-R04,AW-R05,AW-R06 | 模糊/未解析阻塞；修正只支持唯一现有字段，尚无OCR。 |
| AW-A07 | 部分覆盖 | AW-R08,AW-R14,AW-R30 | 范围与失败单列；适用性未知、逐项排除及项级运行故障隔离不足。 |
| AW-A08 | 受控范围已覆盖 | AW-R20 | 排除与理由追加保存，原系统结果保持。 |
| AW-A09 | 部分覆盖 | AW-R21,AW-R26,AW-R28 | 输入修订隔离已验证；通用规则/知识换版和停用后历史路径不全。 |
| AW-A10 | 部分覆盖 | AW-R22,AW-R23 | 未复核/失败标记及服务层越权拒绝有测试；真实企业身份未接。 |
| AW-A11 | 受控范围已覆盖 | AW-R29 | 同请求幂等、失败保存和新运行恢复有现有测试。 |

## 共用知识库与RAG验收对照

| 用例 | AI Work覆盖 | 对照单元 | 判断 |
| --- | --- | --- | --- |
| KB-A01 | 部分覆盖 | AW-R19,AW-R25 | 受控块身份、版本、原文和scope可追溯；完整授权/审核责任元数据不足。 |
| KB-A02 | 受控范围已覆盖 | AW-R05,AW-R09 | 支持模板的单位/脚注及局部条件可绑定；未知内容停检。 |
| KB-A03 | 未覆盖 | AW-R26 | 无运行时发布、原子切换及失败不切换验证。 |
| KB-A04 | 受控范围已覆盖 | AW-R16,AW-R23 | 上传报告在任务存储并以当前快照扫描，不自动进入客服静态索引；owner校验。 |
| KB-A05 | 部分覆盖 | AW-R23,AW-R28 | 现时role/owner/source校验存在；停用/撤权生命周期和历史核验未完整实现。 |
| KB-A06 | 部分覆盖 | AW-R19 | 引用ID和报告逐字定位检查已做；全面语义支持仍需专业验收。 |
| KB-A07 | 受控范围已覆盖 | AW-R24,AW-R36 | 输入不生成工具执行；受控注入文本不改规则；无任意代码执行路径。 |
| KB-A08 | 部分覆盖 | AW-R27,AW-R33,AW-R36 | 界面/数据明确模拟；模拟块在演示包publication_status=active，不是正式规则active状态，尚无生产目录。 |
| KB-A09 | 部分覆盖 | AW-R17,AW-R18,AW-R21,AW-R31 | 本机现有run快照/检索可回放；动态知识版本仓及AI Work模型配置链尚未建。 |
| KB-A10 | 部分覆盖 | AW-R20,AW-R29,AW-R26 | 运行幂等与复核并发已验证；发布流程未实现，不能宣称发布幂等。 |

## 缺口处理顺序

| 编号及等级 | 进入时点 | 问题与下一动作 | 验收要求 |
| --- | --- | --- | --- |
| G01 · P1 | 下一轮优先补齐，可用现有模拟资料验证 | 停用依据后历史证据不可核对。将新运行依据有效性与历史读取授权分开；依据停用后保留现有权限下的快照及原文入口并展示变化，权限撤销继续拒绝；更新现有停用测试的断言。 | 仅停用时旧任务/结果/PDF可按权限查看、新运行被拦截；撤销访问权时相关入口全部拒绝；原结果和复核历史不变。 |
| G02 · 试点前置条件 | 接入任何真实业务前 | 真实资料 专业复核 身份与效果门槛未落实。明确材料授权及规则白名单、独立专业复核、真实身份和部署/保留策略；锁定人工可用性与质量/总耗时评测方案。 | 对应责任与授权、部署方案及指标有可审核记录，再启动真实试点；当前保持模拟演示。 |
| G03 · P1 | AI Work RAG扩展决策前 | 设计中的混合检索和模型辅助未在AI Work接通。对同一检查集比较现有BM25/字段扫描与候选语义检索/模型辅助的证据命中、误配、延迟和成本；明确采用简化RAG或补足能力的决策。 | AI Work独立trace、证据与效果对比可复现；若模型接入，引用/适用条件失败须收敛，不把客服结果冒充此链路结果。 |
| G04 · P1 | 需要变更知识或规则的内部试点前 | 静态知识包与固定规则缺发布维护闭环。先补简易入库核验、发布记录、版本切换/失败回退、停用与规则状态门禁；复杂管理后台继续后移。 | 未核验资料不默认可检索；失败不切换当前快照；新旧任务分别绑定正确版本；停用与撤权按G01验证。 |
| G05 · P1 | 扩大型号 依据或检查范围前 | 身份 依据 清单和修正流程固定。补必要身份字段、依据选择/任务附件、逐项适用性及排除理由；多记录重映射和条件修改需保存明确证据。 | 型号或条件无法确认时阻塞相应项目，旧快照不改写；用户选定范围与明细及导出对账一致。 |
| G06 · P1 | 承诺结论一致性自动核对前 | 通用报告结论与数据对照未实现。先选受控结论表达和字段白名单；未知表述显示未核验，再评测模型辅助是否必要。 | 结论与明确矛盾数据展示双方；缺证不自动判不符合或通过；不把摘要数值核对等同通用结论核对。 |
| G07 · P1 | 扩展并发 长任务或测量业务效果前 | 阶段 事件和项级失败记录不足。补持久阶段与关键事件、失败计时、单项异常隔离及恢复规则；计入人工准备/复核成本。 | 可定位失败阶段且失败样本进入指标；一项异常不覆盖已完成项；不把系统毫秒当人工省时。 |
| G08 · P2 | 交付阅读体验优化时 | Excel宽表和条件JSON可读性。以中文条件字段呈现，优先冻结识别列/安排阅读列序；保持四表信息、单位、引用及历史。 | 实际应用导出可读；全值/结果/历史一致，原生Excel阅读仍需使用者验收。 |
| G09 · P2 | 实际任务积累或名称辨识成为问题时 | 任务名及列表完整性。补可编辑任务名、基本状态/日期及分页；不把任务名当身份。 | 名称变更不改文件哈希与运行；超过50项时可取回旧任务。 |
| G10 · 范围外候选 | 出现代表性扫描/图片资料且收益明确后 | OCR及复杂图片自动判读。保留当前停检；另行用代表性资料验证OCR与关键值人工核验成本。 | 未核实图内字段不产生确定结论；是否纳入MVP需证据支持。 |

## 本轮新增观察与已有证据

本轮仅新增7项隔离服务观察，均在临时模拟库中执行，不读取或改动本机任务/模型配置。观察包含固定目录、拒绝依据选择字段、拒绝适用项排除字段、依据停用后的历史路径、解析拒绝无失败任务、拒绝任务名称字段、拒绝任务内依据附件字段；其中“拒绝”用于确认当前未支持的接口，不记作功能通过率。

历史依据问题已复现：停用SYN-NORM-RESPONSE且用户访问权不变时，task、run、pdf和新运行均被ValueError拦截。原因是_task先调用当前basis_catalog。tests/test_ai_work.py现有测试也断言停用后task读取失败，因此133项回归通过与这一需求差距可以同时成立。后续修复应分开资料停用和权限撤销，并调整相应断言，不能放松越权拒绝。

最近133项回归、三场景51项HTTP结果及正常r3代理走查作为既有证据引用，本轮应用未修改，未重跑全量回归；没有新增留出集或独立评测分数。旧首次成绩保持。专业规则、实际使用者体验与人工省时仍待验证。

## RAG与知识库当前边界

AI Work运行从固定来源ID取得模拟要求，并用任务内BM25页排序与全页字段扫描定位报告记录，随后执行确定性比较并保存引用。输出说明为规则模板，本链路模型请求为0。

共用Assistant.search已有BM25与向量融合实现，属于智能客服执行路径；AI Work没有调用它，也未接通模型字段对齐。共用设计允许经任务验证的简化检索，下一轮应明确简化配置的支持证据或做候选方案比较；无需为了结构齐全把明确数值交给模型判断。

知识库目前为静态发布包，来源与原文可查，但缺运行时核验/发布/停用维护流程。demo-rules.json为结构样例，当前评审执行器没有把它作为通用规则注册表加载。模拟知识块的publication_status=active表示演示包可检索，不表示真实规则已专业审核active；真实合规开关仍关闭。

## 证据索引

代码链接固定到本次核对基线；本轮新记录使用main链接。完整SHA-256及结构化需求映射见机器记录。

| 证据 | 内容 | 维护源 |
| --- | --- | --- |
| E01 | 受控PDF校验、文件身份与规格版本提取 | [app/ai_work/review.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/ai_work/review.py#L52) |
| E02 | 候选审计、跨行归属、局部条件与图片停检 | [app/ai_work/parsing.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/ai_work/parsing.py#L78) |
| E03 | 确认快照、单一记录修正与修订约束 | [app/ai_work/review.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/ai_work/review.py#L348) |
| E04 | 固定清单、检索记录、确定性计算与检查结果 | [app/ai_work/review.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/ai_work/review.py#L134) |
| E05 | 任务所有者、输入/运行/复核存储及幂等 | [app/ai_work/review.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/ai_work/review.py#L283) |
| E06 | 四表导出、范围与历史记录 | [app/ai_work/export.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/ai_work/export.py#L14) |
| E07 | 本机会话、路由及服务端访问检查 | [app/knowledge_assistant/server.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/knowledge_assistant/server.py#L127) |
| E08 | 页面输入、证据、筛选、复核及状态展示 | [app/knowledge_assistant/static/work.js](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/knowledge_assistant/static/work.js) |
| E09 | 静态语料载入、权限与原文章节 | [app/knowledge_assistant/core.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/knowledge_assistant/core.py#L69) |
| E10 | 智能客服混合检索，AI Work未调用 | [app/knowledge_assistant/core.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/knowledge_assistant/core.py#L182) |
| E11 | 模拟规则结构示例，非运行时通用注册表 | [data/bootstrap-v0.1/rules/demo-rules.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/data/bootstrap-v0.1/rules/demo-rules.json) |
| E12 | 现有功能、越权、幂等、并发与失败回归 | [tests/test_ai_work.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/tests/test_ai_work.py) |
| E13 | 既有模板、条件、快照及导出回归 | [tests/test_pdf_variants.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/tests/test_pdf_variants.py) |
| E14 | 未知编号、混排图片和局部条件回归 | [tests/test_ai_work_p0.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/tests/test_ai_work_p0.py) |
| E15 | 跨行摘要和单位归属回归 | [tests/test_ai_work_p1.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/tests/test_ai_work_p1.py) |
| E16 | 既有三场景51项HTTP结果 | [eval-results/workflow-http-v0.4.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/eval-results/workflow-http-v0.4.json) |
| E17 | 既有正常r3代理走查及源码摘要 | [eval-results/delegated-walkthrough-v0.1.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/eval-results/delegated-walkthrough-v0.1.json) |
| E18 | 最近一次133项完整回归日志 | [eval-results/delegated-walkthrough-regression-v0.1.txt](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/eval-results/delegated-walkthrough-regression-v0.1.txt) |
| E19 | 本轮7项临时库观察，含预期拒绝及历史停用缺口 | [eval-results/prd-implementation-audit-probes-v0.1.json](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/prd-implementation-audit-probes-v0.1.json) |
| E20 | 静态样本包与索引元数据校验 | [scripts/validate_bootstrap_pack.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/scripts/validate_bootstrap_pack.py) |
| E21 | 共用设计及KB验收口径 | [docs/shared/knowledge-base-rag.md](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/docs/shared/knowledge-base-rag.md) |
| E22 | 当前页面支持范围与固定清单说明 | [app/knowledge_assistant/static/index.html](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/app/knowledge_assistant/static/index.html#L42) |
| E23 | 本轮隔离观察复现脚本 | [scripts/probe_ai_work_prd_gaps.py](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/scripts/probe_ai_work_prd_gaps.py) |

- [完整结构化核对结果](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/prd-implementation-audit-v0.1.json)。
- [本轮7项隔离观察](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/prd-implementation-audit-probes-v0.1.json)。
- [原PRD设计基线](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/docs/ai-work/PRD.md)及[原MVP范围](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/73abf7a55ec33734296fc7e4d626cb4e5eee5d2d/docs/ai-work/MVP.md)。

[文档引用与映射一致性校验](https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/eval-results/prd-implementation-audit-validation-v0.1.json)只检查文档结构与来源，不计入应用功能测试。

本轮观察可用以下命令复现，输出须为新路径，临时库随运行清理。

```bash
python3 scripts/probe_ai_work_prd_gaps.py --output eval-results/prd-audit-probes-new.json
```

## 首版交付判断

受控模拟演示可继续交付；先补G01历史依据停用后的核验路径，再处理G03检索/模型方案验证与G04简易知识发布维护。G05、G06、G07在对应能力扩展前验收；G08、G09进入后续体验排序；G10保持范围外。G02作为真实试点准入条件独立跟踪。

本轮交付为需求实现与验收对照，未实施上述缺口修复，也未把模拟流程标为完整MVP通过。后续操作指南与三场景演示可引用本页支持范围；企业试点需另具备G02证据。
