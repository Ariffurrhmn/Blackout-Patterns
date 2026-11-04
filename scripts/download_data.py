#!/usr/bin/env python3
"""Tell you where to put the raw data, and check it once it is there.

Mendeley Data and the UCI repository do not offer a stable direct-download URL
that works without a browser session, so this script does not guess one. It
prints the landing pages and the file name each dataset must be saved under,
then verifies whatever is already in ``data/raw/``.

    python scripts/download_data.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from blackout import config  # noqa: E402


def main() -> int:
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    missing = 0
    for key, meta in config.DATASETS.items():
        target = config.DATA_RAW / meta["target"]
        print(f"[{key}] {meta['title']}  ({meta['licence']})")
        print(f"      page : {meta['landing_page']}")
        if target.exists():
            sha = hashlib.sha256(target.read_bytes()).hexdigest()
            print(f"      found: {target.name}  {target.stat().st_size / 1e6:.2f} MB  sha256 {sha[:16]}...")
        else:
            missing += 1
            print(f"      save the file as: {target}")
    if missing:
        print(f"\n{missing} dataset(s) missing. Download from the pages above, then run:")
        print("  blackout inspect   # check the columns and inferred roles")
        print("  blackout clean")
        print("  blackout profile")
    return 0 if config.MAIN_DATASET_PATH.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
