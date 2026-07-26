(() => {
  const items = window.CONTENT_ITEMS || [];
  const categories = window.CONTENT_CATEGORIES || [];
  const grid = document.querySelector('#contentGrid');
  const filterRoot = document.querySelector('#categoryFilters');
  const searchInput = document.querySelector('#searchInput');
  const summary = document.querySelector('#resultsSummary');
  const itemCount = document.querySelector('#itemCount');

  let activeCategory = new URLSearchParams(window.location.search).get('category') || 'all';
  let searchTerm = '';
  if (!categories.some(({ id }) => id === activeCategory)) activeCategory = 'all';
  itemCount.textContent = items.length;

  const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[char]);

  const renderFilters = () => {
    filterRoot.innerHTML = categories.map(({ id, label }) => `
      <button class="filter${id === activeCategory ? ' is-active' : ''}" type="button" data-category="${id}" aria-pressed="${id === activeCategory}">${label}</button>
    `).join('');
  };

  const renderItems = () => {
    const keyword = searchTerm.trim().toLocaleLowerCase('zh-CN');
    const visible = items.filter((item) => {
      const inCategory = activeCategory === 'all' || item.category === activeCategory;
      const searchable = [item.title, item.subtitle, item.description, ...item.tags].join(' ').toLocaleLowerCase('zh-CN');
      return inCategory && (!keyword || searchable.includes(keyword));
    });

    summary.textContent = `显示 ${visible.length} / ${items.length} 份资料`;
    grid.innerHTML = visible.length ? visible.map((item) => `
      <article class="resource-card accent-${escapeHtml(item.accent)}">
        <div class="card-topline"><span class="resource-type">${escapeHtml(item.type)}</span><time datetime="${escapeHtml(item.updated)}">更新于 ${escapeHtml(item.updated)}</time></div>
        <h3>${escapeHtml(item.title)}</h3>
        <p class="subtitle">${escapeHtml(item.subtitle)}</p>
        <p class="description">${escapeHtml(item.description)}</p>
        <ul class="tag-list" aria-label="标签">${item.tags.map((tag) => `<li>${escapeHtml(tag)}</li>`).join('')}</ul>
        <a class="resource-link" href="${escapeHtml(item.href)}"${item.download ? ' download' : ''}>${escapeHtml(item.action)} <span aria-hidden="true">↗</span></a>
      </article>
    `).join('') : '<p class="empty-state">没有匹配的资料。请换一个关键词或分类。</p>';
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
})();
