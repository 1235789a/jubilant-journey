const pages = [
  ["overview", "OV", "Overview"], ["assets", "AS", "Assets"], ["verticals", "VT", "Verticals"], ["platforms", "PL", "Platforms"],
  ["accounts", "AC", "Accounts"], ["jobs", "JB", "Jobs"], ["publications", "PB", "Publications"],
  ["analytics", "AN", "Analytics"], ["experiments", "EX", "Experiments"], ["human-queue", "HQ", "Human Queue"],
  ["rules", "RU", "Rules"], ["health", "HL", "Health"], ["logs", "LG", "Logs"], ["settings", "ST", "Settings"]
];
const nav = document.querySelector("#nav");
const content = document.querySelector("#content");
const title = document.querySelector("#page-title");
const state = { page: location.hash.slice(1) || "overview" };

for (const [id, icon, label] of pages) {
  const button = document.createElement("button");
  button.className = "nav-item";
  button.dataset.page = id;
  button.innerHTML = `<span class="nav-icon">${icon}</span><span>${label}</span>`;
  button.addEventListener("click", () => { location.hash = id; });
  nav.append(button);
}

const esc = value => String(value ?? "—").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const num = value => new Intl.NumberFormat("en", { maximumFractionDigits: 2 }).format(Number(value || 0));
const badge = value => `<span class="badge ${esc(value)}">${esc(value)}</span>`;
const short = value => {
  if (value === null || value === undefined || value === "") return "—";
  if (Array.isArray(value)) return value.map(v => esc(v)).join(", ");
  if (typeof value === "object") return `<span class="mono json" title="${esc(JSON.stringify(value))}">${esc(JSON.stringify(value))}</span>`;
  return esc(value);
};

