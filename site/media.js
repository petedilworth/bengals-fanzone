// Renders data/media/index.json + data/media/<season>-wNN.json as a source × topic grid.
// Written by the private round-up session each Wednesday. Topic names and source names only.

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
async function getJSON(path) {
  const r = await fetch(path, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

function renderWeek(w, weeks, current) {
  const srcs = w.sources;
  // Topics ordered by how many sources raised them, most first; ties keep the file's order.
  const topics = w.topics.map((t, i) => ({ ...t, i, n: t.sources.length })).sort((a, b) => b.n - a.n || a.i - b.i);
  const byId = Object.fromEntries(srcs.map(s => [s.id, s]));
  const consensus = topics.filter(t => t.n >= 3), unique = topics.filter(t => t.n === 1);
  const uniqueBySource = {};
  unique.forEach(t => { (uniqueBySource[t.sources[0]] ||= []).push(t.topic); });

  const nav = `<div class="wk-nav">${weeks.map(k => `<a href="#w${k}" class="pill ${k === current ? 'ok' : ''}">Week ${k}</a>`).join(' ')}</div>`;
  const head = `<div class="section-head"><h2>Week ${w.week} ${esc(w.opponent || '')}</h2><p class="lede">${srcs.length} sources, ${topics.length} topics. Written ${esc(w.written)}.</p></div>`;

  const grid = `<div class="grid-scroll"><table class="topic-grid" aria-label="Sources by topic">
    <thead><tr><th scope="col" class="src-col">Source</th>${topics.map(t => `<th scope="col"><span class="th-rot">${esc(t.topic)}</span></th>`).join('')}</tr></thead>
    <tbody>${srcs.map(s => `<tr><th scope="row" class="src-col"><span class="src-type">${esc(s.type)}</span>${s.url ? `<a href="${esc(s.url)}">${esc(s.name)}</a>` : esc(s.name)}</th>${
      topics.map(t => { const on = t.sources.includes(s.id); return `<td class="${on ? 'on' : ''}${t.n === 1 && on ? ' only' : ''}" title="${esc(s.name)}: ${esc(t.topic)}">${on ? '<span class="dot"></span>' : ''}</td>`; }).join('')}</tr>`).join('')}
    <tr class="totals"><th scope="row" class="src-col">Sources per topic</th>${topics.map(t => `<td>${t.n}</td>`).join('')}</tr></tbody>
  </table></div>
  <p class="legend"><span class="dot inline"></span> raised it · <span class="dot inline only"></span> only this source raised it · scroll sideways for more topics</p>`;

  const lists = `<div class="counter">
    <div class="cblock"><span class="chip">Consensus</span><h2>${consensus.length ? `${consensus.length} topic${consensus.length === 1 ? '' : 's'} most sources share` : 'No topic reached 3 sources'}</h2>
      <ul>${consensus.map(t => `<li><b>${esc(t.topic)}</b> – ${t.n} of ${srcs.length}${t.stat_verdict ? ` · stats: ${esc(t.stat_verdict)}` : ''}</li>`).join('') || '<li>Nothing yet.</li>'}</ul></div>
    <div class="cblock"><span class="chip">Unique</span><h2>${unique.length ? `${unique.length} topic${unique.length === 1 ? '' : 's'} only one source raised` : 'No unique topics'}</h2>
      <ul>${Object.entries(uniqueBySource).map(([id, ts]) => `<li><b>${esc(byId[id]?.name || id)}</b>: ${ts.map(esc).join('; ')}</li>`).join('') || '<li>Every topic came from at least two sources.</li>'}</ul></div>
  </div>`;
  return nav + head + grid + lists;
}

async function main() {
  const el = document.getElementById('media');
  try {
    const index = await getJSON('data/media/index.json');
    const weeks = (index.weeks || []).slice().sort((a, b) => a - b);
    if (!weeks.length) { el.innerHTML = '<p class="status">No round-up yet. The first one lands on a Wednesday after the next game.</p>'; return; }
    const pick = () => { const h = parseInt((location.hash || '').replace('#w', ''), 10); return weeks.includes(h) ? h : weeks[weeks.length - 1]; };
    const show = async () => {
      const k = pick();
      const w = await getJSON(`data/media/${index.season}-w${String(k).padStart(2, '0')}.json`);
      el.innerHTML = renderWeek(w, weeks, k);
    };
    window.addEventListener('hashchange', show);
    await show();
  } catch (err) {
    el.innerHTML = `<p class="status">Couldn't load the media topics (${esc(err.message)}).</p>`;
  }
}
main();
