(() => {
  const items = window.CONTENT_ITEMS || [];
  const categories = window.CONTENT_CATEGORIES || [];
  const grid = document.querySelector('#contentGrid');
  const filterRoot = document.querySelector('#categoryFilters');
  const searchInput = document.querySelector('#searchInput');
  const summary = document.querySelector('#resultsSummary');
  const itemCount = document.querySelector('#itemCount');
  const paperGallery = document.querySelector('#paperGallery');

  const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[char]);

  const isPdf = (item) => typeof item.href === 'string' && /\.pdf$/i.test(item.href);

  const joinBase = (base, path) => {
    if (!path) return path;
    if (/^(?:[a-z]+:)?\/\//i.test(path) || path.startsWith('/')) return path;
    if (!base) return path;
    return base.replace(/\/?$/, '/') + path.replace(/^\.\//, '');
  };

  const coverPath = (item, base = '') => {
    if (item.cover) return joinBase(base, item.cover);
    if (!isPdf(item)) return null;
    const file = item.href.split('/').pop().replace(/\.pdf$/i, '');
    return joinBase(base, `assets/covers/${file}.jpg`);
  };

  const itemHref = (item, base = '') => {
    if (!isPdf(item)) return joinBase(base, item.href);
    // PDF 统一进阅读器（reader.html 按 id 选中），原文件仍可单独下载。
    const id = item.id || item.href.split('/').pop().replace(/\.pdf$/i, '');
    return joinBase(base, `reader.html?paper=${encodeURIComponent(id)}`);
  };

  const renderCard = (item, base = '') => {
    const cover = coverPath(item, base);
    const pdf = isPdf(item);
    const href = itemHref(item, base);
    const action = pdf
      ? (item.action && !/^(打开|预览) PDF$/.test(item.action) ? item.action : '在阅读器打开')
      : item.action;
    const directPdf = pdf ? joinBase(base, item.href) : '';
    const coverBlock = cover ? `
      <a class="card-cover" href="${escapeHtml(href)}" tabindex="-1" aria-hidden="true">
        <img src="${escapeHtml(cover)}" alt="" loading="lazy" decoding="async">
      </a>` : '';

    return `
      <article class="resource-card accent-${escapeHtml(item.accent || 'blue')}${pdf ? ' is-pdf' : ''}">
        ${coverBlock}
        <div class="card-body">
          <div class="card-topline"><span class="resource-type">${escapeHtml(item.type)}</span><time datetime="${escapeHtml(item.updated || '')}">${item.updated ? `更新于 ${escapeHtml(item.updated)}` : ''}</time></div>
          <h3>${escapeHtml(item.title)}</h3>
          <p class="subtitle">${escapeHtml(item.subtitle || '')}</p>
          <p class="description">${escapeHtml(item.description || '')}</p>
          <ul class="tag-list" aria-label="标签">${(item.tags || []).map((tag) => `<li>${escapeHtml(tag)}</li>`).join('')}</ul>
          <div class="card-actions">
            <a class="resource-link" href="${escapeHtml(href)}">${escapeHtml(action || '打开')} <span aria-hidden="true">↗</span></a>
            ${pdf ? `<a class="resource-link resource-link-secondary" href="${escapeHtml(directPdf)}" download>下载</a>` : ''}
          </div>
        </div>
      </article>`;
  };

  // Homepage library grid
  if (grid && filterRoot && searchInput && summary) {
    let activeCategory = new URLSearchParams(window.location.search).get('category') || 'all';
    let searchTerm = '';
    if (!categories.some(({ id }) => id === activeCategory)) activeCategory = 'all';
    if (itemCount) itemCount.textContent = items.length;

    const renderFilters = () => {
      filterRoot.innerHTML = categories.map(({ id, label }) => `
        <button class="filter${id === activeCategory ? ' is-active' : ''}" type="button" data-category="${id}" aria-pressed="${id === activeCategory}">${label}</button>
      `).join('');
    };

    const renderItems = () => {
      const keyword = searchTerm.trim().toLocaleLowerCase('zh-CN');
      const visible = items.filter((item) => {
        const inCategory = activeCategory === 'all' || item.category === activeCategory;
        const searchable = [item.title, item.subtitle, item.description, ...(item.tags || [])].join(' ').toLocaleLowerCase('zh-CN');
        return inCategory && (!keyword || searchable.includes(keyword));
      });

      summary.textContent = `显示 ${visible.length} / ${items.length} 份资料`;
      const pdfCount = visible.filter(isPdf).length;
      const waterfall = activeCategory === 'papers' || (pdfCount > 0 && pdfCount >= visible.length * 0.6);
      grid.classList.toggle('is-waterfall', waterfall);
      grid.innerHTML = visible.length
        ? visible.map((item) => renderCard(item)).join('')
        : '<p class="empty-state">没有匹配的资料。请换一个关键词或分类。</p>';
    };

    filterRoot.addEventListener('click', (event) => {
      const button = event.target.closest('[data-category]');
      if (!button) return;
      activeCategory = button.dataset.category;
      const url = new URL(window.location.href);
      activeCategory === 'all' ? url.searchParams.delete('category') : url.searchParams.set('category', activeCategory);
      window.history.replaceState({}, '', url);
      renderFilters();
      renderItems();
    });

    searchInput.addEventListener('input', () => {
      searchTerm = searchInput.value;
      renderItems();
    });

    renderFilters();
    renderItems();
  }

  // Papers ledger page gallery
  if (paperGallery) {
    const base = paperGallery.dataset.base || '';
    const papers = items.filter((item) => item.category === 'papers' && isPdf(item));
    paperGallery.classList.add('is-waterfall');
    paperGallery.innerHTML = papers.length
      ? papers.map((item) => renderCard(item, base)).join('')
      : '<p class="empty-state">暂无论文 PDF。</p>';
  }
})();
