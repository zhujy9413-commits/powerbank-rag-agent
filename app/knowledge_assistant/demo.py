"""Display-only examples. Never passed to Assistant, retrieval, or generation."""
from copy import deepcopy
from hashlib import sha256

ORIGINALS = {
    'SYN-SPEC-PB01-RevB': 'd2ed2688e839ba912e9b39f0c40573e4300fc416382bd520c4531c028fcdf5b1',
    'SYN-SPEC-PB01-RevA': '144a0d942f2d899630ca8b21084f7d8125c639ceed1a51c49b05d5ea7658a024',
    'SYN-QA-SC-1.0': 'fd57f543d6dd26eff9e8f406a03947c6ff5e4d9c3f3f50e9ffccbb22bb6b150e',
    'SYN-TR-001-R1': '6772d18a4cccfcfaa31241b46177d02b84b9bb5703f4df9555d17ce3cf240d62',
    'PUB-01': '635c37206b51af2ca645d2b880467af72c934c548d061e22b04fd25f2f336ef7',
    'POLICY-REVIEW': '7a9913d45cdec5e949b85bb7fe270d06c73cd13bb13464f27f19627d9b62b67e',
}


def fact(label, value, source):
    return dict(label=label, value=value, chunk_id=source)


def case(identity, title, query, documents, facts, expectation, groups, *, task=False, history=False, status=None):
    return dict(id=identity, title=title, request=dict(query=query, mode='search',
        model='PB-DEMO-01' if identity != 'D08' else None, document_ids=documents,
        task_id='DEMO-TASK-001' if task else None, include_archived=history),
        facts=facts, expectation=expectation,
        groups=[dict(label=label, chunk_ids=ids) for label, ids in groups], expected_status=status)