async function get(path) {
  const response = await fetch(`/api/${path}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
}

function table(rows, columns) {
  if (!rows?.length) return document.querySelector("#empty-template").innerHTML;
  return `<div class="panel table-wrap"><table><thead><tr>${columns.map(([,label]) => `<th>${esc(label)}</th>`).join("")}</tr></thead><tbody>${rows.map(row => `<tr>${columns.map(([key,,render]) => `<td>${render ? render(row[key], row) : short(row[key])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function stat(label, value, note, accent) {
  return `<article class="stat" style="--accent:${accent}"><div class="stat-label">${esc(label)}</div><div class="stat-value">${esc(value)}</div><div class="stat-note">${esc(note)}</div></article>`;
}

async function renderOverview() {
  const data = await get("overview");
  const p2 = (await get("platforms")).filter(item => item.adapter_maturity === "P2").length;
  const jobs = data.jobs;
  document.querySelector("#safety-banner").innerHTML = `<strong>Fail-closed:</strong> package generation is active; every public upload, identity step, payment, contract and final submission is locked.`;
  content.innerHTML = `
    <div class="grid stat-grid">
      ${stat("Active assets", data.counts.active_assets, `${data.counts.assets} registered`, "#6ee7d2")}
      ${stat("Platforms", data.counts.platforms, `${data.counts.verticals} verticals · ${p2} P2`, "#75a7ff")}
      ${stat("Jobs today", data.jobs_today, `${jobs.SUCCESS || 0} successful`, "#8a7cff")}
      ${stat("Human required", data.counts.human_required, "L0 review queue", "#f7c66a")}
      ${stat("Publications", data.counts.publications, "local packages only", "#6ee7d2")}
      ${stat("Failed / blocked", (jobs.FAILED || 0) + (jobs.BLOCKED || 0) + (jobs.DEAD_LETTER || 0), "platform-isolated", "#ff727b")}
      ${stat("Total tokens", num(data.tokens.total_tokens), "instrumentation active", "#75a7ff")}
      ${stat("Revenue", `$${num(data.analytics.revenue)}`, "mock data excluded from claims", "#76e6a8")}
    </div>
    <div class="grid two-col">
      <section class="panel"><div class="panel-head"><h2>Recent jobs</h2><span>Newest first</span></div>${table(data.recent_jobs, [
        ["job_type","Job"], ["platform_id","Platform"], ["asset_id","Asset"], ["status","Status",badge], ["output_url","Output"]
      ]).replace('class="panel table-wrap"','class="table-wrap"')}</section>
      <section class="panel"><div class="panel-head"><h2>Today needs you</h2><span>${data.human_queue.length} shown</span></div><div class="panel-body task-list">${data.human_queue.length ? data.human_queue.map(item => `<div class="task"><strong>${esc(item.action)}</strong><p>${esc(item.platform_id)} · ${esc(item.reason)}</p></div>`).join("") : `<div class="empty">No pending review.</div>`}</div></section>
    </div>
    <section class="panel section-gap"><div class="panel-head"><h2>Adapter maturity coverage</h2><span>No P3 live adapters</span></div><div class="panel-body coverage">
      <div><strong>${data.counts.platforms - p2}</strong><span>P0 · REGISTRY</span></div><div><strong>0</strong><span>P1 · PACKAGE</span></div><div><strong>${p2}</strong><span>P2 · DRY RUN</span></div><div><strong>0</strong><span>P3 · LIVE</span></div>
    </div></section>`;
}

const pageConfig = {
  assets: ["assets", [["name","Asset"],["vertical_id","Vertical"],["status","Status",badge],["master_version","Version"],["distribution_mode","Mode",badge],["quality_score","Quality"],["yield_score","Yield"],["priority","Priority"]]],
  verticals: ["verticals", [["name","Vertical"],["vertical_id","ID"],["status","State",badge],["evaluated_score","Score"],["priority","Priority",badge],["pilot_limit","Pilot cap"],["scores","Components"]]],
  platforms: ["platforms", [["platform_name","Platform"],["verticals_supported","Verticals"],["adapter_maturity","Maturity",badge],["rule_status","Rules",badge],["natural_traffic_score","Traffic"],["age_requirement","Age"],["live_publish","Live"],["last_verified_at","Verified"]]],
  accounts: ["accounts", [["brand_name","Brand"],["platform_id","Platform"],["account_type","Type"],["age_status","Age"],["status","Status",badge],["health_status","Health",badge],["payout_ready","Payout"],["credential_reference","Credential ref"]]],
  jobs: ["jobs", [["created_at","Created"],["job_type","Type"],["platform_id","Platform"],["asset_id","Asset"],["status","Status",badge],["retry_count","Retries"],["token_usage","Tokens"],["output_url","Output"],["error","Error"]]],
  publications: ["publications", [["created_at","Created"],["asset_id","Asset"],["platform_id","Platform"],["status","Status",badge],["mode","Mode",badge],["asset_version","Version"],["adapter_version","Adapter"],["output_url","Local package"]]],
  experiments: ["experiments", [["experiment_id","Experiment"],["vertical","Vertical"],["platform","Platforms"],["hypothesis","Hypothesis"],["token_budget","Token budget"],["time_budget","Minutes"],["money_budget","Money"],["decision","Decision",badge]]],
  "human-queue": ["human-queue", [["created_at","Created"],["action","Action"],["platform_id","Platform"],["asset_id","Asset"],["risk_level","Risk",badge],["status","Status",badge],["reason","Reason"]]],
  rules: ["rules", [["platform_name","Platform"],["rule_status","Status",badge],["rule_version","Version"],["last_verified_at","Verified"],["age_requirement","Age"],["guardian_supported","Guardian"],["exclusivity_rules","Exclusivity"],["ai_content_policy","AI policy"],["automation_policy","Automation"]]],
  logs: ["logs", [["timestamp","Time"],["actor","Who"],["action","What"],["target_type","Target"],["target_id","ID"],["reason","Why"],["token_usage","Tokens"],["result","Result",badge]]]
};

async function renderAnalytics() {
  const data = await get("analytics");
  const a = data.aggregate, t = data.tokens;
  content.innerHTML = `${data.mock_data_present ? '<div class="notice">Demo metrics are present and explicitly marked MOCK. They are not real platform performance.</div>' : ''}
    <div class="panel"><div class="panel-head"><h2>Portfolio metrics</h2><span>Unified nullable schema</span></div><div class="panel-body metric-grid">
      ${Object.entries({Impressions:a.impressions,Views:a.views,Clicks:a.clicks,Downloads:a.downloads,Installs:a.installs,"Active users":a.active_users,Revenue:`$${num(a.revenue)}`,Cost:`$${num(a.cost)}`,"Human minutes":a.human_minutes}).map(([k,v]) => `<div class="metric"><span>${esc(k)}</span><strong>${typeof v === 'number' ? num(v) : esc(v)}</strong></div>`).join("")}
    </div></div><div class="section-gap">${table(data.metrics, [["timestamp","Time"],["asset_id","Asset"],["platform_id","Platform"],["source","Source",badge],["impressions","Impressions"],["views","Views"],["installs","Installs"],["downloads","Downloads"],["revenue","Revenue"],["human_minutes","Human min"]])}</div>`;
}

async function renderHealth() {
  const data = await get("health");
  content.innerHTML = `<div class="grid stat-grid">${stat("Healthy",data.healthy,`of ${data.total} platforms`,"#76e6a8")}${stat("Action required",data.summary.ACTION_REQUIRED || 0,"rule or account review","#f7c66a")}${stat("Broken",data.summary.BROKEN || 0,"isolated by platform","#ff727b")}${stat("Failed jobs",data.failed_jobs,"includes blocked and DLQ","#ff727b")}</div><div class="section-gap">${table(data.platforms, [["platform_name","Platform"],["status","Health",badge],["adapter_maturity","Adapter",badge],["circuit","Circuit",badge],["last_verified_at","Rule checked"],["reasons","Reasons"]])}</div>`;
}

async function renderSettings() {
  const data = await get("settings");
  content.innerHTML = `<section class="panel"><div class="panel-head"><h2>Safety and runtime settings</h2><span>Live enable is intentionally unavailable</span></div><div class="panel-body metric-grid">${Object.entries(data).filter(([,v]) => typeof v !== 'object').map(([k,v]) => `<div class="metric"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join("")}</div></section><section class="panel section-gap"><div class="panel-head"><h2>Registered adapters</h2><span>P2 package builders</span></div>${table(Object.entries(data.adapter_coverage).map(([platform,value]) => ({platform,...value})), [["platform","Platform"],["name","Adapter"],["version","Version"]]).replace('class="panel table-wrap"','class="table-wrap"')}</section>`;
}

async function render() {
  state.page = location.hash.slice(1) || "overview";
  document.querySelectorAll(".nav-item").forEach(item => item.classList.toggle("active", item.dataset.page === state.page));
  title.textContent = pages.find(([id]) => id === state.page)?.[2] || "Overview";
  content.innerHTML = '<div class="loading">Loading…</div>';
  try {
    if (state.page === "overview") await renderOverview();
    else if (state.page === "analytics") await renderAnalytics();
    else if (state.page === "health") await renderHealth();
    else if (state.page === "settings") await renderSettings();
    else {
      const [endpoint, columns] = pageConfig[state.page] || pageConfig.assets;
      content.innerHTML = table(await get(endpoint), columns);
    }
  } catch (error) { content.innerHTML = `<div class="notice">Could not load this module: ${esc(error.message)}</div>`; }
}

document.querySelector("#refresh").addEventListener("click", render);
document.querySelector("#kill-switch").addEventListener("click", async () => {
  if (!confirm("Stop every pending real publication job? Generation and analytics will continue.")) return;
  await fetch("/api/kill-switch/stop", { method: "POST" });
  await render();
});
addEventListener("hashchange", render);
render();
