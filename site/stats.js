// Renders data/stats/line.json (built by pipeline/build_stats.py) as three question sections.
// The page only displays. All math lives in the pipeline.

const MIN_N = 8;

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
const pct = v => v == null ? '–' : `${Math.round(v * 100)}%`;
const num = (v, d = 2) => v == null ? '–' : (+v).toFixed(d);
const signed = (v, d = 2) => v == null ? '–' : (Math.abs(v) < 0.005 ? '0.00' : (v > 0 ? '+' : '') + (+v).toFixed(d));
const rank = r => r == null ? '' : `<span class="rk">${r}${['st','nd','rd'][((r+90)%100-10)%10-1] || 'th'}</span>`;
const small = n => n < MIN_N ? ' small' : '';
const nTag = n => `<span class="n">${n} play${n === 1 ? '' : 's'}</span>`;

async function getJSON(path) {
  const r = await fetch(path, { cache: 'no-cache' });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

// A horizontal bar with a league-average tick. value and league are 0..1 or EPA-ish numbers; scale picks the max.
function bar(value, league, scale, label, n, cls = '') {
  const w = v => Math.max(0, Math.min(100, ((v - scale.min) / (scale.max - scale.min)) * 100));
  return `<div class="bar-row${small(n)}${cls}">
    <span class="bar-label">${label}</span>
    <span class="bar-track"><span class="bar-fill" style="width:${value == null ? 0 : w(value)}%"></span>${league == null ? '' : `<span class="bar-tick" style="left:${w(league)}%" title="League average"></span>`}</span>
    <span class="bar-value">${scale.fmt(value)} ${nTag(n)}</span>
  </div>`;
}

function section(id, title, answer, body) {
  return `<section aria-labelledby="${id}"><div class="section-head"><h2 id="${id}">${title}</h2><p class="answer">${answer}</p></div>${body}</section>`;
}

function weeklyTable(rows, cols) {
  return `<div class="table-scroll"><table class="wk"><thead><tr>${cols.map(c => `<th scope="col">${c.h}</th>`).join('')}</tr></thead><tbody>${
    rows.map(r => `<tr>${cols.map(c => `<td${c.cls ? ` class="${c.cls}"` : ''}>${c.f(r)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}

function renderFreshness(st, generated) {
  const names = { pbp: 'Play-by-play', ftn: 'FTN charting', pfr_pass: 'PFR pressures', ngs_passing: 'Next Gen Stats' };
  return Object.entries(st).map(([k, v]) =>
    `<span class="pill ${v.pending ? 'q' : 'ok'}">${names[k] || k}: through Week ${v.through_week}${v.pending ? ' (waiting)' : ''}</span>`
  ).join(' ') + `<span class="meta">Built ${esc(generated.slice(0, 10))}</span>`;
}

function renderProtection(p, last, espn) {
  const sr = p.sack_rate, pr = p.pressure_rate, tt = p.time_to_throw, qf = p.qb_fault_sacks;
  const parts = [];
  // Headline answer, written from the numbers.
  const whom = [];
  if (sr) whom.push(`Burrow has been sacked on ${pct(sr.value)} of dropbacks (${sr.sacks} in ${sr.n}), ${rank(sr.rank)} in the NFL against a league rate of ${pct(sr.league)}.`);
  if (pr) whom.push(`Pressure on ${pct(pr.value)} of dropbacks through Week ${pr.through_week}, ${rank(pr.rank)}.`);
  if (tt) whom.push(`He holds the ball ${num(tt.value)} s on average, ${rank(tt.rank_fastest)} fastest, against ${num(tt.league)} s league-wide.`);
  if (qf) whom.push(`FTN charted ${qf.value} of ${qf.n} sacks as the QB's fault.`);
  if (espn) whom.push(`ESPN's pass block win rate: ${pct(espn.pass_block_win_rate.value)}, ${rank(espn.pass_block_win_rate.rank)} <a class="src" href="${esc(espn.url)}">ESPN, ${esc(espn.as_of)}</a>.`);
  const answer = whom.join(' ');

  const tiles = [];
  if (sr) tiles.push(tile('Sack rate', pct(sr.value), sr.rank, `league ${pct(sr.league)}`, sr.n, last?.sack_rate && `2025: ${pct(last.sack_rate.value)}, ${rank(last.sack_rate.rank)}`));
  if (pr) tiles.push(tile('Pressure rate', pct(pr.value), pr.rank, `league ${pct(pr.league)} · through Wk ${pr.through_week}`, pr.n, last?.pressure_rate && `2025: ${pct(last.pressure_rate.value)}, ${rank(last.pressure_rate.rank)}`));
  if (tt) tiles.push(tile('Time to throw', `${num(tt.value)} s`, tt.rank_fastest, `league ${num(tt.league)} s · rank = fastest`, tt.n, last?.time_to_throw && `2025: ${num(last.time_to_throw.value)} s`));
  if (qf) tiles.push(tile('QB-fault sacks', `${qf.value} of ${qf.n}`, null, 'FTN charting', qf.n, last?.qb_fault_sacks && `2025: ${last.qb_fault_sacks.value} of ${last.qb_fault_sacks.n}`));
  parts.push(`<div class="tiles">${tiles.join('')}</div>`);

  if (p.by_rushers) {
    const scale = { min: -0.6, max: 0.6, fmt: v => `${signed(v)} EPA` };
    parts.push(`<h3>EPA per dropback by number of pass rushers</h3><div class="bars">${p.by_rushers.map(b => bar(b.epa, null, scale, b.label, b.n)).join('')}</div>`);
  }
  if (p.weekly?.length) {
    parts.push(`<h3>Week by week</h3>` + weeklyTable(p.weekly, [
      { h: 'Wk', f: r => `${r.week} ${esc(r.opp)}` }, { h: 'Dropbacks', f: r => r.dropbacks },
      { h: 'Sacks', f: r => r.sacks }, { h: 'Pressures', f: r => r.pressures ?? '<span class="muted">–</span>' },
      { h: 'Blitzed', f: r => r.blitzed ?? '<span class="muted">–</span>' }, { h: 'Time to throw', f: r => r.time_to_throw == null ? '–' : `${num(r.time_to_throw)} s` },
      { h: 'EPA/play', f: r => signed(r.epa) },
    ]));
  }
  parts.push(`<p class="src-line">Sources: nflverse play-by-play, FTN charting, Pro Football Reference and Next Gen Stats via nflverse. "Pressures" and "Blitzed" show – where PFR has not posted that week yet.</p>`);
  return section('blame', 'Who is to blame for sacks?', answer, parts.join(''));
}

function tile(label, value, rk, sub, n, last) {
  return `<div class="tile${small(n)}"><span class="tile-label">${label}</span><span class="tile-value">${value} ${rank(rk)}</span><span class="tile-sub">${sub} · ${nTag(n)}</span>${last ? `<span class="tile-sub">${last}</span>` : ''}</div>`;
}

function renderRunPass(r, last) {
  const pa = r.play_action, npa = r.no_play_action, asr = r.after_successful_run, afr = r.after_failed_run, ap = r.after_pass;
  const bits = [];
  if (pa && npa) bits.push(`On play-action, Burrow averages ${signed(pa.epa)} EPA per dropback (${pa.n} plays, ${rank(pa.rank)} in the NFL) against ${signed(npa.epa)} without it (${npa.n}).`);
  if (asr && afr) bits.push(`Right after a successful run he averages ${signed(asr.epa)} (${asr.n}); after a failed run ${signed(afr.epa)} (${afr.n}); after a pass ${signed(ap.epa)} (${ap.n}).`);
  const gap = pa && npa && pa.epa != null && npa.epa != null ? pa.epa - npa.epa : null;
  if (gap != null) bits.push(gap > 0.1 ? 'The run fake is doing real work.' : gap < -0.1 ? 'Play-action has hurt more than helped so far.' : 'So far the fake changes little.');
  const scale = { min: -0.4, max: 0.8, fmt: v => `${signed(v)} EPA` };
  const bars = [];
  if (pa) bars.push(bar(pa.epa, pa.league, scale, 'Play-action', pa.n));
  if (npa) bars.push(bar(npa.epa, npa.league, scale, 'No play-action', npa.n));
  if (asr) bars.push(bar(asr.epa, asr.league, scale, 'After a successful run', asr.n));
  if (afr) bars.push(bar(afr.epa, afr.league, scale, 'After a failed run', afr.n));
  if (ap) bars.push(bar(ap.epa, null, scale, 'After a pass', ap.n));
  const parts = [`<div class="bars">${bars.join('')}</div><p class="legend">Tick = league average.</p>`];
  if (last?.play_action) parts.push(`<p class="muted">2025 season: play-action ${signed(last.play_action.epa)} (${last.play_action.n}), without ${signed(last.no_play_action.epa)} (${last.no_play_action.n}).</p>`);
  if (r.weekly?.length) parts.push(`<h3>Week by week</h3>` + weeklyTable(r.weekly, [
    { h: 'Wk', f: x => `${x.week} ${esc(x.opp)}` }, { h: 'Dropbacks', f: x => x.dropbacks }, { h: 'EPA/play', f: x => signed(x.epa) },
    { h: 'Play-action', f: x => x.pa_n == null ? '–' : `${x.pa_n}` }, { h: 'PA EPA/play', f: x => signed(x.pa_epa) },
  ]));
  parts.push(`<p class="src-line">Sources: nflverse play-by-play and FTN charting (play-action flag). "After a run" means the previous play on the same drive.</p>`);
  return section('runpass', 'Does the run set up the pass?', bits.join(' '), parts.join(''));
}

function renderAttack(off, oppDef, ownDef, nextOpp, last, espn) {
  const o = off.overall;
  const bits = [`Cincinnati's designed runs succeed ${pct(o.success)} of the time (${o.n} carries, ${rank(o.rank)}), ${num(o.ypc, 1)} yards a carry against a league ${pct(o.league_success)} and ${num(o.league_ypc, 1)}.`];
  if (espn) bits.push(`ESPN's run block win rate: ${pct(espn.run_block_win_rate.value)}, ${rank(espn.run_block_win_rate.rank)} <a class="src" href="${esc(espn.url)}">ESPN, ${esc(espn.as_of)}</a>.`);
  let best = null;
  if (oppDef && nextOpp.abbr) {
    const cands = oppDef.gaps.filter(g => g.n >= MIN_N && g.success != null && g.league_success != null).map(g => ({ ...g, over: g.success - g.league_success }));
    cands.sort((a, b) => b.over - a.over);
    best = cands[0];
    if (best) bits.push(`${esc(nextOpp.abbr)} (Week ${nextOpp.week}) allows a ${pct(best.success)} success rate at ${best.gap} (${best.n} carries), ${Math.round(best.over * 100)} points above league average there.`);
  }
  const scale = { min: 0, max: 0.8, fmt: v => pct(v) };
  const parts = [];
  parts.push(`<h3>Bengals runs by gap: success rate</h3><div class="bars">${off.gaps.map(g => bar(g.success, g.league_success, scale, g.gap, g.n, g.rank === 1 ? ' top' : '')).join('')}</div><p class="legend">Tick = league average for that gap.</p>`);
  if (oppDef && nextOpp.abbr) {
    parts.push(`<h3>What ${esc(nextOpp.abbr)}'s defence allows by gap</h3><div class="bars">${oppDef.gaps.map(g => bar(g.success, g.league_success, scale, g.gap, g.n, best && g.gap === best.gap ? ' top' : '')).join('')}</div>`);
  }
  parts.push(`<h3>And the Bengals' own run defence</h3><div class="bars">${ownDef.gaps.map(g => bar(g.success, g.league_success, scale, g.gap, g.n)).join('')}</div><p class="muted">Overall: ${pct(ownDef.overall.success)} allowed (${ownDef.overall.n} carries, ${rank(ownDef.overall.rank)}), ${num(ownDef.overall.ypc, 1)} a carry.</p>`);
  if (last?.offence_by_gap) parts.push(`<p class="muted">2025 season offence: ${pct(last.offence_by_gap.overall.success)} success (${last.offence_by_gap.overall.n} carries), ${num(last.offence_by_gap.overall.ypc, 1)} a carry.</p>`);
  if (off.weekly?.length) parts.push(`<h3>Week by week</h3>` + weeklyTable(off.weekly, [
    { h: 'Wk', f: x => `${x.week} ${esc(x.opp)}` }, { h: 'Carries', f: x => x.n }, { h: 'Success', f: x => pct(x.success) }, { h: 'Yards/carry', f: x => num(x.ypc, 1) },
  ]));
  parts.push(`<p class="src-line">Source: nflverse play-by-play, designed runs only (no scrambles). "Success" is a play with positive expected points added.</p>`);
  return section('attack', `Where to attack ${nextOpp.abbr ? esc(nextOpp.abbr) : 'next'}?`, bits.join(' '), parts.join(''));
}

async function main() {
  const el = document.getElementById('stats');
  try {
    const [line, espn] = await Promise.all([getJSON('data/stats/line.json'), getJSON('data/stats/espn-winrates.json').catch(() => null)]);
    document.getElementById('freshness').innerHTML = renderFreshness(line.status, line.generated);
    const last = line.last_season || {};
    el.innerHTML = [
      renderProtection(line.protection, last.protection, espn),
      renderRunPass(line.run_sets_up_pass, last.run_sets_up_pass),
      renderAttack(line.offence_by_gap, line.opponent_defence_by_gap, line.own_defence_by_gap, line.next_opponent, last, espn),
    ].join('');
  } catch (err) {
    el.innerHTML = `<p class="status">Couldn't load the stats (${esc(err.message)}). The pipeline may not have run yet.</p>`;
  }
}
main();
