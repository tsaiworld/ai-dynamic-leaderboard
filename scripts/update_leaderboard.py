#!/usr/bin/env python3

"""
Computes a weighted leaderboard across categories using recent news signals.
Updates data/ai_dashboard.json (keeps 'top_news', updates 'leaderboard').

Weights:
  Popularity 40%, Performance 25%, Cost 10%, Privacy 10%, Innovation 15%
"""
import os, json, re
from collections import defaultdict
from datetime import datetime, timezone

ISO = "%Y-%m-%dT%H:%M:%SZ"

WEIGHTS = {
  "popularity": 0.40,
  "performance": 0.25,
  "cost": 0.10,
  "privacy": 0.10,
  "innovation": 0.15,
}

CATEGORIES = ["LLM/Text","Image/Vision","Video/Motion","Audio/Music","Multi-Modal/Agentic"]

KEYWORDS = {
  "popularity":  [r"\b(launch|release|now available|partnership|user[s]?|adoption|daily active)\b"],
  "performance": [r"\b(benchmark|leaderboard|MMLU|reasoning|accuracy|SOTA|realism|fidelity)\b"],
  "cost":        [r"\b(cost|cheap|affordab|pricing|tokens?|throughput|latency|efficien|serverless)\b"],
  "privacy":     [r"\b(privacy|copyright|likeness|opt[- ]?out|consent|watermark|safety|on[- ]?device)\b"],
  "innovation":  [r"\b(multimodal|agents?|tool[- ]?use|ecosystem|plugins|extensions|vision|audio|video)\b"],
}

BUCKET_RULES = {
  "LLM/Text":           [r"\b(GPT|Claude|Gemini|Llama|Mistral|command|text|RAG|token)\b"],
  "Image/Vision":       [r"\b(image|vision|diffusion|sdxl|stability|midjourney|segmentation|detection)\b"],
  "Video/Motion":       [r"\b(video|Sora|Veo|motion|frame|temporal|UHD)\b"],
  "Audio/Music":        [r"\b(audio|music|voice|TTS|ASR|Whisper|chorus|suno)\b"],
  "Multi-Modal/Agentic":[r"\b(multimodal|agent|tool[- ]?use|orchestration|workflow|planner)\b"],
}

VENDOR_HINT = [
  "openai","google","deepmind","microsoft","meta","anthropic","amazon","xai",
  "stability","midjourney","runway","pika","elevenlabs","coqui","suno","mistral",
  "databricks","snowflake","perplexity","reka","nvidia","intel","amd","apple"
]

BEST_FOR_DEFAULT = {
  "LLM/Text": "Reasoning, chat, knowledge tasks",
  "Image/Vision": "Image generation & perception",
  "Video/Motion": "Video synthesis & motion effects",
  "Audio/Music": "Voice, TTS, music generation",
  "Multi-Modal/Agentic": "Orchestration & tool-use"
}

def read_json(path, default=None):
  try:
    with open(path, "r", encoding="utf-8") as f:
      return json.load(f)
  except FileNotFoundError:
    return default if default is not None else {}

def write_json(path, data):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

def score_from_keywords(text, patterns):
  t = text.lower()
  s = 0.0
  for pat in patterns:
    if re.search(pat, t):
      s += 1.0
  return min(1.0, s / max(1, len(patterns)))

def detect_vendor(text):
  t = text.lower()
  for v in VENDOR_HINT:
    if v in t:
      return v.title()
  return "Other"

def buckets_for(text):
  hits = []
  for cat, pats in BUCKET_RULES.items():
    if any(re.search(p, text, flags=re.IGNORECASE) for p in pats):
      hits.append(cat)
  return hits or ["LLM/Text"]

def derive_whats_new_and_date(item):
  title = (item.get("title") or "").strip()
  date  = item.get("published_at") or item.get("date")
  return title[:140] or "Recent update", date

