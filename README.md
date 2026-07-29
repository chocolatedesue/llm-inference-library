# LLM 推理资料库

这是一个无后端、无数据库的轻量静态 CMS：首页由 `site/assets/catalog.js` 中的内容清单自动渲染，原始 HTML 作为独立页面保留。它适合 GitHub Pages、Cloudflare Pages、Netlify 等任意静态托管服务。

维护要点与易错点整理在 [`.kiro/skills/llm-inference-library/SKILL.md`](.kiro/skills/llm-inference-library/SKILL.md)：
常用脚本、排版升级后"只重渲染不重跑"的做法、以及 10 条踩过的坑。

## 已整理的内容

| 类别 | 页面 / 文件 | 固定公开 URL（相对路径） |
| --- | --- | --- |
| 调研报告 | 分布式 LLM 推理并行化 | `/content/research/distributed-llm-inference-survey.html` |
| 调研报告 | 细粒度 GPU 算力调度 | `/content/research/fine-grained-gpu-scheduling-survey.html` |
| 调研报告 | 卫星网络研究调研报告 | `/content/research/leo-satellite-networking-survey.html` |
| 调研报告 | AI 求职项目调研（应用/Agent + Infra） | `/content/research/ai-job-projects-2026.html` |
| 开源资源 | 开源代码清单 | `/content/resources/open-source-llm-inference-shortlist.html` |
| 演示文稿 | LLM 推理仿真实验平台 | `/downloads/llm-inference-simulation-platform-slides.pptx` |
| 论文解构 | 18 篇论文报告 PDF + 运行账本索引 | `/content/papers/index.html` |

下载目录中重复的 ` (1)` 文件与原件大小一致，因此未重复发布。

## 本地预览与校验

```bash
cd /Users/ccds/tmp/llm-inference-library
npm run validate
npm start
```

然后访问 <http://localhost:8000>。本项目没有 npm 运行时依赖；`npm start` 仅调用 macOS 自带的 `python3` HTTP 服务器。

## 通过 GitHub Pages 公开发布（推荐）

1. 在 GitHub 创建一个**空的公开仓库**，例如 `llm-inference-library`。
2. 在终端执行下列命令；将 `<GITHUB用户名>` 改为你的用户名：

   ```bash
   cd /Users/ccds/tmp/llm-inference-library
   git init -b main
   git add README.md package.json scripts site .github
   git commit -m "Publish LLM inference library"
   git remote add origin https://github.com/<GITHUB用户名>/llm-inference-library.git
   git push -u origin main
   ```

3. 在 GitHub 仓库依次打开 **Settings → Pages → Build and deployment → Source**，选择 **GitHub Actions**。
4. 等待 Actions 中的 `Deploy static site to GitHub Pages` 完成。公开地址将是：

   ```text
   https://<GITHUB用户名>.github.io/llm-inference-library/
   ```

工作流已在每次推送到 `main` 时自动验证链接并重新发布。首次启用 Pages 后，部署通常需要几分钟。

## 新增、改名或分类内容

1. 将 HTML 放入 `site/content/<分类>/`，将附件放入 `site/downloads/`。
2. 在 `site/assets/catalog.js` 的 `CONTENT_ITEMS` 中新增或更新一项：`title`、`category`、`tags`、`href` 与 `action` 是关键字段。
3. 如需新增大类，同时在 `CONTENT_CATEGORIES` 加入对应的 `{ id, label }`。
4. 运行 `npm run validate`，确认新登记的 `href` 存在，再提交并推送。

已发布的 `href` 就是稳定 URL。需要“重命名”时，建议保留旧文件或建立跳转页，避免已分享的链接失效。

## PDF 封面瀑布流与站内阅读器

论文 PDF 有两个入口，职责分开：

