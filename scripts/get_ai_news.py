#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fetch recent AI news from public RSS feeds (no API key) and update
the "whats_new" field per tool if a matching keyword is found.

Requirements:
  pip install feedparser python-dateutil

Usage:
  python scripts/get_ai_news.py

Notes:
- This is heuristic keyword matching to keep things simple.
- You can add or adjust feeds and keyword maps below.
"""
import json, pathlib, datetime, re, sys
from dateutil import parser as dtparser

try:
    import feedparser
except ImportError as e:
    print("Missing dependency: feedparser. Install with 'pip install feedparser'")
    sys.exit(1)

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "ai_dashboard.json"

FEEDS = [
    "https://openai.com/blog/rss.xml",
    "https://www.anthropic.com/index.xml",
    "https://ai.googleblog.com/atom.xml",
    "https://stability.ai/blog?format=rss",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.techmeme.com/feed.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.reddit.com/r/MachineLearning/.rss"
]

# Map substrings to tools
KEYWORDS = {
    "gpt-4o": "GPT-4o (OpenAI)",
    "openai": "GPT-4o (OpenAI)",
    "claude": "Claude 3.5 (Anthropic)",
    "anthropic": "Claude 3.5 (Anthropic)",
    "gemini": "Gemini 1.5 Pro (Google)",
    "google": "Gemini 1.5 Pro (Google)",
    "llama": "Llama 3.1 (Meta)",
    "sora": "Sora (OpenAI)",
    "pika": "Pika 1.5",
    "runway": "Runway Gen-2",
    "elevenlabs": "ElevenLabs v3",
    "sunō": "Sunō v3",
    "suno": "Sunō v3",
    "play.ht": "Play.ht v2",
    "gpt": "OpenAI GPTs / Assistants",
    "assistants": "OpenAI GPTs / Assistants",
    "computer use": "Anthropic Computer Use",
    "autogen": "CrewAI / AutoGen",
    "crewai": "CrewAI / AutoGen",
    "copilot": "GitHub Copilot Workspace",
    "cursor": "Cursor IDE",
    "replit": "Replit Agent"
}

def normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def main():
    with open(DATA) as f:
        data = json.load(f)

    # Collect items
    news_hits = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:40]:
            title = normalize(getattr(entry, "title", ""))
            link = normalize(getattr(entry, "link", ""))
            summary = normalize(getattr(entry, "summary", ""))
            date_str = getattr(entry, "published", "") or getattr(entry, "updated", "")
            try:
                dt = dtparser.parse(date_str).date()
            except Exception:
                dt = datetime.date.today()
            text = f"{title} {summary}".lower()
            for k, tool in KEYWORDS.items():
                if k in text:
                    news_hits.append({"tool": tool, "title": title, "date": dt.isoformat(), "link": link})
                    break

    # Update what's_new for first recent hit per tool
    recent_by_tool = {}
    for hit in sorted(news_hits, key=lambda x: x["date"], reverse=True):
        if hit["tool"] not in recent_by_tool:
            recent_by_tool[hit["tool"]] = hit

    # Walk categories and update
    updates = 0
    for cat in data["categories"]:
        for e in cat["entries"]:
            t = e["tool"]
            if t in recent_by_tool:
                h = recent_by_tool[t]
                e["whats_new"] = f"{h['title']} ({h['date']})"
                # optionally store link for UI (not rendered by default to keep table clean)
                e.setdefault("links", {})["news"] = h["link"]
                updates += 1

    data["meta"]["last_updated"] = datetime.date.today().isoformat()

    with open(DATA, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Updated 'whats_new' for {updates} tools.")

if __name__ == "__main__":
    main()
