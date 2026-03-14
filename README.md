<p align="center">
  <img src="https://img.shields.io/badge/OSINT%20ARENA-v3.0-00c8ff?style=for-the-badge&labelColor=02040a&color=00c8ff" alt="version"/>
  <img src="https://img.shields.io/badge/Streamlit-1.35+-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white&labelColor=02040a" alt="streamlit"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=02040a" alt="python"/>
  <img src="https://img.shields.io/badge/License-MIT-00e676?style=for-the-badge&labelColor=02040a" alt="license"/>
</p>

<h1 align="center">
  <br/>Geo-Locator
  <br/><sub><sup>Global Intelligence Operations Center</sup></sub>
</h1>

<p align="center">
  A luxury-aesthetic, intelligence-grade Streamlit dashboard combining live Earth signals,
  civil movement tracking, conflict monitoring, multi-source news aggregation,
  AI-powered analysis, and gamified OSINT training challenges — all in a single dark ops interface.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#features">Features</a> ·
  <a href="#conflict-dashboard">Conflict Dashboard</a> ·
  <a href="#data-sources">Data Sources</a> ·
  <a href="#ai-setup">AI Setup</a> ·
  <a href="#tech-stack">Tech Stack</a> ·
  <a href="#live-api-integration">Live API Integration</a> ·
  <a href="#deployment">Deployment</a>
</p>

---

## Quick Start

```bash
# 1. Clone / download
git clone https://github.com/your-org/osint-arena
cd osint-arena

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
streamlit run app.py
```

Opens at **http://localhost:8501**

No API keys required to run — all live feeds degrade gracefully to rich synthetic fallback data when offline.

---

## Features

OSINT Arena v3 is organised into six tabs, each a full analytical instrument.

### ⚔ Conflict Dashboard *(new in v3)*

The centrepiece of v3. A full conflict-intelligence workstation covering four active theatres with theatre-select, incident mapping, faction tracking, supply arc visualisation, escalation gauges, timelines, risk matrices, media bias analysis, and an AI situation report generator.