- **浏览**：首页「论文解构」分类下的**封面瀑布流**（CSS 多列），封面按 A4 比例预留空间，加载时不抖动。
- **阅读**：`site/reader.html` —— 左侧按主题分层的目录（分组表在 `catalog.js` 的 `window.PAPER_GROUPS`），
  右侧 [EmbedPDF](https://github.com/embedpdf/embed-pdf-viewer)（PDFium/WASM）直接阅读，带文本选中、搜索、
  缩略图、打印。URL 形如 `reader.html?paper=<slug>`，点侧栏走 `pushState`，浏览器后退回到上一篇。

阅读器的几个刻意选择：

- EmbedPDF 从 jsdelivr 加载并**钉死版本** `@embedpdf/snippet@2.14.4`（JS ~1.8MB + pdfium.wasm ~4.5MB），
  且只在**第一次点开某篇论文时才动态 import**——只逛首页的访客不付这份流量。
- `fonts: { ui: null, signature: null }` 与 `stamp: { manifests: [] }`：把第三方来源收敛到 jsdelivr 一个，
  不再请求 Google Fonts。
- 初始缩放 `ZoomMode.FitWidth` + 默认双栏 `SpreadMode.Odd`（第 1 页排在跨页左侧，报告首页就是正文而非书籍封面）。
  双栏下 FitWidth 是让整个跨页横向铺满：实测 984px 宽的阅读区里跨页占 963px、页面 477×675（FitPage 时只有 355×503）。
  代价是这些报告上边距很大，首屏会先看到一段空白，标题在下面一点。
  双栏是排版完成后才生效的，所以还订阅了 `scroll.onLayoutReady`，每份文档就绪后再 `requestZoom(FitWidth)` 一次；
  侧栏拖宽/收起与窗口缩放之后也会重新请求一次，否则比例还是按旧宽度算的。
- **关闭内部标签**：工具条的「关闭标签」按钮，或 `Alt+W`（macOS 上即 `⌥W`；判定走 `event.code === 'KeyW'`，因为 `⌥W` 的 `event.key` 是 `∑`）。关掉后切到相邻标签；关掉最后一个则回空态并清掉 URL 上的 `?paper=`。
  `Ctrl/⌘+W` 绑了同一个动作，但**页面能不能拿到它取决于平台**：
  - Windows / Linux 的 Chrome / Edge：进全屏后代码会申请 Keyboard Lock（`navigator.keyboard.lock(['KeyW'])`），
    此时 `Ctrl+W` 归页面。非全屏一律归浏览器。
  - macOS：实测 Chromium（含 Chrome for Testing 无头与有头）**根本没有 `navigator.keyboard`**，
    `⌘+W` 无论是否全屏都拦不住。MDN 的兼容表只写 "Chrome 68+"，没标这个平台差异。
  所以「关闭标签」按钮和 `Alt+W` 才是保底路径。
- 阅读页**没有站头**：整屏都归目录 + 阅读区，返回链接放在侧栏顶部。
- **目录是抽屉**：默认全收，`☰ 目录` 按钮、`D` 键开合，`Esc` 或点遮罩收起，**选中一篇后自动收起**。
  抽屉是 `position:absolute` 覆盖在阅读区之上、不占列宽，所以开合不改变 PDF 的可用宽度——
  也就不必因为开合去重算 FitWidth（只有窗口 resize 才重算）。阅读区因此恒为整屏宽：
  1280px 视口下跨页从 963px 涨到 1259px、缩放 80% → 105%。
  抽屉右缘那条 `role="separator"` 把手可拖宽（左右方向键微调，`Shift` 加大步长），宽度存 `localStorage`。
  关着时对 `aside` 加 `aria-hidden` + `visibility:hidden`，否则 Tab 会跑进屏幕外的抽屉里。
- **原文链接**：阅读器标题下方与首页卡片都会显示 arXiv / DOI / 原文链接。数据优先取 catalog 条目里的
  `source`（由流水线抽到 `links` 时生成），缺失则回落到 `catalog.js` 里手工维护的 `window.PAPER_SOURCES`——
  18 篇里流水线只抽到 7 篇的链接，所以覆盖表是常态而非例外。它同样放在生成块之外，重跑流水线不会被覆盖。
- **多标签**：点开一篇就在阅读器内部多开一个 tab（标签名取论文短标题），已开过的直接切过去、不重复开。
  标签由 EmbedPDF 的 document-manager 维护，左侧目录负责"开哪一篇"，标签负责"在开着的几篇之间跳"。
- **全屏**：工具条的「全屏」把整块 `#readerShell`（含左侧目录）送进 Fullscreen API，所以全屏里还能换论文；
  `.reader-shell:fullscreen` 要吃满 `100vh`，否则底部会空出站头的 67px。
- 加载失败（CDN 不可达等）自动退回浏览器自带 PDF 阅读器，仍可阅读与下载。

新论文若没登记进 `window.PAPER_GROUPS`，会落到侧栏的「未分组」；`npm run validate` 会提示但不失败。
这份分组表放在 `catalog.js` 生成块之外，`build-papers-page.py` 重写论文条目时不会覆盖它。

封面图由每份 PDF 首页渲染，保存在 `site/assets/covers/`：

```bash
# 依赖 poppler（pdftoppm）。macOS: brew install poppler
npm run covers
```

`scripts/build-papers-page.py` 在同步 PDF 后会自动尝试生成封面。校验时若缺封面会失败：

```bash
npm run covers
npm run validate
```

## 更新论文解构报告

论文那一类不手工维护：`site/content/papers/index.html`、`catalog.js` 中的论文条目、
首页的报告篇数，全部由脚本从流水线的运行账本重新生成。新跑完一批论文后：

```bash
# 1. 在跑流水线的机器上导出运行清单
python3 scripts/collect-runs.py > /tmp/runs.json

# 2. 把每次干净运行的 report.compact.pdf 取到本地，按 <job-id>.pdf 命名
mkdir -p /tmp/lil-pdfs   # scp <host>:<job-dir>/report.compact.pdf /tmp/lil-pdfs/<job-id>.pdf

# 3. 重新生成页面与清单
python3 scripts/build-papers-page.py
npm run validate
```

`collect-runs.py` 按 `full-text.md` 的哈希（即那次运行实际读到的 OCR 文本）归并多次
运行，而不是按标题——标题由模型抽取，早期后端抽错过：同一份 OCR 在旧后端被标成
“SARATHI”，在当前后端才得到论文首页真正印着的 “Revisiting Pipeline Parallelism”。
按标题归并会把两者当成两篇分别发布，错的那篇还会一直留在站上。

归并后优先保留整条流水线跑完的那次；只产出了正文、排版渲染失败的运行不会进入正表，
而是列在页面末尾的“未收录的运行”，以便上表的口径可被检验。

`build-papers-page.py` 里的 `SLUG_FIX` 固定了已发布论文的文件名，新增论文才走自动
slug——改动它会让已分享的 PDF 链接失效。`TITLE_FIX` 用来纠正 OCR 返回的全大写标题。

## 发布单次运行与原始运行数据

论文那一类平时由运行清单整体重建，但有两种情况走不通：某次运行还没进清单（例如 v12-preview 的重渲染），
或者只想补上"这份报告是怎么产出的"证据。这两件事各有一个脚本。

**发布一次运行**（PDF + 运行数据 + catalog 条目 + 封面）：

```bash
# 本地 job 目录
python3 scripts/publish-run.py /path/to/data/jobs/<job-id> --pdf report.v12-preview.pdf --slug aegaeon

# 流水线主机上的 job 目录（按需 rsync 到临时目录，只取文本与选定 PDF）
python3 scripts/publish-run.py yqh2:/opt/paper-pipeline/data/jobs/<job-id>
```

它写入 `site/downloads/<slug>.pdf`、`site/downloads/runs/<slug>-run.zip`、封面，并在 `catalog.js` 的
**manual 块**里插入条目——那个块在 generated 块之外，重跑 `build-papers-page.py` 不会覆盖。
slug 会登记进 `scripts/manual-papers.txt`，`build-papers-page.py` 读它来决定"这些 PDF/封面不是孤儿、
首页篇数要算上"。**发布后记得把 slug 加进 `window.PAPER_GROUPS`**，否则阅读器侧栏会归到「未分组」。

**批量补齐已发布论文的运行数据**：

```bash
python3 scripts/fetch-run-bundles.py --host yqh2      # --dry-run 先看映射
python3 scripts/link-run-bundles.py                   # 把 runData 写进 catalog 条目
npm run validate
```

`fetch-run-bundles.py` 把 `collect-runs.py` 送到主机上执行，所以论文身份仍按 `full-text.md` 的哈希归并，
slug 也复用 `build-papers-page.py` 的 `SLUG_FIX`，不会和已发布链接对不上。18 篇共约 2.3MB。

包里放什么、不放什么（两个脚本一致）：

| 放 | 为什么 |
| --- | --- |
| `full-text.md`、`pages/page-*.md` | 模型实际读到的 OCR 文本，是复核报告结论的前提 |
| `metadata.json`、`job.json`、`usage.json` | 抽取出的元数据、运行状态、token 账本 |
| `report*.md`、`report*.layout.yaml`、`report*.typ` | 正文、排版 DSL、Typst 编译输入 |
| `figure-analyses/` | 逐图分析结果 |

| 不放 | 为什么 |
| --- | --- |
| `input/source.pdf` | 论文原文，第三方版权；包里记了 `source_url`，一键可取 |
| `assets/`、`*-groups/*.png` | 从原文切出的图片，同上；且是 job 目录里的大头（16MB 中的 11MB） |

因此一个包约 100–200KB 而不是 9MB。代价是不能"解压即重编译"——要重新渲染得取回原文重跑流水线，
或者用 `report*.typ` 配自己的图片资源编译。这是拿"可检验"换"仓库不膨胀"。

## 渲染产物已经在本机时（只发布，不重渲染）

排版阶段跑过一轮、19 篇的 `report.compact.pdf` 已经在本机 job 目录里时，站点只需要把结果捡起来：

```bash
python3 scripts/publish-local-renders.py ~/work/paper-pipeline/data/jobs --dry-run
python3 scripts/publish-local-renders.py ~/work/paper-pipeline/data/jobs
npm run covers && npm run validate
```

slug 仍由各 job 的 `metadata.json` 经 `TITLE_FIX` / `SLUG_FIX` 推出，已发布链接不会变。
两条安全规则来自这个 job store 的实际情况：

- **同一篇取最新那次渲染**。store 里会堆着同一篇的多次运行（旧版排版、失败的尝试），
  按 mtime 选并把选择打印出来，便于核对（本次 frontier / memocr / prefill-decode 各有两份）。
- **只更新已发布过的 slug**。store 里可能有站上没有的论文（本次有三份 `phantora`），
  新增是一个决定而不是副作用，要加 `--allow-new`。

## 流水线换了最后一步之后（只重渲染，不重跑）

排版阶段升级（字体、版式、出处样式）后，站上的 PDF 还是旧样式。**不要重跑整条流水线**：那会重新 OCR、
重新合成正文，产出的是另一份报告，台账页上的运行记录也就不再描述已发布的内容了。只重放最后一步：

```bash
python3 scripts/restyle-published.py --host yqh2 --dry-run   # 先看要动哪些
python3 scripts/restyle-published.py --host yqh2 --only servegen
python3 scripts/restyle-published.py --host yqh2             # 全量
npm run covers && npm run validate
```

它对每篇做的事：rsync job 目录（排除 `input/`）→ `paper-pipeline render --job <id> --layout <既有 layout>`
→ 覆盖 `site/downloads/<slug>.pdf` → 重建运行数据包。关键是 `--layout` 复用既有的排版 DSL，
**跳过布局模型调用**，所以整个过程没有 API 调用、结果确定：正文不变、配图位置不变，只有样式变。
`input/source.pdf` 不需要（它只用于重切高清图，缺失时 `upgrade_job_ocr_assets` 直接跳过，
沿用已发布 PDF 用的那批图）。18 篇实测约 1 分钟，每篇 Typst 编译约 3 秒。

样式变化会让页数增加 1–2 页（字号行距变化所致），这是预期的；脚本会把页数变化标出来。
台账页那张表里的 `PDF` 体积列来自上一次运行清单重建，重渲染后会略偏小，下次跑
`build-papers-page.py` 时自动对齐。

## 其他托管选项

- **Cloudflare Pages**：连接 GitHub 仓库；构建命令留空；输出目录填 `site`。
- **Netlify**：导入 GitHub 仓库；Build command 留空；Publish directory 填 `site`。

两者都可自动从 GitHub 更新，且无需维护服务器。
