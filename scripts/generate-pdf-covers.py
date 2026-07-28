#!/usr/bin/env python3
"""Render first-page JPEG covers for every PDF under site/downloads/.

Requires poppler's pdftoppm. Optionally shrinks with macOS sips when present.
Safe to re-run: only (re)writes covers whose PDF is newer than the JPEG, unless
--force is passed.

  python3 scripts/generate-pdf-covers.py
  python3 scripts/generate-pdf-covers.py --force
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOWNLOADS = REPO / "site" / "downloads"
COVERS = REPO / "site" / "assets" / "covers"
DPI = 120
MAX_EDGE = 480


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def render(pdf: Path, out_jpg: Path) -> None:
    COVERS.mkdir(parents=True, exist_ok=True)
    stem_out = out_jpg.with_suffix("")  # pdftoppm appends .jpg with -singlefile
    cmd = [
        "pdftoppm",
        "-f", "1",
        "-l", "1",
        "-jpeg",
        "-r", str(DPI),
        "-singlefile",
        str(pdf),
        str(stem_out),
    ]
    subprocess.run(cmd, check=True)
    if not out_jpg.exists():
        raise RuntimeError(f"pdftoppm did not produce {out_jpg}")
    if have("sips"):
        subprocess.run(
            ["sips", "-Z", str(MAX_EDGE), str(out_jpg)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="rebuild every cover")
    args = parser.parse_args()

    if not have("pdftoppm"):
        print("pdftoppm not found (install poppler)", file=sys.stderr)
        return 1

    pdfs = sorted(DOWNLOADS.glob("*.pdf"))
    if not pdfs:
        print("no PDFs in site/downloads/")
        return 0

    built = skipped = 0
    for pdf in pdfs:
        out = COVERS / f"{pdf.stem}.jpg"
        if (
            not args.force
            and out.exists()
            and out.stat().st_mtime >= pdf.stat().st_mtime
        ):
            skipped += 1
            continue
        print(f"cover {pdf.name} -> {out.relative_to(REPO)}")
        render(pdf, out)
        built += 1

    # Drop covers whose PDF is gone.
    keep = {p.stem for p in pdfs}
    for jpg in COVERS.glob("*.jpg"):
        if jpg.stem not in keep:
            print(f"removed orphan {jpg.relative_to(REPO)}")
            jpg.unlink()

    print(f"covers built={built} skipped={skipped} total_pdfs={len(pdfs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
