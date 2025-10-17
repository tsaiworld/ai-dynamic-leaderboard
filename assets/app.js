const DATA_URL = "data/ai_dashboard.json";

const WEIGHTS = {
  popularity: 0.40,
  performance: 0.25,
  cost: 0.10,
  privacy: 0.10,
  innovation: 0.15
};

function chip(k,v){
  const s = document.createElement("span");
  s.className = "chip";
  s.textContent = `${k} ${Math.round(v*100)}%`;
  return s;
}

function fmt(n){ return (Math.round(n*100)/100).toFixed(2); }

async function loadData(){
  const res = await fetch(`${DATA_URL}?_=${Date.now()}`);
  if(!res.ok) throw new Error("Failed to fetch data");
  return res.json();
}

function renderNews(list){
  const el = document.getElementById("newsList");
  el.innerHTML = "";
  (list || []).slice(0,5).forEach(item => {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = item.url; a.target = "_blank"; a.rel = "noopener";
    a.textContent = item.title || "Untitled";
    const meta = document.createElement("small");
    meta.className = "muted";
    const src = item.source ? ` ${item.source}` : "";
    const ts = item.published_at ? `, ${new Date(item.published_at).toLocaleString()}` : "";
    meta.textContent = `${src}${ts}`;
    li.appendChild(a); li.appendChild(meta);
    el.appendChild(li);
  });
}

function renderLeaderboard(lb){
  const root = document.getElementById("leaderboard");
  root.innerHTML = "";

  const legend = document.getElementById("legend");
  legend.innerHTML = "";
  Object.entries(WEIGHTS).forEach(([k,v]) => legend.appendChild(chip(k,v)));

  const medalFor = (rank) => (rank===1?'🥇':rank===2?'🥈':rank===3?'🥉':'');

  Object.entries(lb || {}).forEach(([bucket, rows]) => {
    const wrap = document.createElement("div");
    wrap.className = "bucket";
    const h = document.createElement("h3");
    h.textContent = bucket;
    wrap.appendChild(h);

    (rows || []).slice(0,3).forEach((r, i) => {
      const rank = i+1;
      const row = document.createElement("div");
      row.className = "row row-grid";

      const cRank = document.createElement("div");
      cRank.className = "col rank";
      cRank.innerHTML = `<span class="medal">${medalFor(rank)}</span> ${rank}`;

      const cLabel = document.createElement("div");
      cLabel.className = "col label";
      cLabel.textContent = r.label;

      const cScore = document.createElement("div");
      cScore.className = "col score";
      cScore.textContent = fmt(r.score_total);

      const cNew = document.createElement("div");
      cNew.className = "col whatsnew";
      const wn = r.whats_new || (r.examples && r.examples[0]?.title) || "—";
      const wdate = r.whats_new_date || (r.examples && r.examples[0]?.date) || null;
      cNew.innerHTML = `${wn}${wdate ? `<span class="subtle">${new Date(wdate).toLocaleDateString()}</span>` : ""}`;

      const cBest = document.createElement("div");
      cBest.className = "col bestfor";
      cBest.textContent = r.best_used_for || "—";

      const cProCon = document.createElement("div");
      cProCon.className = "col procon";
      const pro = r.main_pro || "—";
      const con = r.main_con || "—";
      cProCon.innerHTML = `<div>Pro: ${pro}</div><div>Con: ${con}</div>`;

      row.appendChild(cRank);
      row.appendChild(cLabel);
      row.appendChild(cScore);
      row.appendChild(cNew);
      row.appendChild(cBest);
      row.appendChild(cProCon);

      wrap.appendChild(row);
    });

    root.appendChild(wrap);
  });
}

function setUpdated(ts){
  const el = document.getElementById("lastUpdated");
  try { el.textContent = `Last updated: ${new Date(ts).toLocaleString()}`; }
  catch { el.textContent = "Last updated: unknown"; }
}

async function start(){
  document.getElementById("year").textContent = new Date().getFullYear();
  try{
    const data = await loadData();
    setUpdated(data.generated_at || new Date().toISOString());
    renderNews(data.top_news || []);
    renderLeaderboard(data.leaderboard || {});
  }catch(e){
    console.error(e);
    document.getElementById("newsList").innerHTML = "<li>Failed to load data.</li>";
    document.getElementById("leaderboard").textContent = "Failed to load data.";
  }
}
document.getElementById("refreshBtn").addEventListener("click", start);
start();
