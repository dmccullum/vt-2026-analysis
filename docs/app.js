// Vermont 2026 post-election report. Data: window.VT26 (scripts/build_viz.py), map: window.VT_MAP (from vt-needle).
(() => {
  const D = window.VT26, V = window.VT_MAP;
  const $ = (id) => document.getElementById(id);
  const NS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs = {}, parent, text) => {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    if (parent) parent.appendChild(n);
    return n;
  };
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const pct = (x, d = 1) => (x == null ? "–" : (100 * x).toFixed(d) + "%");
  const pts = (x, d = 1) => { if (x == null) return "–"; const v = +(100 * x).toFixed(d); return (v > 0 ? "+" : v < 0 ? "−" : "") + Math.abs(v).toFixed(d); };
  const margin = (r) => { const m = 100 * (2 * r - 1); return (m >= 0 ? "R+" : "D+") + Math.abs(m).toFixed(1); };
  const sideClass = (p) => (/^REP/i.test(p) ? "r" : /^PROG/i.test(p) ? "p" : /^DEM/i.test(p) ? "d" : "");
  const partyShort = (p) => ({ "REPUBLICAN": "R", "DEMOCRATIC": "D", "DEM/PROG": "D/P", "PROG/DEM": "P/D", "PROGRESSIVE": "P", "REP/DEM": "R/D", "INDEPENDENT": "I" }[p] || p);
  const pill = (p) => `<span class="pill ${sideClass(p)}">${partyShort(p)}</span>`;
  const seg = (id, cb) => $(id).addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    $(id).querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
    cb(b.dataset);
  });
  const pressed = (id) => $(id).querySelector('[aria-pressed="true"]').dataset;

  // ---------- tooltip
  const tip = $("tip");
  const showTip = (html, evt) => {
    tip.innerHTML = html; tip.style.display = "block";
    const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    let x = evt.pageX + pad, y = evt.pageY + pad;
    if (x + w > window.scrollX + innerWidth - 8) x = evt.pageX - w - pad;
    if (y + h > window.scrollY + innerHeight - 8) y = evt.pageY - h - pad;
    tip.style.left = x + "px"; tip.style.top = y + "px";
  };
  const hideTip = () => (tip.style.display = "none");
  const row = (k, v, cls = "") => `<div class="tt-r"><span>${k}</span><b class="${cls}">${v}</b></div>`;

  // ---------- derived numbers
  const S = D.statewide, gov = D.toplines.GOVERNOR;
  const scott = gov.find((c) => /SCOTT/.test(c.candidate)), janoo = gov.find((c) => /JANOO/.test(c.candidate));
  const hs = D.house.seats26, ss = D.senate.seats26, h24 = D.seats24.house, s24 = D.seats24.senate;
  const towns = D.towns.filter((t) => t.s26 != null && t.s24 != null);
  towns.forEach((t) => { t.swing = t.s24 - t.s26; t.janoo = 1 - t.s26; t.vsTicket = -t.x26; });
  const maxTownSwing = towns.reduce((a, t) => Math.max(a, t.swing), 0), minTownSwing = towns.reduce((a, t) => Math.min(a, t.swing), 1);
  const bins = (g) => D.bins[g];

  $("stamp").textContent = `Secretary of State unofficial results as of ${D.meta.sos_updated} (${D.meta.towns_reporting} towns). Analysis by town and House district.`;
  $("stats").innerHTML = [
    ["Governor", `<span class="r">Scott ${pct(scott.pct / 100)}</span>`, `Janoo ${pct(janoo.pct / 100)}`],
    ["Scott's change since 2024", `<span class="d">${pts(S.scott_R2_26 - S.scott_R2_24)} pts</span>`, `share of Scott–Dem. vote, from ${pct(S.scott_R2_24)}`],
    ["House", `<span class="d">${hs.L} Dem./Prog.</span> · <span class="r">${hs.R} Rep.</span>`, `was ${h24.L}–${h24.R}; ${hs.I} independents. Veto override needs 100`],
    ["Senate", `<span class="d">${ss.L} Dem./Prog.</span> · <span class="r">${ss.R} Rep.</span>`, `was ${s24.L}–${s24.R}${ss.I ? `; ${ss.I} independent` : ""}. Veto override needs 20`],
  ].map(([l, v, s]) => `<div class="stat"><div class="l">${l}</div><div class="v">${v}</div><div class="s">${s}</div></div>`).join("");

  // ---------- findings
  const tier = bins("tier"), ba = bins("ba_q"), inc = bins("inc_q");
  const closest = D.house.closest[0];
  const lostR = D.house.lost.filter((x) => /^REP/.test(x.party)).length;
  const progs = D.house.all.concat(D.senate.all).filter((c) => /^PROG/.test(c.party));
  const progWar = progs.reduce((a, c) => a + c.war, 0) / progs.length;
  const sp = D.split;
  const findings = [
    `<b>Scott won a sixth term by ${(scott.pct - janoo.pct).toFixed(1)} points</b>, down from ${(100 * (D.offices[0]["2024"].R - D.offices[0]["2024"].L)).toFixed(0)} in 2024. All ${towns.length} towns counted here moved toward the Democrat, by ${(100 * minTownSwing).toFixed(0)} to ${(100 * maxTownSwing).toFixed(0)} points.`,
    `<b>Scott's drop was much larger than other Republicans'.</b> The other Republicans running statewide fell by about 5 to 12 points, and the Republican share for U.S. House barely changed. Scott ran ${(100 * (S.scott_R2_24 - S.env_R2_24)).toFixed(0)} points ahead of the rest of the Republican ticket in 2024 and ${(100 * (S.scott_R2_26 - S.env_R2_26)).toFixed(0)} points ahead in 2026.`,
    `<b>Democrats and Progressives won two-thirds of both chambers</b>: ${hs.L} House seats (up from ${h24.L}) and ${ss.L} in the Senate (up from ${s24.L}), above the thresholds needed to override a veto. ${lostR} Republican House members who won in 2024 lost their seats.`,
    `<b>Many Scott voters also backed Democrats for the Legislature.</b> Scott carried ${sp.scott_districts} of ${sp.districts} House districts (down from ${sp.scott_districts_24}), and ${sp.scott_no_R} of those districts elected no Republican.`,
    D.eduinc && D.controls ? `<b>Janoo's support was strongest where education outpaces income.</b> Comparing each town's college share with what is typical for its income per person, her share rose from ${pct(D.eduinc.bins[0].janoo, 0)} in towns where education lags income to ${pct(D.eduinc.bins[4].janoo, 0)} where it most exceeds income, and her gain over the 2024 Democrat from ${pts(D.eduinc.bins[0].swing, 0)} to ${pts(D.eduinc.bins[4].swing, 0)}. This one measure accounts for ${Math.round(100 * D.eduinc.models.janoo.gap_r2)}% of the differences in her share across towns, compared with ${Math.round(100 * D.controls.models.janoo["Education only"].r2)}% for education alone, ${Math.round(100 * D.controls.models.janoo["Density only"].r2)}% for density, and ${Math.round(100 * D.controls.models.janoo["Income only"].r2)}% for income.` : "",
    `<b>Towns with more college graduates moved furthest toward Janoo.</b> Her gain over the 2024 Democrat ranged from ${pts(ba[0].swing_to_dem, 0)} in the least-educated fifth of towns to ${pts(ba[4].swing_to_dem, 0)} in the most. Comparing towns of the same density and income, education was the only one of the three with a clear effect on the size of the shift.`,
    `<b>Rural and urban towns moved by similar amounts.</b> Janoo gained ${pts(tier[0].swing_to_dem, 0)} over the 2024 Democrat in rural towns and ${pts(tier[3].swing_to_dem, 0)} in the most urban places. Among towns with similar education levels, density made little difference.`,
    D.controls ? `<b>Towns with more second homes moved less toward Janoo.</b> Comparing towns with similar education, income, density, age, and 2024 vote, each 10 points more seasonal housing meant about ${Math.abs(100 * D.controls.models.swing_lean["All three + age, second homes"].seas10.b).toFixed(1)} points less shift. In resort towns where most homes are seasonal, such as Killington, Winhall, Dover, and Warren, that adds up to roughly 4 points compared with a typical town.` : "",
    `<b>Scott kept more Democratic support in higher-income towns.</b> Janoo ran ${Math.abs(100 * inc[4].janoo_vs_ticket).toFixed(0)} points behind the rest of the Democratic ticket in the highest-income fifth of towns and ${Math.abs(100 * inc[0].janoo_vs_ticket).toFixed(0)} points behind in the lowest. That gap holds when comparing towns with the same education and density.`,
    D.schools ? `<b>School closures, small schools, and school tax increases showed no measurable link to the shift.</b> Towns with a closure voted or proposed moved ${Math.abs(100 * D.schools.models.swing["any_closure|controlled"].b).toFixed(1)} points more than comparable towns, within the margin of error, and towns with bigger school tax increases moved about the same as others. Towns with no public school of their own moved ${Math.abs(100 * D.schools.models.swing["no_school|controlled"].b).toFixed(1)} points less.` : "",
    `<b>Progressive-labeled legislative candidates ran behind expectations</b> (on average ${Math.abs(100 * progWar).toFixed(0)} points below expected, ${progs.length} candidates), while Democrats in comparable districts did not. The gap is clearest in Burlington and Montpelier.`,
    `<b>The closest House race was ${closest.district}</b>: ${closest.votes} votes separated the last winner from the first loser. Three towns (${D.meta.unreported.join(", ")}) had not reported yet, so Caledonia-2 and the Caledonia Senate seat are still provisional.`,
  ];
  $("findings").innerHTML = findings.filter(Boolean).map((f) => `<li>${f}</li>`).join("");
  $("x24").textContent = (100 * (S.scott_R2_24 - S.env_R2_24)).toFixed(0) + " points";
  $("x26").textContent = (100 * (S.scott_R2_26 - S.env_R2_26)).toFixed(0) + " points";

  // ---------- generic axis helpers
  const lin = (d0, d1, r0, r1) => (v) => r0 + ((v - d0) / (d1 - d0)) * (r1 - r0);
  const ticks = (a, b, n = 5) => {
    const step = Math.pow(10, Math.floor(Math.log10((b - a) / n))), err = ((b - a) / n) / step;
    const s = step * (err >= 7.5 ? 10 : err >= 3.5 ? 5 : err >= 1.5 ? 2 : 1);
    const out = []; for (let v = Math.ceil(a / s) * s; v <= b + 1e-9; v += s) out.push(+v.toFixed(10)); return out;
  };

  // ---------- offices dumbbell
  function renderOffices() {
    const svg = $("offices"), W = 760, rowH = 34, top = 24, L = 140, R = 30, H = top + D.offices.length * rowH + 10;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = "";
    const x = lin(0.2, 0.8, L, W - R);
    ticks(0.2, 0.8, 6).forEach((t) => { el("line", { x1: x(t), x2: x(t), y1: top - 6, y2: H - 6, class: t === 0.5 ? "zero" : "grid" }, svg); el("text", { x: x(t), y: 12, "text-anchor": "middle" }, svg, (100 * t).toFixed(0) + "%"); });
    D.offices.forEach((o, i) => {
      const y = top + i * rowH + rowH / 2, a = o["2024"].R, b = o["2026"].R, rep = css("--rep");
      el("text", { x: L - 12, y: y + 4, "text-anchor": "end", class: i === 0 ? "lab-strong" : "lab" }, svg, o.office);
      el("line", { x1: x(a), x2: x(b), y1: y, y2: y, stroke: rep, "stroke-width": 2, opacity: 0.45 }, svg);
      el("circle", { cx: x(a), cy: y, r: 5, fill: css("--panel"), stroke: rep, "stroke-width": 2 }, svg);
      el("circle", { cx: x(b), cy: y, r: 5.5, fill: rep, stroke: css("--panel"), "stroke-width": 2 }, svg);
      el("text", { x: Math.min(x(a), x(b)) - 10, y: y + 4, "text-anchor": "end" }, svg, pts(b - a) );
      const hit = el("rect", { x: 0, y: y - rowH / 2, width: W, height: rowH, fill: "transparent" }, svg);
      const c = (yr) => o[yr].cands.map((c) => row(`${c.name} <span class="pill ${sideClass(c.party)}">${partyShort(c.party)}</span>`, pct(c.pct))).join("");
      hit.addEventListener("mousemove", (e) => showTip(`<div class="tt-h"><b>${o.office}</b><span>R ${pct(a)} → ${pct(b)}</span></div><div class="tt-f" style="color:var(--muted);font-size:12px">2024</div>${c("2024")}<div class="tt-s" style="border-top:1px solid var(--line);margin-top:4px;padding-top:4px;color:var(--muted);font-size:12px">2026</div>${c("2026")}`, e));
      hit.addEventListener("mouseleave", hideTip);
    });
  }

  // ---------- map
  const mapPos = (t) => V.towns[t.n] || (t.n === "Essex Junction City" ? [V.towns["Essex"][0] + 6, V.towns["Essex"][1] + 4] : null);
  const arrowPath = (x, y, len, right) => {
    const a = (30 * Math.PI) / 180, dx = Math.cos(a) * len * (right ? 1 : -1), dy = -Math.sin(a) * len;
    const ex = x + dx, ey = y + dy, h = Math.min(4, 2 + len * 0.12), ux = dx / len, uy = dy / len;
    const bx = ex - ux * h * 1.6, by = ey - uy * h * 1.6;
    return { line: `M${x},${y}L${bx.toFixed(1)},${by.toFixed(1)}`, head: `M${ex.toFixed(1)},${ey.toFixed(1)}L${(bx - uy * h).toFixed(1)},${(by + ux * h).toFixed(1)}L${(bx + uy * h).toFixed(1)},${(by - ux * h).toFixed(1)}Z` };
  };
  let mapPts = [];
  function renderMap(mode) {
    const svg = $("map"); svg.setAttribute("viewBox", `-6 -6 ${V.w + 12} ${V.h + 12}`); svg.innerHTML = "";
    el("path", { d: V.state, class: "state" }, svg);
    V.counties.forEach((c) => el("path", { d: c.d, class: "county" }, svg));
    const g = el("g", {}, svg); mapPts = [];
    const val = (t) => (mode === "swing" ? -t.swing : mode === "res" ? t.res : t.x26);
    const vals = towns.map(val).filter((v) => v != null).map(Math.abs).sort((a, b) => a - b);
    const ref = vals[Math.floor(vals.length * 0.9)], k = (mode === "swing" ? 15 : 26) / ref;
    towns.slice().sort((a, b) => a.v - b.v).forEach((t) => {
      const p = mapPos(t); if (!p) return; const v = val(t); if (v == null) return;
      if (mode === "cross") {
        const r = Math.max(1.6, Math.min(7, Math.sqrt(t.v) / 9));
        el("circle", { cx: p[0], cy: p[1], r, fill: css("--rep"), opacity: Math.max(0.15, Math.min(1, v / ref)), stroke: css("--panel2"), "stroke-width": 0.6 }, g);
      } else {
        const len = Math.max(2.5, Math.min(44, Math.abs(v) * k)), ap = arrowPath(p[0], p[1], len, v > 0), col = css(v > 0 ? "--rep" : "--dem");
        const ag = el("g", { opacity: 0.85 }, g);
        el("path", { d: ap.line, stroke: col, "stroke-width": 1.4, "stroke-linecap": "round", fill: "none" }, ag);
        el("path", { d: ap.head, fill: col }, ag);
      }
      mapPts.push({ t, p });
    });
    const ring = el("circle", { r: 4.5, class: "ring", style: "display:none" }, svg);
    V.labels.forEach(([n, x, y]) => el("text", { x: x + 4, y: y - 3, class: "city" }, svg, n.replace(/ City$/, "")));
    $("mapNote").textContent = {
      swing: "Each arrow shows how far the town moved toward the Democrat since 2024; longer arrows mean bigger shifts. Every town moved toward the Democrat, so every arrow points left.",
      res: "Each town compared with what it would have done if it had followed the statewide shift. Red arrows pointing right: Scott held up better than expected. Blue arrows pointing left: he fell further than expected.",
      cross: "How far Scott ran ahead of the other Republicans on the ballot in each town. Darker dots mean a bigger gap (more voters splitting their ticket); larger dots mean more votes.",
    }[mode];
    svg.onmousemove = (e) => {
      const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY;
      const q = pt.matrixTransform(svg.getScreenCTM().inverse());
      let best = null, bd = 144;
      for (const m of mapPts) { const d = (m.p[0] - q.x) ** 2 + (m.p[1] - q.y) ** 2; if (d < bd) { bd = d; best = m; } }
      if (!best) { ring.style.display = "none"; return hideTip(); }
      ring.setAttribute("cx", best.p[0]); ring.setAttribute("cy", best.p[1]); ring.style.display = "";
      const t = best.t;
      showTip(`<div class="tt-h"><b>${t.n}</b><span>${t.c || ""}</span></div>${row("Scott 2026", pct(t.s26), "r")}${row("Scott 2024", pct(t.s24), "r")}${row("Change since 2024", pts(-t.swing) + " pts")}${row("vs. statewide trend", pts(t.res) + " pts")}${row("Scott vs. other Reps.", pts(t.x26) + " pts")}<div class="tt-s" style="border-top:1px solid var(--line);margin-top:4px;padding-top:4px"></div>${row("College degree", pct(t.ba, 0))}${row("Income per person", t.inc ? "$" + Math.round(t.inc / 1000) + "k" : "–")}${row("Votes", t.v.toLocaleString())}`, e);
    };
    svg.onmouseleave = () => { ring.style.display = "none"; hideTip(); };
  }
  function renderMovers() {
    const big = towns.filter((t) => t.v >= 400).sort((a, b) => b.swing - a.swing);
    const pick = big.slice(0, 6).concat(big.slice(-5).reverse());
    $("moverTable").innerHTML = `<tr><th class="l">Town</th><th>2024</th><th>2026</th><th>Change</th></tr>` +
      pick.map((t, i) => (i === 6 ? `<tr><td colspan="4" class="sub" style="padding-top:14px">Smallest swings</td></tr>` : "") +
        `<tr><td class="nm">${t.n}<div class="sub" style="font-weight:400">${t.c || ""}</div></td><td class="r">${pct(t.s24, 0)}</td><td class="r">${pct(t.s26, 0)}</td><td>${pts(-t.swing, 0)}</td></tr>`).join("");
    const strafford = towns.find((t) => t.n === "Strafford");
    $("mapLede").innerHTML = `Scott's biggest losses were in the Upper Valley and central Vermont: towns with many college graduates where many Democrats had voted for him before. In Strafford he went from ${pct(strafford.s24, 0)} to ${pct(strafford.s26, 0)}. He held up best in Essex, Franklin, and Rutland counties. Even so, the smallest swing anywhere was ${(100 * minTownSwing).toFixed(0)} points.`;
  }

  // ---------- Janoo by density, education, income
  function hbars(svgId, rows, metric, opts = {}) {
    const svg = $(svgId), W = 380, rowH = 26, L = Math.max(96, 8 + 6.2 * Math.max(...rows.map((r) => r.label.length))), R = 52, H = rows.length * rowH + 22;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = "";
    const isShare = metric === "janoo", vs = rows.map((r) => r.v);
    const lo = isShare ? 0 : Math.min(0, ...vs) * 1.08, hi = isShare ? 0.7 : Math.max(0, ...vs) * 1.08;
    const x = lin(lo, hi, L, W - R);
    if (isShare) el("line", { x1: x(0.5), x2: x(0.5), y1: 0, y2: H - 18, class: "grid", "stroke-dasharray": "3 3" }, svg);
    el("line", { x1: x(0), x2: x(0), y1: 0, y2: H - 18, class: "zero" }, svg);
    rows.forEach((r, i) => {
      const y = i * rowH + 4, col = r.color || css("--dem");
      el("text", { x: L - 8, y: y + 13, "text-anchor": "end", class: "lab" }, svg, r.label);
      const a = x(Math.min(0, r.v)), w = Math.abs(x(r.v) - x(0));
      el("rect", { x: a, y: y + 3, width: Math.max(1, w), height: 14, rx: 4, fill: col, opacity: r.dim ? 0.5 : 1 }, svg);
      el("text", { x: W - 2, y: y + 14, "text-anchor": "end", class: "lab" }, svg, isShare ? pct(r.v, 0) : pts(r.v));
      const hit = el("rect", { x: 0, y, width: W, height: rowH, fill: "transparent" }, svg);
      hit.addEventListener("mousemove", (e) => showTip(`<div class="tt-h"><b>${r.label}</b><span>${r.towns} towns</span></div>${row("Janoo share", pct(r.b.janoo))}${row("Charlestin (D) 2024", pct(r.b.dem_gov_24))}${row("Gain vs. 2024", pts(r.b.swing_to_dem) + " pts")}${row("Other Democrats 2026", pct(r.b.dem_ticket_26))}${row("Janoo vs. other Dems.", pts(r.b.janoo_vs_ticket) + " pts")}${row("Turnout", pct(r.b.turnout, 0))}${row("College degree", pct(r.b.ba, 0))}${row("Income per person", "$" + Math.round(r.b.inc / 1000) + "k")}`, e));
      hit.addEventListener("mouseleave", hideTip);
    });
    el("text", { x: W - R, y: H - 4, "text-anchor": "end", class: "axis-l" }, svg, opts.axis || "");
  }
  // ---------- education relative to income
  function renderEduInc() {
    const E = D.eduinc; if (!E) return;
    const svg = $("eiScatter"), W = 760, H = 400, L = 58, R = 16, T = 14, B = 40;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = "";
    const pts_ = towns.filter((t) => t.ba != null && t.inc && E.towns[t.n.toUpperCase().replace(/^ST\. /, "SAINT ").replace(/^ESSEX$/, "ESSEX TOWN")] !== undefined);
    const x = lin(0.1, 0.9, L, W - R), ly = (v) => Math.log(v), y = lin(ly(25000), ly(115000), H - B, T);
    [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9].forEach((v) => { el("line", { x1: x(v), x2: x(v), y1: T, y2: H - B, class: "grid" }, svg); el("text", { x: x(v), y: H - B + 16, "text-anchor": "middle" }, svg, (100 * v).toFixed(0) + "%"); });
    [25000, 30000, 40000, 50000, 60000, 75000, 90000, 115000].forEach((v) => { el("line", { x1: L, x2: W - R, y1: y(ly(v)), y2: y(ly(v)), class: "grid" }, svg); el("text", { x: L - 8, y: y(ly(v)) + 4, "text-anchor": "end" }, svg, "$" + v / 1000 + "k"); });
    el("text", { x: (L + W - R) / 2, y: H - 4, "text-anchor": "middle", class: "axis-l" }, svg, "Adults with a college degree");
    el("text", { x: 12, y: (T + H - B) / 2, "text-anchor": "middle", class: "axis-l", transform: `rotate(-90 12 ${(T + H - B) / 2})` }, svg, "Income per person");
    // typical-education line: ba = a + b ln(inc)  ->  ln(inc) = (ba - a)/b
    const { a, b } = E.fit, li = (ba) => (ba - a) / b;
    const x0 = 0.18, x1 = 0.72;
    el("line", { x1: x(x0), y1: y(li(x0)), x2: x(x1), y2: y(li(x1)), stroke: css("--muted"), "stroke-width": 1.5, "stroke-dasharray": "5 4" }, svg);
    el("text", { x: x(x1) + 6, y: y(li(x1)) + 14, "text-anchor": "start", class: "lab" }, svg, "typical for that income");
    el("text", { x: x(0.7), y: y(ly(28000)), "text-anchor": "middle", class: "axis-l" }, svg, "education outpaces income ↘");
    el("text", { x: x(0.22), y: y(ly(100000)), "text-anchor": "middle", class: "axis-l" }, svg, "↖ income outpaces education");
    const dem = css("--dem"), rep = css("--rep"), panel = css("--panel");
    pts_.sort((p, q) => q.v - p.v).forEach((t) => {
      const j = t.janoo, col = j >= 0.5 ? dem : rep, op = 0.25 + Math.min(1, Math.abs(j - 0.5) / 0.25) * 0.75;
      const c = el("circle", { cx: x(t.ba), cy: y(ly(t.inc)), r: Math.max(2.5, Math.min(14, Math.sqrt(t.v) / 7)), fill: col, "fill-opacity": op, stroke: panel, "stroke-width": 1 }, svg);
      c.addEventListener("mousemove", (e) => showTip(`<div class="tt-h"><b>${t.n}</b><span>${t.c || ""}</span></div>${row("Janoo", pct(t.janoo), "d")}${row("Scott", pct(t.s26), "r")}${row("Gain vs. 2024 Dem.", pts(t.swing) + " pts")}${row("College degree", pct(t.ba, 0))}${row("Income per person", "$" + Math.round(t.inc / 1000) + "k")}${row("Votes", t.v.toLocaleString())}`, e));
      c.addEventListener("mouseleave", hideTip);
    });
    $("eiLegend").innerHTML = `<span><i style="background:var(--dem);border-radius:50%"></i>Janoo won the town (darker = bigger margin)</span><span><i style="background:var(--rep);border-radius:50%"></i>Scott won the town</span><span>Dot size = votes cast</span>`;
    const bins = E.bins, M = E.models;
    $("eiLede").innerHTML = `Education was the demographic that best tracked Janoo's vote, and it mattered most relative to income. The dashed line marks the college share typical for a town's income; towns to its right have more graduates than their income would predict, led by ${E.bins[4].examples.slice(0, 2).join(", ")}, and ${E.bins[4].examples[2]}. Janoo's share rises from ${pct(E.bins[0].janoo, 0)} in towns furthest left of the line to ${pct(E.bins[4].janoo, 0)} furthest right. This one measure accounts for ${Math.round(100 * M.janoo.gap_r2)}% of the town-to-town differences in her share, more than education (${D.controls ? Math.round(100 * D.controls.models.janoo["Education only"].r2) : "–"}%), density (${D.controls ? Math.round(100 * D.controls.models.janoo["Density only"].r2) : "–"}%), or income (${D.controls ? Math.round(100 * D.controls.models.janoo["Income only"].r2) : "–"}%) alone. Income and density add little once education is accounted for: in the grid below, Janoo's share rises steadily with college graduates at every income level, but barely changes with income among towns with similar education.`;
  }
  function renderEduIncBars() {
    const E = D.eduinc; if (!E) return;
    const k = "janoo", names = ["Education well below income", "Somewhat below", "About typical", "Somewhat above", "Education well above income"];
    const rows = E.bins.map((b, i) => ({ label: names[i], v: b[k], towns: b.towns, b: { janoo: b.janoo, dem_gov_24: b.janoo - b.swing, swing_to_dem: b.swing, dem_ticket_26: b.janoo - b.vs_ticket, janoo_vs_ticket: b.vs_ticket, turnout: 0, ba: b.ba, inc: b.inc }, dim: false }));
    hbars("eiBars", rows, k === "swing" ? "swing_to_dem" : k === "vs_ticket" ? "janoo_vs_ticket" : "janoo", { axis: { janoo: "share of Scott–Janoo vote", swing: "points gained vs. 2024 Democrat", vs_ticket: "points vs. other Democrats" }[k] });
    const ex = E.bins.map((b, i) => `${names[i].toLowerCase()}: ${b.examples.slice(0, 3).join(", ")}`);
    $("eiNote").textContent = `Each group holds a fifth of the vote. Her gain over the 2024 Democrat rose across the same groups, from ${pts(E.bins[0].swing, 0)} to ${pts(E.bins[4].swing, 0)}. Largest towns in the lowest group: ${E.bins[0].examples.slice(0, 3).join(", ")}; in the highest: ${E.bins[4].examples.slice(0, 3).join(", ")}.`;
  }

  // ---------- schools
  function renderSchools() {
    const Sx = D.schools; if (!Sx) return;
    const st = Sx.status, M = Sx.models;
    $("schTable").innerHTML = `<tr><th class="l">Group</th><th>Towns</th><th>Scott 2024</th><th>Scott 2026</th><th>Shift to Janoo</th><th>vs. statewide trend</th></tr>` +
      Sx.order.map((k) => { const g = st[k]; return `<tr><td class="nm">${k}<div class="sub" style="font-weight:400">${g.examples.slice(0, 3).join(", ")}</div></td><td>${g.towns}</td><td class="r">${pct(g.scott24, 0)}</td><td class="r">${pct(g.scott26, 0)}</td><td>${pts(g.swing)}</td><td>${pts(g.res)}</td></tr>`; }).join("");
    const nEn = Sx.closure_towns.filter((c) => c.enacted).length, nAll = Sx.closure_towns.length;
    const rowsC = [["closure|controlled", `Closure voted or enacted (${nEn} towns)`], ["any_closure|controlled", `Closure voted or proposed (${nAll})`], ["small_school|controlled", "Has a school under 100 students"], ["I(adm_change*10)|controlled", "Student count down 10% since 2020"], ["no_school|controlled", "No public school in town"]];
    const TX = D.taxes;
    if (TX) { rowsC.push(["tax|dr_chg_25_27|controlled", "School tax rate rose 10% more, FY25–27"]); rowsC.push(["tax|dr_chg_26_27|controlled", "School tax rate rose 10% more, FY26–27"]); }
    $("schCtl").innerHTML = `<tr><th class="l">Towns where…</th><th>Extra shift</th></tr>` + rowsC.map(([k, l]) => {
      const e = k.startsWith("tax|") ? TX.models.swing[k.slice(4)] : M.swing[k], sig = e.lo > 0 || e.hi < 0, v = k.startsWith("I(adm") ? { ...e, b: -e.b, lo: -e.hi, hi: -e.lo } : e;
      return `<tr><td class="nm" style="font-weight:500">${l}</td><td style="${sig ? "" : "color:var(--muted)"}"><b style="font-weight:${sig ? 700 : 500}">${pts(v.b)}</b><div class="sub" style="text-align:right;font-size:11px">${pts(v.lo)} to ${pts(v.hi)}</div></td></tr>`;
    }).join("");
    $("schTowns").innerHTML = `<tr><th class="l">Town</th><th>2024</th><th>2026</th><th>vs. trend</th></tr>` +
      Sx.closure_towns.map((c) => `<tr><td class="nm">${c.town}${c.enacted ? "" : ' <span class="pill">proposed</span>'}<div class="sub" style="font-weight:400">${/pre-K/.test(c.school) ? c.school : c.school.replace(/ \(\d+\)/g, "").split(";")[0]}</div></td><td class="r">${pct(c.s24, 0)}</td><td class="r">${pct(c.s26, 0)}</td><td>${pts(c.res)}</td></tr>`).join("");
    const ns = M.swing["no_school|controlled"], cl = M.swing["any_closure|controlled"], sm = M.swing["small_school|controlled"];
    $("schLede").innerHTML = `The 2025 education law (Act 73) set minimum school sizes and encouraged consolidation, and several small schools closed or faced closure votes in 2025–26. If school changes affected the vote locally, towns with small or closing schools would show bigger shifts. They didn't, at least not measurably: towns with a closure voted or proposed shifted about ${Math.abs(100 * cl.b).toFixed(1)} points more than similar towns, within the margin of error, and towns with a school under 100 students moved about the same as similar towns. The one clear difference runs the other way: towns with no public school of their own, which mostly pay tuition for students to attend school elsewhere, shifted ${Math.abs(100 * ns.b).toFixed(1)} points <i>less</i> toward Janoo than comparable towns.`;
    $("schNote").textContent = `School data: Agency of Education Redistricting Task Force data files and NCES 2024–25 enrollment (${Sx.n_small} towns have a public school under 100 students). Closures are hand-coded from AOE's closure list and news reports and may be incomplete; Essex Junction and Greensboro are grade reconfigurations rather than closures, and Marlboro is left out because of its governor reporting error. The Task Force did not adopt a district map, and town-level tax rate changes were not available, so neither is tested. In the Vermont Public / VSU poll (Sept. 2026), 41% said lowering property taxes mattered more than keeping local schools, 28% said keeping schools, and 29% said both equally; the "property taxes" answer was more common among people without a college degree (51% with high school or less, 31% with a bachelor's or more). School tax rates are the equalized district rates from the Vermont Department of Taxes (FY2025–FY2027); across towns they rose ${D.taxes ? Math.round(100 * D.taxes.state.dr_chg_25_26) : "–"}% on average for FY2026 and changed ${D.taxes ? pts(D.taxes.state.dr_chg_26_27, 0) : "–"}% for FY2027. This town-level test can\'t detect effects that were spread evenly across the state, and statewide tax increases were.`;
  }

  // ---------- confounders: stratified grid + controlled estimates
  const GRID = {
    den3_ba3: { rows: ["Rural", "Small town", "Suburban/urban"], cols: ["Fewer grads", "Middle", "More grads"], rl: "Density", cl: "College graduates" },
    inc3_ba3: { rows: ["Lower income", "Middle", "Higher income"], cols: ["Fewer grads", "Middle", "More grads"], rl: "Income per person", cl: "College graduates" },
    den3_inc3: { rows: ["Rural", "Small town", "Suburban/urban"], cols: ["Lower income", "Middle", "Higher income"], rl: "Density", cl: "Income per person" },
  };
  const MET = { swing: ["Janoo's gain over the 2024 Democrat", (v) => pts(v)], janoo: ["Janoo's share", (v) => pct(v)], vs_ticket: ["Janoo vs. other Democrats", (v) => pts(v)] };
  function renderGrid() {
    const C = D.controls; if (!C) return;
    const gk = pressed("gridPair").g, mk = pressed("gridMetric").k, G = GRID[gk], cells = C.grids[gk];
    const svg = $("grid"), W = 440, L = 96, T = 40, cw = (W - L) / 3, ch = 64, H = T + 3 * ch + 8;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = "";
    const vals = Object.values(cells).map((c) => c[mk]), lo = Math.min(...vals), hi = Math.max(...vals);
    el("text", { x: L + 1.5 * cw, y: 12, "text-anchor": "middle", class: "axis-l" }, svg, G.cl + " →");
    el("text", { x: 4, y: 12, class: "axis-l" }, svg, G.rl + " ↓");
    G.cols.forEach((c, j) => el("text", { x: L + (j + 0.5) * cw, y: T - 10, "text-anchor": "middle", class: "lab" }, svg, c));
    const accent = css("--accent"), ink = css("--ink");
    G.rows.forEach((r, i) => {
      el("text", { x: L - 12, y: T + i * ch + ch / 2 + 4, "text-anchor": "end", class: "lab" }, svg, r);
      G.cols.forEach((c, j) => {
        const cell = cells[`${r}|${c}`]; if (!cell) return;
        const x = L + j * cw + 2, y = T + i * ch + 2, f = (cell[mk] - lo) / (hi - lo || 1), few = cell.towns < 5;
        el("rect", { x, y, width: cw - 4, height: ch - 4, rx: 8, fill: accent, "fill-opacity": few ? 0.05 : 0.08 + 0.55 * f, stroke: css("--line"), "stroke-dasharray": few ? "3 3" : "none" }, svg);
        el("text", { x: x + (cw - 4) / 2, y: y + 28, "text-anchor": "middle", style: `font:700 17px var(--display);fill:${ink}` }, svg, MET[mk][1](cell[mk]));
        el("text", { x: x + (cw - 4) / 2, y: y + 46, "text-anchor": "middle", style: "font-size:11px" }, svg, `${cell.towns} town${cell.towns === 1 ? "" : "s"}`);
        const hit = el("rect", { x, y, width: cw - 4, height: ch - 4, fill: "transparent" }, svg);
        hit.addEventListener("mousemove", (e) => showTip(`<div class="tt-h"><b>${r} · ${c}</b><span>${cell.towns} towns</span></div>${row("Janoo's share", pct(cell.janoo))}${row("Gain vs. 2024 Democrat", pts(cell.swing) + " pts")}${row("vs. other Democrats", pts(cell.vs_ticket) + " pts")}${row("College degree", pct(cell.ba, 0))}${row("Income per person", "$" + Math.round(cell.inc / 1000) + "k")}${row("People / sq mi", Math.round(cell.den).toLocaleString())}${row("Votes", cell.votes.toLocaleString())}`, e));
        hit.addEventListener("mouseleave", hideTip);
      });
    });
    const val = (r, c) => { const x = cells[`${r}|${c}`]; return x && x.towns >= 5 ? x[mk] : NaN; };  // skip cells with too few towns
    const colEff = G.rows.map((r) => val(r, G.cols[2]) - val(r, G.cols[0])).filter(Number.isFinite);
    const rowEff = G.cols.map((c) => val(G.rows[2], c) - val(G.rows[0], c)).filter(Number.isFinite);
    const avg = (a) => a.reduce((x, y) => x + y, 0) / a.length;
    const lc = (x) => x.toLowerCase();
    $("gridTitle").textContent = `${MET[mk][0]}, by ${lc(G.rl)} and ${lc(G.cl)}`;
    $("gridSpread").innerHTML = `Moving across a row (${lc(G.cl)}, lowest to highest group): <b>${pts(avg(colEff))} pts</b> on average. Moving down a column (${lc(G.rl)}, lowest to highest group): <b>${pts(avg(rowEff))} pts</b>. Cells with fewer than 5 towns are left out of these averages.`;
    $("gridNote").textContent = `Each cell is the vote-weighted average for its towns. Density groups: under 50, 50–200, and over 200 people per square mile. Education and income groups each hold a third of the vote. Darker cells are higher. Cells with fewer than 5 towns are dashed.`;
  }
  function renderControls() {
    const C = D.controls; if (!C) return;
    const spec = "All three + age, second homes", M = C.models;
    const vars = [["ba10", "College graduates +10 pts"], ["logden", "Density ×10"], ["inc10", "Income per person +$10k"], ["age10", "Median age +10 years"], ["seas10", "Second homes +10 pts"]];
    const cols = [["swing", "Gain vs. 2024 Dem."], ["swing_lean", "Gain, also matching 2024 vote"], ["janoo", "Janoo's share"], ["vs_ticket", "vs. other Democrats"]];
    const cellHtml = (e) => {
      const sig = e.lo > 0 || e.hi < 0;
      return `<td style="${sig ? "" : "color:var(--muted)"}"><b style="font-weight:${sig ? 700 : 500}">${pts(e.b)}</b><div class="sub" style="text-align:right;font-size:11px">${pts(e.lo)} to ${pts(e.hi)}</div></td>`;
    };
    $("ctlTable").innerHTML = `<tr><th class="l">Towns that differ by…</th>${cols.map(([, l]) => `<th>${l}</th>`).join("")}</tr>` +
      vars.map(([v, l]) => `<tr><td class="nm">${l}</td>${cols.map(([k]) => cellHtml(M[k][spec][v])).join("")}</tr>`).join("");
    const s = M.swing[spec], t = M.vs_ticket[spec], g = C.grids.den3_ba3;
    const f1 = (x) => pts(x, 1);
  }

  // ---------- over time
  function renderOvertime() {
    const gk = pressed("otGroup").g, arr = bins(gk), years = [2016, 2018, 2020, 2022, 2024, 2026];
    const keys = ["dem_gov_16", "dem_gov_18", "dem_gov_20", "dem_gov_22", "dem_gov_24", "janoo"];
    const cols = gk === "ba_q" ? ["--q1", "--q2", "--q3", "--q4", "--q5"] : ["--q1", "--q2", "--q4", "--q5"];
    const names = gk === "ba_q" ? ["Fewest grads", "Fewer grads", "Middle", "More grads", "Most grads"] : ["Rural", "Small town", "Suburban", "Urban"];
    const svg = $("overtime"), W = 760, H = 320, L = 44, R = 110, T = 14, B = 30;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = "";
    const x = lin(2016, 2026, L, W - R), y = lin(0.1, 0.65, H - B, T);
    ticks(0.1, 0.65, 6).forEach((v) => { el("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), class: v === 0.5 ? "zero" : "grid" }, svg); el("text", { x: L - 8, y: y(v) + 4, "text-anchor": "end" }, svg, (100 * v).toFixed(0) + "%"); });
    const cand = { 2016: "Minter", 2018: "Hallquist", 2020: "Zuckerman", 2022: "Siegel", 2024: "Charlestin", 2026: "Janoo" };
    years.forEach((yr) => { el("text", { x: x(yr), y: H - B + 16, "text-anchor": "middle" }, svg, yr); el("text", { x: x(yr), y: H - 2, "text-anchor": "middle", style: "font-size:10px" }, svg, cand[yr]); });
    const labelYs = [];
    arr.forEach((b, i) => {
      const c = css(cols[i]), d = keys.map((k, j) => `${j ? "L" : "M"}${x(years[j]).toFixed(1)},${y(b[k]).toFixed(1)}`).join("");
      el("path", { d, fill: "none", stroke: c, "stroke-width": 2, "stroke-linejoin": "round" }, svg);
      keys.forEach((k, j) => el("circle", { cx: x(years[j]), cy: y(b[k]), r: 3, fill: c, stroke: css("--panel"), "stroke-width": 1.5 }, svg));
      labelYs.push({ y: y(b.janoo), name: names[i] });
    });
    labelYs.sort((a, b) => a.y - b.y).forEach((l, i, a) => { if (i && l.y - a[i - 1].y < 13) l.y = a[i - 1].y + 13; el("text", { x: W - R + 10, y: l.y + 4, class: "lab" }, svg, l.name); });
    const cross = el("line", { y1: T, y2: H - B, class: "zero", style: "display:none" }, svg);
    const hit = el("rect", { x: L, y: T, width: W - R - L, height: H - B - T, fill: "transparent" }, svg);
    hit.addEventListener("mousemove", (e) => {
      const pt = svg.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY; const q = pt.matrixTransform(svg.getScreenCTM().inverse());
      const j = Math.max(0, Math.min(5, Math.round((q.x - L) / ((W - R - L) / 5))));
      cross.setAttribute("x1", x(years[j])); cross.setAttribute("x2", x(years[j])); cross.style.display = "";
      showTip(`<div class="tt-h"><b>${years[j]}</b><span>Dem. governor share</span></div>` + arr.map((b, i) => row(`<i style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${css(cols[i])};margin-right:6px"></i>${names[i]}`, pct(b[keys[j]]))).reverse().join("") + (j === 5 || j === 4 ? `<div style="color:var(--muted);font-size:12px;margin-top:4px">Harris 2024: ${pct(arr[0].harris_24, 0)} → ${pct(arr[arr.length - 1].harris_24, 0)}</div>` : ""), e);
    });
    hit.addEventListener("mouseleave", () => { cross.style.display = "none"; hideTip(); });
    const gap = (k) => arr[arr.length - 1][k] - arr[0][k];
    $("otLegend").innerHTML = names.map((n, i) => `<span><i style="background:var(${cols[i]})"></i>${n}</span>`).join("") +
      `<span style="margin-left:auto">Gap between top and bottom groups: 2016 ${pts(gap("dem_gov_16"), 0)} · 2024 ${pts(gap("dem_gov_24"), 0)} · 2026 ${pts(gap("janoo"), 0)} · Harris ${pts(gap("harris_24"), 0)}</span>`;
  }

  // ---------- governor vs statehouse strip
  function renderStrip() {
    const svg = $("strip"), W = 760, H = 150, L = 20, R = 20;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = "";
    const x = lin(0.15, 0.85, L, W - R), base = 100;
    ticks(0.2, 0.8, 6).forEach((v) => { el("line", { x1: x(v), x2: x(v), y1: 8, y2: base + 6, class: v === 0.5 ? "zero" : "grid" }, svg); el("text", { x: x(v), y: base + 22, "text-anchor": "middle" }, svg, (100 * v).toFixed(0) + "%"); });
    el("text", { x: x(0.5) + 6, y: 18, class: "axis-l" }, svg, "Scott wins →");
    el("text", { x: (L + W - R) / 2, y: H - 4, "text-anchor": "middle", class: "axis-l" }, svg, "Scott's share of the Scott–Janoo vote in the district");
    const ds = D.hdist.filter((d) => d.gov != null).sort((a, b) => a.gov - b.gov), bucket = {};
    ds.forEach((d) => {
      const bx = Math.round(x(d.gov) / 9); bucket[bx] = (bucket[bx] || 0) + 1;
      const cy = base - 6 - (bucket[bx] - 1) * 9;
      const col = d.R === 0 && d.I === 0 ? "--dem" : d.L === 0 && d.I === 0 ? "--rep" : "--ind";
      const c = el("circle", { cx: bx * 9, cy, r: 4, fill: css(col), stroke: css("--panel"), "stroke-width": 1 }, svg);
      c.addEventListener("mousemove", (e) => showTip(`<div class="tt-h"><b>${d.d}</b></div>${row("Scott 2026", pct(d.gov), "r")}${row("Scott 2024", pct(d.gov24), "r")}${row("Other Republicans", pct(d.env), "r")}${row("Seats 2026", `${d.L} Dem./Prog. · ${d.R} Rep.${d.I ? " · " + d.I + " I" : ""}`)}${row("Seats 2024", `${d.L24} Dem./Prog. · ${d.R24} Rep.`)}`, e));
      c.addEventListener("mouseleave", hideTip);
    });
    const sp = D.split;
    $("splitLede").innerHTML = `In 2024 Scott carried ${sp.scott_districts_24} of ${sp.districts} House districts. This year he carried ${sp.scott_districts}. Democrats or Progressives won ${sp.L_seats_in_scott} of the ${sp.L_seats_in_scott + sp.R_seats_in_scott} seats in the districts he carried, and ${sp.scott_no_R} of those districts elected no Republican at all. The House chart below shows the same pattern over a longer span: Vermont has often elected Republican governors alongside Democratic legislatures.`;
  }
  function renderHistory() {
    const H0 = D.history; if (!H0) return;
    const hs26 = D.house.seats26, ss26 = D.senate.seats26;
    // 2026 from this analysis; Prog-first labels counted as P to match the history table
    const rows = H0.map((h) => ({ y: h.year, hD: h.house_D, hR: h.house_R, hP: h.house_P, hI: (h.house_I || 0) + (h.house_other || 0), gR: h.gov_R_pct, w: h.gov_winner }));
    rows.push({ y: 2026, hD: hs26.L - hs26.P, hR: hs26.R, hP: hs26.P, hI: hs26.I, gR: scott.pct, w: "Scott" });
    const wrap = $("histWrap");
    wrap.innerHTML = `<div class="card chart" style="margin-top:12px"><h3>House seats won, 2000–2026</h3><svg id="hist"></svg><div class="legendrow"><span><i style="background:var(--dem)"></i>Democratic</span><span><i style="background:var(--prog)"></i>Progressive</span><span><i style="background:var(--ind)"></i>Independent / other</span><span><i style="background:var(--rep)"></i>Republican</span></div></div>
      <div class="card chart" style="margin-top:12px"><h3>Republican share of the governor's vote, same years</h3><svg id="histGov"></svg></div>
      <details class="src"><summary>Sources and notes</summary><p class="note">Seat counts before 2026 were compiled from Wikipedia, the Vermont party-strength table, and Ballotpedia (some years come from a single source). Legislators with fusion labels are counted under their first-listed party. The 2026 numbers come from this analysis and are unofficial.</p></details>`;
    const svg = $("hist"), W = 760, Hh = 220, L = 34, R = 78, T = 8, B = 22, n = rows.length, bw = (W - L - R) / n;
    svg.setAttribute("viewBox", `0 0 ${W} ${Hh}`);
    const y = lin(0, 150, Hh - B, T);
    [0, 50, 100, 150].forEach((v) => { el("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), class: "grid" }, svg); el("text", { x: L - 6, y: y(v) + 4, "text-anchor": "end" }, svg, v); });
    rows.forEach((r, i) => {
      const x0 = L + i * bw + 3, w = bw - 6; let acc = 0;
      el("text", { x: x0 + w / 2, y: Hh - 6, "text-anchor": "middle", style: r.y === 2026 ? "font-weight:700;fill:var(--ink)" : "" }, svg, String(r.y).slice(2) === "00" ? "2000" : "'" + String(r.y).slice(2));
      if (r.hD == null) { el("text", { x: x0 + w / 2, y: y(70), "text-anchor": "middle" }, svg, "n/a"); return; }
      [["hD", "--dem"], ["hP", "--prog"], ["hI", "--ind"], ["hR", "--rep"]].forEach(([k, c]) => {
        const v = r[k] || 0; if (!v) return;
        el("rect", { x: x0, y: y(acc + v) + 1, width: w, height: Math.max(0, y(acc) - y(acc + v) - 2), fill: css(c), rx: 2 }, svg); acc += v;
      });
      const hit = el("rect", { x: x0 - 3, y: T, width: bw, height: Hh - B - T, fill: "transparent" }, svg);
      hit.addEventListener("mousemove", (e) => showTip(`<div class="tt-h"><b>${r.y}</b><span>Gov: ${r.w}</span></div>${row("Democratic", r.hD, "d")}${row("Progressive", r.hP || 0, "p")}${row("Independent / other", r.hI || 0)}${row("Republican", r.hR, "r")}${row("Gov. R share", r.gR != null ? r.gR.toFixed(1) + "%" : "–", "r")}`, e));
      hit.addEventListener("mouseleave", hideTip);
    });
    // two-thirds threshold drawn over the bars, labeled in the right margin
    el("line", { x1: L, x2: W - R + 4, y1: y(100), y2: y(100), stroke: css("--ink"), "stroke-width": 1.25, "stroke-dasharray": "4 3", "pointer-events": "none" }, svg);
    el("text", { x: W - R + 8, y: y(100) - 2, class: "axis-l" }, svg, "Two-thirds");
    el("text", { x: W - R + 8, y: y(100) + 11, style: "font-size:10px" }, svg, "100 seats");
    const g = $("histGov"), Hg = 120; g.setAttribute("viewBox", `0 0 ${W} ${Hg}`);
    const yg = lin(20, 80, Hg - 18, 8);
    [20, 50, 80].forEach((v) => { el("line", { x1: L, x2: W - R, y1: yg(v), y2: yg(v), class: v === 50 ? "zero" : "grid" }, g); el("text", { x: L - 6, y: yg(v) + 4, "text-anchor": "end" }, g, v + "%"); });
    const pts2 = rows.map((r, i) => [L + i * bw + bw / 2, r.gR]).filter((p) => p[1] != null);
    el("path", { d: pts2.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${yg(p[1]).toFixed(1)}`).join(""), fill: "none", stroke: css("--rep"), "stroke-width": 2 }, g);
    pts2.forEach((p) => el("circle", { cx: p[0], cy: yg(p[1]), r: 3.5, fill: css("--rep"), stroke: css("--panel"), "stroke-width": 1.5 }, g));
    rows.forEach((r, i) => el("text", { x: L + i * bw + bw / 2, y: Hg - 2, "text-anchor": "middle" }, g, "'" + String(r.y).slice(2)));
  }

  // ---------- WAR tables
  let warExpanded = false;
  function renderWar() {
    const lvl = pressed("warLevel").l, sd = pressed("warSide").s, L = D[lvl];
    const ranked = L.all.filter((c) => (sd === "top" ? c.war >= 0.0005 : c.war <= -0.0005))  /* at least ±0.1 pts as displayed */.sort((a, b) => (sd === "top" ? b.war - a.war : a.war - b.war));
    const all = warExpanded ? ranked : ranked.slice(0, 12);
    $("warMore").textContent = warExpanded ? "Show top 12" : `Show all ${ranked.length} ${sd === "top" ? "above" : "below"} expectations`;
    $("warMore").style.display = ranked.length > 12 ? "" : "none";
    const mx = Math.max(...L.all.map((c) => Math.abs(c.war)));
    $("warTable").innerHTML = `<tr><th class="l">Candidate</th><th class="l">District</th><th>% of voters</th><th>Expected</th><th>Above expected</th><th class="l"></th></tr>` +
      all.map((c) => {
        const w = (Math.abs(c.war) / mx) * 50, col = c.war >= 0 ? "var(--accent)" : "var(--muted)";
        return `<tr><td class="nm">${c.candidate} ${pill(c.party)}${c.incumbent ? ' <span class="pill">inc.</span>' : ""}${c.incomplete ? ' <span class="pill warn">incomplete</span>' : ""}</td><td class="sub">${c.district}${c.vote_for > 1 ? ` · ${c.vote_for} seats` : ""}${c.won ? "" : " · lost"}</td><td>${pct(c.share)}</td><td>${pct(c.expected)}</td><td><b>${pts(c.war)}</b></td><td><div class="barcell"><div class="z"></div><div class="b" style="background:${col};${c.war >= 0 ? `left:50%;width:${w}%` : `right:50%;width:${w}%`}"></div></div></td></tr>`;
      }).join("");
    const m = L.model;
    $("warNote").textContent = `${lvl === "house" ? "House" : "Senate"}: ${m.n} candidates in contested races were modeled${m.parts.single ? ", with one-seat and multi-seat races modeled separately" : ""}; ${L.all.length} are listed, leaving out races with an independent candidate or more same-party candidates than seats. The model explains ${Math.round(100 * m.r2)}% of the variation, and being an incumbent was worth about ${pts(m.incumbent)} points. "% of voters" is the share of the district's voters who voted for the candidate. In districts with two or three seats, voters can pick more than one candidate, so a candidate can run well ahead of expectations, with support from many voters who backed the other party's candidates too, and still finish out of the running. Differences under about 3 points are within normal variation.`;
    $("mHn").textContent = D.house.model.n; $("mHr").textContent = D.house.model.r2; $("mSn").textContent = D.senate.model.n; $("mSr").textContent = D.senate.model.r2;
  }
  function renderLostClose() {
    $("lostTable").innerHTML = `<tr><th class="l">Member</th><th class="l">District</th><th>% of voters</th></tr>` +
      D.house.lost.concat(D.senate.lost.map((x) => ({ ...x, district: x.district + " (Sen.)" }))).map((x) => `<tr><td class="nm">${x.candidate} ${pill(x.party)}</td><td class="sub">${x.district}${x.seats > 1 ? ` · ${x.seats} seats, finished ${["", "1st", "2nd", "3rd", "4th", "5th", "6th"][x.place] || x.place + "th"}` : ""}</td><td>${pct(x.share)}</td></tr>`).join("");
    $("closeTable").innerHTML = `<tr><th class="l">District</th><th class="l">Last in / first out</th><th>Votes</th></tr>` +
      D.house.closest.slice(0, 8).map((c) => `<tr><td class="nm">${c.district}${c.incomplete ? ' <span class="pill warn">incomplete</span>' : ""}</td><td class="sub">${c.winner} ${pill(c.wparty)} over ${c.loser} ${pill(c.lparty)}</td><td>${c.votes}</td></tr>`).join("");
    $("mSos").textContent = D.meta.sos_updated; $("mTowns").textContent = D.meta.towns_reporting;
  }

  // ---------- wire up
  const renderAll = () => { renderOffices(); renderMap(pressed("mapMode").m); renderEduInc(); renderEduIncBars(); renderGrid(); renderControls(); renderSchools(); renderOvertime(); renderStrip(); renderHistory(); renderWar(); };
  seg("mapMode", (d) => renderMap(d.m)); seg("gridPair", renderGrid); seg("gridMetric", renderGrid);
   seg("otGroup", renderOvertime); seg("warLevel", renderWar); $("warMore").addEventListener("click", () => { warExpanded = !warExpanded; renderWar(); if (!warExpanded) $("warTable").scrollIntoView({ block: "nearest" }); }); seg("warSide", renderWar);
  
  $("theme").addEventListener("click", () => {
    const cur = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = cur === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = next;
    try { localStorage.setItem("vt-theme", next); } catch (e) {}
    renderAll();
  });
  renderMovers(); renderLostClose(); renderAll();
})();
