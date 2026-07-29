---
name: llm-inference-library
description: >-
  Operate the static LLM inference library: regenerate the papers page from run
  manifests, publish a single run, fetch run-data bundles, restyle published PDFs
  after a render-stage change, and work on the EmbedPDF reader. Use when working in
  the llm-inference-library repo, adding or re-rendering paper reports, or touching
  the reader / cover waterfall.
---

# LLM 推理资料库（静态站）

无后端静态站，GitHub Pages 托管 `site/`。内容清单在 `site/assets/catalog.js`，
论文那一类由脚本从流水线的运行账本重新生成。服务端版本在姊妹项目 `paper-library-service`
（本站按决策 D2 冻结为快照、随缘维护）。

`README.md` 是权威说明，这里只写操作要点与**易错点**。

## 常用操作

```bash
npm run validate     # 发布前必跑：链接、封面、阅读器文件、manual 运行齐备性
npm start            # 本地预览 http://localhost:8000
npm run covers       # 重新生成封面（需 poppler）
```

| 场景 | 命令 |
| --- | --- |
| 重建论文那一类（跑完一批） | `python3 scripts/collect-runs.py > /tmp/runs.json` → `python3 scripts/build-papers-page.py` |
| 发布单次运行（不在清单里） | `python3 scripts/publish-run.py <job-dir 或 host:path> --pdf report.v12-preview.pdf --slug <slug>` |
| 批量补运行数据包 | `python3 scripts/fetch-run-bundles.py --host yqh2` → `python3 scripts/link-run-bundles.py` |
| 排版阶段升级后重渲染 | `python3 scripts/restyle-published.py --host yqh2`（先 `--dry-run`） |

流水线 job 数据在 **yqh2**（`/opt/paper-pipeline/data/jobs` 与 `~/work/paper-pipeline/data/jobs`），
不在 yqh1。

## 易错点（都踩过）

### 1. 排版升级要"重放最后一步"，不是重跑流水线
重跑会重新 OCR、重新合成正文，产出的是**另一份报告**，台账页上那次运行的耗时与 token
就不再描述站上的 PDF 了。正确做法是 `render --job <id> --layout <既有 layout>`：
复用排版 DSL 会跳过布局模型调用，结果确定、无 API 调用。18 篇约 1 分钟。

### 2. 论文身份按 `full-text.md` 哈希归并，不按标题
同一份 OCR 在旧后端被标成 "SARATHI"、在当前后端才得到 "Revisiting Pipeline Parallelism"。
按标题归并会把一篇发布成两篇，错的那篇还会一直留着。`collect-runs.py` 已经这么做，别改回去。

### 3. 手工发布的 PDF 会被下一次同步删掉
`build-papers-page.py` 把 `downloads/` 里不在运行清单中的 PDF 当孤儿删除，并整块重写论文条目。
所以手工发布必须两件事都做：条目写进 `catalog.js` 的 **manual 块**（generated 块之外），
slug 写进 `scripts/manual-papers.txt`。`publish-run.py` 会替你做，别绕过它。

### 4. `[hidden]` 会被类选择器上的 `display` 盖掉
`.reader-empty { display:grid }` 让带 `hidden` 的元素照样占位，把阅读区顶到视口外
（实测阅读区被推到 18000px 之外，看着像"加载失败"）。写成 `.reader-empty:not([hidden])`。

### 5. 抽屉收起时不能 `display:none`
那会把 `aside` 从 grid 里摘掉，后面的列整体左移一格，阅读区只剩 6px。
现在抽屉是覆盖式（`position:absolute`），阅读区宽度恒定，顺带省掉了"开合后重算 FitWidth"。

### 6. `FitWidth` 要在排版就绪后再请求一次
init 时的计算发生在双栏排版生效之前，按单页宽度算出的比例不对。
所以订阅 `scroll.onLayoutReady`，并在侧栏拖宽 / 窗口 resize 后重算（`refitCurrent`，140ms 防抖）。

### 7. `Ctrl/⌘+W` 在 macOS 上拦不住
实测 macOS 的 Chromium **没有** `navigator.keyboard`（无头与 headed 都是 false），
Keyboard Lock 用不了，`⌘+W` 一定归浏览器。MDN 只写 "Chrome 68+"，没标平台差异。
所以保底路径是「关闭标签」按钮和 `Alt/⌥+W`（判定走 `event.code === 'KeyW'`，
因为 `⌥W` 的 `event.key` 是 `∑`）。

### 8. 封面比例要按产物算
封面实际 339×480（A4），早期 `site.js` 写死 `480×640`，浏览器按错的比例预留高度，
瀑布流首屏会跳一下。现在用 CSS `aspect-ratio: 1/1.414` + `object-fit: cover`。

### 9. 运行数据包只收文本，且要写清为什么
一个 job 目录 16MB，其中原文 PDF 6.6MB、图片切片 4.5MB+。包里只收
`.md/.json/.yaml/.typ`（约 200KB），因为可检验性需要的是"模型读到什么、决定了什么、怎么排版"。
不放的东西在包内 README 里写明理由——否则下一个人会以为是漏了。

### 10. agent-browser 的会话按参数分组
先带 `--proxy` 开页，后面不带同样参数的 `eval`/`screenshot` 会落到另一个空白会话，
看着像页面全白。同一组参数贯穿一次排查。

## 发布

推 `main` 即触发 GitHub Actions 部署到 Pages。推完确认：

```bash
gh run list --limit 1
curl -s -o /dev/null -w '%{http_code}\n' https://chocolatedesue.github.io/llm-inference-library/reader.html
```
