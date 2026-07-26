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
    id: 'leo-satellite-networking-survey',
    category: 'research',
    type: '调研报告',
    title: '卫星网络研究调研报告',
    subtitle: '2026.07 · LEO Satellite Networking',
    description: '覆盖 2025–2026 年低轨卫星网络的部署现状、顶会优秀论文、网络仿真/仿真器开源生态，以及分域（分区/分层）路由技术路线的系统梳理与选题建议。',
    tags: ['卫星网络', 'LEO', '分域路由'],
    href: 'content/research/leo-satellite-networking-survey.html',
    action: '打开阅读',
    updated: '2026-07-26',
    accent: 'green'
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
  },
  /* BEGIN generated: paper reports */
  {
    id: 'paper-analysis-index',
    category: 'papers',
    type: '运行账本',
    title: '论文解构报告索引',
    subtitle: "11 篇 · 每阶段耗时与 token",
    description: '一张表看完所有解构报告的 OCR 页数、总耗时、模型调用次数与缓存命中率，数据读自各任务的 usage.json。',
    tags: ['运行账本', '流水线', 'token 用量'],
    href: 'content/papers/index.html',
    action: '查看索引',
    updated: '2026-07-26',
    accent: 'violet'
  },
  {
    id: 'image-worth-16x16-words',
    category: 'papers',
    type: '论文解构',
    title: "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale",
    subtitle: "Alexey Dosovitskiy 等 · 预印本",
    description: "虽然 Transformer 架构已成为自然语言处理任务事实上的标准，但其在计算机视觉领域的应用仍然有限。在视觉任务中，注意力机制要么与卷积网络结合使用，要么在保持卷积网络整体结构不变的情况下用于替换其部分组…",
    tags: ['Vision Transformer', '图像分类', '自注意力机制'],
    href: 'downloads/image-worth-16x16-words.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'blue'
  },
  {
    id: 'attention-all-you-need',
    category: 'papers',
    type: '论文解构',
    title: "Attention Is All You Need",
    subtitle: "Ashish Vaswani 等 · NeurIPS (NIPS) 2017 · 2017",
    description: "目前主流的序列转导模型都基于复杂的循环神经网络或卷积神经网络，包含一个编码器和一个解码器。表现最好的模型还会通过注意力机制将编码器和解码器连接起来。我们提出了一种新的简单网络架构——Transformer，它…",
    tags: ['Transformer', '自注意力机制', '机器翻译'],
    href: 'downloads/attention-all-you-need.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'violet'
  },
  {
    id: 'deep-residual-learning-image-recognition',
    category: 'papers',
    type: '论文解构',
    title: "Deep Residual Learning for Image Recognition",
    subtitle: "Kaiming He 等 · 预印本",
    description: "更深的神经网络更难训练。我们提出一种残差学习框架，以简化比以往使用的网络更深得多的网络的训练。我们将网络层显式地重新表述为学习相对于层输入的残差函数，而不是学习无参照的函数。我们通过大量实验证据表明，这些残差…",
    tags: ['深度学习', '残差网络', '图像分类'],
    href: 'downloads/deep-residual-learning-image-recognition.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'orange'
  },
  {
    id: 'flexpipe',
    category: 'papers',
    type: '论文解构',
    title: "FlexPipe: Adapting Dynamic LLM Serving Through Inflight Pipeline Refactoring in Fragmented Serverless Clusters",
    subtitle: "Yanying Lin 等 · 2026",
    description: "在生产环境中部署大语言模型（LLM）服务面临着来自无服务器集群中高度多变的请求模式和严重资源碎片化的重大挑战。当前系统依赖于静态流水线配置，难以适应动态的工作负载条件，从而导致显著的效率低下。 我们提出了 F…",
    tags: ['大语言模型', '无服务器计算', '流水线并行'],
    href: 'downloads/flexpipe.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'green'
  },
  {
    id: 'gpemu',
    category: 'papers',
    type: '论文解构',
    title: "GPEmu: A GPU Emulator for Faster and Cheaper Prototyping and Evaluation of Deep Learning System Research",
    subtitle: "Meng Wang 等 · PVLDB · 2025",
    description: "深度学习（DL）系统研究常常受限于 GPU 的有限可用性和高昂成本。在本文中，我们推出了 GPEmu，这是一款无需使用真实 GPU 即可对深度学习系统研究进行更快、更低成本原型设计与评估的 GPU 仿真器。G…",
    tags: ['GPU仿真', '深度学习系统', '分布式训练'],
    href: 'downloads/gpemu.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'blue'
  },
  {
    id: 'pipelive',
    category: 'papers',
    type: '论文解构',
    title: "PipeLive: Efficient Live In-place Pipeline Parallelism Reconfiguration for Dynamic LLM Serving",
    subtitle: "Xu Bai 等 · 2026",
    description: "为了加速大语言模型（LLM）推理，流水线并行将模型层划分为顺序阶段，并分别分配给不同的设备并发执行。然而，由于尾部阶段的计算不均衡，这种方法通常会受到流水线气泡的影响。尽管上游阶段仅关注层的正向传播操作，但最…",
    tags: ['Large Language Models', 'Pipeline Parallelism', 'Dynamic Workload Balancing'],
    href: 'downloads/pipelive.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'violet'
  },
  {
    id: 'realb',
    category: 'papers',
    type: '论文解构',
    title: "ReaLB: Real-Time Load Balancing for Multimodal MoE Inference",
    subtitle: "Yu Wang 等 · 2026",
    description: "混合专家（MoE）架构在现代大语言模型和多模态模型中被广泛使用。然而，不同模态之间高度动态且倾斜的专家工作负载往往限制了推理效率。在具有大批量大小的预填充（prefill）阶段，视觉 Token 经常在输入序…",
    tags: ['混合专家模型 (MoE)', '负载均衡', '多模态大模型'],
    href: 'downloads/realb.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'orange'
  },
  {
    id: 'sarathi',
    category: 'papers',
    type: '论文解构',
    title: "SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills",
    subtitle: "Amey Agrawal 等 · 2023",
    description: "由于单张 GPU 的显存容量不足以容纳大语言模型（LLM），模型并行已成为在多张 GPU 上运行 LLM 服务的标准方法。在在线服务环境中，张量并行由于可以通过并行执行来降低计算延迟，已成为单节点多 GPU …",
    tags: ['Pipeline Parallelism', 'LLM Serving', 'Chunked Prefill'],
    href: 'downloads/sarathi.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'green'
  },
  {
    id: 'servegen',
    category: 'papers',
    type: '论文解构',
    title: "ServeGen: Workload Characterization and Generation of Large Language Model Serving in Production",
    subtitle: "Yuyuan Xiang 等 · 2025",
    description: "随着大语言模型（LLM）的广泛应用，服务 LLM 推理请求已成为一项日益重要的任务，吸引了积极的研究进展。实际的工作负载在这一过程中起着至关重要的作用：它们对于激发和评估服务技术和系统是必不可少的。然而，由于…",
    tags: ['大语言模型服务', '工作负载特征分析', '基准测试'],
    href: 'downloads/servegen.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'blue'
  },
  {
    id: 'torchfx',
    category: 'papers',
    type: '论文解构',
    title: "Torch.fx: Practical Program Capture and Transformation for Deep Learning in Python",
    subtitle: "James K Reed 等 · 预印本",
    description: "现代深度学习框架提供了嵌入在 Python 中的命令式、即时执行（eager execution）编程接口，以带来高效的开发体验。然而，深度学习从业者有时需要捕获并变换程序结构，以用于性能优化、可视化、分析和…",
    tags: ['PyTorch', '程序捕获', '程序变换'],
    href: 'downloads/torchfx.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'violet'
  },
  {
    id: 'understanding-diffusion-model-serving-production',
    category: 'papers',
    type: '论文解构',
    title: "Understanding Diffusion Model Serving in Production: A Top-Down Analysis of Workload, Scheduling, and Resource Efficiency",
    subtitle: "Yanying Lin 等 · 2025",
    description: "本文对生产云环境中扩散模型推理服务所面临的挑战进行了全面分析。我们研究了区分扩散模型服务与传统机器学习（ML）工作负载的独特计算模式和资源需求，揭示了其多阶段流水线（pipeline）架构带来的根本性系统级挑…",
    tags: ['Diffusion Models', 'Model Serving', 'Cloud Computing'],
    href: 'downloads/understanding-diffusion-model-serving-production.pdf',
    action: '打开 PDF',
    updated: '2026-07-26',
    accent: 'orange'
  },
  /* END generated: paper reports */
];

window.CONTENT_CATEGORIES = [
  { id: 'all', label: '全部资料' },
  { id: 'research', label: '调研报告' },
  { id: 'resources', label: '开源资源' },
  { id: 'papers', label: '论文解构' },
  { id: 'slides', label: '演示文稿' }
];
