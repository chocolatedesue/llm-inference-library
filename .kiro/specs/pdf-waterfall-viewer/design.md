# 论文阅读器（EmbedPDF）— 设计

## 约束

- 纯静态：无后端、无构建步骤、无 npm 运行时依赖；GitHub Pages 直接托管 `site/`。
- 相对 URL；已发布 PDF 文件名（`build-papers-page.py` 的 `SLUG_FIX`）不得变更。
- 台账表格是运维口径来源，阅读器只是浏览/阅读层，两者职责不合并。

## 模块

| 路径 | 角色 |
| --- | --- |
| `site/reader.html` | 阅读页骨架：站头 + 左目录 + 右阅读区 + 降级区 |
| `site/assets/reader.js` | 目录渲染、筛选、路由、EmbedPDF 生命周期（ES module） |
| `site/assets/catalog.js` | 内容清单 + `window.PAPER_GROUPS`（分组表，手工维护） |
| `site/assets/site.js` | 首页/论文页卡片；PDF 卡片指向 `reader.html?paper=<id>` |
| `site/assets/site.css` | 瀑布流、封面比例、阅读器两栏布局 |
| `scripts/validate.mjs` | 校验阅读器文件、封面齐备、未分组论文提示 |

## 关键决策

### D1 分组表放在生成块之外，与流水线零耦合
`build-papers-page.py` 只重写 `catalog.js` 里 `/* BEGIN generated */ … /* END generated */` 之间的内容，
所以 `window.PAPER_GROUPS` 定义在该块之外即可长期存活。分组按 slug 列举（不按标签推断）：标签由模型抽取、
批次间会漂移，按标签自动分组会让侧栏结构随每次重跑变化。代价是新论文要手工登记一次，未登记的落到「未分组」。

### D2 EmbedPDF 走 CDN 钉死版本，首次点开才 import
`@embedpdf/snippet@2.14.4`：JS 约 1.8MB（含 worker/engine 分包）+ `pdfium.wasm` 4.5MB。
若 vendored 进仓库需提交约 6.6MB，且要引入 npm 安装步骤——与"无构建步骤"的前提冲突。
折中：CDN + 版本钉死 + **动态 import 延后到第一次选中论文**，只逛首页的访客不付这份流量。
`fonts:{ui:null,signature:null}` 与 `stamp:{manifests:[]}` 把第三方来源收敛到 jsdelivr 一个
（默认配置会请求 Google Fonts，已实测确认关掉后只剩 jsdelivr）。

### D3 多标签：目录管"开哪篇"，标签管"在开着的几篇之间跳"
先前版本是"一份文档主义"（切换时 `closeDocument` 旧的），理由是标签栏与侧栏职责重复。
按用户要求改为多标签：点开一篇就 `openDocumentUrl(..., name: 短标题, autoActivate: true)` 多开一个标签；
已在 `openedDocs` 里的走 `setActiveDocument`，不重复开（实测再点已开的那篇标签数不变）。
`name` 用来让标签显示论文标题——不传时 EmbedPDF 会显示 `Document <id>`。
init 时仍不传 `src`：否则会先冒出一个我们无法按 slug 引用的自动 id 文档（曾出现 `Document doc-1785`）。

代价：EmbedPDF 内部切标签时我们的侧栏高亮与 URL 不会跟着变（状态是单向的，见 D5）。
接受这个不对称——URL 反映的是"最后从目录点开的那篇"。

### D4 初始缩放 FitWidth + 默认双栏 SpreadMode.Odd
双栏用 `Odd`（第 1 页在跨页左侧）而不是 `Even`：报告首页是正文标题页，不是书籍封面。

缩放默认几经反复，最后定在 **FitWidth**（按用户要求）。三种口径的实测对比（984×549 的阅读区、双栏）：
`FitPage` 页面 355×503、跨页只占约 710px，横向留白多、字小；`FitWidth` 页面 477×675、跨页占 963px、80%，
字大但页面高于视口，首屏会先看到报告的大上边距。取舍是"字大优先"。

