# LLM 推理资料库

这是一个无后端、无数据库的轻量静态 CMS：首页由 `site/assets/catalog.js` 中的内容清单自动渲染，原始 HTML 作为独立页面保留。它适合 GitHub Pages、Cloudflare Pages、Netlify 等任意静态托管服务。

## 已整理的内容

| 类别 | 页面 / 文件 | 固定公开 URL（相对路径） |
| --- | --- | --- |
| 调研报告 | 分布式 LLM 推理并行化 | `/content/research/distributed-llm-inference-survey.html` |
| 调研报告 | 细粒度 GPU 算力调度 | `/content/research/fine-grained-gpu-scheduling-survey.html` |
| 调研报告 | 卫星网络研究调研报告 | `/content/research/leo-satellite-networking-survey.html` |
| 开源资源 | 开源代码清单 | `/content/resources/open-source-llm-inference-shortlist.html` |
| 演示文稿 | LLM 推理仿真实验平台 | `/downloads/llm-inference-simulation-platform-slides.pptx` |
| 论文解构 | 16 篇论文报告 PDF + 运行账本索引 | `/content/papers/index.html` |

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

`collect-runs.py` 会按论文标题归并多次运行，优先保留整条流水线跑完的那次；
只产出了正文、排版渲染失败的运行不会进入正表，而是列在页面末尾的“未收录的运行”，
以便上表的口径可被检验。`build-papers-page.py` 里的 `SLUG_FIX` 固定了已发布论文的
文件名，新增论文才走自动 slug——改动它会让已分享的 PDF 链接失效。

## 其他托管选项

- **Cloudflare Pages**：连接 GitHub 仓库；构建命令留空；输出目录填 `site`。
- **Netlify**：导入 GitHub 仓库；Build command 留空；Publish directory 填 `site`。

两者都可自动从 GitHub 更新，且无需维护服务器。
