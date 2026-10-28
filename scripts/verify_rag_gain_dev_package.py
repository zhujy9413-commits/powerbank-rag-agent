"""Verify all archive members and their byte hashes, without network or Git."""
import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.output.exists(): p.error("拒绝覆盖既有结果")
    checks = []
    def check(name, value): checks.append(dict(name=name, passed=bool(value)))
    with ZipFile(a.archive) as z:
        names = z.namelist()
        m = json.loads(z.read("package-manifest.json"))
        check("no_duplicates", len(names) == len(set(names)))
        check("safe_relative_paths", all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts for n in names))
        check("exact_member_set", set(names) == set(m["asset_sha256"]) | {"package-manifest.json"})
        check("no_unlisted_or_private_runtime_state", all(".local/" not in n and not n.endswith((".db", ".sqlite", ".env")) for n in names))
        for name, expected in m["asset_sha256"].items(): check("hash:"+name, sha256(z.read(name)).hexdigest() == expected)
        content_manifest = json.loads(z.read("data/ai-work-rag-gain-dev-v0.1/material-manifest.json"))
        for name, expected in content_manifest["asset_sha256"].items(): check("material_hash:"+name, sha256(z.read(name)).hexdigest() == expected)
        for field in ["audit", "visual"]: check(field+"_receipt_hash", sha256(z.read(content_manifest[field+"_path"])).hexdigest() == content_manifest[field+"_sha256"])
    result = dict(kind="offline_package_integrity", archive=str(a.archive), archive_sha256=sha256(a.archive.read_bytes()).hexdigest(),
                  package_members=len(names), checks=checks, passed=sum(x["passed"] for x in checks), total=len(checks),
                  model_requests=0, application_tests_executed=0)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["kind", "package_members", "passed", "total", "archive_sha256"]}))
    if result["passed"] != result["total"]: raise SystemExit(1)


if __name__ == "__main__": main()
