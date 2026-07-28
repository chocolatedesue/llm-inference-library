#!/usr/bin/env python3
"""Point every catalog paper entry at its run bundle, if one has been fetched.

`fetch-run-bundles.py` drops zips into site/downloads/runs/. The catalog entries
for the manifest-driven papers are rewritten by build-papers-page.py, which adds
`runData` itself when the file is there — this script is for the in-between state:
bundles fetched now, next regeneration later. Idempotent, so it is safe to re-run.

  python3 scripts/link-run-bundles.py
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "site" / "assets" / "catalog.js"
RUNS = REPO / "site" / "downloads" / "runs"


def main() -> int:
    if not RUNS.exists():
        print("no bundles in site/downloads/runs/")
        return 0

    slugs = sorted(p.name[: -len("-run.zip")] for p in RUNS.glob("*-run.zip"))
    text = CATALOG.read_text()
    linked, already, missing = [], [], []

    for slug in slugs:
        entry = re.search(r"\{\n    id: '" + re.escape(slug) + r"'.*?\n  \}", text, re.S)
        if not entry:
            missing.append(slug)
            continue
        block = entry.group(0)
        if "runData:" in block:
            already.append(slug)
            continue
        updated = block.replace(
            f"href: 'downloads/{slug}.pdf',",
            f"href: 'downloads/{slug}.pdf',\n    runData: 'downloads/runs/{slug}-run.zip',",
        )
        if updated == block:
            missing.append(slug)
            continue
        text = text[: entry.start()] + updated + text[entry.end() :]
        linked.append(slug)

    CATALOG.write_text(text)
    print(f"linked {len(linked)}, already linked {len(already)}")
    if missing:
        print(f"no matching catalog entry for: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