[Full breakdown below ↓](#conflict-dashboard)

### 🌍 Earth Signals

Live geophysical monitoring combining three independent feeds into a single interactive map.

- **Seismic layer** — USGS M2.5+ earthquakes, last 24 hours, colour-coded by magnitude
- **Volcanic/EONET layer** — NASA Earth Observatory Natural Event Tracker (active volcanoes, wildfires, severe storms)
- **Geomagnetic layer** — NOAA SWPC Kp-index sparkline with storm threshold indicator
- **Heatmap mode** — PyDeck `HeatmapLayer` showing seismic density
- Magnitude histogram and M4.5+ significant events list in sidebar

### ✊ Civil Movements

Civil unrest and large-scale public movement tracker.

- Interactive map with sentiment-coloured markers (CRIT / HIGH / MED)
- Scale bar per event (0–100 mobilisation index)
- Filter by type: protest / strike / civil
- Movement chart (horizontal bar, sorted by scale)
- Age tracking and participant count

### 📡 Live News Feeds

Multi-source RSS aggregation across 16 curated feeds in 6 categories. 10-minute TTL cache.

| Category | Sources |
|---|---|
| 🌐 Global Wire | Reuters World, BBC World, Al Jazeera, AP News |
| 🔬 Earth Science | NASA JPL, USGS News, Phys.org Earth |
| 🗺 Geopolitics | Foreign Policy, The Diplomat, Defense One |
| ⚔ Conflict | ACLED Updates, ISW Daily, CSIS Analysis |
| 🌱 Climate | Carbon Brief |
| ☀ Space Weather | SpaceWeather.com, NOAA SWPC |

Each article card shows source name, category badge, headline, excerpt, publication age, and a direct link. Category-specific left-border accent colours distinguish feed origins at a glance. Falls back to the full source directory (with RSS endpoints) when offline.

### 🎯 Arena Challenges

Gamified OSINT training system with XP progression, leaderboard, and four intelligence challenges of increasing difficulty.

| Challenge | Difficulty | XP | Topic |
|---|---|---|---|
| Seismic Trail | ANALYST | 250 | Tsunami risk assessment from seismic parameters |
| Civil Unrest Assessment | AGENT | 400 | ACLED escalation methodology |
| Conflict Intelligence | ANALYST | 350 | Convergent OSINT — satellite + SOCMINT + SIGINT |
| Multi-Source Fusion | HANDLER | 500 | Compound risk correlation across data streams |

Tier system: RECRUIT → ANALYST (2,000 XP) → AGENT (5,000 XP) → HANDLER (10,000 XP)

### 🤖 AI Analyst

Natural language intelligence analysis powered by your choice of LLM provider.

- Provider-agnostic: Groq (fastest), Ollama (fully offline), OpenRouter (model variety)
- 7 pre-built prompt templates covering seismic risks, conflict assessment, Kp impacts, and multi-theatre correlation
- **Live context injection** — automatically appends top earthquakes, Kp index, all conflict data, and civil movement sentiment to every query
- Outputs to a styled terminal-aesthetic code block
- Magnitude donut, movement sentiment bar, and raw earthquake data table alongside

---

## Conflict Dashboard

The ⚔ Conflict Dashboard is the primary new module in v3. It tracks four active conflict theatres with intelligence-grade depth.

### Monitored Theatres

| Theatre | Region | Intensity | Escalation Index | Casualties | Displaced |
|---|---|---|---|---|---|
| Ukraine–Russia War | Eastern Europe | CRITICAL | 87/100 | ~350,000 | 14.2M |
| Gaza Conflict | Middle East | CRITICAL | 92/100 | ~46,000 | 1.9M |
| Sudan Civil War | Sub-Saharan Africa | HIGH | 74/100 | ~15,000 | 8.1M |
| Myanmar Civil War | Southeast Asia | HIGH | 68/100 | ~50,000 | 2.6M |

### Per-Theatre Panels

#### 1. Incident Map
PyDeck `ScatterplotLayer` with severity-coloured markers and `ArcLayer` supply lines. Click any event for a tooltip showing type, location, severity, date, and casualty count.

**Incident types tracked:**
`💥 airstrike` · `⚔️ ground` · `🛸 drone` · `⚓ naval` · `🚀 rocket` · `💻 cyber` · `🤝 diplomatic` · `🏥 humanitarian`

**Severity levels:** `CRITICAL` (red) · `HIGH` (orange) · `MED` (amber) · `LOW` (green) · `INFO` (muted)

#### 2. Escalation Gauge
Plotly indicator gauge (0–100) with colour-coded risk zones:
- 0–30: Low (green)
- 30–60: Elevated (amber)
- 60–80: High (orange)
- 80–100: Critical (red)

#### 3. Faction Tracker
Each belligerent shown with:
- Territory control percentage + visual bar
- Operational strength (High / Med / Low)
- Current operational status (Offensive / Defending / Advancing / Active)
- Key weapons systems
- External support providers
- Colour-coded by alignment

#### 4. Incident Feed
Filterable real-time incident list. Filters: ALL / airstrike / ground / drone / naval / rocket / cyber / humanitarian / diplomatic. Each row shows icon, title, location, date, casualty count, severity badge, and type badge.

#### 5. Conflict Timeline
- Plotly scatter timeline with colour-coded event types (escalation / milestone / diplomatic / setback / ongoing)
- Scrollable chronological list below with full event descriptions
- Type colours: 🔴 escalation · 🔵 milestone · 🟢 diplomatic · 🟡 setback · 🟣 ongoing

#### 6. Supply & Support Lines
PyDeck `ArcLayer` arcs drawn from provider to recipient:
- 🔴 Military Aid / Arms Supply (red arcs)
- 🟢 Humanitarian corridors (green arcs)
- Toggleable via sidebar "Supply Arc Lines" toggle

Card list below the map shows provider, route type, and coordinates.

#### 7. Media Reliability Tracker
Per-conflict bar chart showing each media outlet's reliability score (0–100) colour-coded by editorial bias:
- 🔵 Centre
- 🟣 Centre-Left
- 🟠 Right / Pro-party
- 🔴 State media (lowest trust)

#### 8. Risk Assessment Matrix
Six-dimension risk matrix across all four conflicts simultaneously:

| Dimension | Description |
|---|---|
| Escalation | Probability of further escalation |
| Humanitarian | Civilian population risk level |
| Regional Spillover | Cross-border spread risk |
| Nuclear/WMD | Non-conventional weapon use risk |
| Ceasefire Probability | Likelihood of near-term ceasefire |
| External Intervention | Risk of new external actor entry |

#### 9. Cross-Theatre Analytics
- **Casualties & Displacement** — grouped bar chart comparing all theatres
- **Escalation vs Casualties** — scatter plot, bubbles sized by displaced population
- **Global Conflict Map** — all 4 theatres combined on one world map

#### 10. AI Situation Report Generator
Select from six report types and generate an AI-authored intelligence brief, with all structured conflict data (factions, incidents, timeline, escalation index) auto-injected as context:

- Executive Summary (3 paragraphs)
- Escalation Risk Assessment
- Humanitarian Impact Brief
- Supply Chain & External Support Analysis
- Media Bias & Information Environment Report
- Ceasefire / Diplomatic Prospects

---

## Data Sources

### Live APIs (auto-cached)

| Source | Endpoint | Cache TTL | What it provides |
|---|---|---|---|
| USGS Earthquake | `.../2.5_day.geojson` | 60s | M2.5+ earthquakes, global, last 24h |
| NASA EONET v3 | `eonet.gsfc.nasa.gov/api/v3/events` | 5 min | Active volcanoes, wildfires, severe storms |
| NOAA SWPC | `.../noaa-planetary-k-index.json` | 3 min | Kp geomagnetic index, 24h series |
| RSS Feeds × 16 | Per-source endpoints (see table above) | 10 min | News articles with headline, excerpt, link |

### Conflict Data (structured mock, ready for live API)

The four conflict datasets are structured Python dicts designed to be directly replaced by live API responses. See [Live API Integration](#live-api-integration) for wiring instructions.

### Fallback Behaviour

Every live fetcher wraps in `try/except` and returns a synthetic fallback dataset if the network is unavailable. The app is fully functional offline — no blank panels, no crash.

---

## AI Setup

Configure an AI provider in the sidebar to enable the AI Analyst tab and the Conflict Sitrep generator.

### Option 1 — Groq (recommended: fastest, free tier)

1. Create an account at [console.groq.com](https://console.groq.com)
2. Generate an API key
3. Select **groq** in the sidebar, paste your key
4. Default model: `llama-3.1-8b-instant` (8,000 tok/s, free tier)

```python
# To change model, edit this line in app.py:
"model": "llama-3.1-8b-instant"
# Other options: "llama3-70b-8192", "mixtral-8x7b-32768"
```

### Option 2 — Ollama (fully offline, no key needed)

1. Install Ollama: [ollama.com](https://ollama.com)
2. Pull a model and start the server:

```bash
ollama pull llama3
ollama serve
```

3. Select **ollama** in the sidebar — no API key required
4. Default model: `llama3` (editable in `call_ai()`)

### Option 3 — OpenRouter (widest model selection)

1. Create an account at [openrouter.ai](https://openrouter.ai)
2. Generate an API key
3. Select **openrouter** in the sidebar, paste your key
4. Default model: `meta-llama/llama-3.1-8b-instruct:free`

```python
# Swap to any OpenRouter model:
"model": "anthropic/claude-3.5-sonnet"
"model": "google/gemini-flash-1.5"
"model": "mistralai/mistral-7b-instruct:free"
```

---

## Tech Stack

### WorldMonitor → OSINT Arena Mapping

| WorldMonitor Original | OSINT Arena Equivalent |
|---|---|
| Vanilla TypeScript + Vite | Python 3.12 + Streamlit |
| globe.gl + Three.js | PyDeck `ScatterplotLayer` (3D globe-capable via pitch) |
| deck.gl + MapLibre GL | PyDeck (official Python deck.gl bindings) |
| Tauri 2 (Rust desktop) | `streamlit run` / Docker / Railway / PWA |
| Ollama / Groq / OpenRouter | Direct HTTP calls — same APIs, provider-switchable in sidebar |
| Protocol Buffers (92 protos) | Python dataclasses + Pandas DataFrames |
| Vercel Edge Functions (60+) | `@st.cache_data(ttl=…)` per-feed caching |
| Redis Upstash 3-tier cache | Tiered TTLs: 60s → 180s → 300s → 600s |
| CDN + service worker | Streamlit built-in asset caching |
| AISStream / OpenSky | Extendable — add `fetch_ais()` / `fetch_opensky()` |

### Python Dependencies

```
streamlit>=1.35.0   # UI framework
pydeck>=0.9.0       # deck.gl maps (ScatterplotLayer, HeatmapLayer, ArcLayer)
plotly>=5.20.0      # Charts (gauge, donut, scatter, bar, histogram, sparkline)
pandas>=2.0.0       # DataFrames
numpy>=1.26.0       # Synthetic data generation
requests>=2.31.0    # HTTP fetching (APIs + RSS)
```

No additional dependencies. No `feedparser` required — RSS is parsed with standard `re` and `html`.

### Typography & Design System

| Role | Font | Usage |
|---|---|---|
| Display / Numbers | Bebas Neue | Headlines, metric values, leaderboard scores |
| Data / Code | IBM Plex Mono | Coordinates, times, API output, terminal |
| UI / Body | DM Sans | Labels, descriptions, buttons |

Colour system (CSS variables):

```css
--cyan:   #00c8ff   /* Primary accent — seismic, info */
--amber:  #ffb400   /* Warning — Kp, medium severity */
--red:    #ff3d5a   /* Critical — conflict, high magnitude */
--green:  #00e676   /* Safe — correct answers, ceasefire */
--violet: #9d6eff   /* OSINT challenges, XP system */
--orange: #ff8c42   /* High severity, faction labels */
```

---

## Live API Integration

To replace mock conflict data with live feeds, implement the following integrations:

### ACLED (Armed Conflict Location & Event Data)

The gold standard for conflict event data. Free with registration.

```python
import requests

@st.cache_data(ttl=300, show_spinner=False)
def fetch_acled(country: str, api_key: str, email: str) -> pd.DataFrame:
    """
    Fetch recent ACLED events for a given country.
    Register at: developer.acleddata.com
    """
    url = "https://api.acleddata.com/acled/read"
    params = {
        "key": api_key,
        "email": email,
        "country": country,
        "limit": 50,
        "fields": "event_date|event_type|sub_event_type|location|latitude|longitude|fatalities|notes",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return pd.DataFrame(r.json()["data"])
```

### GDELT Project (Global events, 15-min updates)

```python
@st.cache_data(ttl=900, show_spinner=False)
def fetch_gdelt_conflict() -> pd.DataFrame:
    """
    GDELT GKG — real-time global event data.
    No API key required.
    """
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "conflict war military",
        "mode": "artlist",
        "maxrecords": 25,
        "format": "json",
    }
    r = requests.get(url, params=params, timeout=12)
    return pd.DataFrame(r.json().get("articles", []))
```

### ReliefWeb API (UN humanitarian data)

```python
@st.cache_data(ttl=600, show_spinner=False)
def fetch_reliefweb(country: str) -> list:
    """
    ReliefWeb — UN OCHA humanitarian reports.
    No API key required.
    """
    url = "https://api.reliefweb.int/v1/reports"
    params = {
        "filter[field]": "country.name",
        "filter[value]": country,
        "limit": 10,
        "fields[include][]": ["title", "body", "date", "source"],
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json().get("data", [])
```

### ISW (Institute for the Study of War) — daily Ukraine updates

ISW publishes daily narrative updates. Fetch via their RSS feed (already configured in `NEWS_SOURCES`) or scrape the daily PDF via their API. The `fetch_rss()` function already handles `https://understandingwar.org/rss.xml`.

### Replacing the `CONFLICTS` dict

The `CONFLICTS` dictionary schema is designed to accept live API data. Minimum required fields per theatre:

```python
{
  "status": str,          # "ACTIVE" | "FROZEN" | "RESOLVED"
  "intensity": str,       # "CRITICAL" | "HIGH" | "MED" | "LOW"
  "start": str,           # ISO date "YYYY-MM-DD"
  "region": str,
  "escalation": int,      # 0–100
  "ceasefire": bool,
  "casualties_total": int,
  "displaced": int,
  "description": str,
  "factions": list[dict], # name, side, color, territory_pct, strength, weapons, support, status
  "incidents": list[dict],# type, title, loc, lat, lon, date, severity, casualties
  "timeline": list[dict], # date, event, type
  "supply_lines": list[dict], # from_lat, from_lon, to_lat, to_lon, type, provider
  "media_sources": list[dict],# name, bias, reliability, coverage
}
```

---

## Deployment

### Streamlit Community Cloud (free, simplest)

1. Push to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → select `app.py` → deploy
4. Add secrets in the Streamlit Cloud dashboard (optional for AI keys)

### Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
```

```bash
docker build -t osint-arena .
docker run -p 8501:8501 osint-arena
```

### Railway (mirrors WorldMonitor's Railway relay)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

Add a `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

### Environment Variables (for AI keys in production)

```bash
# .env or deployment secrets
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...
```

Read in `app.py`:
```python
import os
groq_key = os.environ.get("GROQ_API_KEY", "")
```

---

## Project Structure

```
osint-arena/
├── app.py              # Main application (1,378 lines)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

The entire application is intentionally single-file to mirror Streamlit's deployment simplicity. For a production architecture, consider splitting into:

```
osint-arena/
├── app.py
├── requirements.txt
├── data/
│   ├── conflicts.py    # CONFLICTS dict + ACLED fetcher
│   ├── earth.py        # USGS, EONET, NOAA fetchers
│   └── news.py         # RSS sources + fetch_rss()
├── ui/
│   ├── charts.py       # All Plotly chart builders
│   ├── maps.py         # All PyDeck layer builders
│   └── styles.py       # CSS string
└── config.py           # Constants, tier thresholds, source registry
```

---

## Roadmap

Features planned for v4:

- [ ] **Live ACLED integration** — real conflict event data replacing mock incidents
- [ ] **GDELT streaming** — 15-minute event updates via GDELT 2.0
- [ ] **AIS vessel tracking** — shipping lane monitoring (AISStream.io)
- [ ] **OpenSky Network** — live airspace / military aviation overlay
- [ ] **Telegram channel monitor** — open-source conflict reporting channels
- [ ] **SIGINT frequency map** — radio spectrum anomaly visualisation
- [ ] **Export to PDF** — one-click situation report export
- [ ] **User authentication** — persistent XP scores, team leaderboards
- [ ] **Alert webhooks** — push notifications for CRITICAL events to Slack / Discord
- [ ] **Historical playback** — scrub through conflict timelines with animated map

---

## Contributing

Pull requests welcome. Please open an issue first for significant changes.

Areas most in need of contribution:
- Additional conflict theatres (Sahel, South China Sea, Taiwan Strait)
- Live API integrations (ACLED, GDELT, ReliefWeb)
- Additional OSINT challenge questions
- Mobile layout optimisation

---

## Disclaimer

OSINT Arena is an educational and analytical tool. Conflict data presented in the dashboard is a combination of public open-source intelligence and structured mock data for demonstration purposes. Casualty and displacement figures are approximations drawn from public reporting and should not be used as authoritative counts. The AI-generated situation reports are LLM outputs and do not constitute professional intelligence assessments.

---

## License

MIT — see `LICENSE` for details.

---

<p align="center">
  Built with Streamlit · PyDeck · Plotly · IBM Plex Mono · Bebas Neue
  <br/>
  <sub>OSINT ARENA v3 — Global Intelligence Operations Center</sub>
</p>