def derive_pro_con(text):
  t = text.lower()
  pro = []
  con = []
  if re.search(KEYWORDS["performance"][0], t) or "benchmark" in t:
    pro.append("Strong benchmarks")
  if any(k in t for k in ["cheap","afford","pricing","throughput","latency","serverless","efficient"]):
    pro.append("Good cost/throughput")
  if any(k in t for k in ["privacy","on-device","watermark","consent","likeness"]):
    pro.append("Privacy-friendly")

  if any(k in t for k in ["limited","bug","outage","downtime","restriction","waitlist"]):
    con.append("Availability limits")
  if any(k in t for k in ["price increase","expensive","costly"]):
    con.append("Higher cost")
  if any(k in t for k in ["copyright","likeness","lawsuit"]):
    con.append("Potential IP/likeness risk")

  return ("; ".join(pro) or None, "; ".join(con) or None)

def main():
  out_path = os.getenv("OUTPUT_JSON", "data/ai_dashboard.json")
  top_per  = int(os.getenv("TOP_PER_BUCKET", "5"))

  dashboard = read_json(out_path, default={"top_news": [], "leaderboard": {}})
  news = dashboard.get("top_news", [])

  per_bucket = {c: defaultdict(lambda: {
    "popularity":0,"performance":0,"cost":0,"privacy":0,"innovation":0,
    "examples":[], "whats_new":None, "whats_new_date":None,
    "best_used_for":BEST_FOR_DEFAULT.get(c,""), "main_pro":None, "main_con":None
  }) for c in CATEGORIES}

  for item in news:
    title = item.get("title","")
    summary = item.get("summary","")
    text = f"{title} {summary}"
    vendor = detect_vendor(text)
    cats = buckets_for(text)

    signals = {
      "popularity":  min(1.0, 0.5 + (item.get("score",0)*0.5) + score_from_keywords(text, KEYWORDS["popularity"])*0.5),
      "performance": score_from_keywords(text, KEYWORDS["performance"]),
      "cost":        score_from_keywords(text, KEYWORDS["cost"]),
      "privacy":     score_from_keywords(text, KEYWORDS["privacy"]),
      "innovation":  score_from_keywords(text, KEYWORDS["innovation"]),
    }

    wn, wdate = derive_whats_new_and_date(item)
    pro, con  = derive_pro_con(text)

    for cat in cats:
      agg = per_bucket[cat][vendor]
      for k,v in signals.items(): agg[k] = max(agg[k], v)
      if not agg["whats_new"]: agg["whats_new"] = wn
      if not agg["whats_new_date"]: agg["whats_new_date"] = wdate
      if pro and not agg["main_pro"]: agg["main_pro"] = pro
      if con and not agg["main_con"]: agg["main_con"] = con

      if len(agg["examples"]) < 3:
        ex = {"title": title, "url": item.get("url"), "signal": round(item.get("score",0),2)}
        if item.get("published_at"): ex["date"] = item["published_at"]
        agg["examples"].append(ex)

  leaderboard = {}
  for cat, vendors in per_bucket.items():
    rows = []
    for vendor, subs in vendors.items():
      total = (
        subs["popularity"] * WEIGHTS["popularity"] +
        subs["performance"] * WEIGHTS["performance"] +
        subs["cost"]       * WEIGHTS["cost"] +
        subs["privacy"]    * WEIGHTS["privacy"] +
        subs["innovation"] * WEIGHTS["innovation"]
      )
      rows.append({
        "label": vendor,
        "score_total": round(total, 4),
        "scores": {k: round(subs[k],3) for k in WEIGHTS},
        "examples": subs["examples"],
        "whats_new": subs["whats_new"],
        "whats_new_date": subs["whats_new_date"],
        "best_used_for": subs["best_used_for"],
        "main_pro": subs["main_pro"],
        "main_con": subs["main_con"],
      })
    rows.sort(key=lambda r: r["score_total"], reverse=True)
    leaderboard[cat] = rows[:top_per]

  dashboard["leaderboard"] = leaderboard
  dashboard["generated_at"] = datetime.now(timezone.utc).strftime(ISO)
  write_json(out_path, dashboard)
  print(f"Updated leaderboard → {out_path}")

if __name__ == "__main__":
  main()
