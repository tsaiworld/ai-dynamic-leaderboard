#!/usr/bin/env python3

"""
Top-5 AI news -> writes/updates data/ai_dashboard.json (top_news only).
If ai_dashboard.json exists, preserves 'leaderboard' and updates 'top_news'.

ENV:
  NEWS_API_PROVIDER=newsapi|rss   (default: rss)
  NEWS_API_KEY=...                (required if provider=newsapi)
  NEWS_QUERY="AI OR artificial intelligence OR generative AI"
  NEWS_WINDOW_DAYS=2
  TOP_N_SOURCES=40
  TOP_N_ITEMS=5
  OUTPUT_JSON=data/ai_dashboard.json
"""
import os, json, math, hashlib
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import requests
import xml.etree.ElementTree as ET

ISO = "%Y-%m-%dT%H:%M:%SZ"
NOW = datetime.now(timezone.utc)

def env(name, default=None, cast=str):
    v = os.getenv(name, default)
    return cast(v) if (v is not None and cast is not str) else v

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

def sha16(s): return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]

def _rss_to_iso(pubdate_str):
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(pubdate_str).astimezone(timezone.utc)
        return dt.strftime(ISO)
    except Exception:
        return datetime.now(timezone.utc).strftime(ISO)

def fetch_news_newsapi(query, window_days, top_src, api_key):
    frm = (NOW - timedelta(days=window_days)).strftime("%Y-%m-%d")
    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "from": frm, "language": "en", "sortBy": "publishedAt", "pageSize": min(100, top_src)}
    r = requests.get(url, params=params, headers={"X-Api-Key": api_key}, timeout=30)
    r.raise_for_status()
    arts = r.json().get("articles", [])
    items = []
    for a in arts:
        items.append({
            "id": sha16(a.get("url","")),
            "title": (a.get("title") or "").strip(),
            "url": a.get("url"),
            "source": (a.get("source") or {}).get("name"),
            "published_at": a.get("publishedAt"),
            "summary": (a.get("description") or "").strip(),
        })
    return items

def fetch_news_rss(query, window_days, top_src):
    feed_url = "https://www.bing.com/news/search"
    q = {"q": query, "qft": 'sortbydate="1"', "format": "rss"}
    url = f"{feed_url}?{urlencode(q)}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    items = []
    for it in root.findall(".//item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        pub  = it.findtext("pubDate") or ""
        items.append({
            "id": sha16(link),
            "title": title,
            "url": link,
            "source": "Bing RSS",
            "published_at": _rss_to_iso(pub),
            "summary": ""
        })
    return items

def recency_score(published_at, window_days=2):
    try:
        dt = datetime.fromisoformat(published_at.replace("Z","+00:00"))
    except Exception:
        dt = datetime.now(timezone.utc)
    age_h = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds()/3600.0)
    half_life_h = (window_days * 24) / 2
    return math.exp(-age_h / half_life_h)

def source_weight(name):
    if not name: return 1.0
    n = name.lower()
    if any(k in n for k in ["reuters","bloomberg","wsj","financial times"]): return 1.15
    if any(k in n for k in ["openai","google","microsoft","meta","anthropic","amazon"]): return 1.2
    return 1.0

def main():
    provider = os.getenv("NEWS_API_PROVIDER", "rss").lower()
    api_key  = os.getenv("NEWS_API_KEY")
    query = os.getenv("NEWS_QUERY", "AI OR artificial intelligence OR generative AI")
    window = env("NEWS_WINDOW_DAYS", 2, int)
    top_n = env("TOP_N_ITEMS", 5, int)
    out_path = os.getenv("OUTPUT_JSON", "data/ai_dashboard.json")

    items = fetch_news_newsapi(query, window, 40, api_key) if provider == "newsapi" and api_key else fetch_news_rss(query, window, 40)

    for it in items:
        it["score"] = round(recency_score(it["published_at"], window) * source_weight(it.get("source")), 4)
    items.sort(key=lambda x: x["score"], reverse=True)
    top_news = items[:top_n]

    existing = read_json(out_path, default={})
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime(ISO),
        "top_news": top_news,
        "leaderboard": existing.get("leaderboard", {})
    }
    write_json(out_path, payload)
    print(f"Wrote Top-{top_n} news → {out_path}")

if __name__ == "__main__":
    main()
