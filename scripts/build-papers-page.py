#!/usr/bin/env python3
"""Regenerate the paper-report ledger page and its catalog entries from a run manifest.

Reads the JSON emitted by collect_runs.py, writes:
  site/content/papers/index.html   — full page (hero, reproduction guide, ledger)
  site/assets/catalog.js           — the BEGIN/END generated block only

Everything shown is read from each job's own job.json / usage.json, so re-running
this after another batch finishes is the whole update procedure.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Manifest from scripts/collect-runs.py, and a directory of <job-id>.pdf staged
# from the pipeline host. Override with PAPERS_MANIFEST / PAPERS_PDFS.
MANIFEST = Path(os.environ.get("PAPERS_MANIFEST", "/tmp/runs.json"))
STAGING = Path(os.environ.get("PAPERS_PDFS", "/tmp/lil-pdfs"))
DOWNLOADS = REPO / "site" / "downloads"
CATALOG = REPO / "site" / "assets" / "catalog.js"
PAGE = REPO / "site" / "content" / "papers" / "index.html"
# Runs published by scripts/publish-run.py: not in the manifest, but their files
# must survive regeneration and their count must show on the homepage.
MANUAL_LIST = REPO / "scripts" / "manual-papers.txt"


def manual_slugs():
    if not MANUAL_LIST.exists():
        return []
    return [
        line.strip()
        for line in MANUAL_LIST.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

BUILD_DATE = subprocess.run(["date", "-u", "+%Y-%m-%d %H:%M UTC"], capture_output=True, text=True).stdout.strip()

# Matched as prefixes of the normalized title, so they survive the collector's
# truncation and小 OCR drift between runs.
#
# TITLE_FIX: OCR sometimes returns a title in full caps, which mangles the heading.
TITLE_FIX = [
    ("an image is worth 16x16 words", "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale"),
    ("torch fx practical program capture", "Torch.fx: Practical Program Capture and Transformation for Deep Learning in Python"),
    (
        "flexpipe adapting dynamic llm serving",
        "FlexPipe: Adapting Dynamic LLM Serving Through Inflight Pipeline Refactoring in Fragmented Serverless Clusters",
    ),
]

# SLUG_FIX: published URLs must not move, so pin the slug of every paper that has
# already appeared on the site. New papers fall through to slugify().
SLUG_FIX = [
    ("an image is worth 16x16 words", "image-worth-16x16-words"),
    ("attention is all you need", "attention-all-you-need"),
    ("deep residual learning for image recognition", "deep-residual-learning-image-recognition"),
    ("flexpipe adapting dynamic llm serving", "flexpipe"),
    ("gpemu a gpu emulator", "gpemu"),
    ("realb real time load balancing", "realb"),
    ("servegen workload characterization", "servegen"),
    ("torch fx practical program capture", "torchfx"),
    ("understanding diffusion model serving in production", "understanding-diffusion-model-serving-production"),
    ("tally non intrusive performance isolation", "tally"),
    ("towards high goodput llm serving", "prefill-decode-multiplexing"),
    # Papers whose only earlier run carried a wrong title; slugged on first
    # correct listing. `sarathi` and `pipelive` are deliberately absent — they
    # were never real papers here, just mis-extracted captions for the runs now
    # listed as Revisiting Pipeline Parallelism and DynaPipe.
    ("revisiting pipeline parallelism", "revisiting-pipeline-parallelism"),
    ("dynapipe dynamic layer redistribution", "dynapipe"),
    ("frontier towards comprehensive", "frontier"),
    ("memocr layout aware visual memory", "memocr"),
    ("deterministic inference across tensor parallel", "deterministic-inference"),
    ("simai unifying architecture design", "simai"),
    ("tensor parallelism with partially synchronized", "tensor-parallelism-partial-sync"),
]


def _lookup(table, norm, default=None):
    for prefix, value in table:
        if norm.startswith(prefix):
            return value
    return default

ACCENTS = ["blue", "violet", "orange", "green"]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def attr(s):
    return esc(s).replace('"', "&quot;")


def slugify(title):
    base = title.split(":")[0] if ":" in title else " ".join(title.split()[:6])
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "paper"


def fmt_int(n):
    return f"{n:,}"


def paper_link(p):
    """Prefer arXiv, fall back to DOI, then code. Returns (label, url) or None."""
    links = p.get("links") or {}
    ax = links.get("arxiv")
    if ax:
        ax_id = str(ax).rstrip("/").split("/")[-1].replace(".pdf", "")
        return f"arXiv:{ax_id}", f"https://arxiv.org/abs/{ax_id}"
    doi = links.get("doi")
    if doi and str(doi).startswith("http"):
        return "DOI", doi
    src = links.get("source")
    if src and str(src).startswith("http"):
        return "原文", src
    return None


def main():
    data = json.loads(MANIFEST.read_text())
    papers = data["papers"]

    for p in papers:
        p["title"] = _lookup(TITLE_FIX, p["norm"], p["title"])
        p["slug"] = _lookup(SLUG_FIX, p["norm"]) or slugify(p["title"])

    clean = [p for p in papers if p["clean"]]
    degraded = [p for p in papers if not p["clean"]]
    clean.sort(key=lambda p: p["title"].lower())
    degraded.sort(key=lambda p: p["title"].lower())

    # ---- copy PDFs -------------------------------------------------------
    for p in clean:
        src = STAGING / f"{p['job_id']}.pdf"
        if not src.exists():
            sys.exit(f"missing staged PDF for {p['slug']} ({p['job_id']})")
        shutil.copyfile(src, DOWNLOADS / f"{p['slug']}.pdf")
        p["pdf_kb"] = round((DOWNLOADS / f"{p['slug']}.pdf").stat().st_size / 1024)

    # First-page JPEG covers for the homepage / papers waterfall gallery.
    cover_script = REPO / "scripts" / "generate-pdf-covers.py"
    if cover_script.exists():
        result = subprocess.run([sys.executable, str(cover_script)], check=False)
        if result.returncode != 0:
            print("warning: cover generation failed; gallery will fall back to text cards")

    # ---- aggregates ------------------------------------------------------
    manual = manual_slugs()
    n = len(clean)
    pages = sum(p["pages"] for p in clean)
    calls = sum(p["calls"] for p in clean)
    current = [p for p in clean if p["prompt_version"] == "v11" and p["model"] == "claude-sonnet-5"]
    stale = [p for p in clean if p not in current]
    tok_papers = [p for p in clean if p["reports_tokens"]]
    total_prompt = sum(p["prompt_tokens"] for p in tok_papers)
    avg_hit = round(sum(p["cache_hit"] for p in tok_papers) / len(tok_papers)) if tok_papers else 0
    latest_run = max(p["run_date"] for p in clean)

    # ---- ledger rows -----------------------------------------------------
    rows = []
    for p in clean:
        is_stale = p in stale
        cls = ' class="stale"' if is_stale else ""
        tok = fmt_int(p["prompt_tokens"]) if p["reports_tokens"] else "未上报"
        hit = f'{p["cache_hit"]}%' if p["reports_tokens"] else "未上报"
        link = paper_link(p)
        origin = f' <a class="src" href="{attr(link[1])}" rel="noopener">{esc(link[0])}</a>' if link else ""
        rows.append(
            f'<tr>'
            f'<td><a href="../../downloads/{p["slug"]}.pdf">{esc(p["title"])}</a>{origin}</td>'
            f'<td class="num date">{p["run_date"]}</td>'
            f'<td{cls}><code>{esc(p["prompt_version"] or "—")}</code></td>'
            f'<td{cls}><code>{esc(p["model"] or "—")}</code></td>'
            f'<td class="num">{p["pages"]}</td>'
            f'<td class="num">{p["wall_s"]}s</td>'
            f'<td class="num">{p["calls"]}</td>'
            f'<td class="num">{tok}</td>'
            f'<td class="num">{hit}</td>'
            f'<td class="num">{p["pdf_kb"]} KB</td>'
            f'</tr>'
        )

    REASONS = {
        "render-failed": "报告已生成，但排版渲染失败",
        "no-pdf": "尚未渲染出 PDF",
        "no-ledger": "缺少阶段账本",
        "error": "运行中出错",
    }
    deg_rows = "".join(
        f'<tr><td>{esc(p["title"])}</td><td class="num date">{p["run_date"]}</td>'
        f'<td><code>{esc(p["prompt_version"] or "—")}</code></td>'
        f'<td><code>{esc(p["model"] or "—")}</code></td>'
        f'<td>{esc(REASONS.get(p["reason"], p["reason"]))}</td></tr>'
        for p in degraded
    )

    deg_section = ""
    if degraded:
        deg_section = f"""
    <section class="library shell" aria-labelledby="skipped-title">
      <div class="section-heading"><div><p class="eyebrow">NOT LISTED</p><h2 id="skipped-title">未收录的 {len(degraded)} 次运行</h2></div></div>
      <p class="pipeline-note">这些运行的正文报告已经产出，但整条流水线没有跑完，因此它们的耗时与调用次数描述的是一次中断，而不是一份完整产物。列在这里是为了让上表的口径可被检验，而不是让失败悄悄消失。</p>
      <div class="table-wrap">
        <table class="run-table skipped">
          <thead><tr><th>论文</th><th class="num">运行日期</th><th>Prompt</th><th>模型</th><th>未收录原因</th></tr></thead>
          <tbody>{deg_rows}</tbody>
        </table>
      </div>
    </section>
