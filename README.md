# LLM 推理资料库

这是一个无后端、无数据库的轻量静态 CMS：首页由 `site/assets/catalog.js` 中的内容清单自动渲染，原始 HTML 作为独立页面保留。它适合 GitHub Pages、Cloudflare Pages、Netlify 等任意静态托管服务。

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
- 初始缩放 `ZoomMode.FitPage` + 默认双栏 `SpreadMode.Odd`（第 1 页排在跨页左侧，报告首页就是正文而非书籍封面）。
  这些报告上边距很大，FitWidth 会让首屏全是空白。双栏是排版完成后才生效的，所以还订阅了
  `scroll.onLayoutReady`，每份文档就绪后再 `requestZoom(FitPage)` 一次——否则 init 时按单页算出的比例会让跨页超出视口。
- **关闭内部标签**：工具条的「关闭标签」按钮，或 `Alt+W`（macOS 上即 `⌥W`；判定走 `event.code === 'KeyW'`，因为 `⌥W` 的 `event.key` 是 `∑`）。关掉后切到相邻标签；关掉最后一个则回空态并清掉 URL 上的 `?paper=`。
  `Ctrl/⌘+W` 绑了同一个动作，但**页面能不能拿到它取决于平台**：
  - Windows / Linux 的 Chrome / Edge：进全屏后代码会申请 Keyboard Lock（`navigator.keyboard.lock(['KeyW'])`），
    此时 `Ctrl+W` 归页面。非全屏一律归浏览器。
  - macOS：实测 Chromium（含 Chrome for Testing 无头与有头）**根本没有 `navigator.keyboard`**，
    `⌘+W` 无论是否全屏都拦不住。MDN 的兼容表只写 "Chrome 68+"，没标这个平台差异。
  所以「关闭标签」按钮和 `Alt+W` 才是保底路径。
- 阅读页**没有站头**：整屏都归目录 + 阅读区，返回链接放在侧栏顶部。
- **侧栏可拖宽、可收起**：列之间是一条 `role="separator"` 的把手（左右方向键可微调，`Shift` 加大步长），
  宽度与收起状态存在 `localStorage`。收起时不能对 `aside` 用 `display:none`——那会把它从 grid 里摘掉、
  后面的列整体左移一格，阅读区只剩 6px；改成保留占位、宽度归零。
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

## 其他托管选项

- **Cloudflare Pages**：连接 GitHub 仓库；构建命令留空；输出目录填 `site`。
- **Netlify**：导入 GitHub 仓库；Build command 留空；Publish directory 填 `site`。

两者都可自动从 GitHub 更新，且无需维护服务器。
