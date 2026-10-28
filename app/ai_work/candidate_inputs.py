"""Explicit development input loader. Never opens labels or user settings."""
import json
from pathlib import Path


def load_input(directory, root):
    root, directory = Path(root).resolve(), Path(directory).resolve()
    allowed = root/"data/ai-work-rag-gain-dev-v0.1/application-inputs"
    if directory.parent != allowed:
        raise ValueError("只接受已核验的开发应用输入目录。")
    task = json.loads((directory/"task.json").read_text())
    expected_pdf=root/"output/pdf/rag-gain-dev-v0.1"/(directory.name+".pdf")
    if task["report_id"]!=directory.name or (root/task["pdf_path"]).resolve()!=expected_pdf:
        raise ValueError("任务PDF身份或路径不符。")
    chunks = [json.loads(line) for line in (directory/"chunks.jsonl").read_text().splitlines()]
    from pypdf import PdfReader
    originals = {}
    for c in chunks:
        rel = Path(c["source_path"])
        path = (root/rel).resolve()
        permitted = (path == (root/task["pdf_path"]).resolve()
                     or path.is_relative_to(root/"data/bootstrap-v0.1/knowledge/synthetic")
                     or path == directory/"task-background.md")
        if rel.is_absolute() or not path.is_relative_to(root) or not permitted:
            raise ValueError("原文路径超出当前任务及选定知识范围。")
        if path.suffix == ".pdf":
            if (str(rel), c["page"]) not in originals:
                reader = PdfReader(path)
                for page, item in enumerate(reader.pages, 1):
                    originals[(str(rel), page)] = item.extract_text() or ""
        else:
            originals[(str(rel), None)] = path.read_text()
    return task, chunks, originals
