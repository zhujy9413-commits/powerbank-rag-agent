"""Seal the reviewed development assets and create a reproducible download."""
from hashlib import sha256
import argparse
import json
from pathlib import Path
import shutil
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT/"data/ai-work-rag-gain-dev-v0.1"


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
def digest(path): return sha256(path.read_bytes()).hexdigest()
def relative(path): return str(path.relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-archive", action="store_true", help="Repackage documentation only; locked material bytes must match.")
    args = parser.parse_args()
    target = ROOT/"output/packages/ai-work-rag-gain-dev-v0.1.zip"
    if target.exists() or (PACK/"material-manifest.json").exists():
        if not args.refresh_archive: raise SystemExit("已锁定，拒绝覆盖。")
        locked = json.loads((PACK/"material-manifest.json").read_text())
        if not all(digest(ROOT/p) == expected for p, expected in locked["asset_sha256"].items()): raise SystemExit("材料字节已变，禁止以文档刷新名义重封包。")
    receipt = json.loads((ROOT/"tmp/pdfs/rag-gain-dev-v0.1/render-receipt.json").read_text())
    qa = ROOT/"output/qa/rag-gain-dev-v0.1"; qa.mkdir(parents=True, exist_ok=True)
    for path in receipt["contact_sheets"]: shutil.copyfile(ROOT/path, qa/Path(path).name)
    visual = dict(kind="same_author_visual_material_review", reviewer="Codex material author", date="2026-10-29",
                  method="Viewed all 24 pages in six 100dpi Poppler contact sheets, then separately viewed corrected SYND-804 page 1.",
                  pages_reviewed=24, final_observed_visual_defects=0,
                  corrected_draft_defect="SYND-804: interleaved recovery row broke the two-row ms header scope; response rows now contiguous, separate A2 recovery heading.",
                  criteria=["readable_synthetic_identity", "no_clipped_or_overlapping_text", "complete_records_and_local_conditions", "legible_footer_and_page_numbers", "correct_unit_header_extent"],
                  pdfs=[dict(**x, page_observations=[dict(page=n, status="reviewed_no_observed_visual_defect") for n in [1, 2]]) for x in receipt["pdfs"]],
                  contact_sheets={relative(p): digest(p) for p in sorted(qa.glob("*.png"))})
    dump(ROOT/"eval-results/rag-gain-dev-visual-review-v0.1.json", visual)
    assets = sorted([p for p in PACK.rglob("*") if p.is_file() and p.name != "material-manifest.json"]+list((ROOT/"output/pdf/rag-gain-dev-v0.1").glob("*.pdf")))
    for p in assets:
        if p.suffix.lower() in [".sqlite", ".db"] or ".local" in p.parts: raise ValueError("禁止打包本地私有状态")
    manifest = dict(material_id="AIWORK-RAG-GAIN-DEV-0.1", status="material_verified_development_only", date="2026-10-29",
                    content_reports=12, pdf_pages=24, offline_fixtures=4, holdout_materialized=0,
                    candidate_chain_frozen=False, experiments_executed=0, model_requests=0,
                    reference_review="same_author_internal_not_expert_or_external_independent",
                    audit_path="eval-results/rag-gain-dev-material-validation-v0.2.json", audit_sha256=digest(ROOT/"eval-results/rag-gain-dev-material-validation-v0.2.json"),
                    visual_path="eval-results/rag-gain-dev-visual-review-v0.1.json", visual_sha256=digest(ROOT/"eval-results/rag-gain-dev-visual-review-v0.1.json"),
                    excludes="This manifest itself; documentation and reproducible QA images covered by package manifest.",
                    asset_sha256={relative(p): digest(p) for p in assets})
    if args.refresh_archive:
        if manifest != locked: raise SystemExit("已锁定内容清单发生变化，禁止重封包。")
    else: dump(PACK/"material-manifest.json", manifest)
    docs = [ROOT/"docs/ai-work"/("rag-gain-dev-"+s+"-v0.1.md") for s in ["sample-pack", "reference", "material-audit"]]
    source_paths = {x["source_path"] for x in json.loads((PACK/"selected-basis/chunks.json").read_text())}
    scripts = [ROOT/"scripts"/n for n in ["build_rag_gain_dev.py", "validate_rag_gain_dev.py", "render_rag_gain_dev.py", "document_rag_gain_dev.py", "package_rag_gain_dev.py", "verify_rag_gain_dev_package.py", "check_rag_gain_dev_metric_readiness.py"]]
    members = sorted(set(assets+[PACK/"material-manifest.json"]+docs+scripts+[ROOT/p for p in source_paths]+list(qa.glob("*.png"))+[
        ROOT/"eval-results/rag-gain-dev-material-validation-v0.2.json", ROOT/"eval-results/rag-gain-dev-visual-review-v0.1.json", ROOT/"eval-results/rag-gain-dev-metric-readiness-v0.1.json",
        ROOT/"data/ai-work-rag-gain-v0.1/protocol.json", ROOT/"data/ai-work-rag-gain-v0.1/cases.json"]))
    package_manifest = dict(package_id="AIWORK-RAG-GAIN-DEV-0.1", excludes="package-manifest.json itself", asset_sha256={relative(p): digest(p) for p in members})
    target.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(target, "w", compression=ZIP_DEFLATED) as archive:
        for p in members:
            info = ZipInfo(relative(p), date_time=(2026, 10, 29, 0, 0, 0)); info.compress_type = ZIP_DEFLATED
            archive.writestr(info, p.read_bytes())
        info = ZipInfo("package-manifest.json", date_time=(2026, 10, 29, 0, 0, 0)); info.compress_type = ZIP_DEFLATED
        archive.writestr(info, json.dumps(package_manifest, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(dict(archive=relative(target), files=len(members)+1, bytes=target.stat().st_size, sha256=digest(target))))


if __name__ == "__main__": main()
