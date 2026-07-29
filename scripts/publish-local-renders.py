#!/usr/bin/env python3
"""Publish PDFs that were already rendered in a local job store.

`restyle-published.py` re-renders on this machine from a remote job store. This is
the other case: the render already happened locally (a new layout version was run
over every job), and the site just needs to pick the results up.

  python3 scripts/publish-local-renders.py ~/work/paper-pipeline/data/jobs --dry-run
  python3 scripts/publish-local-renders.py ~/work/paper-pipeline/data/jobs
  python3 scripts/publish-local-renders.py <jobs> --only frontier,tally

Slugs come from each job's own metadata.json through the same TITLE_FIX / SLUG_FIX
tables build-papers-page.py uses, so published URLs never move.

Two safety rules, both learned from this job store:

  - **Newest render wins.** A store accumulates several runs of the same paper
    (an older layout version, a failed attempt). Picking by mtime keeps the run
    that was rendered last, and the choice is printed so it can be checked.
  - **Only already-published slugs are updated.** A job store can hold papers the
    site never published (three `phantora` runs here). Adding one is a decision,
    not a side effect, so it needs --allow-new.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
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


def norm_title(title: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", " ", (title or "").lower())
    return " ".join(lowered.split())[:60]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("jobs", type=Path, help="job store, e.g. ~/work/paper-pipeline/data/jobs")
    parser.add_argument("--pdf", default="report.compact.pdf", help="which rendered PDF to publish")
    parser.add_argument("--only", help="comma-separated slugs")
    parser.add_argument("--allow-new", action="store_true", help="also publish papers the site does not have yet")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    jobs_dir = args.jobs.expanduser()
    if not jobs_dir.is_dir():
        sys.exit(f"not a job store: {jobs_dir}")

    build = load("build_papers_page", "build-papers-page.py")
    fetch = load("fetch_run_bundles", "fetch-run-bundles.py")
    wanted = {s.strip() for s in args.only.split(",")} if args.only else None

    # slug -> best candidate, newest render wins
    candidates: dict[str, dict] = {}
    for job in sorted(jobs_dir.iterdir()):
        pdf = job / args.pdf
        meta = job / "metadata.json"
        if not (pdf.is_file() and meta.is_file()):
            continue
        try:
            title = json.loads(meta.read_text()).get("title") or ""
        except json.JSONDecodeError:
            continue
        norm = norm_title(title)
        title = build._lookup(build.TITLE_FIX, norm, title)
        slug = build._lookup(build.SLUG_FIX, norm) or build.slugify(title)
        entry = {
            "slug": slug,
            "job_id": job.name,
            "dir": job,
            "pdf": pdf,
            "title": title,
            "mtime": pdf.stat().st_mtime,
            "bytes": pdf.stat().st_size,
        }
        previous = candidates.get(slug)
        if previous is None or entry["mtime"] > previous["mtime"]:
            if previous:
                print(f"note: {slug} has several renders; keeping {entry['job_id'][:8]} "
                      f"(newer than {previous['job_id'][:8]})")
            candidates[slug] = entry

    plan, skipped = [], []
    for slug, entry in sorted(candidates.items()):
        if wanted and slug not in wanted:
            continue
        published = DOWNLOADS / f"{slug}.pdf"
        if not published.exists() and not args.allow_new:
            skipped.append(slug)
            continue
        entry["live_bytes"] = published.stat().st_size if published.exists() else 0
        plan.append(entry)

    print(f"{len(plan)} papers to update from {jobs_dir}")
    if skipped:
        print(f"not published yet, skipped (use --allow-new): {', '.join(skipped)}")

    if args.dry_run:
        for entry in plan:
            published = DOWNLOADS / f"{entry['slug']}.pdf"
            before = f"{entry['live_bytes'] // 1024}KB/{pdf_pages(published)}p" if entry["live_bytes"] else "new"
            print(f"  {entry['slug']:50s} {entry['job_id'][:8]}  {before} -> "
                  f"{entry['bytes'] // 1024}KB/{pdf_pages(entry['pdf'])}p")
        return 0

    for entry in plan:
        published = DOWNLOADS / f"{entry['slug']}.pdf"
        before_pages = pdf_pages(published) if entry["live_bytes"] else "-"
        shutil.copyfile(entry["pdf"], published)
        after_pages = pdf_pages(published)
        # The bundle must describe the PDF next to it, so it is rebuilt from the
        # same job directory (text only, same rules as fetch-run-bundles.py).
        paper = {
            "title": entry["title"],
            "job_id": entry["job_id"],
            "run_date": "",
            "prompt_version": "",
            "model": "",
            "pages": "",
        }
        job_json = entry["dir"] / "job.json"
        if job_json.is_file():
            try:
                info = json.loads(job_json.read_text())
                paper.update(run_date=(info.get("updated_at") or "")[:10],
                             prompt_version=info.get("report_prompt_version") or "",
                             model=info.get("report_model") or "",
                             pages=info.get("page_count") or "")
            except json.JSONDecodeError:
                pass
        bundle_bytes = fetch.write_bundle(entry["dir"], entry["slug"], paper)
        flag = "" if before_pages == after_pages else f"  ⚠ pages {before_pages} -> {after_pages}"
        print(f"✓ {entry['slug']:50s} {entry['live_bytes'] // 1024:5d} -> {entry['bytes'] // 1024:5d} KB, "
              f"{after_pages}p, bundle {bundle_bytes // 1024}KB{flag}")

    print("\n接下来：npm run covers && npm run validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
