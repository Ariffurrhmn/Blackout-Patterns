"""Build demo/index.html: inline the dataset CSV and the exported model into the HTML template.

Run from the project root:  python3 demo/make_html.py [csv_path]
The CSV defaults to demo/data/daily_demo.csv (made by demo/build_demo.py).
Result is one self-contained file that opens by double-click.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent


def js_literal(obj) -> str:
    # "</" would close the script tag; U+2028/2029 break old JS parsers.
    return json.dumps(obj).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def main(csv_path: Path, out: Path) -> None:
    if not csv_path.exists():
        sys.exit(f"CSV not found: {csv_path}\nRun demo/build_demo.py (needs data/raw/) or copy daily_demo.csv there.")
    model = json.loads((DEMO / "model" / "model_f1.json").read_text())
    html = (DEMO / "index.template.html").read_text(encoding="utf-8")
    html = html.replace("/*__CSV__*/\"\"", js_literal(csv_path.read_text(encoding="utf-8")))
    html = html.replace("/*__MODEL__*/null", js_literal(model))
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    csv = Path(sys.argv[1]) if len(sys.argv) > 1 else DEMO / "data" / "daily_demo.csv"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else DEMO / "index.html"
    main(csv, out)
