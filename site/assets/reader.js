/*
 * 论文阅读器：左侧分层目录 + 右侧 EmbedPDF 阅读区。
 *
 * EmbedPDF（PDFium/WASM，约 6MB）只在第一次真正选中论文时才动态 import，
 * 首屏不为没点开任何 PDF 的访客付这份流量。加载失败则退回浏览器自带阅读器。
 */
const EMBEDPDF_URL = 'https://cdn.jsdelivr.net/npm/@embedpdf/snippet@2.14.4/dist/embedpdf.js';
let ZoomMode = null;   // 由动态 import 填充：初始缩放
let SpreadMode = null; // 由动态 import 填充：默认双栏

const items = window.CONTENT_ITEMS || [];
const groupDefs = window.PAPER_GROUPS || [];

const el = {
  tree: document.querySelector('#navTree'),
  search: document.querySelector('#navSearch'),
  navToggle: document.querySelector('#navToggle'),
  nav: document.querySelector('#readerNav'),
  title: document.querySelector('#docTitle'),
  meta: document.querySelector('#docMeta'),
  download: document.querySelector('#downloadLink'),
  openTab: document.querySelector('#openTab'),
  shell: document.querySelector('#readerShell'),
  fullscreen: document.querySelector('#fullscreenBtn'),
  closeTab: document.querySelector('#closeTabBtn'),
  prev: document.querySelector('#prevPaper'),
  next: document.querySelector('#nextPaper'),
  empty: document.querySelector('#readerEmpty'),
  host: document.querySelector('#pdfHost'),
  fallback: document.querySelector('#readerFallback'),
  fallbackFrame: document.querySelector('#fallbackFrame'),
  fallbackNote: document.querySelector('#fallbackNote')
};

const isPdf = (item) => typeof item.href === 'string' && /\.pdf$/i.test(item.href);
const papers = items.filter((item) => item.category === 'papers' && isPdf(item));
const byId = new Map(papers.map((item) => [item.id, item]));

// 分组表里没登记的论文不会消失，落到「未分组」。
const grouped = groupDefs
  .map((group) => ({
    id: group.id,
    label: group.label,
    items: (group.papers || []).map((id) => byId.get(id)).filter(Boolean)
  }))
  .filter((group) => group.items.length);
const claimed = new Set(grouped.flatMap((group) => group.items.map((item) => item.id)));
const orphans = papers.filter((item) => !claimed.has(item.id));
if (orphans.length) grouped.push({ id: 'ungrouped', label: '未分组', items: orphans });

const flat = grouped.flatMap((group) => group.items);

const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
})[char]);

const shortTitle = (item) => {
  const title = item.title || item.id;
  return title.includes(':') ? title.split(':')[0] : title;
};

const renderTree = () => {
  el.tree.innerHTML = grouped.map((group) => `
    <details class="reader-group" open data-group="${escapeHtml(group.id)}">
      <summary><span>${escapeHtml(group.label)}</span><em>${group.items.length}</em></summary>
      <ul>
        ${group.items.map((item) => `
          <li data-paper="${escapeHtml(item.id)}" data-search="${escapeHtml([item.title, item.subtitle, ...(item.tags || [])].join(' ').toLocaleLowerCase('zh-CN'))}">
            <a href="reader.html?paper=${encodeURIComponent(item.id)}" data-id="${escapeHtml(item.id)}">
              <span class="reader-item-title">${escapeHtml(shortTitle(item))}</span>
              <span class="reader-item-sub">${escapeHtml(item.subtitle || '')}</span>
            </a>
          </li>`).join('')}
      </ul>
    </details>`).join('');
};

const markActive = (id) => {
  el.tree.querySelectorAll('li').forEach((li) => {
    const active = id !== null && li.dataset.paper === id;
    li.classList.toggle('is-active', active);
    const link = li.querySelector('a');
    if (link) active ? link.setAttribute('aria-current', 'page') : link.removeAttribute('aria-current');
    if (active) li.closest('details')?.setAttribute('open', '');
  });
};

const applyFilter = () => {
  const keyword = el.search.value.trim().toLocaleLowerCase('zh-CN');
  el.tree.querySelectorAll('details').forEach((group) => {
    let shown = 0;
    group.querySelectorAll('li').forEach((li) => {
      const hit = !keyword || li.dataset.search.includes(keyword);
      li.hidden = !hit;
      if (hit) shown += 1;
    });
    group.hidden = shown === 0;
    if (keyword && shown) group.setAttribute('open', '');
  });
};

