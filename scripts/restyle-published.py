#!/usr/bin/env python3
"""Re-render published reports with the current Typst style, reusing their run data.

The pipeline's last stage changed (typography and provenance styling). The
reports on the site were rendered by the old one. Re-running the whole pipeline
would mean new OCR and a new synthesis — different text, new cost, and the run
ledger on the papers page would no longer describe what is published.

Instead this replays only the last stage: `paper-pipeline render --job <id>
--layout <existing report.layout.yaml>`. Reusing the layout skips the layout
model call, so the render is deterministic — same report text, same figure
placement, new styling. Roughly 3s of Typst per paper, no API calls.

  python3 scripts/restyle-published.py --host yqh2 --dry-run
  python3 scripts/restyle-published.py --host yqh2 --only servegen,simai
  python3 scripts/restyle-published.py --host yqh2

Per paper it rsyncs the job dir without `input/` (the source PDF is only needed to
re-crop figures, and `upgrade_job_ocr_assets` no-ops without it — the existing
crops are the ones the published PDF already used), renders, replaces
site/downloads/<slug>.pdf, and refreshes site/downloads/runs/<slug>-run.zip so the
bundle keeps matching the PDF it explains.
"""
from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOWNLOADS = REPO / "site" / "downloads"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pdf_pages(pdf: Path) -> str:
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if line.startswith("Pages:"):
                return line.split()[1]
    except FileNotFoundError:
        pass
    return "?"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", required=True, help="ssh host holding the job store, e.g. yqh2")
    parser.add_argument(
        "--pipeline-dir",
        type=Path,
        default=Path("~/work/paper-pipeline").expanduser(),
        help="local paper-pipeline checkout carrying the new render stage",
    )
    parser.add_argument("--only", help="comma-separated slugs")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-temp", action="store_true")
    args = parser.parse_args()

    if not (args.pipeline_dir / "pyproject.toml").is_file():
        sys.exit(f"not a paper-pipeline checkout: {args.pipeline_dir}")

    fetch = load("fetch_run_bundles", "fetch-run-bundles.py")
    build = load("build_papers_page", "build-papers-page.py")

    data = fetch.remote_manifest(args.host)
    wanted = {s.strip() for s in args.only.split(",")} if args.only else None

    plan = []
    for paper in data["papers"]:
        if not paper.get("clean"):
            continue
        title = build._lookup(build.TITLE_FIX, paper["norm"], paper["title"])
        slug = build._lookup(build.SLUG_FIX, paper["norm"]) or build.slugify(title)
        if wanted and slug not in wanted:
            continue
        if not (DOWNLOADS / f"{slug}.pdf").exists():
            print(f"skip {slug}: not published")
            continue
        paper["title"] = title
        plan.append((slug, paper))

    print(f"{len(plan)} published papers to re-render with {args.pipeline_dir}")
    if args.dry_run:
        for slug, paper in plan:
            published = DOWNLOADS / f"{slug}.pdf"
            print(f"  {slug:48s} {paper['job_id']}  now {published.stat().st_size // 1024} KB / {pdf_pages(published)}p")
        return 0

    ok, failed = [], []
    for slug, paper in plan:
        tmp = Path(tempfile.mkdtemp(prefix=f"lil-restyle-{slug}-"))
        job_dir = tmp / "jobs" / paper["job_id"]
        job_dir.mkdir(parents=True)
        published = DOWNLOADS / f"{slug}.pdf"
        before = (published.stat().st_size // 1024, pdf_pages(published))
        try:
            subprocess.run(
                ["rsync", "-a", "--exclude=input/**", f"{args.host}:{paper['dir'].rstrip('/')}/", f"{job_dir}/"],
                check=True,
            )
            layout = job_dir / "report.layout.yaml"
            if not layout.is_file():
                raise RuntimeError("no report.layout.yaml in the job dir")
            out_pdf = tmp / f"{slug}.pdf"
            subprocess.run(
                [
                    "uv", "run", "paper-pipeline",
                    "--data-dir", str(tmp),
                    "render", "--job", paper["job_id"],
                    "--layout", str(layout),
                    "--output", str(out_pdf),
                ],
                cwd=args.pipeline_dir,
                check=True,
                capture_output=True,
            )
            shutil.copyfile(out_pdf, published)
            fetch.write_bundle(job_dir, slug, paper)
            after = (published.stat().st_size // 1024, pdf_pages(published))
            flag = "" if before[1] == after[1] else f"  ⚠ pages {before[1]} -> {after[1]}"
            print(f"✓ {slug:48s} {before[0]:5d} -> {after[0]:5d} KB, {after[1]}p{flag}")
            ok.append(slug)
        except (subprocess.CalledProcessError, RuntimeError) as error:
            detail = getattr(error, "stderr", b"")
            print(f"✗ {slug}: {error}", file=sys.stderr)
            if detail:
                print(detail.decode()[-400:], file=sys.stderr)
            failed.append(slug)
        finally:
            if not args.keep_temp:
                shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nre-rendered {len(ok)}, failed {len(failed)}")
    if failed:
        print("failed: " + ", ".join(failed))
    print("接下来：npm run covers（封面按新 PDF 重生成）然后 npm run validate")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
