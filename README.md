# 🌐 The Geo-Locator v8

> A real-time global intelligence dashboard built with Streamlit — tracking conflicts, signals intelligence, live markets, earth events, and geopolitical risk across eight specialised tabs.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37%2B-FF4B4B?logo=streamlit&logoColor=white)
![pydeck](https://img.shields.io/badge/pydeck-0.9%2B-4B8BBE)
![plotly](https://img.shields.io/badge/plotly-5.18%2B-3F4F75)
![License](https://img.shields.io/badge/License-Research%20Use-lightgrey)

---

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Python 3.9+ required. The app runs fully without any API keys — optional keys unlock higher-quality data for four sources (see [Optional API Keys](#configuration-all-optional)).

**Repo requirement:** this app is split across two files, `app.py` and `data_constants.py`, which must live in the same directory and be committed together — `app.py` imports directly from `data_constants.py` at startup.

---

## Features

| Tab | What it shows |
|---|---|
| ⚔ Conflict Dashboard | Live-duration tracker per active conflict, GDELT news overlay, casualty/timeline/media-bias charts |
| 🌍 Earth Signals | USGS earthquakes, NASA EONET events, Kp-index space weather, significant-quake history |
| ✊ Civil Movements | Global protest/unrest tracking |
| 📡 Live News | Live TV stream embeds, RSS aggregation, source directory |
| 🛰 Intel Dashboard | GPS jamming, cyber threats, derived signal blending, country instability index |
| 📻 SIGINT | MASINT/ELINT/COMINT-style derived signal panels |
| 📊 Economic & Markets | Indices, commodities, forex, crypto, defense stocks, shipping rates, critical minerals |
| 🏭 Facility Map | Refineries, storage/SPR sites, satellite tile imagery |

Plus a cross-tab **🌐 Global Command Map** with 37 toggleable layers, clearly split into:
- **● LIVE** — auto-refreshes every 30s: seismic, EONET/wildfires, cyber threats, GDELT events, AIS vessels, flights, ACLED
- **● REFERENCE** — curated baselines: military bases, nuclear sites, undersea cables, pipelines

And optional **🔔 webhook alerts** (Slack/Discord-compatible, plain HTTP — no AI involved).

---

## Repository structure

```
.
├── app.py                # Main Streamlit app — UI, tabs, live fetchers, map building
├── data_constants.py     # Static reference datasets — pure data, no imports
├── requirements.txt      # Python dependencies
└── README.md
```

> ⚠️ `app.py` runs `from data_constants import *` at import time. If `data_constants.py` is missing, out of date, or in a different directory, the app fails immediately with `ModuleNotFoundError` or `NameError` — before any UI renders.

---

## Deploying on Streamlit Community Cloud

1. Push `app.py`, `data_constants.py`, and `requirements.txt` to your repo (same directory).
2. On [share.streamlit.io](https://share.streamlit.io), point a new app at the repo, branch, and `app.py` as the entry point.
3. *(Optional)* Add secrets — see below — under **App settings → Secrets**.
4. Deploy. Streamlit Cloud reinstalls from `requirements.txt` and redeploys automatically on every push to the tracked branch.

---

## Configuration (all optional)

The app is fully functional out of the box using public, keyless endpoints and static fallback data. Adding secrets unlocks fuller live data and alerting. Set these in `.streamlit/secrets.toml` locally, or under **App settings → Secrets** on Streamlit Cloud:

```toml
# Live ACLED conflict-event data (falls back to GDELT scraping if unset)
ACLED_KEY = "your-acled-api-key"
ACLED_EMAIL = "your-registered-acled-email"

# Full live AIS vessel-tracking feed (falls back to a reduced/static set if unset)
AISSTREAM_KEY = "your-aisstream-io-key"

# Historical/persisted data backend (used as a cache/fallback layer; app works without it)
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-supabase-service-or-anon-key"

# Webhook alerts — plain HTTP POST, no AI/LLM involved. Any Slack or Discord
# "Incoming Webhook" URL works.
ALERT_WEBHOOK_URL = "https://hooks.slack.com/services/..."
```

| Secret | Unlocks | Without it |
|---|---|---|
| `ACLED_KEY` + `ACLED_EMAIL` | Live ACLED conflict events | Falls back to GDELT scraping |
| `AISSTREAM_KEY` | Full live AIS vessel feed | Falls back to a reduced/static set |
| `SUPABASE_URL` + `SUPABASE_KEY` | Persisted history/cache backend | Falls back to in-session cache only |
| `ALERT_WEBHOOK_URL` | Slack/Discord push alerts | Alerts panel shows "off" |

Currently wired alert conditions (debounced — each fires once per transition into the alert state):
- Critical-intensity conflict active
- Geomagnetic storm (Kp index ≥ 5)

---

## Architecture notes

- **Lazy tab loading** — Streamlit's `st.tabs()` executes every tab's code on every rerun regardless of which tab is visible. This app uses a session-state-backed tab selector instead, so only the active tab's API calls run per interaction.
- **Caching & fallbacks** — nearly every live fetch is wrapped in `@st.cache_data` with a per-source TTL, and falls back to a static baseline on failure so a flaky third-party API degrades gracefully instead of crashing a tab.
- **Logging** — failures in the highest-traffic fetchers are logged via Python's `logging` module (visible in the server console / Streamlit Cloud's "Manage app" logs) rather than failing silently.
- **Module split (phase 1)** — static reference datasets live in `data_constants.py`; live fetchers, map building, and tab UIs remain in `app.py`. Further splitting is a reasonable next step, deliberately deferred for now.

---

## Known limitations

- Curated baseline datasets (military postures, nuclear-site status, instability index) reflect a point-in-time snapshot and are not continuously verified.
- Some "SIGINT"-flavored panels (MASINT/ELINT/COMINT) are derived/illustrative signal blends, not real classified feeds.
- Free-tier public APIs (GDELT, ACLED without a key, EONET, USGS) are rate-limited; heavy concurrent use may see more fallback-to-baseline behavior.
