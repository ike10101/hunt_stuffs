(() => {
  const filename = prompt('Enter filename (without extension):', 'js-urls');
  if (!filename) { console.log('Download cancelled'); return; }

  const urls = new Set();

  // 1) External <script src="...">
  document.querySelectorAll('script[src]').forEach(s => urls.add(s.src));

  // 2) performance resources (includes scripts fetched dynamically)
  try {
    performance.getEntriesByType('resource').forEach(r => {
      if (r.initiatorType === 'script' || /\.js(\?|#|$)/i.test(r.name)) urls.add(r.name);
    });
  } catch (e) {
    /* some environments may restrict performance API */
  }

  // 3) link rel=modulepreload / preload that point to JS
  document.querySelectorAll('link[rel="modulepreload"], link[rel="preload"]').forEach(l => {
    const href = l.href || l.getAttribute('href');
    if (href && /\.js(\?|#|$)/i.test(href)) urls.add(href);
  });

  const list = Array.from(urls).filter(Boolean);
  if (list.length === 0) { console.log('No JS URLs found on this page.'); return; }

  const blob = new Blob([list.join('\n')], { type: 'text/plain;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename.endsWith('.txt') ? filename : filename + '.txt';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);

  console.log(`Saved ${list.length} JS URL(s) to "${a.download}"`);
})();