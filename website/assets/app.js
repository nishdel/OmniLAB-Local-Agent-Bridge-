const input = document.querySelector('#search');
const results = document.querySelector('#results');
let index;
input.addEventListener('input', async () => {
  const query = input.value.trim().toLowerCase();
  results.replaceChildren();
  if (!query) return;
  try {
    index ||= await fetch(window.docsBase + 'search.json').then(r => {if (!r.ok) throw Error(); return r.json();});
    if (input.value.trim().toLowerCase() !== query) return;
    const matches = index.filter(item => `${item.title} ${item.headings}`.toLowerCase().includes(query)).slice(0, 12);
    for (const item of matches) {
      const a = document.createElement('a'); a.href = window.docsBase + item.url; a.textContent = item.title; results.append(a);
    }
    if (!matches.length) results.textContent = 'No matching guide.';
  } catch {results.textContent = 'Search unavailable. Use the navigation or documentation index.';}
});
window.addEventListener('load', async () => {
  if (!window.mermaid) return; // Raw diagram text remains readable if the CDN is unavailable.
  mermaid.initialize({startOnLoad:false, securityLevel:'strict', theme:'base', themeVariables:{primaryColor:'#e8f3ef',primaryTextColor:'#172c38',primaryBorderColor:'#83aaa2',lineColor:'#526672',fontFamily:'system-ui',fontSize:'14px'}});
  try {
    await mermaid.run({querySelector:'.mermaid'});
    document.querySelectorAll('.diagram').forEach(figure => {
      const button = figure.querySelector('.expand-diagram');
      button.hidden = false;
      button.addEventListener('click', () => {
        const dialog = document.createElement('dialog');
        dialog.setAttribute('aria-label', 'Expanded workflow diagram');
        const close = document.createElement('button'); close.textContent = 'Close diagram';
        close.addEventListener('click', () => dialog.close());
        const diagram = figure.querySelector('svg').cloneNode(true);
        diagram.style.minWidth = '1000px'; diagram.style.maxWidth = 'none';
        const canvas = document.createElement('div'); canvas.className = 'diagram-canvas'; canvas.append(diagram);
        dialog.append(close, canvas); document.body.append(dialog);
        dialog.addEventListener('close', () => {dialog.remove(); button.focus();});
        dialog.showModal();
      });
    });
  } catch {document.querySelectorAll('.diagram details').forEach(d => {d.open = true;});}
});
