# 论文阅读器（EmbedPDF）— 任务

## 已完成（本轮，均已验证）

- [x] 1. 仓库卫生：新增 `.gitignore`（`__pycache__/`、`*.py[cod]`、`.DS_Store`），删除 `scripts/__pycache__/`
- [x] 2. 分组表：`catalog.js` 新增 `window.PAPER_GROUPS`（5 组 / 18 篇），置于生成块之外
- [x] 3. 阅读页：`site/reader.html` + `site/assets/reader.js`（目录、筛选、上一篇/下一篇、`?paper=` 深链、pushState）
- [x] 4. EmbedPDF 接入：jsdelivr `@embedpdf/snippet@2.14.4`，首次选中才动态 import，FitPage，关闭 Google Fonts / 图章库
- [x] 5. 多标签：点开一篇多开一个 tab（`name` 取论文短标题），已开过的走 `setActiveDocument` 不重复开
- [x] 5b. 默认双栏 `SpreadMode.Odd` + 「全屏」按钮（Fullscreen API 作用于 `#readerShell`）
- [x] 5c. 排版就绪后重新 `requestZoom(FitPage)`，修双栏下跨页超出视口
- [x] 5d. 关闭当前内部标签：「关闭标签」按钮 + `Alt+W`（`Ctrl/⌘+W` 绑同一动作，受平台/浏览器保留键限制）
- [x] 5e. 阅读页移除站头，shell 吃满 `100vh`，返回链接移到侧栏顶部
- [x] 6. 降级路径：import/init 失败 → 浏览器自带阅读器 iframe
- [x] 7. 卡片改道：`site.js` 中 PDF 卡片指向 `reader.html?paper=<id>`，动作文案改为「在阅读器打开」，保留「下载」
- [x] 8. 封面不抖：去掉写死的 `480×640`，改 `aspect-ratio:1/1.414` + `object-fit:cover`
- [x] 9. 删除旧 `site/viewer.html`（PDF.js 单篇预览），`validate.mjs` 改查 `reader.html` / `assets/reader.js`
- [x] 10. 校验增强：未登记进 `PAPER_GROUPS` 的论文给警告（不失败）
- [x] 11. 修 `[hidden]` 被类选择器 `display` 覆盖导致的布局崩坏（空状态与降级区各占一屏）
- [x] 12. 文档：README 重写「PDF 封面瀑布流与站内阅读器」；本 spec 三份同步到 EmbedPDF 方案

## 未做 / 待定

- [ ] A. 台账表格里的裸 PDF 链接是否也改走阅读器？（现在仍直链 `../../downloads/<slug>.pdf`）
- [ ] B. 移动端是否直接走原生阅读器，避免 wasm 首载？（现在移动端也加载 EmbedPDF）
- [ ] C. 是否 vendored EmbedPDF 到 `site/vendor/`（+约 6.6MB、需安装步骤）以支持完全离线
- [ ] D. 侧栏是否加键盘快捷键（j/k 或 `[`/`]` 翻篇）
- [ ] G. 在 **Windows** 的 Chrome/Edge 上确认全屏 + Keyboard Lock 下 `Ctrl+W` 是否真被接走（macOS 已确认无此 API，不可能）
- [ ] E. 新论文进站后是否要求必须登记分组（把 validate 的警告升级为失败）
- [ ] F. 提交与推送到 `chocolatedesue/llm-inference-library`（**需用户确认**）

## 回归清单（改动阅读器后跑一遍）

```bash
npm run validate
npm start   # 然后：
# 1. /reader.html?paper=attention-all-you-need 直接可读
# 2. 点侧栏另一篇 → 多一个标签、URL 变、后退回到上一篇；再点已开的那篇不重复开
# 2b. 点「全屏」→ 整块（含目录）全屏、无留白；再点退出
# 2c. 首屏是双栏（并排两页）且整页可见，不被裁
# 2d. Alt+W 关当前标签 → 切到相邻标签；关到最后一个 → 回空态、URL 去掉 ?paper=
# 3. 侧栏筛选框输入关键词 → 命中为空的组隐藏
# 4. 首页「论文解构」→ 卡片「在阅读器打开」/「下载」都对
# 5. 断网重开一篇 → 落到浏览器自带阅读器且有说明
```
