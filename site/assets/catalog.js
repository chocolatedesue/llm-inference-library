/*
 * 轻量 CMS 内容清单。
 * 添加资料时：复制文件到 site/content/<category>/ 或 site/downloads/，
 * 然后在此数组新增一项即可。slug 与 href 一经发布请尽量保持不变。
 */
window.CONTENT_ITEMS = [
  {
    id: 'distributed-llm-inference-survey',
    category: 'research',
    type: '调研报告',
    title: '分布式 LLM 推理并行化',
    subtitle: '调研报告 2024–2026',
    description: '系统梳理推理并行轴、调度策略与代表性系统，适合作为分布式 LLM 推理研究的入门索引。',
    tags: ['分布式推理', '并行化', '系统调研'],
    href: 'content/research/distributed-llm-inference-survey.html',
    action: '打开阅读',
    updated: '2026-07-26',
    accent: 'violet'
  },
  {
    id: 'fine-grained-gpu-scheduling-survey',
    category: 'research',
    type: '调研报告',
    title: '细粒度 GPU 算力调度',
    subtitle: '分布式推理续篇',
    description: '聚焦 GPU 共享粒度、干扰隔离和推理服务调度，帮助选择适合的资源管理路径。',
    tags: ['GPU 调度', '资源共享', '推理服务'],
    href: 'content/research/fine-grained-gpu-scheduling-survey.html',
    action: '打开阅读',
    updated: '2026-07-26',
    accent: 'orange'
  },
  {
    id: 'open-source-llm-inference-shortlist',
    category: 'resources',
    type: '开源资源',
    title: '开源代码清单',
    subtitle: '分布式推理 + 细粒度 GPU 调度',
    description: '从两份调研中筛选的可用开源项目，按服务框架、KV/通信、模拟器与评测等维度整理。',
    tags: ['开源项目', '工程实践', '工具选型'],
    href: 'content/resources/open-source-llm-inference-shortlist.html',
    action: '查看清单',
    updated: '2026-07-26',
    accent: 'blue'
  },
  {
    id: 'llm-inference-simulation-platform-slides',
    category: 'slides',
    type: '演示文稿',
    title: 'LLM 推理仿真实验平台',
    subtitle: '组会分享',
    description: '组会演示文稿原文件，可在线下载后用 PowerPoint、Keynote 或 WPS 打开。',
    tags: ['仿真平台', '组会分享', 'PPTX'],
    href: 'downloads/llm-inference-simulation-platform-slides.pptx',
    action: '下载 PPTX',
    download: true,
    updated: '2026-07-26',
    accent: 'green'
  }
];

window.CONTENT_CATEGORIES = [
  { id: 'all', label: '全部资料' },
  { id: 'research', label: '调研报告' },
  { id: 'resources', label: '开源资源' },
  { id: 'slides', label: '演示文稿' }
];
