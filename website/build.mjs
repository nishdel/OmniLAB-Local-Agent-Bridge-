// Static documentation only. No LAB imports, model calls or runtime configuration.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const {marked} = await import(process.env.MARKED_MODULE || 'marked');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(root, 'website', 'dist');
const revision = execFileSync('git', ['rev-parse', 'HEAD'], {cwd: root, encoding: 'utf8'}).trim();
const repo = 'https://github.com/nishdel/OmniLAB-Local-Agent-Bridge-';
const manifest = (await fs.readFile(path.join(root, 'PUBLIC-FILES.txt'), 'utf8')).split(/\r?\n/).filter(x => x && !x.startsWith('#'));
const documents = manifest.filter(x => x.endsWith('.md') && !x.startsWith('.github/'));
const outputName = name => name === 'docs/index.md' ? 'index.html' : name.replace(/\.md$/, '.html');
const escape = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const relative = (from, to) => path.posix.relative(path.posix.dirname(from), to) || path.posix.basename(to);
const nav = [
  ['Start here', [['docs/index.md', 'Documentation home'], ['README.md', 'Overview'], ['docs/QUICKSTART.md', 'Quickstart'], ['docs/USER-GUIDE.md', 'Using the dock']]],
  ['Understand the system', [['docs/WORKFLOW.md', 'Lanes, transport & verification'], ['docs/ARCHITECTURE.md', 'Retained interfaces'], ['docs/CONFIGURATION.md', 'Configuration'], ['docs/OPERATIONS.md', 'Standalone apps & Docker']]],
  ['Evidence & direction', [['docs/INFERENCE-ROADMAP.md', 'Strata qualification'], ['docs/research/JANAS.md', 'Independent Janas research'], ['docs/SELECTIVE-IMPLEMENTATION-REPORT.md', 'Implementation evidence'], ['docs/OPENHANDS-STRONGER-QUALIFICATION.md', 'Ollama / OpenHands evidence'], ['docs/RELEASE-READINESS.md', 'Release gates']]]
];
await fs.mkdir(out, {recursive: true});
const search = [];
const allLinks = [];
for (const name of documents) {
  const text = await fs.readFile(path.join(root, name), 'utf8');
  const file = outputName(name);
  const title = text.match(/^#\s+(.+)$/m)?.[1] || name;
  const headings = [];
  const counts = new Map();
  const renderer = new marked.Renderer();
  renderer.heading = function(token) {
    const plain = token.text.replace(/[`*_]/g, '');
    const base = plain.toLowerCase().replace(/[^\p{L}\p{N}\s_-]/gu, '').replace(/\s/g, '-');
    const n = counts.get(base) || 0; counts.set(base, n + 1);
    const id = n ? `${base}-${n}` : base;
    if (token.depth === 2) headings.push({title: plain, id});
    return `<h${token.depth} id="${escape(id)}">${this.parser.parseInline(token.tokens)}<a class="anchor" href="#${escape(id)}" aria-label="Link to ${escape(plain)}">#</a></h${token.depth}>`;
  };
  renderer.code = ({text: code, lang}) => lang === 'mermaid'
    ? `<figure class="diagram"><pre class="mermaid">${escape(code)}</pre><button class="expand-diagram" type="button" hidden>Expand diagram</button><details><summary>Diagram source</summary><pre><code>${escape(code)}</code></pre></details></figure>`
    : `<pre><code class="language-${escape(lang || 'text')}">${escape(code)}</code></pre>`;
  const resolveLink = href => {
    if (/^(?:[a-z]+:|#|\/\/)/i.test(href)) return href;
    const [raw, fragment] = href.split('#');
    const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(name), raw));
    const isDirectory = manifest.some(x => x.startsWith(resolved.replace(/\/$/, '') + '/'));
    if (!manifest.includes(resolved) && !isDirectory) throw new Error(`${name}: link outside public manifest: ${href}`);
    let target;
    if (documents.includes(resolved)) target = relative(file, outputName(resolved));
    else if (/\.(png|jpg|svg)$/i.test(resolved)) target = relative(file, resolved);
    else target = `${repo}/${isDirectory ? 'tree' : 'blob'}/${revision}/${resolved}`;
    if (fragment) target += '#' + fragment;
    allLinks.push({from: file, target});
    return target;
  };
  renderer.link = function(token) {return `<a href="${escape(resolveLink(token.href))}">${this.parser.parseInline(token.tokens)}</a>`;};
  renderer.image = token => `<img loading="lazy" src="${escape(resolveLink(token.href))}" alt="${escape(token.text)}">`;
  const body = marked.parse(text, {renderer});
  const sidebar = nav.map(([group, links]) => `<p class="nav-label">${group}</p>${links.map(([target, label]) => `<a ${target === name ? 'aria-current="page"' : ''} href="${relative(file, outputName(target))}">${label}</a>`).join('')}`).join('');
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Source-linked OmniLAB development documentation: advisory, OpenHands implementation, inference and independent acceptance."><title>${escape(title)} · OmniLAB</title><link rel="stylesheet" href="${relative(file, 'assets/style.css')}"></head><body>
  <a class="skip" href="#content">Skip to content</a><header><a class="brand" href="${relative(file, 'index.html')}"><span class="brand-mark">O</span> OmniLAB <span class="brand-sub">/ Docs</span></a><span class="status">DEVELOPMENT · 0.5.0.dev0</span><a href="${repo}/pull/1">Development PR ↗</a></header>
  <div class="layout"><aside aria-label="Documentation navigation"><label for="search">Find a guide</label><input id="search" type="search" placeholder="Search documentation…" autocomplete="off"><div id="results" aria-live="polite"></div><nav>${sidebar}</nav></aside>
  <main id="content"><div class="eyebrow">SUPERVISED LOCAL DEVELOPMENT</div><article>${body}</article><footer>Source revision <a href="${repo}/tree/${revision}">${revision.slice(0, 7)}</a> · <a href="${repo}/blob/${revision}/${name}">View this page on GitHub</a><br>Implementation, dated qualification and future plans are separate. Local output requires independent acceptance.</footer></main>
  <nav class="toc" aria-label="On this page"><p class="nav-label">On this page</p>${headings.map(h => `<a href="#${escape(h.id)}">${escape(h.title)}</a>`).join('')}</nav></div>
  <script>window.docsBase=${JSON.stringify(relative(file, 'search.json').replace('search.json', ''))};</script><script src="${relative(file, 'assets/app.js')}"></script><script src="https://cdn.jsdelivr.net/npm/mermaid@11.12.2/dist/mermaid.min.js" defer></script></body></html>`;
  await fs.mkdir(path.dirname(path.join(out, file)), {recursive: true});
  await fs.writeFile(path.join(out, file), html);
  search.push({title, url: file, headings: headings.map(h => h.title).join(' ')});
}
for (const name of manifest.filter(x => /^docs\/images\/.+\.png$/.test(x))) {
  await fs.mkdir(path.dirname(path.join(out, name)), {recursive: true});
  await fs.copyFile(path.join(root, name), path.join(out, name));
}
await fs.cp(path.join(root, 'website/assets'), path.join(out, 'assets'), {recursive: true});
await fs.writeFile(path.join(out, 'search.json'), JSON.stringify(search));
await fs.writeFile(path.join(out, '.nojekyll'), '');
await fs.writeFile(path.join(out, 'build.json'), JSON.stringify({revision, pages: documents.length, diagrams: 'Mermaid 11.12.2; raw source retained', source: repo}, null, 2));
for (const {from, target} of allLinks) {
  if (/^https?:/.test(target)) continue;
  const [filename, anchor] = target.split('#');
  const destination = path.resolve(out, path.posix.dirname(from), filename);
  await fs.access(destination);
  if (anchor && destination.endsWith('.html')) {
    const html = await fs.readFile(destination, 'utf8');
    if (!html.includes(`id="${anchor}"`) && !html.includes(`id='${anchor}'`)) throw new Error(`${from}: missing anchor ${target}`);
  }
}
console.log(`Built ${documents.length} public pages; local links and anchors verified; source ${revision}`);
