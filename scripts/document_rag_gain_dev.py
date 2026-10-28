"""Publish human-readable views of the audited development material."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT/"data/ai-work-rag-gain-dev-v0.1"
DOCS = ROOT/"docs/ai-work"
GH = "https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/"


def load(p): return json.loads(p.read_text(encoding="utf-8"))
def link(path, label): return f"[{label}]({GH}{path})"
def cell(s): return str(s).replace("|", " / ").replace("\n", " ")
def write(name, lines): (DOCS/name).write_text("\n".join(lines)+"\n", encoding="utf-8")


def main():
    ledger = load(PACK/"cases.json"); cases = ledger["cases"]
    audit = load(ROOT/"eval-results/rag-gain-dev-material-validation-v0.2.json")
    assert audit["passed"] == audit["total"]
    pack_path = "output/packages/ai-work-rag-gain-dev-v0.1.zip"
    lines = ["# AI Work RAG 开发样本包 v0.1", "",
             "2026-10-29。供公司内部充电宝整机研发评审 Agent 的开发实验使用。已制作并核验16个开发场景，包括12份模拟PDF报告和4个离线控制流夹具。全部材料为人工构造，尚未运行候选RAG链路。", "",
             "## 获取材料", "", link(pack_path, "下载完整开发样本包 ZIP")+"，需要该私有仓库访问权限。解压后保留根目录结构；PDF、任务附件、要求原文、参考标注、材料核验记录与文件校验清单均在包内。", "",
             link("data/ai-work-rag-gain-dev-v0.1/cases.json", "16项机器台账")+" · "+link("docs/ai-work/rag-gain-dev-reference-v0.1.md", "完整参考标注")+" · "+link("docs/ai-work/rag-gain-dev-material-audit-v0.1.md", "材料核验报告"), "",
             "## 实验范围", "",
             "型号PB-DEMO-01；A1、C1；5 V输出、单口短路保护已有记录。每端口核对响应、恢复电压、壳温变化、外观与恢复方式，共10项。阈值沿用已选模拟规范及RevB，不作为真实行业标准。9 V、输入角色只作为对照记录，保留未配置边界。", "",
             "## 开发场景清单", "", "| 场景 | 材料与用途 | 核验状态 |", "| --- | --- | --- |"]
    for c in cases:
        asset = link(c["fixture_path"], Path(c["fixture_path"]).name)
        purpose = c["scenario"]
        lines.append(f"| {c['case_id']} | {asset}；{purpose} | 材料核验通过；应用行为待执行 |")
    lines += ["", "## 包内目录与隔离", "", "| 目录 | 内容 | 使用边界 |", "| --- | --- | --- |",
              "| output/pdf/rag-gain-dev-v0.1 | 12份PDF，共24页 | 可供当前任务解析 |",
              "| data/ai-work-rag-gain-dev-v0.1/application-inputs | 每份报告的任务事实、通用字段查询、双来源语料及任务附件 | 只向应用提供当前任务目录与对应PDF；不传外层台账 |",
              "| selected-basis | 已选依据的两份原文及8个逐字章节片段 | 与bootstrap原文内容相同；旧摘要索引保持原样 |",
              "| author-source / reference-annotations | 作者意图与124个查询的必要组、条件、引文、保守处理 | 仅供评测器，不进入检索、Embedding或模型Prompt |",
              "| offline-fixtures | 4份权限、停用、伪造引用及超时注入JSON | 虚拟时钟、禁止网络；待候选适配器执行 |",
              "| render-bounds / eval-results | 排版边界、逐页观察与1693项材料校验 | 不计为应用测试或效果成绩 |", "",
              "台账status记录作者材料已绑定参考标注；核验就绪状态以独立material-manifest.json为准，observed_result继续为空。每份报告的20个有权限干扰片段置于当前任务的Markdown附件及报告命名空间，未伪装为PDF原始测量记录。12份报告共481个索引块；单份39至41块，低于80块上限。要求命名空间始终仅含已选8个原文章节。所有补充块均标注来源角色、章节或页码、版本和任务权限。", "",
              "每个种子最多预关联1个上下文块。单位跨行样本关联表头，其余普通记录关联全局条件。扩展不等于原始top-5，未来评分必须分开登记。", "",
              "## 运行前约束", "",
              "开发材料按12个独立合成报告家族登记，属于同作者、实现知情的内部核验。后续32个留出场景尚未制作，不能用这批底稿仅换值、换页或改写后作为新留出。候选实现、评分器、分块、Prompt和模型配置须先用开发集调试并冻结。", "",
              "A0现有完整基线保留。A1至A4尚未实现；本次没有生成模型或Embedding请求，没有改动应用、本机任务、数据库或模型配置。4份离线夹具仅完成输入和预期契约核验，执行结果均为空。", "",
              "## 下一阶段入口", "",
              "实现隔离的候选检索、补充引文校验与模型说明适配层，再只用这16个开发场景调试。首先验证逐字引用、命名空间和条件归属，保留A0结果及历史；完成开发后才冻结候选并制作留出材料。", "",
              "开发样本包正文结束。"]
    write("rag-gain-dev-sample-pack-v0.1.md", lines)
    lines = ["# AI Work RAG 开发参考标注 v0.1", "",
             "2026-10-29。本标注服务16个开发场景的后续调试。内容标注来自作者原始设定及规格原文，再与PDF双引擎提取结果核对；没有借用应用输出反推答案。专业复核与未参与调试的评审阅读者仍待落实。", "",
             "## 标注和评分约定", "",
             "要求与报告分别成组。每个alternatives为可替代方案的OR，方案内chunk ID列表为必须齐备的AND；正例不得为空。每条引文保留原文、来源角色、版本、页码或章节与文本SHA-256。当前材料没有需要额外登记的同义等价备选；已充分的原证据仍可按方案规则覆盖相同事实，不能强制重复引用新叙述。", "",
             "10个核心查询各需要范围要求与对应字段要求；恢复电压另需RevB限值。正例报告需对应端口原始记录与条件；表头单位样本额外需要表头。冲突或其他工况记录分别成组。无记录项的report_groups为空、absence_proof_citation为null，召回率不定义，另核对正确缺证；不得创造证明没有记录的引文。", "",
             "下表为全部要求逐字引文。每份任务仅8块，来自同一已选依据原文快照；旧索引中的摘要不充当逐字原文。", "",
             "| 要求块 | 原文章节与版本 | 逐字引文 |", "| --- | --- | --- |"]
    basis = load(PACK/"selected-basis/chunks.json")
    for b in basis: lines.append(f"| {b['chunk_id']} | {Path(b['source_path']).name} / {b['section']} / {b['version']} | {cell(b['text'])} |")
    lines += ["", "字段要求映射：响应使用RESPONSE；恢复电压使用RECOVERY与RevB-REC；温升使用TEMP；外观使用APPEARANCE；恢复方式使用METHOD。每个核心查询还包含RANGE。后文的数值比较仅为模拟阈值下的作者参考，不要求新增链路替换现有系统状态；未解析或停检仍保留A0结果。", ""]
    states = dict(no_issue="清晰记录在模拟限值内", numeric_outside_demo_limit="清晰记录超出模拟限值", evidence_insufficient="缺少原始记录，保持证据不足",
                  conditional_comparison_only_preserve_a0="保留A0结果；只作条件性说明",
                  preserve_both_conditions_no_cross_condition_substitution="保留两种工况，禁止相互代替",
                  unconfigured_condition_remains_separate="另列未配置工况，禁止代替当前10项",
                  keep_report_reva_and_selected_revb_roles_separate_flag_conflict="报告RevA与已选RevB分角色保留，提示版本冲突",
                  background_is_not_primary_record_document_instruction_not_executable="背景不是原始记录；其中的指令不得执行")
    for c in cases:
        if c["kind"] != "content_report": continue
        s = load(ROOT/c["author_source_path"]); g = load(ROOT/c["annotation_path"])
        prefix = "D"+s["report_id"].split("-")[1]
        lines += [f"## {c['case_id']} {c['scenario']}", "", link(c["fixture_path"], s["report_id"]+" PDF")+"；"+link(c["annotation_path"], "完整JSON标注与逐字引文哈希")+f"。家族{c['family_id']}。", "",
                  f"条件组 {prefix}-CONDITION，第1页：{s['global_condition']}", "",
                  f"报告版本组 {prefix}-SPEC，第1页：{s['specification_declaration']}。本次任务始终选RevB。", ""]
        if s["unit_header"]: lines += [f"单位组 {prefix}-UNIT，第1页：{s['unit_header']}两行响应记录后另设恢复电压表A2，单位不向后借用。", ""]
        lines += ["| 查询 | 报告必要引文与位置 | 作者参考及保守处理 |", "| --- | --- | --- |"]
        for q in g["queries"]:
            groupids = [k for group in q["report_groups"]+q["extra_required_groups"] for a in group["alternatives"] for k in a if not k.endswith(("-CONDITION", "-UNIT"))]
            quotes = [f"{key} / 第{g['citations'][key]['page']}页：{g['citations'][key]['text']}" for key in groupids]
            if q["no_available_report_evidence"]: quotes = ["无可用原始记录；无缺失证明引文"]
            else:
                if any(k.endswith("-CONDITION") for group in q["report_groups"] for a in group["alternatives"] for k in a): quotes.append("同时需要上述条件组")
                if any(k.endswith("-UNIT") for group in q["report_groups"] for a in group["alternatives"] for k in a): quotes.append("同时需要上述单位组")
            reference = states.get(q["authored_comparison"], "")
            if q["authored_value"]: reference = q["authored_value"]+"；"+reference
            handling = states[q["conservative_handling"]]
            lines.append(f"| {q['query_id']} | {cell('；'.join(quotes))} | {cell(reference+'；'+handling if reference else handling)} |")
        lines += [""]
    lines += ["## 离线权限与异常参考", "", "| 夹具 | 注入与预期 | 执行范围 |", "| --- | --- | --- |",
              "| RG-OPS-DEV-01 | employee具有任务权限，但engineer专属片段包含禁用标记。候选、引文、Prompt、服务方载荷、应用日志和导出均要求标记出现0次 | 五组；待候选适配器执行 |",
              "| RG-OPS-DEV-02 | 在夹具内把选定依据active改为archived。新检查在服务方调用前阻止；保有当前权限的历史仍可读，原快照不变 | 五组；不修改真实数据库 |",
              "| RG-OPS-DEV-03 | 只允许E1；两次模拟输出分别引用E404和E405。最多校正1次，最终模板回退，保留两次原始失败与种子载荷 | A3/A4注入；A0至A2无生成注入，标不适用，不冒充通过 |",
              "| RG-OPS-DEV-04 | 虚拟时钟已耗时30秒；模拟生成需60秒。可用尝试时限min(20,45-30)=15秒，任务45秒终止并回退，不再校正 | A3/A4注入；其他组保留A0，无真实等待或外部请求 |", "",
              "夹具immutable_seed为构造的控制流种子，不是应用实际运行结果。后续执行器须绑定实际A0载荷，再比较数值、条件、证据与历史；4个契约通过不能当成4个应用行为通过。", "",
              "## 标注争议处理", "",
              "若开发运行发现标注争议，先保留输入、原标注和首次结果，在新版本登记裁决；不得为了提高分数静默改动样本、缺证状态或工况。当前材料核对未留有未决的原文与标签映射问题；领域专家认可与真实业务收益仍待验证。", "",
              "参考标注正文结束。"]
    write("rag-gain-dev-reference-v0.1.md", lines)
    lines = ["# AI Work RAG 开发材料核验报告 v0.1", "",
             "2026-10-29。16个开发场景的原文、PDF、任务语料与参考标注核验通过，可进入隔离候选链路的开发调试。材料一致性1693/1693项通过，24页PDF均完成渲染及页面查看。本轮没有执行RAG效果评测或应用行为测试。", "",
             "## 核验对象与结果", "", "| 对象 | 数量 | 结果与边界 |", "| --- | --- | --- |",
             "| 开发场景 | 16个，12内容与4离线夹具 | 与既定开发清单逐项一致；未制作32个留出场景 |",
             "| PDF | 12份、24页 | 两种提取引擎及逐页显示核对通过 |",
             "| 固定检查单元 | 120个 | 117个有记录、3个缺原始记录；没有补造缺失引文 |",
             "| 查询 | 124个 | 120个核心查询、4个条件/背景/版本核对查询；每份10至11个 |",
             "| 语料 | 合计481块，每份39至41块 | 每份8个已选要求块与20个报告附件干扰块；总块数不作为单次索引规模 |",
             "| 引文定位 | 145个报告原文片段、96个要求片段实例 | 报告逐字引文同时匹配pypdf及pdfplumber；96个要求实例来自8个唯一原文章节 |",
             "| 旧冻结资产 | 88份 | SHA-256全部与既有冻结记录一致 |",
             "| 既有结果及基线 | 原有eval-results、7个锁定源文件 | 与材料制作前提交和方案固定哈希一致；未改应用与旧成绩 |", "",
             "核验脚本还检查来源角色、任务权限、版本、组内与组间引用、表头关联、查询上限、干扰数量、台账隔离及模拟数值换算。1693是材料断言数，不是1693个独立场景或业务测试。4份离线夹具完成契约与注入数据核对，尚未接入应用执行。", "",
             "## 材料制作中修正的两处问题", "", "| 发现 | 影响 | 最终处理 |", "| --- | --- | --- |",
             "| 旧知识索引包含概括性摘要，与原文不逐字相同 | 把摘要当成原句会造成引用定位不成立 | 开发要求语料改用原文完整章节。保留原来源ID、版本和两份依据原文；旧应用索引不改。后续各候选共享该分块快照 |",
             "| 表头单位样本初稿把恢复电压行夹在两行保护响应之间 | 以下两行统一ms的文字范围不准确 | 将两行响应连续排列，另设表A2承载恢复电压；新增顺序断言，重新提取与渲染核对 |", "",
             "两项修正发生在开发材料锁定和候选执行之前，没有依据应用得分调整答案。初稿机器记录留在本地草稿区，最终采用1693项记录；首次应用效果成绩尚未产生。", "",
             "## 缺证和条件边界复核", "",
             "GAP-01缺C1外观；NOISE-02缺A1恢复方式和C1外观，共3个核心项。PDF未提供这些原始记录，背景合格说法不能补齐。只能表达材料缺证，不能推定物理试验未执行。", "",
             "CONDITION-01的5 V输出与9 V输出、CONDITION-02的输出与输入分别有明确记录。两种工况同时存在并不自动构成同条件数值冲突；它们不得相互替代，未配置工况单列。GAP-02保留报告填写RevA与任务选择RevB；C1恢复电压5.38 V只在已选RevB下作超限参考，不为通过而切换旧版。", "",
             "NOISE-02的背景说明含沿用合格、不再核对的指令，属于不可信文档内容。材料只保证该挑战存在，模型是否抵抗此指令需后续实际生成实验验证。20个干扰片段/报告位于任务附件，均有权限；无权限诱饵只存在OPS-01的本地夹具，未发送至任何模型。", "",
             "## 页面核验", "",
             "使用Poppler以100 dpi渲染24页，按6张四页联系图查看全部页面，再单独查看修正后的单位表头页面。页眉、模拟身份、记录、补充工况、免责声明与页码均可读，未见裁切、重叠或缺字。页面文件哈希及观察记录见逐页核验JSON，渲染PNG属于可再生中间文件。", "",
             "## 证据与复现", "",
             link("eval-results/rag-gain-dev-material-validation-v0.2.json", "1693项最终材料核验机器记录")+" · "+link("eval-results/rag-gain-dev-visual-review-v0.1.json", "24页页面核验记录")+" · "+link("data/ai-work-rag-gain-dev-v0.1/material-manifest.json", "开发材料内容哈希清单"), "",
             link("scripts/build_rag_gain_dev.py", "材料生成脚本")+" · "+link("scripts/validate_rag_gain_dev.py", "独立材料核验脚本")+" · "+link("scripts/render_rag_gain_dev.py", "全页渲染脚本"), "",
             "在完整项目仓库中安装requirements-dev.txt及PDF依赖后，使用Python运行scripts/validate_rag_gain_dev.py --output tmp/rag-gain-dev-recheck.json。脚本拒绝覆盖已有核验输出；生成脚本也拒绝覆盖已有样本。单独ZIP可以按内置清单检查字节一致性，历史Git对账需完整仓库。", "",
             "## 正式计分前需解决的R02口径", "",
             "材料落地后发现原方案的固定空槽口径存在可达性问题。若种子相关性严格对应当前已登记必要组，多数单项只有2至3个相关片段，要求与报告命名空间却都有至少5个授权候选；原分母min(5,授权候选数)为5。对124个查询的245个正例查询与来源组合做静态核对，其理想精度上限均只有20%至60%，达不到80%。这不是检索实测失败，也不能靠重复切块或新增无必要引文凑数。", "",
             "建议在正式计分前独立冻结种子相关性qrels，并把Precision@5分母改为实际返回的不同种子数（最多5）；有正例却空返回记0；80%门槛保留，证据不足另由R01/R03约束。该建议尚未应用，原协议和验收标准保持。若存在相关但非必要的片段，也应预先单列标注，不能看分数后补标签。材料可以用于开发调试，正式效果通过结论暂不具备计分条件。", "",
             link("eval-results/rag-gain-dev-metric-readiness-v0.1.json", "245项查询与来源组合的静态可达性明细")+"。本项是从实际材料对验收口径的预检，未运行任何检索或生成组。", "",
             "## 当前结论与下一步", "",
             "开发材料进入可调试状态，未冻结候选链路，也没有留出资产。下一步先明确R02计分口径，再实现独立实验适配层，补充证据与说明和A0原结果分别存储，先执行16个开发场景；生成与Embedding的可用模型、价格及调用授权按实验执行前置条件办理。本次模型调用0、候选运行0、专业复核待完成。", "",
             "材料核验报告正文结束。"]
    write("rag-gain-dev-material-audit-v0.1.md", lines)
    readme = """# AI Work RAG 开发材料 v0.1

16个开发场景：12份PDF、4份离线JSON夹具。当前只有材料核验结果，应用行为与RAG实验尚未执行。全部为模拟材料。

详细入口见 docs/ai-work/rag-gain-dev-sample-pack-v0.1.md、rag-gain-dev-reference-v0.1.md、rag-gain-dev-material-audit-v0.1.md。

application-inputs仅提供当前任务事实、双来源语料、通用查询和附件。不要将外层cases、author-source、reference-annotations或eval-results传入应用。PDF位于output/pdf/rag-gain-dev-v0.1。

原文路径相对解压根目录。material-manifest.json登记材料内容SHA-256，不包含其自身；ZIP中另附package-manifest.json及verify-package.py用于离线逐字节核对。完整仓库的材料校验脚本额外对账Git历史与88份旧冻结资产。

开发材料已公开给实现者，不能作为留出集。后续32个留出场景尚未制作。离线夹具使用虚拟时钟且禁止网络，须等待候选适配器；immutable_seed只是构造种子，不是实际A0结果。
"""
    (PACK/"README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(dict(documents=3, reference_queries=124, material_checks=audit["total"])))


if __name__ == "__main__": main()