只在 init 里写 `defaultZoomLevel` 不够：那次计算发生在双栏排版生效之前，是按单页宽度算的。
因此订阅 `scroll.onLayoutReady`，每份文档排版就绪后再 `zoom.forDocument(id).requestZoom(FitWidth)` 一次；
侧栏拖宽/收起、窗口 resize 之后也重新请求（`refitCurrent`，带 140ms 防抖）。

### D4c 关闭内部标签：Alt+W 为主，Ctrl/⌘+W 尽力而为
`Ctrl/⌘+W` 是浏览器保留键，网页默认拿不到——除非在全屏下用 Keyboard Lock
（`navigator.keyboard.lock(['KeyW'])`，Chrome/Edge 专有，需安全上下文）。
所以键位绑两套：`Alt+W` 任何环境都归页面，是保底路径；`Ctrl/⌘+W` 绑同一个动作，能截住就截。
关闭后切到相邻标签；关掉最后一个则回空态并从 URL 去掉 `?paper=`（用 `replaceState`，不往后退栈里塞垃圾）。

平台事实（实测）：macOS 的 Chromium 里 `navigator.keyboard` 直接不存在——无头与 `--headed` 都是 `false`，
且 `isSecureContext` 为 true，所以不是安全上下文的问题。MDN 的 `api.Keyboard.lock` 兼容表写 "Chrome 68+" 且
未标平台差异，这里以实测为准：**macOS 上 `⌘+W` 拦不住，任何状态都拦不住**。
Windows/Linux 的 Chrome/Edge 有这个 API，代码在进全屏时申请 `lock(['KeyW'])`，但本机无法验证该分支。

因此增加了不依赖键位的路径：工具条「关闭标签」按钮（任何平台可用，且在没有打开文档时 disabled）。
无头环境下 CDP 派发的 `Control+w` 会直接进页面，不能作为"真实浏览器已被截获"的证据。

### D4b 全屏对整块 shell
「全屏」按钮把 `#readerShell`（左侧目录 + 右侧阅读区）一起送进 Fullscreen API，而不是只全屏 PDF 区，
这样全屏状态下还能换论文。CSS 需要 `.reader-shell:fullscreen { height:100vh }`，
因为常态下它的高度是 `calc(100vh - 67px)`（减站头），全屏时站头不存在。
用原生 Fullscreen API 而不是 EmbedPDF 的 fullscreen 插件：后者只能全屏它自己的容器，且不在默认工具条上。

### D4d 目录做成覆盖式抽屉，不再占列
最初是两栏 grid（目录 + 阅读区）+ 收起把列压到 0。改成抽屉：`aside` 绝对定位、`translateX(-102%)` 藏在屏外，
开合只切一个 class，阅读区永远是整屏宽。

这样换来两件事：一是阅读区宽度不再随目录开合变化，`FitWidth` 不需要在开合时重算（只留 window resize 那条路径），
少一个会抖的耦合；二是同一套交互在窄屏与宽屏一致，不用再维护 900px 以下的另一种布局。
代价是打开时目录盖住一部分正文——对"挑一篇然后读"的动线可以接受，何况选中后自动收起。

细节：关着时给 `aside` 加 `aria-hidden="true"` + `visibility:hidden`，否则 Tab 会走进屏幕外的抽屉；
`Esc` 与遮罩点击都收起；`D` 键开合但在输入框里不抢键（判 `event.target` 是否 input/textarea/contenteditable）。
宽度仍写 `localStorage`（读写包在 try 里，隐私模式会抛）；开合状态**不**持久化——每次进来都是整屏阅读。

### D4e 原文链接：条目优先，覆盖表兜底
`links` 由模型从 OCR 文本里抽，18 篇只成功 7 篇，所以不能只依赖生成数据。
解析顺序是"条目的 `source` → `window.PAPER_SOURCES[id]`"，后者手工维护、放在生成块之外。
上游若要根治，应让流水线在收到 `--url` 时**确定性地**把该 URL 记为 `links.source`，
而不是让模型从 OCR 里认——那是 `/Users/ccds/work/paper-pipeline` 的改动，不在本仓库范围内。