"""

    # The note has to describe the table that actually got generated: claims about
    # an "unreported" column or a section of skipped runs read as evasion once the
    # thing they refer to is gone.
    note_parts = [
        "下表数据全部读自各任务的 <code>usage.json</code>，不是估算值。缓存命中率为 "
        "<code>cache_read_input_tokens ÷ prompt tokens</code>。"
    ]
    if any(not p["reports_tokens"] for p in clean):
        note_parts.append(
            "<strong>未上报</strong>表示该后端不返回 token 计数（早期的 <code>agy</code> 后端如此），并非命中率为零。"
        )
    if degraded:
        note_parts.append("只收录整条流水线跑完的运行，其余列在下一节。")
    else:
        note_parts.append("只收录整条流水线跑完的运行；本次没有中途失败的运行。")
    if stale:
        note_parts.append(
            f"当前仍有 <strong>{len(stale)}</strong> 篇是早期后端产出（表中橙色标注），正在逐篇用当前配置重跑。"
        )
    else:
        note_parts.append(f"这 {n} 篇全部由上面那一套配置产出，因此各行的耗时与 token 可以直接横向比较。")
    ledger_note = "\n      ".join(note_parts)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="OCR + Agent 流水线生成的论文解构报告索引：每篇的运行日期、prompt 版本、阶段耗时与 token 用量，并附完整复现步骤。">
  <title>论文解构报告索引 · LLM 推理资料库</title>
  <link rel="stylesheet" href="../../assets/site.css">
  <style>
    .run-table {{ width:100%; border-collapse:collapse; margin:24px 0 12px; font-size:14px; }}
    .run-table th, .run-table td {{ padding:10px 12px; border-bottom:1px solid var(--line); text-align:left; }}
    .run-table th {{ color:var(--muted); font-size:12px; letter-spacing:.06em; text-transform:uppercase; font-weight:700; }}
    .run-table td.num, .run-table th.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
    .run-table td.date {{ color:var(--muted); font-size:13px; }}
    .run-table tbody tr:hover {{ background:rgba(50,101,214,.04); }}
    .run-table a {{ color:var(--blue); font-weight:640; text-decoration:none; }}
    .run-table a:hover {{ text-decoration:underline; }}
    .run-table a.src {{ margin-left:8px; color:var(--muted); font-weight:500; font-size:12px; white-space:nowrap; }}
    .run-table.skipped td {{ color:#5b6577; }}
    .table-wrap {{ overflow-x:auto; }}
    .pipeline-note {{ max-width:820px; color:#4b5668; }}
    .pipeline-note code, .run-table code, .repro code {{ padding:1px 5px; border:1px solid var(--line); border-radius:5px; background:#fff; font-size:12px; }}
    .run-table code {{ display:inline-block; white-space:nowrap; }}
    .run-table td.stale code {{ color:var(--orange); border-color:#f0d3bd; background:#fdf5ef; }}

    .updated {{ display:inline-flex; align-items:center; gap:8px; margin:0 0 18px; padding:5px 12px; border:1px solid var(--line); border-radius:999px; background:var(--panel); color:var(--muted); font-size:13px; }}
    .updated b {{ color:var(--ink); font-weight:640; }}
    .updated .dot {{ width:7px; height:7px; border-radius:50%; background:var(--green); }}

    .repro {{ padding:52px 0 12px; border-top:1px solid var(--line); }}
    .flow {{ display:flex; flex-wrap:wrap; gap:8px; margin:22px 0 30px; }}
    .flow li {{ display:flex; align-items:center; gap:8px; padding:9px 14px; border:1px solid var(--line); border-radius:10px; background:var(--panel); font-size:13.5px; }}
    .flow li b {{ font-weight:640; }}
    .flow li span {{ color:var(--muted); font-size:12px; }}
    .flow li::before {{ content:attr(data-n); display:grid; place-items:center; width:20px; height:20px; border-radius:6px; background:rgba(50,101,214,.1); color:var(--blue); font-size:11px; font-weight:760; }}
    .flow-arrow {{ align-self:center; color:var(--muted); font-size:13px; }}
    .repro-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(290px, 1fr)); gap:18px; margin-top:8px; }}
    .repro-card {{ padding:20px 22px; border:1px solid var(--line); border-radius:14px; background:var(--panel); box-shadow:var(--shadow); }}
    .repro-card h3 {{ margin:0 0 6px; font-size:15px; }}
    .repro-card p {{ margin:0 0 12px; color:var(--muted); font-size:13px; }}
    .repro pre {{ margin:0; padding:14px 16px; overflow-x:auto; border:1px solid var(--line); border-radius:10px; background:#f8fafc; font-family:ui-monospace, SFMono-Regular, Menlo, monospace; font-size:12.5px; line-height:1.7; }}
    .repro pre b {{ color:var(--blue); font-weight:600; }}
    .repro pre i {{ color:var(--muted); font-style:normal; }}
    .versions {{ display:flex; flex-wrap:wrap; gap:0; margin:26px 0 0; border:1px solid var(--line); border-radius:14px; overflow:hidden; background:var(--panel); }}
    .versions div {{ flex:1 1 150px; padding:14px 18px; border-right:1px solid var(--line); }}
    .versions div:last-child {{ border-right:0; }}
    .versions dt {{ margin:0 0 3px; color:var(--muted); font-size:11.5px; letter-spacing:.06em; text-transform:uppercase; font-weight:700; }}
    .versions dd {{ margin:0; font-size:14px; font-weight:600; }}
    @media (max-width:640px) {{ .flow-arrow {{ display:none; }} }}
  </style>
</head>
<body>
  <header class="site-header">
    <div class="shell header-content">
      <a class="brand" href="../../" aria-label="LLM 推理资料库首页">
        <span class="brand-mark" aria-hidden="true">λ</span><span>LLM 推理资料库</span>
      </a>
      <p class="header-note">论文解构报告索引</p>
    </div>
  </header>

  <main>
    <section class="hero shell">
      <p class="eyebrow">PIPELINE OUTPUT / 2026</p>
      <h1>{n} 篇论文的结构化解构报告</h1>
      <p class="updated"><span class="dot" aria-hidden="true"></span>本页生成于 <b>{BUILD_DATE}</b> · 最新一次论文运行 <b>{latest_run}</b></p>
      <p class="intro">每份报告都由同一条流水线生成：云端 OCR 转逐页 Markdown，再依次做全文分析、逐图视觉分析、报告合成与布局 DSL，最后由 Pandoc + Typst 编译成图左文右的紧凑 PDF。下表与本页的每个数字都读自各任务的运行账本，不是手工誊写。</p>
      <div class="stat-row" aria-label="运行概览">
        <div><strong>{n}</strong><span>已解构论文</span></div>
        <div><strong>{pages}</strong><span>OCR 页数</span></div>
        <div><strong>{calls}</strong><span>模型调用次数</span></div>
        <div><strong>{avg_hit}%</strong><span>平均缓存命中</span></div>
      </div>
    </section>

    <section class="repro shell" aria-labelledby="repro-title">
      <p class="eyebrow">HOW IT'S PRODUCED</p>
      <h2 id="repro-title">这些报告是怎么跑出来的</h2>
      <p class="pipeline-note">流水线只接收一个 PDF 或它的 URL，其余阶段全部自动串起来。除 OCR 由云端模型完成、排版由 Typst 确定性编译外，中间每一步的推理都由同一个 Agent 后端承担。</p>

      <ol class="flow">
        <li data-n="1"><b>云端 OCR</b><span>PaddleOCR-VL → 逐页 Markdown + 图片</span></li>
        <span class="flow-arrow" aria-hidden="true">→</span>
        <li data-n="2"><b>全文分析</b><span>论文主张地图</span></li>
        <span class="flow-arrow" aria-hidden="true">→</span>
        <li data-n="3"><b>逐图视觉分析</b><span>每 2 图一批，最多 6 批并行</span></li>
        <span class="flow-arrow" aria-hidden="true">→</span>
        <li data-n="4"><b>报告合成</b><span>compose → critique_refine</span></li>
        <span class="flow-arrow" aria-hidden="true">→</span>
        <li data-n="5"><b>布局 DSL</b><span>校验后的 YAML</span></li>
        <span class="flow-arrow" aria-hidden="true">→</span>
        <li data-n="6"><b>Pandoc + Typst</b><span>紧凑 PDF</span></li>
      </ol>

      <div class="repro-grid">
        <div class="repro-card">
          <h3>后端配置</h3>
          <p>Agent 阶段不走 API key，而是直接调用已登录的 Claude Code CLI。</p>
<pre><b>AGENT_BACKEND</b>=cli_agent
<b>CLI_AGENT_COMMAND</b>=claude
<b>CLI_AGENT_MODEL</b>=claude-sonnet-5
<b>CLI_AGENT_ARGS</b>=["--effort","medium",
  "--dangerously-skip-permissions",
  "--add-dir","{{workspace}}","--print"]
<b>CLI_AGENT_OUTPUT_FORMAT</b>=json
<b>AGENT_TIMEOUT_SECONDS</b>=900</pre>
        </div>
        <div class="repro-card">
          <h3>运行命令</h3>
          <p>提交一个 URL 即可跑完全程；复用已有 OCR 产物则跳过云端调用。</p>
<pre><i># 从 URL 跑完整流程</i>
paper-pipeline run \\
  --url https://arxiv.org/pdf/2410.07381

<i># 复用已存 OCR，只重做分析</i>
paper-pipeline analyze \\
  --ocr-dir data/jobs/&lt;job-id&gt;</pre>
        </div>
      </div>

      <dl class="versions">
        <div><dt>Prompt 版本</dt><dd>v11</dd></div>
        <div><dt>Agent 模型</dt><dd>claude-sonnet-5</dd></div>
        <div><dt>推理力度</dt><dd>medium</dd></div>
        <div><dt>OCR 模型</dt><dd>PaddleOCR-VL-1.6</dd></div>
        <div><dt>图批并行</dt><dd>6</dd></div>
      </dl>
    </section>

    <section class="library shell" aria-labelledby="gallery-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">PDF GALLERY</p>
          <h2 id="gallery-title">封面瀑布流</h2>
        </div>
      </div>
      <p class="pipeline-note">每张封面取自解构报告首页。点击卡片进入站内阅读器（左侧按主题分层，右侧 EmbedPDF 直接阅读），也可直接下载原 PDF。</p>
      <div class="content-grid is-waterfall" id="paperGallery" data-base="../../"></div>
    </section>

    <section class="library shell" aria-labelledby="ledger-title">
      <div class="section-heading"><div><p class="eyebrow">RUN LEDGER</p><h2 id="ledger-title">每篇的运行账本</h2></div></div>
      <p class="pipeline-note">{ledger_note}</p>
      <div class="table-wrap">
        <table class="run-table">
          <thead><tr><th>论文</th><th class="num">运行日期</th><th>Prompt</th><th>模型</th><th class="num">OCR 页</th><th class="num">总耗时</th><th class="num">调用</th><th class="num">Prompt token</th><th class="num">缓存命中</th><th class="num">PDF</th></tr></thead>
          <tbody>
{chr(10).join(rows)}
          </tbody>
        </table>
      </div>
    </section>
{deg_section}  </main>

  <footer class="site-footer">
    <div class="shell"><span>LLM 推理资料库</span><span>本页由运行账本自动生成 · {BUILD_DATE}</span></div>
  </footer>
  <script src="../../assets/catalog.js"></script>
  <script src="../../assets/site.js"></script>
</body>
</html>
"""
    PAGE.write_text(html)

    # ---- catalog entries -------------------------------------------------
    entries = [
        f"""  {{
    id: 'paper-analysis-index',
    category: 'papers',
    type: '运行账本',
    title: '论文解构报告索引',
    subtitle: "{n} 篇 · 运行日期、版本与 token",
    description: '一张表看完所有解构报告的运行日期、prompt 版本、OCR 页数、耗时与缓存命中率，并附完整的复现配置与命令。',
    tags: ['运行账本', '流水线', '可复现'],
    href: 'content/papers/index.html',
    action: '查看索引',
    updated: '{BUILD_DATE[:10]}',
    accent: 'violet'
  }},
"""
    ]
    for i, p in enumerate(clean):
        authors = p.get("authors") or []
        first = authors[0] if authors else "Unknown"
        subtitle = f"{first} 等 · {p['year']}" if p.get("year") else f"{first} 等"
        abstract = p.get("abstract_cn") or ""
        desc = (abstract[:118] + "…") if len(abstract) > 118 else abstract
        tags = ", ".join(f"'{t}'" for t in (p.get("tags") or [])[:3])
        # 原文链接：抽到了就写进条目，页面缺失时回落到 catalog.js 的 PAPER_SOURCES。
        link = paper_link(p)
        # 运行数据包（scripts/fetch-run-bundles.py 拉的）：在就挂上，不在就不提。
        bundle = REPO / "site" / "downloads" / "runs" / f"{p['slug']}-run.zip"
        run_data = f"\n    runData: 'downloads/runs/{p['slug']}-run.zip'," if bundle.exists() else ""
        source = (
            f"\n    source: {{ label: {json.dumps(link[0], ensure_ascii=False)}, "
            f"url: {json.dumps(link[1], ensure_ascii=False)} }},"
            if link else ""
        )
        entries.append(
            f"""  {{
    id: '{p["slug"]}',
    category: 'papers',
    type: '论文解构',
    title: {json.dumps(p["title"], ensure_ascii=False)},
    subtitle: {json.dumps(subtitle, ensure_ascii=False)},
    description: {json.dumps(desc, ensure_ascii=False)},
    tags: [{tags}],{source}
    href: 'downloads/{p["slug"]}.pdf',{run_data}
    action: '在阅读器打开',
    updated: '{p["run_date"]}',
    accent: '{ACCENTS[i % len(ACCENTS)]}'
  }},
"""
        )

    # The homepage carries its own hardcoded count of paper reports; keep it in step.
    home = REPO / "site" / "index.html"
    home_html = home.read_text()
    home_html = re.sub(
        r"<div><strong>\d+</strong><span>论文解构报告</span></div>",
        f"<div><strong>{n + len(manual)}</strong><span>论文解构报告</span></div>",
        home_html,
    )
    home.write_text(home_html)

    cat = CATALOG.read_text()
    start = cat.index("  /* BEGIN generated: paper reports */")
    end = cat.index("  /* END generated: paper reports */")
    cat = (
        cat[:start]
        + "  /* BEGIN generated: paper reports */\n"
        + "".join(entries)
        + cat[end:]
    )
    CATALOG.write_text(cat)

    # Drop PDFs / covers for papers that are no longer listed.
    keep = {f"{p['slug']}.pdf" for p in clean} | {f"{s}.pdf" for s in manual}
    for f in DOWNLOADS.glob("*.pdf"):
        if f.name not in keep:
            f.unlink()
            print(f"removed orphan {f.name}")
    covers = REPO / "site" / "assets" / "covers"
    if covers.exists():
        keep_covers = {f"{p['slug']}.jpg" for p in clean} | {f"{s}.jpg" for s in manual}
        for f in covers.glob("*.jpg"):
            if f.name not in keep_covers:
                f.unlink()
                print(f"removed orphan cover {f.name}")

    if manual:
        print(f"manual runs kept: {', '.join(manual)}")
    print(f"papers={n} pages={pages} calls={calls} avg_hit={avg_hit}% stale={len(stale)} degraded={len(degraded)}")
    print(f"latest run {latest_run}, built {BUILD_DATE}")


if __name__ == "__main__":
    main()
