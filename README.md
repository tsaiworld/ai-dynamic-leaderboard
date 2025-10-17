# AI Dynamic Leaderboard

Live, JSON-powered leaderboard by category (LLM/Text, Video, Audio, Agentic AI, Development/Prod).
Weighted by **Popularity 40% · Performance 25% · Cost 10% · Privacy 10% · Innovation 15%**.

## Quick Start (Local)
1. Serve the site (any static server). Example:
   ```bash
   python -m http.server -d . 8080
   ```
   Visit http://localhost:8080

2. Update the data manually:
   ```bash
   python scripts/update_leaderboard.py
   ```

3. Pull AI news and refresh "what's new":
   ```bash
   pip install feedparser python-dateutil
   python scripts/get_ai_news.py
   python scripts/update_leaderboard.py
   ```

## GitHub Pages
- Push this repo to GitHub
- Settings → Pages → Deploy from branch (main) → /(root)
- The static site will read `data/ai_dashboard.json` client-side.

## GitHub Actions (auto-refresh daily 08:00 America/Chicago)
- Workflow: `.github/workflows/refresh.yml`
- It runs `get_ai_news.py` then `update_leaderboard.py` and commits updated JSON.

## Data Schema
`data/ai_dashboard.json` contains:
- `meta` (title, last_updated, weights)
- `categories[]`:
  - `id`, `name`
  - `entries[]`:
    - `tool`, `whats_new`, `best_used_for`, `pro`, `con`
    - `scores`: popularity, performance, cost, privacy, innovation (0-100)
    - optional: `total` (computed), `links.news`

Total score = weighted sum of the five dimensions.
UI shows **top 3** per category with 🥇 🥈 🥉 icons and a score badge.

## Customize
- Add tools or categories in `data/ai_dashboard.json`
- Tune weights in `meta.weights`
- Style in `assets/style.css`