CASES = [
    case('D01', '查当前规格的具体数值', '模拟规格RevB的恢复电压范围是多少，是否包含两端？',
         ['SYN-SPEC-PB01-RevB'],
         [fact('RevB · 恢复电压', '4.75～5.25 V，包含两端', 'SYN-SPEC-PB01-RevB-REC')],
         '找到RevB的SPEC-REC原文，核对上下限及闭区间。',
         [('RevB恢复电压条款', ['SYN-SPEC-PB01-RevB-REC'])]),
    case('D02', '比较历史与当前规格', '请比较模拟规格RevA和RevB的恢复电压范围。',
         ['SYN-SPEC-PB01-RevA', 'SYN-SPEC-PB01-RevB'],
         [fact('RevA · 历史规格', '4.50～5.50 V，包含两端', 'SYN-SPEC-PB01-RevA-REC'),
          fact('RevB · 当前演示规格', '4.75～5.25 V，包含两端', 'SYN-SPEC-PB01-RevB-REC')],
         '同时找到两版条款，分别保留版本；历史范围不能冒充RevB要求。',
         [('RevA条款', ['SYN-SPEC-PB01-RevA-REC']), ('RevB条款', ['SYN-SPEC-PB01-RevB-REC'])], history=True),
    case('D03', '查响应阈值与单位换算', '模拟规范的响应阈值是多少？0.68 s如何换算？',
         ['SYN-QA-SC-1.0'],
         [fact('响应阈值', '不大于500 ms', 'SYN-NORM-RESPONSE'),
          fact('单位关系', '1 s＝1000 ms；0.68 s＝680 ms', 'SYN-NORM-RESPONSE')],
         '找到DEMO-01；比较前先把秒换成毫秒。这里的500 ms是模拟规则。',
         [('响应与单位条款', ['SYN-NORM-RESPONSE'])]),
    case('D04', '查温升规则', '模拟规范的壳温变化上限是多少，起值和末值如何计算？',
         ['SYN-QA-SC-1.0'],
         [fact('温升上限', '末值－起值≤12 K', 'SYN-NORM-TEMP'),
          fact('关键位缺失', '不猜数字，先核实原始记录', 'SYN-NORM-TEMP')],
         '找到DEMO-03，核对减法方向、单位及模糊数字的处理。',
         [('壳温变化条款', ['SYN-NORM-TEMP'])]),
    case('D05', '找报告中的数值冲突', 'R02的0.68 s按演示规范怎么看，同时摘要写了80 ms？',
         ['SYN-QA-SC-1.0'],
         [fact('报告第1页 · S01摘要', 'C1保护响应80 ms', 'TR-P1-SUMMARY'),
          fact('报告第2页 · R02明细', 'C1保护响应0.68 s，报告填写通过', 'TR-P2-RESPONSE'),
          fact('模拟规范DEMO-01', '响应时间≤500 ms', 'SYN-NORM-RESPONSE')],
         '同时找到摘要、明细、阈值与冲突处理条款。680 ms超过模拟阈值，正确响应值仍待核实。',
         [('报告摘要', ['TR-P1-SUMMARY']), ('响应明细', ['TR-P2-RESPONSE']),
          ('响应阈值', ['SYN-NORM-RESPONSE']), ('冲突处理', ['SYN-NORM-CONFLICT'])], task=True),
    case('D06', '验证缺记录的处理', 'C1的外观和恢复方式能判通过吗？',
         ['SYN-QA-SC-1.0'],
         [fact('报告第3页 · C1外观', '横线，缺少明确观察记录', 'TR-P3-OBS'),
          fact('报告第3页 · C1恢复方式', '横线，缺少恢复方式记录', 'TR-P3-OBS')],
         '找到报告横线及对应的两条记录要求；应保留证据不足，不能推定实际未测试。',
         [('报告观察记录', ['TR-P3-OBS']), ('外观记录要求', ['SYN-NORM-APPEARANCE']),
          ('恢复方式要求', ['SYN-NORM-METHOD'])], task=True),
    case('D07', '区分报告判定与采用要求', '报告把R04的5.31 V写通过，按任务RevB应如何处理？',
         ['SYN-SPEC-PB01-RevB', 'SYN-QA-SC-1.0'],
         [fact('报告第2页 · R04', 'C1恢复电压5.31 V，报告填写通过', 'TR-P2-RECOVERY'),
          fact('报告第1页 · 报告采用RevA', '4.50～5.50 V', 'TR-P1-SUMMARY'),
          fact('本次明确选用RevB', '4.75～5.25 V', 'SYN-SPEC-PB01-RevB-REC')],
         '找到测量记录、报告版本和RevB条款；5.31 V超出所选范围，报告通过文字不能覆盖要求。',
         [('恢复电压明细', ['TR-P2-RECOVERY']), ('报告采用版本', ['TR-P1-SUMMARY']),
          ('RevB电压条款', ['SYN-SPEC-PB01-RevB-REC']), ('冲突处理', ['SYN-NORM-CONFLICT'])], task=True),
    case('D08', '验证未收录条款时的提示', '请给GB/T 35590-2017短路条款原文和准确限值。',
         ['PUB-01', 'POLICY-REVIEW'],
         [fact('包内标准资料', '只有题录摘要，未收录技术条款全文或短路限值', 'PUB-01-C1')],
         '可以找到相关题录，但应明确条款与限值依据不足；不得用模拟规则的数值代替国家标准限值。',
         [('标准资料的收录边界', ['PUB-01-C1']), ('缺依据处理约定', ['POL-EVIDENCE'])], status='insufficient_evidence'),
]


def demo_catalog(corpus, principal):
    """Only expose examples whose exact sample originals are still authorized."""
    available = []
    for template in CASES:
        ids = {cid for group in template['groups'] for cid in group['chunk_ids']}
        ids.update(f['chunk_id'] for f in template['facts'])
        references = {}
        try:
            for identity in sorted(ids):
                source = corpus.source(identity, principal)
                expected = ORIGINALS.get(source['document_id'])
                expected_state = 'archived' if source['document_id'] == 'SYN-SPEC-PB01-RevA' else 'active'
                if (sha256(source['original_text'].encode()).hexdigest() != expected or
                        source['publication_status'] != expected_state):
                    raise ValueError('演示原件或状态已变化')
                references[identity] = {key: source[key] for key in
                    ['chunk_id', 'document_id', 'title', 'section', 'version', 'page', 'publication_status']}
            example = deepcopy(template)
            request = example['request']
            selected_docs = request.pop('document_ids')
            selected = [corpus.by_id[cid] for cid in ids if corpus.by_id[cid]['document_id'] in selected_docs]
            request['version_ids'] = sorted({c.get('knowledge_version_id', c['document_id']) for c in selected})
            if len({c['document_id'] for c in selected}) != len(selected_docs):
                continue
            example['references'] = references
            available.append(example)
        except (PermissionError, ValueError, KeyError):
            continue
    return dict(sample_version='bootstrap-v0.1', corpus_digest=corpus.digest,
                note='数值均来自已有模拟原件。预期对照仅供演示验证，不进入检索和模型上下文。',
                cases=available)
