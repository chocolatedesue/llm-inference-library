#!/usr/bin/env python3
"""Publish one pipeline run to the site: its report PDF plus the raw run data.

The papers class is normally regenerated wholesale from a run manifest
(build-papers-page.py). This script is the escape hatch for runs that are not in
that manifest yet — a v12-preview render, a one-off rerun — and it is the only
place that writes the *manual* catalog block, which regeneration never touches.

  # local job directory
  python3 scripts/publish-run.py /path/to/data/jobs/<job-id> --pdf report.v12-preview.pdf

  # job directory on the pipeline host (fetched over ssh into a temp dir)
  python3 scripts/publish-run.py yqh2:/opt/paper-pipeline/data/jobs/<job-id>

What lands on the site:
  site/downloads/<slug>.pdf                  the report
  site/assets/covers/<slug>.jpg              first-page cover (generate-pdf-covers.py)
  site/downloads/runs/<slug>-run.zip         the run's own data, text only
  site/assets/catalog.js                     an entry inside the manual block
  scripts/manual-papers.txt                  slug list, so regeneration keeps the files

Why text only: the bundle carries what the model read and decided (OCR text per
page, metadata, layout DSL, Typst source, figure analyses, usage ledger) — about
200KB compressed. The figure crops and the source paper PDF are deliberately left
out: they are third-party content, they are the bulk of a job directory (11MB of
16MB here), and the published report already embeds the figures it uses. The
bundle records source_url so the original is one click away.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SITE = REPO / "site"
DOWNLOADS = SITE / "downloads"
RUNS = DOWNLOADS / "runs"
CATALOG = SITE / "assets" / "catalog.js"
MANUAL_LIST = REPO / "scripts" / "manual-papers.txt"

MANUAL_BEGIN = "  /* BEGIN manual: hand-published runs */"
MANUAL_END = "  /* END manual: hand-published runs */"
GENERATED_BEGIN = "  /* BEGIN generated: paper reports */"

# Files worth keeping for reproduction. Matched by suffix, images excluded on purpose.
BUNDLE_SUFFIXES = (".md", ".json", ".yaml", ".yml", ".typ")
BUNDLE_SKIP_DIRS = ("input",)
ACCENTS = ["blue", "violet", "orange", "green"]


def slugify(title: str) -> str:
    base = title.split(":")[0] if ":" in title else " ".join(title.split()[:6])
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "paper"


def fetch_remote(spec: str, pdf_name: str) -> Path:
    """Copy the allowlisted files of a remote job dir into a temp dir."""
    host, _, remote_path = spec.partition(":")
    tmp = Path(tempfile.mkdtemp(prefix="lil-run-"))
    includes = [
        "--include=*/",
        f"--include={pdf_name}",
        *[f"--include=*{suffix}" for suffix in BUNDLE_SUFFIXES],
        *[f"--exclude={d}/**" for d in BUNDLE_SKIP_DIRS],
        "--exclude=*",
    ]
    cmd = ["rsync", "-a", "--prune-empty-dirs", *includes, f"{host}:{remote_path.rstrip('/')}/", str(tmp)]
    print("fetching:", " ".join(cmd[:3]), f"{host}:{remote_path}")
    subprocess.run(cmd, check=True)
    return tmp


def bundle_files(job: Path) -> list[Path]:
    files = []
    for path in sorted(job.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(job)
        if rel.parts[0] in BUNDLE_SKIP_DIRS:
            continue
        if path.suffix.lower() in BUNDLE_SUFFIXES:
            files.append(path)
    return files


def write_bundle(job: Path, slug: str, meta: dict, job_info: dict, pdf_name: str) -> Path:
    RUNS.mkdir(parents=True, exist_ok=True)
    out = RUNS / f"{slug}-run.zip"
    files = bundle_files(job)
    readme = f"""这是「{meta.get('title') or slug}」解构报告的原始运行数据（仅文本）。

来源
  job id        {job_info.get('id') or job.name}
  source_url    {job_info.get('source_url') or '（未记录）'}
  OCR 页数      {job_info.get('page_count') or '?'}
  报告模型      {job_info.get('report_model') or '?'}
  prompt 版本   {job_info.get('report_prompt_version') or '?'}
  发布的 PDF    {pdf_name} -> /downloads/{slug}.pdf

包含什么
  full-text.md              整篇 OCR 文本（模型实际读到的东西）
  pages/page-*.md           逐页 OCR
  metadata.json             抽取出的标题/作者/venue/年份/标签/链接
  job.json, usage.json      运行状态与 token 用量账本
  report*.md                合成出的报告正文
  report*.layout.yaml       排版 DSL
  report*.typ               Pandoc + Typst 的编译输入
  figure-analyses/          逐图分析结果

