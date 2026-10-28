"""Render every development PDF page and build review contact sheets."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/"tmp/pdfs/rag-gain-dev-v0.1"
POPPLER = "/Users/zhujiayi/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/pdftoppm"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted((ROOT/"output/pdf/rag-gain-dev-v0.1").glob("*.pdf"))
    def one(path):
        subprocess.run([POPPLER, "-r", "100", "-png", str(path), str(OUT/path.stem)], check=True, capture_output=True)
        return dict(pdf_path=str(path.relative_to(ROOT)), sha256=sha256(path.read_bytes()).hexdigest(),
                    pages=[str(p.relative_to(ROOT)) for p in sorted(OUT.glob(path.stem+"-*.png"))])
    with ThreadPoolExecutor(max_workers=4) as pool: rendered = list(pool.map(one, files))
    sheets = []
    for i in range(0, len(rendered), 2):
        images = [(Path(p).name, Image.open(ROOT/p).convert("RGB")) for item in rendered[i:i+2] for p in item["pages"]]
        w, h = images[0][1].size
        sheet = Image.new("RGB", (2*w, 2*(h+28)), "#D9E1E7")
        d = ImageDraw.Draw(sheet)
        for j, (name, im) in enumerate(images):
            x, y = j%2*w, j//2*(h+28)
            d.text((x+10, y+7), name, fill="black")
            sheet.paste(im, (x, y+28))
        target = OUT/f"contact-{i//2+1:02d}.png"; sheet.save(target)
        sheets.append(str(target.relative_to(ROOT)))
    (OUT/"render-receipt.json").write_text(json.dumps(dict(renderer="Poppler pdftoppm 100dpi", pdfs=rendered, contact_sheets=sheets), indent=2)+"\n")
    print(json.dumps(dict(pdfs=len(rendered), pages=sum(len(x["pages"]) for x in rendered), contact_sheets=sheets)))


if __name__ == "__main__": main()
