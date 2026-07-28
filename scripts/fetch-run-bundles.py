#!/usr/bin/env python3
"""Fetch the raw run data of every published paper from the pipeline host.

`publish-run.py` handles one run at a time. This is the batch case: the 18 papers
already on the site were rendered on the pipeline host, and their run data — the
OCR text the model read, the metadata it extracted, the layout DSL, the Typst
source, the usage ledger — never left that host. Without it, a reader can see the
report but cannot check how it was produced.

  python3 scripts/fetch-run-bundles.py --host yqh2
  python3 scripts/fetch-run-bundles.py --host yqh2 --only servegen,simai
  python3 scripts/fetch-run-bundles.py --host yqh2 --dry-run

How the mapping works: `collect-runs.py` is shipped to the host and run there, so
paper identity comes from the same place the ledger page gets it (a hash of
`full-text.md`, not the model-extracted title). Slugs come from the same
`SLUG_FIX` table `build-papers-page.py` uses, so bundles land next to the PDFs
they belong to and published URLs stay put.

Text only, same reasoning as publish-run.py: no source.pdf, no figure crops.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "site" / "downloads" / "runs"
COLLECT = REPO / "scripts" / "collect-runs.py"
BUNDLE_SUFFIXES = (".md", ".json", ".yaml", ".yml", ".typ")


def load_build_module():
    """Reuse SLUG_FIX / TITLE_FIX / slugify so slugs match the published ones."""
    spec = importlib.util.spec_from_file_location("build_papers_page", REPO / "scripts" / "build-papers-page.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remote_manifest(host: str) -> dict:
    """Run collect-runs.py on the host and read its manifest from stdout."""
    with COLLECT.open("rb") as script:
        result = subprocess.run(
            ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", host, "python3 -"],
            stdin=script,
            capture_output=True,
        )
    if result.returncode != 0:
        raise SystemExit(f"collect-runs.py failed on {host}: {result.stderr.decode()[:400]}")
    return json.loads(result.stdout.decode())


def fetch_job(host: str, job_dir: str, dest: Path) -> None:
    includes = [
        "--include=*/",
        *[f"--include=*{suffix}" for suffix in BUNDLE_SUFFIXES],
        "--exclude=input/**",
        "--exclude=*",
    ]
    subprocess.run(
        ["rsync", "-a", "--prune-empty-dirs", *includes, f"{host}:{job_dir.rstrip('/')}/", str(dest)],
        check=True,
    )


def write_bundle(job: Path, slug: str, paper: dict) -> int:
    RUNS.mkdir(parents=True, exist_ok=True)
    out = RUNS / f"{slug}-run.zip"
    files = [p for p in sorted(job.rglob("*")) if p.is_file() and p.suffix.lower() in BUNDLE_SUFFIXES]
    readme = f"""这是「{paper.get('title')}」解构报告的原始运行数据（仅文本）。

  job id        {paper.get('job_id')}
  运行日期      {paper.get('run_date')}
  prompt 版本   {paper.get('prompt_version')}
  报告模型      {paper.get('model')}
  OCR 页数      {paper.get('pages')}
  发布的 PDF    /downloads/{slug}.pdf

full-text.md 是模型实际读到的 OCR 文本，pages/ 是逐页版本；report*.md 是合成的报告正文，
report*.layout.yaml 是排版 DSL，report*.typ 是 Typst 编译输入，usage.json 是 token 账本。

不含论文原文（input/source.pdf）与从原文切出的图片：第三方版权内容，且已发布的 PDF 里
嵌了实际用到的图。要重新渲染，取回原文重跑流水线，或用 report*.typ 配自己的图片资源编译。
"""
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", readme)
        for path in files:
            zf.write(path, str(path.relative_to(job)))
    return out.stat().st_size


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", required=True, help="ssh host running the pipeline, e.g. yqh2")
    parser.add_argument("--only", help="comma-separated slugs to limit the fetch")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    build = load_build_module()
    data = remote_manifest(args.host)
    wanted = {s.strip() for s in args.only.split(",")} if args.only else None

    plan = []
    for paper in data["papers"]:
        if not paper.get("clean"):
            continue
        title = build._lookup(build.TITLE_FIX, paper["norm"], paper["title"])
        slug = build._lookup(build.SLUG_FIX, paper["norm"]) or build.slugify(title)
        if wanted and slug not in wanted:
            continue
        paper["title"] = title
        plan.append((slug, paper))

    print(f"{len(plan)} clean runs on {args.host}")
    if args.dry_run:
        for slug, paper in plan:
            print(f"  {slug:48s} {paper['job_id']}  {paper['dir']}")
        return 0

    total = 0
    for slug, paper in plan:
        tmp = Path(tempfile.mkdtemp(prefix=f"lil-{slug}-"))
        try:
            fetch_job(args.host, paper["dir"], tmp)
            size = write_bundle(tmp, slug, paper)
            total += size
            print(f"✓ {slug:48s} {size // 1024:5d} KB")
        except subprocess.CalledProcessError as error:
            print(f"✗ {slug}: {error}", file=sys.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{len(plan)} bundles, {total // 1024} KB total in site/downloads/runs/")
    print("接下来：python3 scripts/link-run-bundles.py 把 runData 写进 catalog，再 npm run validate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