不包含什么，以及为什么
  input/source.pdf          论文原文，第三方版权内容，按 source_url 自取
  assets/, *-groups/*.png   从原文切出的图片，同上；已发布的 PDF 里嵌了实际用到的图

要重新渲染报告：取回 source_url 的 PDF 重跑流水线，或用 report*.typ 配合自己的图片资源编译。
"""
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.txt", readme)
        for path in files:
            zf.write(path, str(path.relative_to(job)))
    print(f"bundle {out.relative_to(REPO)} ({out.stat().st_size // 1024} KB, {len(files)} files)")
    return out


def source_of(meta: dict, job_info: dict):
    links = meta.get("links") or {}
    arxiv = links.get("arxiv")
    if arxiv:
        ident = str(arxiv).rstrip("/").split("/")[-1].replace(".pdf", "")
        return f"arXiv:{ident}", f"https://arxiv.org/abs/{ident}"
    doi = links.get("doi")
    if doi and str(doi).startswith("http"):
        return "DOI", str(doi)
    src = links.get("source") or job_info.get("source_url")
    if src and str(src).startswith("http"):
        return "原文", str(src)
    return None


def catalog_entry(slug: str, meta: dict, job_info: dict, accent: str) -> str:
    authors = meta.get("authors") or []
    first = authors[0] if authors else "Unknown"
    bits = [f"{first} 等"]
    if meta.get("year"):
        bits.append(str(meta["year"]))
    if meta.get("venue"):
        bits.append(str(meta["venue"]))
    subtitle = " · ".join(bits)
    abstract = (meta.get("abstract_translation") or "").strip().replace("\n", " ")
    description = (abstract[:118] + "…") if len(abstract) > 118 else abstract
    tags = ", ".join(json.dumps(t, ensure_ascii=False) for t in (meta.get("tags") or [])[:3])
    link = source_of(meta, job_info)
    source = (
        f"\n    source: {{ label: {json.dumps(link[0], ensure_ascii=False)}, url: {json.dumps(link[1], ensure_ascii=False)} }},"
        if link
        else ""
    )
    updated = (job_info.get("updated_at") or "")[:10]
    return f"""  {{
    id: '{slug}',
    category: 'papers',
    type: '论文解构',
    title: {json.dumps(meta.get('title') or slug, ensure_ascii=False)},
    subtitle: {json.dumps(subtitle, ensure_ascii=False)},
    description: {json.dumps(description, ensure_ascii=False)},
    tags: [{tags}],{source}
    href: 'downloads/{slug}.pdf',
    runData: 'downloads/runs/{slug}-run.zip',
    action: '在阅读器打开',
    updated: '{updated}',
    accent: '{accent}'
  }},
"""


def upsert_catalog(slug: str, entry: str) -> None:
    text = CATALOG.read_text()
    if MANUAL_BEGIN not in text:
        anchor = text.index(GENERATED_BEGIN)
        header = (
            MANUAL_BEGIN
            + "\n"
            + "  /* 由 scripts/publish-run.py 维护：不在运行清单里的单次运行。\n"
            + "     放在 generated 块之外，build-papers-page.py 不会覆盖。 */\n"
            + MANUAL_END
            + "\n"
        )
        text = text[:anchor] + header + text[anchor:]

    start = text.index(MANUAL_BEGIN)
    end = text.index(MANUAL_END)
    block = text[start:end]
    # Drop an existing entry for this slug, then append the fresh one.
    block = re.sub(r"  \{\n    id: '" + re.escape(slug) + r"'.*?\n  \},\n", "", block, flags=re.S)
    block = block.rstrip("\n") + "\n" + entry
    CATALOG.write_text(text[:start] + block + text[end:])
    print(f"catalog entry upserted: {slug}")


def register_manual(slug: str) -> None:
    slugs = []
    if MANUAL_LIST.exists():
        slugs = [s.strip() for s in MANUAL_LIST.read_text().splitlines() if s.strip() and not s.startswith("#")]
    if slug not in slugs:
        slugs.append(slug)
    MANUAL_LIST.write_text(
        "# 手工发布的运行（scripts/publish-run.py 维护）。\n"
        "# build-papers-page.py 读这份清单：这些 slug 的 PDF/封面不会被当成孤儿删掉，\n"
        "# 首页的报告篇数也会把它们算进去。\n"
        + "\n".join(sorted(slugs))
        + "\n"
    )
    print(f"registered in {MANUAL_LIST.relative_to(REPO)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("job", help="job directory, local path or host:path")
    parser.add_argument("--pdf", default="report.compact.pdf", help="which report PDF to publish")
    parser.add_argument("--slug", help="override the published slug (published URLs must not move)")
    parser.add_argument("--accent", choices=ACCENTS, default="green")
    parser.add_argument("--keep-temp", action="store_true", help="keep the fetched temp dir")
    args = parser.parse_args()

    remote = ":" in args.job and not Path(args.job).exists()
    job = fetch_remote(args.job, args.pdf) if remote else Path(args.job).expanduser().resolve()
    if not job.is_dir():
        sys.exit(f"not a job directory: {job}")

    meta_path = job / "metadata.json"
    if not meta_path.exists():
        sys.exit(f"missing metadata.json in {job}")
    meta = json.loads(meta_path.read_text())
    job_info = json.loads((job / "job.json").read_text()) if (job / "job.json").exists() else {}

    pdf = job / args.pdf
    if not pdf.exists():
        sys.exit(f"missing {args.pdf} in {job}")

    slug = args.slug or slugify(meta.get("title") or job.name)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, DOWNLOADS / f"{slug}.pdf")
    print(f"pdf -> site/downloads/{slug}.pdf ({(DOWNLOADS / f'{slug}.pdf').stat().st_size // 1024} KB)")

    write_bundle(job, slug, meta, job_info, args.pdf)
    upsert_catalog(slug, catalog_entry(slug, meta, job_info, args.accent))
    register_manual(slug)

    covers = REPO / "scripts" / "generate-pdf-covers.py"
    if covers.exists():
        subprocess.run([sys.executable, str(covers)], check=False)

    if remote and not args.keep_temp:
        shutil.rmtree(job, ignore_errors=True)

    print(
        f"\ndone: {slug}\n"
        f"  记得把 '{slug}' 加进 site/assets/catalog.js 的 window.PAPER_GROUPS，否则阅读器侧栏会归到「未分组」。\n"
        f"  然后跑 npm run validate。"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