// ---- EmbedPDF ----------------------------------------------------------
let viewerPromise = null;
let registryPromise = null;
const openedDocs = new Set();
let mode = 'pending'; // pending | embedpdf | fallback
let currentId = null; // 当前展示的论文 id（也是关闭标签时的目标）

const useFallback = (item, note) => {
  mode = 'fallback';
  el.host.hidden = true;
  el.empty.hidden = true;
  el.fallback.hidden = false;
  if (note) el.fallbackNote.textContent = note;
  // 浏览器自带阅读器：同源相对路径 + 适宽显示。
  el.fallbackFrame.src = `${item.href}#zoom=page-width`;
};

const startViewer = async () => {
  const mod = await import(EMBEDPDF_URL);
  const EmbedPDF = mod.default;
  ZoomMode = mod.ZoomMode || null;
  SpreadMode = mod.SpreadMode || null;
  const viewer = EmbedPDF.init({
    type: 'container',
    target: el.host,
    theme: { preference: 'light' },
    // 只留 jsdelivr 一个第三方来源：不额外拉 Google Fonts 与默认图章库。
    fonts: { ui: null, signature: null },
    stamp: { manifests: [] },
    // FitWidth 会把这些报告的大上边距顶满首屏（点开像是空白页），FitPage 一进来就见内容。
    zoom: ZoomMode ? { defaultZoomLevel: ZoomMode.FitPage } : undefined,
    // 默认双栏：Odd 表示第 1 页排在跨页左侧（报告首页就是正文而非书籍封面）。
    spread: SpreadMode ? { defaultSpreadMode: SpreadMode.Odd } : undefined
  });

  // 双栏是在文档排版完成后才生效的，init 时的 defaultZoomLevel 按单页算过一次，
  // 结果是跨页被裁掉右半边。每份文档排版就绪后再显式请求一次 FitPage。
  try {
    const registry = await viewer.registry;
    const scroll = registry?.getPlugin('scroll')?.provides();
    const zoom = registry?.getPlugin('zoom')?.provides();
    if (scroll && zoom && ZoomMode && typeof scroll.onLayoutReady === 'function') {
      scroll.onLayoutReady((event) => {
        if (!event || event.isInitial === false) return;
        zoom.forDocument?.(event.documentId)?.requestZoom?.(ZoomMode.FitPage);
      });
    }
  } catch (error) {
    console.error(error);
  }
  return viewer;
};

const docManager = async () => {
  const viewer = await viewerPromise;
  registryPromise = registryPromise || Promise.resolve(viewer.registry);
  const registry = await registryPromise;
  return registry?.getPlugin('document-manager')?.provides() || null;
};

const showInViewer = async (item) => {
  viewerPromise = viewerPromise || startViewer();
  await viewerPromise;
  const manager = await docManager();
  if (!manager) throw new Error('document-manager unavailable');

  // 多标签：点开一篇就在阅读器内部多开一个 tab，已开过的直接切过去。
  if (openedDocs.has(item.id) && typeof manager.setActiveDocument === 'function') {
    manager.setActiveDocument(item.id);
  } else {
    // name 用于标签页文案；不被支持时会被忽略，退回默认的 Document <id>。
    await manager.openDocumentUrl({ url: item.href, documentId: item.id, name: shortTitle(item), autoActivate: true });
    openedDocs.add(item.id);
  }
  mode = 'embedpdf';
};

// ---- 选择与路由 --------------------------------------------------------
const select = async (id, { push = false, replace = false } = {}) => {
  const item = byId.get(id);
  if (!item) return;
  currentId = id;

  el.title.textContent = item.title || id;
  el.meta.textContent = [item.subtitle, ...(item.tags || []).slice(0, 2)].filter(Boolean).join(' · ');
  el.download.href = item.href;
  el.download.setAttribute('download', item.href.split('/').pop());
  el.openTab.href = item.href;
  markActive(id);
  document.title = `${shortTitle(item)} · 论文阅读器`;

  el.closeTab.disabled = false;
  const index = flat.findIndex((p) => p.id === id);
  el.prev.disabled = index <= 0;
  el.next.disabled = index === -1 || index >= flat.length - 1;

  if (push || replace) {
    const url = new URL(window.location.href);
    url.searchParams.set('paper', id);
    if (push) window.history.pushState({ paper: id }, '', url);
    else window.history.replaceState({ paper: id }, '', url);
  }
  el.nav.classList.remove('is-open');
  el.navToggle.setAttribute('aria-expanded', 'false');

  if (mode === 'fallback') {
    useFallback(item);
    return;
  }

  el.empty.hidden = true;
  el.host.hidden = false;
  try {
    await showInViewer(item);
  } catch (error) {
    console.error(error);
    useFallback(item, 'EmbedPDF 加载失败（可能是网络或 CDN 不可达），已切换为浏览器自带阅读器。');
  }
};

