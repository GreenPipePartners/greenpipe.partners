/* Prebuilt SVG/PNG strips: no source parsing, diagram engine, or runtime rasterizer. */
(() => {
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };

  class LogicReport extends HTMLElement {
    async connectedCallback() {
      if (this.started) return;
      this.started = true;
      try {
        this.base = new URL(this.getAttribute('src'), location.href);
        const response = await fetch(this.base);
        if (!response.ok) throw new Error(`Index request failed (${response.status})`);
        this.manifest = await response.json();
        if (!['gpp.logic-report/1','gpp.resource-report/1','gpp.screen-report/1'].includes(this.manifest.schema)) throw new Error('Unsupported report index version');
        if (!this.isConnected) { this.started = false; return; }
        this.isScreens = this.manifest.schema === 'gpp.screen-report/1';
        this.isResources = this.manifest.schema !== 'gpp.logic-report/1';
        this.dataset.kind = this.isScreens ? 'screens' : this.isResources ? 'resources' : 'logic';
        this.entries = new Map((this.manifest.routines || this.manifest.resources || this.manifest.screens).map(r => [r.id, r]));
        this.defaultEntry = this.manifest.default_routine || this.manifest.default_resource || this.manifest.default_screen;
        if (!this.entries.has(this.defaultEntry)) throw new Error('Default entry is missing');
        this.group = this.manifest.groups?.[0]?.label;
        this.scale = 0.5;
        this.mode = matchMedia('(max-width:800px)').matches ? 'fixed' : 'fit';
        this.format = this.manifest.default_format || 'svg';
        this.theme = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
        this.dataset.imageTheme = this.theme;
        this.expanded = new Map();
        this.prefetched = new Set();
        this.hashPrefix = `#logic-${this.getAttribute('viewer-id') || this.manifest.id}/`;
        this.renderShell();
        const fromHash = this.readHash();
        this.select(fromHash?.id || this.defaultEntry, false, fromHash?.rung);
        this.onHash = () => {
          const state = this.readHash();
          if (state) this.select(state.id, false, state.rung);
          else if (!location.hash) this.select(this.defaultEntry, false);
        };
        addEventListener('hashchange', this.onHash);
        this.resize = new ResizeObserver(() => { if (this.mode === 'fit') this.fit(); });
        this.resize.observe(this.viewport);
        this.themeObserver = new MutationObserver(() => this.syncTheme());
        this.themeObserver.observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
        this.dataset.ready = 'true';
      } catch (error) {
        this.replaceChildren(element('p', `Unable to open the logic report: ${error.message}`));
        const fallback = element('a', 'Open the static routine index');
        fallback.href = new URL('routines.html', this.base || location.href).href;
        this.append(fallback);
      }
    }

    disconnectedCallback() {
      removeEventListener('hashchange', this.onHash);
      this.resize?.disconnect();
      this.themeObserver?.disconnect();
      cancelAnimationFrame(this.scrollFrame);
      this.started = false;
    }

    asset(path) {
      const url = new URL(path, this.base);
      if (url.origin !== this.base.origin || !url.pathname.startsWith(new URL('.', this.base).pathname)) {
        throw new Error('Asset is outside this report bundle');
      }
      return url.href;
    }

    readHash() {
      if (!location.hash.startsWith(this.hashPrefix)) return null;
      const [id, rung] = location.hash.slice(this.hashPrefix.length).split('/');
      if (!this.entries.has(id)) return null;
      return { id, rung: /^\d+$/.test(rung || '') ? Number(rung) : null };
    }

    link(id, rung) { return this.hashPrefix + id + (Number.isInteger(rung) ? '/' + rung : ''); }

    renderShell() {
      this.innerHTML = `<div class="lv-shell" data-menu="closed">
        <aside class="lv-sidebar"><div class="lv-sidebar-top">
          <div class="lv-section-buttons" aria-label="PLC sections"></div>
          <label>Find a routine<input class="lv-search" type="search" placeholder="Routine or program name"></label>
          <label class="lv-context-label"><input class="lv-context-toggle" type="checkbox"> Show existing application context</label>
        </div><nav class="lv-tree" aria-label="Logic hierarchy"></nav>
        </aside>
        <section class="lv-main" aria-label="Selected routine">
          <header class="lv-titlebar"><button class="lv-browse" type="button" aria-expanded="false">Browse routines</button>
            <details class="lv-key"><summary title="Show or hide legend and details"><h2></h2></summary>
              <div class="lv-key-content"><p class="lv-meta"></p><div class="lv-key-body"></div></div>
            </details>
          </header>
          <div class="lv-tools" aria-label="Drawing controls">
            <button type="button" data-action="out" aria-label="Zoom out">−</button><output aria-label="Drawing zoom"></output>
            <button type="button" data-action="in" aria-label="Zoom in">+</button>
            <button type="button" data-action="fit">Fit width</button><button type="button" data-action="actual">100%</button>
            <label>Rung <select class="lv-rung" aria-label="Jump to rung"></select></label>
            <label>Image <select class="lv-format" aria-label="Image format"><option value="svg">SVG</option><option value="png">PNG</option></select></label>
            <button type="button" data-action="fullscreen">Full screen</button>
            <button type="button" data-action="copy">Copy link</button>
            <a class="lv-svg" target="_blank" rel="noopener">Open SVG</a>
            <a class="lv-source" target="_blank" rel="noopener">RLL source</a>
          </div>
          <div class="lv-viewport" tabindex="0" aria-label="Routine drawing; scroll to navigate"></div>
          <p class="lv-status" role="status" aria-live="polite"></p>
        </section></div>`;
      this.viewport = this.querySelector('.lv-viewport');
      this.tree = this.querySelector('.lv-tree');
      this.search = this.querySelector('.lv-search');
      this.context = this.querySelector('.lv-context-toggle');
      this.rung = this.querySelector('.lv-rung');
      this.status = this.querySelector('.lv-status');
      this.sections = this.querySelector('.lv-section-buttons');
      this.querySelector('.lv-browse').addEventListener('click', () => this.setMenu(this.querySelector('.lv-shell').dataset.menu !== 'open'));
      if (this.isResources) {
        this.sections.hidden = true;
        this.querySelector('.lv-context-label').hidden = true;
        this.search.parentElement.firstChild.textContent = this.isScreens ? 'Find a screen' : 'Find a resource';
        this.search.placeholder = this.isScreens ? 'Page, route or screen state' : 'Schema, messages or calculations';
        this.tree.setAttribute('aria-label',this.isScreens ? 'Perspective screens' : 'Supporting resources');
        this.querySelector('.lv-main').setAttribute('aria-label',this.isScreens ? 'Selected screen' : 'Selected resource');
        this.querySelector('.lv-source').textContent = 'Source';
        this.rung.parentElement.hidden = true;
      }
      if (this.isScreens) {
        this.querySelector('.lv-format').replaceChildren(new Option('PNG','png'));
        this.querySelector('.lv-format').parentElement.hidden = true;
        this.querySelector('.lv-svg').textContent = 'Open image';
        this.querySelector('.lv-source').textContent = 'View JSON';
      }
      for (const group of this.manifest.groups || []) {
        const button = element('button', group.label);
        button.type = 'button';
        button.dataset.group = group.label;
        button.addEventListener('click', () => { this.group = group.label; this.search.value = ''; this.renderTree(); });
        this.sections.append(button);
      }
      this.search.addEventListener('input', () => this.renderTree());
      this.context.addEventListener('change', () => this.renderTree());
      this.querySelector('.lv-format').value = this.format;
      this.querySelector('.lv-format').addEventListener('change', event => {
        this.format = event.target.value;
        this.updateTiles();
      });
      this.viewport.addEventListener('scroll', () => {
        cancelAnimationFrame(this.scrollFrame);
        this.scrollFrame = requestAnimationFrame(() => this.updateTiles());
      }, { passive:true });
      this.rung.addEventListener('change', () => {
        const n = this.rung.value === '' ? null : Number(this.rung.value);
        this.jump(n);
        history.replaceState(null, '', this.link(this.current.id, n));
      });
      this.querySelector('.lv-tools').addEventListener('click', async event => {
        const action = event.target.closest('button')?.dataset.action;
        if (!action) return;
        if (action === 'fit') this.fit();
        if (action === 'actual') this.zoom(1);
        if (action === 'in') this.zoom(this.scale * 1.25);
        if (action === 'out') this.zoom(this.scale / 1.25);
        if (action === 'fullscreen') {
          try { if (document.fullscreenElement) await document.exitFullscreen(); else await this.requestFullscreen(); }
          catch { this.status.textContent = 'Full screen is unavailable in this browser or embed.'; }
        }
        if (action === 'copy') {
          const url = new URL(location.href);
          url.hash = this.link(this.current.id, this.rung.value === '' ? null : Number(this.rung.value));
          try { await navigator.clipboard.writeText(url.href); this.status.textContent = 'Routine link copied.'; }
          catch { this.status.textContent = url.href; }
        }
      });
    }

    renderTree() {
      if (this.isResources) { this.renderResources(); return; }
      const query = this.search.value.trim().toLowerCase();
      const includeContext = this.context.checked && !query;
      const trim = node => {
        const children = (node.children || []).map(trim).filter(Boolean);
        const routine = this.entries.get(node.routine);
        const match = routine && (!query || `${routine.title} ${routine.path}`.toLowerCase().includes(query));
        if (!includeContext && !children.length && !match) return null;
        return { ...node, children, routine: match ? node.routine : null };
      };
      const makeNode = (node, parent = '') => {
        const key = parent + '/' + node.kind + ':' + node.label;
        const li = element('li');
        const label = element('span', node.label, 'lv-node-label');
        const showLabel = container => {
          if (node.routine) {
            const routine = this.entries.get(node.routine);
            const link = element('a', undefined, 'lv-routine');
            link.href = this.link(routine.id);
            link.dataset.routine = routine.id;
            link.dataset.entry = routine.id;
            link.dataset.change = routine.change;
            link.setAttribute('aria-current', String(this.current?.id === routine.id));
            link.append(label, element('span', routine.change, 'lv-badge'));
            link.addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); this.select(routine.id, true); });
            const prefetch = () => this.prefetch(routine);
            link.addEventListener('pointerenter', prefetch, { once:true });
            link.addEventListener('focus', prefetch, { once:true });
            container.append(link);
          } else container.append(label);
          if (node.detail) container.append(element('small', node.detail, 'lv-detail'));
        };
        if (node.children.length) {
          const details = element('details'); details.open = query ? true : (this.expanded.get(key) ?? true);
          details.addEventListener('toggle', () => { if (!query) this.expanded.set(key, details.open); });
          const summary = element('summary'); showLabel(summary);
          const ul = element('ul'); node.children.forEach(child => ul.append(makeNode(child, key)));
          details.append(summary, ul); li.append(details);
        } else {
          const row = element('div', undefined, node.routine ? '' : 'lv-context'); showLabel(row); li.append(row);
        }
        return li;
      };
      const group = this.manifest.groups.find(g => g.label === this.group);
      const ul = element('ul');
      const nodes = group.controllers.map(trim).filter(Boolean);
      nodes.forEach(node => ul.append(makeNode(node)));
      this.tree.replaceChildren(nodes.length ? ul : element('p', 'No matching routines.'));
      this.sections.querySelectorAll('button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.group === this.group)));
    }

    renderResources() {
      const query = this.search.value.trim().toLowerCase();
      const items = [...this.entries.values()].filter(r => `${r.title} ${r.description}`.toLowerCase().includes(query));
      const table = element('table', undefined, 'lv-resource-table');
      table.setAttribute('aria-label',this.isScreens ? 'Perspective screens' : 'Report resources');
      const head = element('thead');
      const heading = element('tr'); heading.append(element('th',this.isScreens ? 'Screen / state' : 'Resource')); head.append(heading);
      const body = element('tbody');
      for (const item of items) {
        const row = element('tr'), cell = element('td');
        const link = element('a',item.title,'lv-resource-link');
        link.href = this.link(item.id);
        link.dataset.resource = item.id;
        if (this.isScreens) link.dataset.screen = item.id;
        link.dataset.entry = item.id;
        link.setAttribute('aria-current',String(this.current?.id===item.id));
        link.addEventListener('click',event => { event.preventDefault(); this.select(item.id,true); });
        link.addEventListener('pointerenter',()=>this.prefetch(item),{once:true});
        link.addEventListener('focus',()=>this.prefetch(item),{once:true});
        cell.append(link,element('small',item.description,'lv-detail'));
        row.append(cell); body.append(row);
      }
      table.append(head,body);
      this.tree.replaceChildren(items.length ? table : element('p',this.isScreens ? 'No matching screens.' : 'No matching resources.'));
    }

    renderLegend() {
      const content = this.querySelector('.lv-key-body');
      content.replaceChildren();
      const legend = this.manifest.legend;
      if (legend) {
        const columns = element('div',undefined,'lv-key-columns');
        for (const [title, entries] of [['Variable colors',legend.variables],['Gutter groups',legend.groups]]) {
          const section = element('section'); section.append(element('h3',title));
          const list = element('ul');
          for (const entry of entries) {
            const row = element('li',entry.label);
            row.style.borderLeftColor = this.theme === 'light' ? entry.light_color : entry.color;
            list.append(row);
          }
          section.append(list); columns.append(section);
        }
        content.append(columns);
      }
      for (const text of legend?.notes || this.current.legend_notes || []) content.append(element('p',text));
    }

    select(id, push, selectedRung = null) {
      const routine = this.entries.get(id);
      if (!routine) return;
      const previousGroup = this.group;
      this.group = routine.group;
      if (previousGroup !== this.group) this.search.value = '';
      this.current = routine;
      this.dataset.current = id;
      this.querySelector('h2').textContent = routine.title;
      this.querySelector('.lv-meta').textContent = this.isResources ? `${routine.description} · ${routine.path}` : `${routine.change} · ${routine.source_rungs} source / ${routine.displayed_rungs} displayed rungs · ${routine.path}`;
      this.renderLegend();
      this.updateDownloadLink();
      this.querySelector('.lv-source').href = this.asset(routine.source);
      const top = element('option', 'Top'); top.value = '';
      this.rung.replaceChildren(top);
      for (const r of routine.rungs || []) {
        const option = element('option', String(r.number).padStart(3, '0') + (r.group ? ' · ' + r.group : ''));
        option.value = String(r.number); this.rung.append(option);
      }
      this.surface = element('div', undefined, 'lv-surface');
      this.surface.setAttribute('aria-label', `${routine.title}; source available through the toolbar`);
      this.tileNodes = routine.tiles.map((tile, index) => {
        const node = element('div', undefined, 'lv-tile');
        node.dataset.tile = index;
        this.surface.append(node);
        return { ...tile, node, index };
      });
      this.viewport.replaceChildren(this.surface);
      this.viewport.scrollTo(0, 0);
      if (this.mode === 'fit') this.scale = this.fitScale();
      this.resizeDrawing();
      this.status.textContent = `Revision ${this.manifest.revision} · source SHA-256 ${routine.source_sha256.slice(0, 16)}… · ${routine.note || 'Read-only published logic; source-backed SVG.'}`;
      if (previousGroup !== this.group || !this.tree.children.length) this.renderTree();
      else this.tree.querySelectorAll('[data-entry]').forEach(link => link.setAttribute('aria-current', String(link.dataset.entry === id)));
      this.rung.value = Number.isInteger(selectedRung) ? String(selectedRung) : '';
      this.jump(selectedRung);
      this.setMenu(false);
      if (push && matchMedia('(max-width:800px)').matches) this.querySelector('.lv-browse').focus({ preventScroll:true });
      if (push) history.pushState(null, '', this.link(id));
    }

    setMenu(open) {
      this.querySelector('.lv-shell').dataset.menu = open ? 'open' : 'closed';
      const button = this.querySelector('.lv-browse');
      button.setAttribute('aria-expanded', String(open));
      button.textContent = open ? 'Close menu' : this.isScreens ? 'Browse screens' : this.isResources ? 'Browse resources' : 'Browse routines';
    }

    themedAsset(item, format, theme = this.theme) {
      return this.asset(item[(theme === 'light' ? 'light_' : '') + format]);
    }

    updateDownloadLink() {
      this.querySelector('.lv-svg').href = this.themedAsset(this.current,this.isScreens ? 'png' : 'svg');
    }

    syncTheme() {
      const theme = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
      if (theme === this.theme) return;
      this.theme = theme;
      this.dataset.imageTheme = theme;
      this.renderLegend();
      this.updateDownloadLink();
      this.updateTiles();
    }

    prefetch(routine) {
      if (navigator.connection?.saveData) return;
      const url = this.themedAsset(routine.tiles[0],this.format);
      if (this.prefetched.has(url)) return;
      this.prefetched.add(url);
      fetch(url, { cache:'force-cache' }).catch(() => this.prefetched.delete(url));
    }

    updateTiles() {
      if (!this.current) return;
      const overscan = this.viewport.clientHeight * .65;
      const top = this.viewport.scrollTop - overscan;
      const bottom = this.viewport.scrollTop + this.viewport.clientHeight + overscan;
      for (const tile of this.tileNodes) {
        const visible = (tile.y+tile.height)*this.scale >= top && tile.y*this.scale <= bottom;
        tile.wanted = visible;
        if (!visible) { tile.requestKey = null; tile.node.replaceChildren(); continue; }
        const key = `${this.theme}:${this.format}`;
        if (tile.requestKey === key) continue;
        tile.requestKey = key;
        tile.requestToken = (tile.requestToken || 0)+1;
        if (tile.node.firstChild?.dataset.variant === key && tile.node.firstChild.dataset.ready === 'true') continue;
        this.loadTile(tile,tile.requestToken,this.theme,this.format);
      }
    }

    async loadTile(tile, token, theme, format) {
      const current = () => this.isConnected && tile.node.isConnected && tile.wanted && tile.requestToken === token && this.theme === theme && this.format === format;
      const img = element('img');
      img.alt = `${this.current.title}, ${theme} image ${tile.index+1} of ${this.tileNodes.length}`;
      img.decoding = 'async';
      img.width = tile.width; img.height = tile.height;
      img.dataset.format = format;
      img.dataset.theme = theme;
      img.dataset.variant = `${theme}:${format}`;
      img.src = this.themedAsset(tile,format,theme);
      // Keep a decoded image visible until its replacement is ready. Geometry and
      // scroll offsets stay unchanged; stale theme requests cannot overwrite it.
      if (!tile.node.firstChild) tile.node.append(img);
      try {
        try { await img.decode(); }
        catch (error) {
          if (!current()) return;
          if (format !== 'svg') throw error;
          img.dataset.format = 'png';
          img.src = this.themedAsset(tile,'png',theme);
          await img.decode();
        }
        if (current()) { img.dataset.ready = 'true'; tile.node.replaceChildren(img); }
      } catch {
        if (current()) this.status.textContent = 'Image unavailable. Open the image or source using the toolbar.';
      }
    }

    resizeDrawing() {
      if (!this.current) return;
      this.surface.style.width = `${this.current.width * this.scale}px`;
      this.surface.style.height = `${this.current.height * this.scale}px`;
      for (const tile of this.tileNodes) {
        tile.node.style.top = `${tile.y * this.scale}px`;
        tile.node.style.height = `${tile.height * this.scale}px`;
      }
      this.querySelector('output').textContent = Math.round(this.scale * 100) + '%';
    }

    zoom(value) {
      const previous = this.scale;
      this.mode = 'fixed';
      this.scale = Math.max(0.1, Math.min(2, value));
      const left = this.viewport.scrollLeft, top = this.viewport.scrollTop;
      this.resizeDrawing();
      this.viewport.scrollTo(left * this.scale / previous, top * this.scale / previous);
      this.updateTiles();
    }

    fitScale() { return Math.max(0.08, (this.viewport.clientWidth - 24) / this.current.width); }

    fit() {
      const previous = this.scale;
      const top = this.viewport.scrollTop;
      this.mode = 'fit'; this.scale = this.fitScale(); this.resizeDrawing();
      this.viewport.scrollTo(0, top * this.scale / previous);
      this.updateTiles();
    }

    jump(number) {
      const rung = (this.current.rungs || []).find(r => r.number === number);
      this.viewport.scrollTo({ left:0, top:rung ? Math.max(0, rung.y * this.scale - 20) : 0 });
      this.updateTiles();
    }
  }

  if (!customElements.get('logic-report')) customElements.define('logic-report', LogicReport);
  // The current report renderer can host the viewer as a normal HTTPS iframe.
  // Same-origin embeds track the existing website theme without reloading the page.
  try {
    const host = window.parent.document.documentElement;
    if (window.parent !== window) {
      document.body.classList.add('logic-embedded');
      const sync = () => { document.documentElement.dataset.theme = host.dataset.theme || 'dark'; };
      sync(); new MutationObserver(sync).observe(host, { attributes:true, attributeFilter:['data-theme'] });
    }
  } catch { /* A separately hosted viewer retains its own theme control. */ }
  document.getElementById('demo-theme')?.addEventListener('click', () => {
    const root = document.documentElement;
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
  });
})();
