#!/usr/bin/env python3
"""Scan every paper-pipeline job store on this host, emit one JSON manifest on stdout.

Groups runs by normalized paper title and keeps the best one per paper:
a clean run (report succeeded, compact PDF rendered, no `error`) always beats a
degraded one, and among equals the newest wins. Degraded runs are still emitted
with `clean: false` and a reason, so the page can decide whether to list them.
"""
import json
import glob
import os
import re
import sys

STORES = [
    ("/opt/paper-pipeline/data/jobs", "opt"),
    (os.path.expanduser("~/work/paper-pipeline/data/jobs"), "dev"),
]


def norm_title(t):
    """Match the same paper across runs despite OCR casing/punctuation drift."""
    t = (t or "").lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return " ".join(t.split())[:60]


def collect():
    runs = []
    for base, store in STORES:
        for d in sorted(glob.glob(base + "/*")):
            jf, mf, uf = (os.path.join(d, n) for n in ("job.json", "metadata.json", "usage.json"))
            if not (os.path.exists(jf) and os.path.exists(mf)):
                continue
            try:
                job = json.load(open(jf))
                meta = json.load(open(mf))
            except Exception:
                continue
            if job.get("report_state") != "succeeded":
                continue

            usage = {}
            if os.path.exists(uf):
                try:
                    usage = json.load(open(uf))
                except Exception:
                    usage = {}
            summary = (usage or {}).get("summary") or {}
            events = (usage or {}).get("events") or []

            pdf = os.path.join(d, "report.compact.pdf")
            has_pdf = bool(job.get("compact_pdf")) and os.path.exists(pdf)

            # A run is "clean" only if the whole pipeline finished: report + render,
            # with no recorded error. A render failure leaves timings that describe a
            # partial run, so it must not be presented next to complete ones.
            reason = None
            if job.get("error"):
                reason = "render-failed" if "render failed" in str(job["error"]) else "error"
            elif not has_pdf:
                reason = "no-pdf"
            elif not events:
                reason = "no-ledger"
            clean = reason is None

            prompt_tok = (summary.get("provider_usage") or {}).get("prompt_tokens") or 0
            cached_tok = (summary.get("provider_usage") or {}).get("cached_content_tokens") or 0
            # The old agy backend billed by subscription and reported no token counts;
            # a zero here means "not reported", not "zero used".
            reports_tokens = prompt_tok > 0

            runs.append(
                dict(
                    job_id=job["id"],
                    store=store,
                    dir=d,
                    title=meta.get("title") or "(untitled)",
                    norm=norm_title(meta.get("title")),
                    authors=meta.get("authors") or [],
                    venue=meta.get("venue") or "",
                    year=meta.get("year") or "",
                    tags=meta.get("tags") or [],
                    abstract_cn=(meta.get("abstract_translation") or "").strip(),
                    links=meta.get("links") or {},
                    run_date=(job.get("updated_at") or "")[:10],
                    prompt_version=job.get("report_prompt_version"),
                    model=job.get("report_model"),
                    pages=job.get("page_count") or 0,
                    wall_s=round((summary.get("pipeline_latency_ms") or 0) / 1000),
                    calls=summary.get("provider_call_count") or 0,
                    prompt_tokens=prompt_tok,
                    cache_hit=round(100 * cached_tok / prompt_tok) if prompt_tok else None,
                    reports_tokens=reports_tokens,
                    stages=[e.get("phase") for e in events],
                    has_pdf=has_pdf,
                    pdf_kb=round(os.path.getsize(pdf) / 1024) if has_pdf else None,
                    clean=clean,
                    reason=reason,
                )
            )

    # Best run per paper: clean wins over degraded, then newest.
    best = {}
    for r in runs:
        cur = best.get(r["norm"])
        if cur is None or (r["clean"], r["run_date"]) > (cur["clean"], cur["run_date"]):
            best[r["norm"]] = r

    return dict(
        runs_total=len(runs),
        papers=sorted(best.values(), key=lambda r: r["title"].lower()),
    )


if __name__ == "__main__":
    json.dump(collect(), sys.stdout, ensure_ascii=False, indent=1)