const step = (delta) => {
  const current = new URLSearchParams(window.location.search).get('paper');
  const index = flat.findIndex((p) => p.id === current);
  const target = flat[index + delta];
  if (target) select(target.id, { push: true });
};

renderTree();

el.tree.addEventListener('click', (event) => {
  const link = event.target.closest('a[data-id]');
  if (!link) return;
  event.preventDefault();
  select(link.dataset.id, { push: true });
});

// ---- 关闭内部标签（劫持 Ctrl/Cmd+W）--------------------------------------
// 浏览器把 Ctrl/Cmd+W 划给"关闭浏览器标签"，网页默认拿不到它。
// 只有在全屏 + Keyboard Lock（Chrome/Edge）下才能真正截住，所以：
//   - 进全屏时申请 navigator.keyboard.lock(['KeyW'])；
//   - 另外提供 Alt+W（macOS 上就是 ⌥W）作为任何环境都能用的等价键。
// 判定用 event.code === 'KeyW'：macOS 下 ⌥W 的 event.key 是 '∑'，按 key 判会漏。
const closeActiveTab = async () => {
  if (mode !== 'embedpdf' || !currentId) return;
  const manager = await docManager().catch(() => null);
  const closing = currentId;
  const order = [...openedDocs];
  const index = order.indexOf(closing);

  if (manager && typeof manager.closeDocument === 'function') manager.closeDocument(closing);
  openedDocs.delete(closing);

  const nextId = order[index + 1] || order[index - 1] || null;
  if (nextId) {
    select(nextId, { push: false, replace: true });
    return;
  }

  // 最后一个标签关掉：回到空态，URL 也不再指向某一篇。
  currentId = null;
  el.closeTab.disabled = true;
  el.host.hidden = true;
  el.empty.hidden = false;
  el.title.textContent = '选择左侧任意一篇开始阅读';
  el.meta.textContent = `${flat.length} 篇解构报告 · ${grouped.length} 个主题`;
  document.title = '论文阅读器 · LLM 推理资料库';
  markActive(null);
  const url = new URL(window.location.href);
  url.searchParams.delete('paper');
  window.history.replaceState({}, '', url);
};

const isCloseTabChord = (event) => {
  const w = event.code === 'KeyW' || event.key === 'w' || event.key === 'W';
  if (!w) return false;
  if (event.altKey && !event.ctrlKey && !event.metaKey) return true;   // Alt/⌥+W：永远可用
  return (event.ctrlKey || event.metaKey) && !event.shiftKey;          // Ctrl/Cmd+W：全屏下才截得住
};

window.addEventListener('keydown', (event) => {
  if (!isCloseTabChord(event)) return;
  event.preventDefault();
  event.stopPropagation();
  closeActiveTab();
}, true);

el.closeTab.addEventListener('click', () => closeActiveTab());

// 全屏：整块 shell（含左侧目录）进全屏，这样全屏里还能换论文。
const syncFullscreenLabel = () => {
  const on = document.fullscreenElement === el.shell;
  el.fullscreen.textContent = on ? '退出全屏' : '全屏';
  el.fullscreen.setAttribute('aria-pressed', String(on));
};
el.fullscreen.addEventListener('click', async () => {
  try {
    if (document.fullscreenElement === el.shell) await document.exitFullscreen();
    else await el.shell.requestFullscreen();
  } catch (error) {
    console.error(error);
  }
});
document.addEventListener('fullscreenchange', () => {
  syncFullscreenLabel();
  const lock = navigator.keyboard?.lock;
  if (!lock) return;
  if (document.fullscreenElement === el.shell) {
    navigator.keyboard.lock(['KeyW']).catch(() => {});
  } else {
    navigator.keyboard.unlock?.();
  }
});

el.search.addEventListener('input', applyFilter);
el.prev.addEventListener('click', () => step(-1));
el.next.addEventListener('click', () => step(1));
el.navToggle.addEventListener('click', () => {
  const open = el.nav.classList.toggle('is-open');
  el.navToggle.setAttribute('aria-expanded', String(open));
});

window.addEventListener('popstate', () => {
  const id = new URLSearchParams(window.location.search).get('paper');
  if (id) select(id);
});

const initial = new URLSearchParams(window.location.search).get('paper');
if (initial && byId.has(initial)) {
  select(initial);
} else {
  el.prev.disabled = true;
  el.next.disabled = flat.length === 0;
  el.closeTab.disabled = true;
  el.meta.textContent = `${flat.length} 篇解构报告 · ${grouped.length} 个主题`;
}
