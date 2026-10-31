// Renders the season strip and the current week's brief from data/*.json.
// Text fields support two marks: [label](https://url) for a source link and **bold**.

const DATA = 'data/';

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// Escape first, then turn the two allowed marks into HTML. Only http(s) links are allowed.
function rich(s) {
  return esc(s)
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, (_, label, url) => `<a class="src" href="${url}">${label}</a>`)
    .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
}

async function getJSON(path) {
  const res = await fetch(DATA + path, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

function renderStrip(team, season) {
  document.getElementById('season-h').textContent = `${team.name} ${season.season}`;
  document.getElementById('season-meta').textContent = `${season.record} · ${team.division} · Updated weekly`;
  const strip = document.getElementById('season-strip');
  strip.innerHTML = season.games.map(g => {
    const wk = `<span class="wk">W${g.week} · ${esc(g.date)}</span>`;
    if (g.bye) return `<li class="g bye${g.week === team.currentWeek ? ' now' : ''}">${wk}<span class="opp">BYE</span><span class="res">–</span></li>`;
    const cls = ['g', g.result === 'W' ? 'w' : g.result === 'L' ? 'l' : '', g.week === team.currentWeek ? 'now' : ''].filter(Boolean).join(' ');
    const res = g.result ? `${g.result} ${esc(g.score)}` : esc(g.time);
    const label = g.result ? `Week ${g.week}, ${g.home ? 'versus' : 'at'} ${g.opp}, ${g.result === 'W' ? 'won' : 'lost'} ${g.score}` : '';
    return `<li class="${cls}"${label ? ` aria-label="${esc(label)}"` : ''}>${wk}<span class="opp">${g.home ? '' : '@'}${esc(g.opp)}</span><span class="res">${res}</span></li>`;
  }).join('');
  // On a phone the strip scrolls sideways: bring the current week into view.
  const now = strip.querySelector('.now');
  const box = document.getElementById('strip-scroll');
  if (now && box.scrollWidth > box.clientWidth) box.scrollLeft = now.offsetLeft - box.clientWidth / 2 + now.offsetWidth / 2;
}

function renderBoard(team, w) {
  const g = w.game;
  const us = g.home.abbr === team.abbr ? g.home : g.away;
  const them = us === g.home ? g.away : g.home;
  const wc = g.winChance;
  const odds = (g.line || wc) ? `
    <dl class="odds">
      ${g.line ? `<dt>Line</dt><dd>${rich(g.line)}</dd>` : ''}
      ${wc ? `<dt>Win chance</dt><dd class="bar"><span class="bar-track" role="img" aria-label="${esc(team.abbr)} win chance ${wc.team} percent"><span class="bar-fill" style="width:${Number(wc.team)}%"></span></span><span class="bar-label">${esc(team.abbr)} ${wc.team}% · ${esc(them.abbr)} ${wc.opp}%</span></dd>
      <p class="note">Win chance: ${esc(wc.source)}</p>` : ''}
    </dl>` : '';
  const side = (t, cls, recLabel) => `<div class="team ${cls}"><span class="abbr">${esc(t.abbr)}</span>${t.score != null ? `<span class="score">${t.score}</span>` : ''}<span class="sub">${recLabel} ${esc(t.record)}</span></div>`;
  const recLabel = g.state === 'Final' ? 'Now' : 'Record';
  return `
  <header class="board" aria-label="This week's game">
    <div class="board-top"><span>${esc(w.label)}</span><span>${esc(w.updated)}</span></div>
    <div class="board-main">
      ${side(us, 'us', recLabel)}
      <div class="mid"><strong>${esc(g.state)}</strong><span>${esc(g.kickoff)}</span><span>${esc(g.venue)}</span></div>
      ${side(them, 'opp', recLabel)}
    </div>
    ${odds}
  </header>`;
}

// Standing "expected points" explainer: words from data/explainers, numbers from the pipeline.
function renderExplainer(team, w, ep, ex) {
  const sign = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(1);
  const sit = ep.situations.filter(s => s.ep != null).map(s => `
    <li><span class="ep-val">${sign(s.ep)}</span><div><h3>${esc(s.label)}</h3><p>${esc(s.why)} <span class="n">${s.n.toLocaleString('en-CA')} plays</span></p></div></li>`).join('');
  const plays = ep.plays.map(p => `
    <li><span class="ep-val ${p.for_team >= 0 ? 'up' : 'down'}">${sign(p.for_team)}</span><div>
      <h3>${esc(p.team)} · ${esc(p.note)}</h3>
      <p class="ep-where">Week ${p.week}, ${esc(p.offence)} vs ${esc(p.defence)} · Q${p.quarter} ${esc(p.clock)} · ${esc(p.situation)} · worth ${sign(p.ep_before)} to ${esc(p.offence)} before the snap</p>
      <p>${esc(p.text)}</p>
    </div></li>`).join('');
  return `
  <section class="explain" aria-labelledby="ep-h">
    <details>
      <summary><h2 id="ep-h">${esc(ex.title)}</h2><span class="lede">${esc(ex.summary)}</span></summary>
      ${ex.body.map(b => `<p>${rich(b)}</p>`).join('')}
      <h3 class="ep-sub">${esc(ex.situationsTitle)}</h3>
      <p class="note">${esc(ex.situationsNote.replace('{seasons}', ep.situations_seasons))}</p>
      <ul class="ep-list">${sit}</ul>
      <h3 class="ep-sub">${esc(ex.playsTitle)}</h3>
      <p class="note">${esc(ex.playsNote)}</p>
      <ul class="ep-list">${plays}</ul>
      <p class="note">Source: <a class="src" href="${esc(ep.source_url)}">nflverse</a> play-by-play, nflfastR expected points model. Pulled ${esc(ep.generated.slice(0, 10))}.</p>
    </details>
  </section>`;
}

function section(id, title, lede, body) {
  return `<section aria-labelledby="${id}"><div class="section-head"><h2 id="${id}">${title}</h2>${lede ? `<p class="lede">${lede}</p>` : ''}</div>${body}</section>`;
}

function renderBrief(team, w, ep, ex) {
  const parts = [renderBoard(team, w)];

  if (w.meaning) parts.push(section('meaning', 'What the result means', '', `<p class="meaning">${rich(w.meaning)}</p>`));

  parts.push(section('stories', 'Main storylines', 'Ranked by how much each can change the result.',
    `<ol class="stories">${w.storylines.map((s, i) => `
      <li><span class="rank" aria-hidden="true">${i + 1}</span><div>
        <h3>${esc(s.title)}</h3><p>${rich(s.fact)}</p>${s.why ? `<p class="read">${rich(s.why)}</p>` : ''}
      </div></li>`).join('')}</ol>`));

  if (ep && ex) parts.push(renderExplainer(team, w, ep, ex));

  parts.push(section('watch', 'Things to watch', 'In game order.',
    `<ul class="watch">${w.watch.map(c => `
      <li><span class="when">${esc(c.when)}</span><div>
        <h3>${esc(c.title)}</h3><p>${rich(c.text)}</p>${c.after ? `<p class="after"><b>What happened:</b> ${rich(c.after)}</p>` : ''}
      </div></li>`).join('')}</ul>`));

  if (w.lineFinding) parts.push(section('line', 'From the line stats', '', `<p class="finding">${rich(w.lineFinding)}</p>`));

  parts.push(`
  <section class="counter" aria-label="Counterpoints">
    <div class="cblock">
      <span class="chip">Devil's Advocate</span>
      <h2>Where this brief may be wrong</h2>
      <ul>${w.devilsAdvocate.map(d => `<li>${rich(d)}</li>`).join('')}</ul>
    </div>
    <div class="cblock">
      <span class="chip">Alternative view</span>
      <h2>${esc(w.alternativeView.title)}</h2>
      <p>${rich(w.alternativeView.text)}</p>
    </div>
  </section>`);

  return parts.join('');
}

async function main() {
  const brief = document.getElementById('brief');
  try {
    const team = await getJSON('team.json');
    const season = await getJSON(`season-${team.currentSeason}.json`);
    renderStrip(team, season);
    const wk = String(team.currentWeek).padStart(2, '0');
    const w = await getJSON(`weeks/${team.currentSeason}-w${wk}.json`);
    // The explainer is optional: skip it if either file is missing, or if the pipeline's
    // examples are for a different opponent than this brief (e.g. Monday before the switch).
    const opp = w.game.home.abbr === team.abbr ? w.game.away.abbr : w.game.home.abbr;
    const [ep, ex] = await Promise.all([getJSON('stats/expected-points.json').catch(() => null), getJSON('explainers/expected-points.json').catch(() => null)]);
    brief.innerHTML = renderBrief(team, w, ep && ep.opponent === opp ? ep : null, ex);
  } catch (err) {
    brief.innerHTML = `<p class="status">Couldn't load the brief (${esc(err.message)}). Try again in a minute.</p>`;
  }
}

main();
