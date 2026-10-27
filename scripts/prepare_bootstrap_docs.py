"""Prepare repository reading snapshots and Feishu Markdown import files."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/bootstrap-v0.1"
REPO = "https://github.com/zhujy9413-commits/powerbank-rag-agent/blob/main/"


def read(name):
    p = BASE / name
    def replace(m):
        target = m.group(2)
        if target.startswith(("https://", "http://", "#")):
            return m.group(0)
        return "[" + m.group(1) + "](" + REPO + str((p.parent / target).resolve().relative_to(ROOT)) + ")"
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace, p.read_text(encoding="utf-8"))


shared = read("资料清单与入库说明.md") + "\n\n" + "\n\n".join(read(f"knowledge/public/PUB-{n:02}.md") for n in range(1,6))
aw = "# AI Work 首批模拟报告与逐项标注\n\n版本v0.1。2026-10-26构造，2026-10-27校验。仅软件流程样本，未进行模型评测或专业验收。\n\n[样本包维护源](" + REPO + "data/bootstrap-v0.1/README.md)\n\n[原始四页模拟PDF](" + REPO + "output/pdf/SYN-TR-001-R1.pdf)\n\n"
for name in ["knowledge/synthetic/SYN-SPEC-PB01-RevB.md", "knowledge/synthetic/SYN-QA-SC-1.0.md", "task-reports/SYN-TR-001-R1.md", "evaluation/报告逐项标注表.md", "evaluation/执行及评分说明.md"]:
    aw += "\n\n" + read(name)
qa = "# 内部智能客服 首批知识样本与问答评测集\n\n版本v0.1。2026-10-26构造，2026-10-27校验。24道开发用例，参考答案由作者拟定，专业复核待完成；模型评测未运行。\n\n[样本包维护源](" + REPO + "data/bootstrap-v0.1/README.md)\n\n"
for name in ["knowledge/policy/review-policy.md", "knowledge/synthetic/SYN-SPEC-PB01-RevB.md", "knowledge/synthetic/SYN-SPEC-PB01-RevA.md", "evaluation/问答评测集.md", "evaluation/执行及评分说明.md"]:
    qa += "\n\n" + read(name)

out = Path("/private/tmp/powerbank-bootstrap-import")
out.mkdir(exist_ok=True)
for repo_path, import_name, text in [
    ("docs/shared/bootstrap-materials.md", "01-首批知识样本与资料清单.md", shared),
    ("docs/ai-work/sample-pack.md", "04-模拟报告与逐项标注.md", aw),
    ("docs/internal-assistant/sample-pack.md", "04-知识样本与问答评测集.md", qa),
]:
    (ROOT / repo_path).write_text(text, encoding="utf-8")
    (out / import_name).write_text(text, encoding="utf-8")
print("Prepared three module/shared reading snapshots and identical Feishu import files.")