### D5 页码状态单向流动
`?paper=<slug>` 是唯一的选中态来源：点击 → `pushState` → 渲染；`popstate` → 按 URL 重新选中。
不做"渲染再回写状态"的反向链路，避免互相触发。

### D6 降级到浏览器自带阅读器
运行时 import 失败或 init 抛错 → 隐藏阅读区，显示 `<iframe src="downloads/x.pdf#zoom=page-width">` 与说明。
一旦进入降级模式就保持，不在同一次会话里反复重试 CDN。

### D7 面板可见性用 `:not([hidden])` 表达
`[hidden]` 的 `display:none` 会被类选择器上的 `display:grid/flex` 盖掉——这是本轮真实踩到的 bug：
空状态与降级区虽然带 `hidden`，仍各占满一屏，把阅读区顶到 18000px 之外，表现为"加载有问题"。
现在写成 `.reader-empty:not([hidden]) { display:grid }`，并额外保留一条 `[hidden]{display:none!important}` 兜底。

### D8 封面比例用 CSS 固定，不进数据层
封面产物是 A4 首页缩放（实测统一 339×480，比例 0.706）。`.card-cover` 用 `aspect-ratio:1/1.414` 预留 +
`object-fit:cover`，比在 catalog 里加 `coverW/coverH` 字段更省事，且完全不需要改流水线脚本。
非 A4 版面（Letter）会被裁掉约 9% 宽度，接受。

### D9 手工发布的运行走独立块 + 保留清单
`build-papers-page.py` 会按运行清单重写论文条目，并把 `downloads/` 里不在清单中的 PDF 当孤儿删掉。
所以手工发布必须做两件事，否则下一次同步会静默地删掉文件、抹掉条目：
条目写进 `catalog.js` 的 `/* BEGIN manual: hand-published runs */` 块（在 generated 块之外），
slug 写进 `scripts/manual-papers.txt`，让重建脚本把它排除在孤儿清理之外、并计入首页篇数。

### D10 运行数据包只收文本
一个 job 目录 16MB，其中 `input/source.pdf` 6.6MB、`assets/` 与图片切片 4.5MB+。
包里只收 `.md/.json/.yaml/.typ`（约 200KB 压缩后），因为可检验性需要的是"模型读到什么、决定了什么、
怎么排版的"，而图片是第三方内容且已经嵌在发布的 PDF 里。放弃的是"解压即可重编译"。

### D11 换渲染阶段用「重放最后一步」而不是重跑
排版阶段升级后，正确的迁移动作是 `render --job <id> --layout <既有 layout>`：复用排版 DSL 会跳过布局模型调用，
于是这次渲染是确定性的——同样的正文、同样的配图位置，只有样式不同。重跑整条流水线会重新 OCR 与重新合成，
产出的是另一份报告，台账页上那次运行的耗时/token 也就不再对应站上的 PDF 了。
实测：18 篇约 1 分钟，无 API 调用；页数普遍 +1~2 页（字体行距变化），脚本把页数变化打出来供核对。

## 数据流

```
catalog.js (CONTENT_ITEMS + PAPER_GROUPS)
  ├─ site.js  → 首页瀑布流卡片 / 论文页 #paperGallery → reader.html?paper=<slug>
  └─ reader.js→ 侧栏分组目录 → EmbedPDF(document-manager).openDocumentUrl(downloads/<slug>.pdf)
                                    └─ 失败 → iframe 原生阅读器
```

## 风险

- **EmbedPDF API 面**：`openDocumentUrl` / `setActiveDocument` / `closeDocument` 属于 document-manager 插件，
  跨大版本可能变动；版本已钉死，升级前需在浏览器里回归一次切换路径。
- **CDN 依赖**：断网/被墙时降级到原生阅读器（可读、可下载，但没有搜索与缩略图）。若要彻底离线，
  需 vendored `dist/` + `wasmUrl`，代价是仓库多约 6.6MB 与一个安装步骤——留作开放项。
- **移动端**：wasm 首次加载在移动网络上偏重；当前未做"移动端直接走原生阅读器"的分流。
