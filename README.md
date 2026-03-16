<p align="center">
  <img src="https://img.shields.io/badge/THE%20GEO--LOCATOR-v7-00c8ff?style=for-the-badge&labelColor=02040a&color=00c8ff" alt="version"/>
  <img src="https://img.shields.io/badge/Streamlit-1.35+-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white&labelColor=02040a" alt="streamlit"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=02040a" alt="python"/>
  <img src="https://img.shields.io/badge/License-MIT-00e676?style=for-the-badge&labelColor=02040a" alt="license"/>
</p>

<h1 align="center">
  <br/>THE GEO-<em>LOCATOR</em>
  <br/><sub><sup>Global Intelligence Operations Center — v7</sup></sub>
</h1>

<p align="center">
  A luxury-aesthetic, intelligence-grade Streamlit dashboard combining a multi-layer global command map,
  live earth signals, conflict monitoring, civil movement tracking, live TV streams,
  multi-source news aggregation, an intelligence operations center, and a full economic &amp; markets suite —
  all in a single dark-ops interface.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="#features">Features</a> ·
  <a href="#global-command-map">Global Command Map</a> ·
  <a href="#conflict-dashboard">Conflict Dashboard</a> ·
  <a href="#intel-dashboard">Intel Dashboard</a> ·
  <a href="#economic--markets">Economic &amp; Markets</a> ·
  <a href="#data-sources">Data Sources</a> ·
  <a href="#tech-stack">Tech Stack</a> ·
  <a href="#deployment">Deployment</a>
</p>

---

## What's New in v7

> **Compared to v3 (the previous README):**

- **REMOVED** AI Provider sidebar, AI Analyst tab, Training Arena tab, AI Situation Report Generator
- **ADDED** 🛰 Intel Dashboard — a full intelligence operations center with country instability index (50 countries), strategic risk matrix, WMD/nuclear posture tracker, geopolitical force posture, and an embedded intel feed
- **ADDED** 📊 Economic & Markets tab — a full financial intelligence suite (see below)
- **ADDED** Global Command Map — a single persistent interactive map above all tabs with 30+ toggleable intelligence layers, a live click-to-analyse Intelligence Profile panel, a live events tracker (GDELT 90s TTL), and a Today's Briefing strip
- **ADDED** Cinematic animated intro screen (skippable) with rotating globe, particle field, conflict hotspots, and live UTC clock
- **ADDED** Live TV Streams sub-tab inside Live News — HLS player supporting 15+ news channels (Bloomberg, Sky News, Euronews, DW, France 24, Al Jazeera, etc.)
- **ADDED** Israel–Iran War as a fifth conflict theatre
- **EXPANDED** Global map to 30+ optional layers across 7 sidebar expander groups
- **ADDED** GDELT-blended live instability scoring for the 50-country index
- **ADDED** Full mobile responsive CSS breakpoints (480px and 768px)
- **ADDED** `streamlit-autorefresh` dependency for live refresh

---

## Quick Start

```bash
# 1. Clone / download
git clone https://github.com/your-org/geo-locator
cd geo-locator

# 2. Install dependencies
pip install streamlit pydeck plotly pandas numpy requests streamlit-autorefresh

# 3. Launch
streamlit run app.py
```

Opens at **http://localhost:8501**

No API keys required — all live feeds degrade gracefully to rich synthetic fallback data when offline.

---

## Features

The Geo-Locator v7 is organised into a persistent Global Command Map plus six tabs, each a full analytical instrument.

### 🌐 Global Command Map *(new in v7)*

A single interactive PyDeck map that sits above all tabs and is always visible. Supports 30+ independently toggleable layers across seven sidebar groups.

**Core Layers (on by default)**

| Layer | Data Source | What it shows |
|---|---|---|
| 🟦 Seismic Events | USGS M2.5+ (60s TTL) | Magnitude-coloured earthquake dots |
| 🟠 Volcanic / EONET | NASA EONET v3 (5min TTL) | Active volcanoes, wildfires, severe storms |
| 🔴 Conflict Incidents | Structured conflict dict | All incidents across 5 active theatres |
| 🟣 Civil Movements | Static + GDELT | Protest/strike/civil unrest markers |
| ⟶ Supply Arc Lines | Conflict supply_lines | Military aid and humanitarian arcs |
| 🌡 Heatmap (Seismic) | USGS | PyDeck HeatmapLayer |
| 📅 Historical Events 2022+ | 60+ curated events | Every major event since Feb 2022 |
| ⚡ Live Events (GDELT) | GDELT Doc API (90s TTL) | Last-hour global events |

**Intelligence Layers (off by default)**

Military Bases · Nuclear Sites · Intel Hotspots · Conflict Zones · Gamma Irradiators · Cyber Threat Actors · GPS Jamming Zones · Orbital Surveillance

**Infrastructure Layers**

Spaceports · Undersea Cables · Oil & Gas Pipelines · AI Data Centers · Military Activity · Ship Traffic Zones · Trade Route Arcs

**Environment & Society Layers**

Climate Anomalies · Weather Alerts · Displacement Flows · Critical Infrastructure Instability · Internet Outages · Active Fire Hotspots · Protest Locations · Aviation Incidents

**Economic Layers**

Economic Centers · Critical Mineral Deposits · Strategic Waterways

#### Click-to-Analyse Intelligence Profile

Clicking any map marker opens a full Intelligence Profile panel showing:
- Country Instability Index score (0–100) with 4-component breakdown (Unrest, Conflict, Security, Information) — **blended live with GDELT tone data** (70% baseline / 30% live, 1h TTL)
- WMD / Nuclear Posture risk score and asset detail
- Recent Historical Events linked to the location
- Signal count badges (conflicts, military bases, nuclear sites, military activity, historical events)
- Formatted intelligence brief

#### Today's Briefing

Auto-generated text brief below the map summarising active critical conflicts, geomagnetic storm status, solar wind speed, latest historical event, live GDELT headline, and NASA FIRMS wildfire count.

---

### ⚔ Conflict Dashboard

Five active conflict theatres with intelligence-grade depth. Select theatre via radio buttons.

| Theatre | Region | Intensity | Escalation | Casualties | Displaced |
|---|---|---|---|---|---|
| Ukraine–Russia War | Eastern Europe | CRITICAL | 87/100 | ~350,000 | 14.2M |
| Gaza Conflict | Middle East | CRITICAL | 92/100 | ~46,000 | 1.9M |
| Israel–Iran War | Middle East | CRITICAL | 88/100 | ~28,000 | 0.7M |
| Sudan Civil War | Sub-Saharan Africa | HIGH | 74/100 | ~15,000 | 8.1M |
| Myanmar Civil War | Southeast Asia | HIGH | 68/100 | ~50,000 | 2.6M |

**Per-Theatre Features**

- **Live Conflict Tracker** — live-running conflict duration clock (years/months/days/hh:mm:ss), GDELT article count with new/recent badges
- **Incident Map** — PyDeck ScatterplotLayer + ArcLayer supply lines, severity-coloured, click for tooltip
- **Escalation Gauge** — Plotly indicator gauge 0–100 with colour-coded risk zones
- **Faction Tracker** — territory control %, operational strength, weapons systems, external support
- **Filterable Incident Feed** — filter by: ALL / airstrike / ground / drone / naval / rocket / cyber / humanitarian / diplomatic
- **Conflict Timeline** — Plotly scatter timeline + scrollable chronological list
- **Supply & Support Lines** — ArcLayer arcs coloured by type (Military Aid, Arms Supply, Humanitarian)
- **Media Reliability Tracker** — bar chart with editorial bias colour coding (Centre / State / Pro-Party)

**Cross-Theatre Analytics**

- Casualties & Displacement grouped bar chart
- Escalation vs Casualties scatter plot (bubbles sized by displaced population)
- Risk Assessment Matrix — 6 dimensions across all theatres (Escalation, Humanitarian, Spillover, WMD Risk, Ceasefire, Intervention)
- Global Events Timeline (2022–present) — 60+ historical events, filterable by type, severity, year, and free-text search

---

### 🌍 Earth Signals

Live geophysical monitoring.

- **Seismic Map** — USGS M2.5+ earthquakes, last 24h, magnitude-coloured PyDeck scatter
- **Kp Sparkline** — NOAA SWPC 24-hour geomagnetic index with Kp≥5 storm threshold annotation
- **M5+ Depth Profile** — 30-day scatter plot (depth vs magnitude) from USGS significant earthquakes feed
- **Significant Events List** — M4.5+ events in sidebar with category badge and date
- **Space Weather Panel** — NOAA live solar wind speed (km/s) and 10cm radio flux (sfu)

---

### ✊ Civil Movements

- Interactive PyDeck map with sentiment-coloured markers (CRIT / HIGH / MED)
- Mobilisation Scale horizontal bar chart (sorted by scale)
- Filter by type: ALL / protest / strike / civil
- Each event card shows title, location, age, size, type badge, sentiment badge, and a visual scale bar

---

### 📡 Live News

Three sub-tabs:

#### 📺 Live TV Streams *(new in v7)*

HLS video player with channel grid supporting 15 channels:

| Category | Channels |
|---|---|
| Global | Bloomberg TV, Sky News, Euronews, DW News, France 24 |
| Middle East | Al Jazeera English, Al Arabiya, i24 News |
| Asia-Pacific | NHK World, CGTN, Arirang TV |
| Conflict/Security | Wion News |
| Business | CNBC International, Reuters TV |
| Americas | PBS NewsHour |

Each channel tries multiple HLS fallback URLs in sequence. If all HLS sources fail, the player displays a direct link to the channel's official live page. 

#### 📰 Article Feeds

Multi-source RSS aggregation across 16 feeds in 6 categories (10-minute TTL). Category filter tabs: ALL · Global · Geopolitics · Conflict · Science · Climate · Space Weather.

| Category | Sources |
|---|---|
| 🌍 Global | Reuters World, BBC World, Al Jazeera, AP News |
| 🔬 Science | NASA JPL, USGS News, Phys.org Earth |
| 🏛 Geopolitics | Foreign Policy, The Diplomat, Defense One |
| ⚔ Conflict | ACLED, ISW Daily, CSIS Analysis |
| 🌿 Climate | Carbon Brief |
| 🌌 Space Weather | SpaceWeather.com, NOAA SWPC |

#### 📋 Source Directory

Full registry of all 16 RSS sources with site, category badge, and feed endpoint.

---

### 🛰 Intel Dashboard *(new in v7)*

A full intelligence operations centre rendered as a rich HTML component.

**KPI Strip**
- High-Risk Nations (instability ≥ 70) · Global Risk Score · Elevated Force Postures · Nuclear CRITICAL sites

**Panels (2-column grid layout)**

- **Country Instability Index** — 50 countries, region-filterable, sorted by score, 4-component bars (U/C/S/I), trend arrows, GDELT live blend indicator
- **Strategic Risk Overview** — SVG donut gauge (score 58 / ELEVATED), 6-dimension breakdown (Military Conflict, Cyber Threats, Economic Disruption, Political Instability, Climate/Disaster, Pandemic Risk)
- **Intelligence Feed** — curated intel/military/cyber headlines with source, category badge (ALERT/REPORT/BRIEF), and tag
- **WMD / Nuclear Posture** — 7-actor tracker (Iran, Russia, DPRK, Israel, Pakistan, China, USA) with risk score, asset description, and status badge
- **Nuclear Site Alerts** — 8-site alert table (Natanz, Fordow, Zaporizhzhia, Yongbyon, Khushab, Dimona, Bushehr, Seversk) with strike/occupation status
- **Geopolitical Force Posture** — military activity tracker (carriers, exercises, missile postures) across 10 active situations
- **Critical Infrastructure Risk** — CII instability by sector with risk bars

---

### 📊 Economic & Markets *(new in v7)*

A full financial intelligence suite rendered as a rich HTML component with live data where possible.

**Live Data Fetchers**
- Yahoo Finance (via `yfinance` JSON endpoint) — equity indices, forex, defense stocks
- CoinGecko API — cryptocurrency prices and market caps (5min TTL)

**KPI Strip**: S&P 500 · Brent Crude · VIX · BTC · USDINR

**Market Panels (4-column grid)**

| Panel | Contents |
|---|---|
| Indices | S&P 500, Nasdaq, DJIA, FTSE 100, DAX, Nikkei 225, Hang Seng, BSE Sensex |
| Forex | 20+ currency pairs vs USD, colour-coded by direction |
| Commodities | Energy (WTI, Brent, NatGas), Precious Metals, Agriculture, Industrial, Nuclear — GEO-tagged where geopolitically driven |
| Defense & Aerospace | Live prices for Lockheed Martin, Raytheon, BAE Systems, Rheinmetall, Leonardo, Thales |

**Additional Panels (3-column grid)**

| Panel | Contents |
|---|---|
| Cryptocurrency | Live CoinGecko prices, % change, market cap (BTC, ETH, BNB, SOL, XRP + more) |
| Active Sanctions | 10 sanctioned entities with scope, impact rating, and detail |
| Currency Devaluation Monitor | 8 crisis currencies with YoY depreciation bar and USD rate |

**Full-Width Panels**

- **Geopolitical Risk Premiums** — how active conflicts and tensions are priced into assets
- **Economic Intelligence** — FRED-style indicators (Fed Funds Rate, CPI, GDP, Unemployment, 10Y-2Y spread)
- **Trade & Tariffs** — active tariff rates (US→China 145%, China→US 125%, US→EU, US→Mexico)
- **Supply Chain Disruption** — Suez/Red Sea rerouting, Strait of Hormuz, Bab el-Mandeb
- **Financial Stress** — Government bonds (10 sovereigns), BTC ETF flows, Tech layoffs tracker
- **Shipping Rates** — Container (FEU), VLCC oil, Suezmax, BDI, LNG spot rates for 8 routes
- **Critical Minerals** — Lithium, Cobalt, REE, Nickel, Graphite, Uranium, Copper, Gallium with supply risk scores
- **Pizza Index (PizzaINT)** — a geopolitical/economic composite tracking cost-of-living stress via real-world pizza prices across 8 cities (modelled on The Economist's Big Mac Index methodology)

---

## Data Sources

### Live APIs (auto-cached)

| Source | Endpoint | Cache TTL | What it provides |
|---|---|---|---|
| USGS Earthquake M2.5+ | `.../2.5_day.geojson` | 60s | Last 24h global earthquakes |
| USGS Significant (M5+) | `.../significant_month.geojson` | 5min | 30-day M5+ feed |
| NASA EONET v3 | `eonet.gsfc.nasa.gov/api/v3/events` | 5min | Active volcanoes, wildfires, storms |
| NOAA SWPC Kp | `.../noaa-planetary-k-index.json` | 3min | Geomagnetic index 24h series |
| NOAA Solar Wind | `.../solar-wind-speed.json` | 5min | Solar wind speed km/s |
| NOAA 10cm Flux | `.../10cm-flux.json` | 5min | Solar radio flux sfu |
| GDELT Doc API (live events) | `api.gdeltproject.org/api/v2/doc/doc` | 90s | Last-hour global events |
| GDELT (conflict-scoped) | GDELT Doc API | 2min | Theatre-filtered conflict news |
| GDELT (instability blend) | GDELT tonechart | 60min | Country instability tone signal |
| NASA FIRMS | `firms.modaps.eosdis.nasa.gov` | 10min | Active fire pixel count |
| CoinGecko | `/api/v3/coins/markets` | 5min | Crypto prices + market caps |
| Yahoo Finance | `query1.finance.yahoo.com` | 5min | Equities, forex, defense stocks |
| RSS Feeds × 16 | Per-source endpoints | 10min | News articles |

### Structured Data (baseline, ready for live API replacement)

- `CONFLICTS` dict — 5 theatres with factions, incidents, timeline, supply lines, media sources
- `COUNTRY_INSTABILITY` — 50 countries, 4-component instability model, baseline March 2026
- `HISTORICAL_EVENTS` — 60+ curated events from 2021–2026
- `MILITARY_BASES`, `NUCLEAR_SITES`, `INTEL_HOTSPOTS`, `CONFLICT_ZONES` — global intelligence overlays
- `SHIPPING_RATES`, `CRIT_MIN_DATA`, `NUKE_ALERTS`, `WMD_POSTURE`, `GOV_BONDS` — economic and threat intelligence
- `PIZZA_INDEX` — 8-city cost-of-living composite with component breakdown

### Fallback Behaviour

Every live fetcher wraps in `try/except` and returns a synthetic fallback dataset if the network is unavailable. The app is fully functional offline.

---

## Tech Stack

### Python Dependencies

```
streamlit>=1.35.0        # UI framework
streamlit-autorefresh    # Periodic rerun for live data
pydeck>=0.9.0            # deck.gl maps (ScatterplotLayer, HeatmapLayer, ArcLayer)
plotly>=5.20.0           # Charts (gauge, scatter, bar, histogram, sparkline)
pandas>=2.0.0            # DataFrames
numpy>=1.26.0            # Synthetic data generation
requests>=2.31.0         # HTTP (APIs + RSS)
```

No `feedparser` required — RSS is parsed with the standard library (`xml.etree.ElementTree`).

### Typography & Design System

| Role | Font | Usage |
|---|---|---|
| Display / Numbers | Bebas Neue | Headlines, metric values, conflict duration clock |
| Data / Code | IBM Plex Mono | Coordinates, times, API output, labels |
| UI / Body | DM Sans | Descriptions, buttons, body copy |

Colour palette (CSS variables):

```css
--cyan:   #00c8ff   /* Primary accent — seismic, live, info */
--amber:  #ffb400   /* Warning — Kp, medium severity */
--red:    #ff3d5a   /* Critical — conflict, high magnitude */
--green:  #00e676   /* Safe — ceasefire, low risk */
--violet: #9d6eff   /* Intel, nuclear, cyber */
--orange: #ff8c42   /* High severity, faction labels */
```

### Map Layers Reference

| PyDeck Layer | Used for |
|---|---|
| `ScatterplotLayer` | Seismic, EONET, conflicts, civil movements, all intelligence overlays |
| `ArcLayer` | Supply lines, undersea cables, pipelines, trade routes, displacement flows |
| `HeatmapLayer` | Seismic density heatmap |

Base map: CARTO Dark Matter (`dark-matter-gl-style`)

---

## Sidebar Map Layer Groups

```
🌍 Core Layers          (8 toggles — on by default)
🎯 Intelligence         (8 toggles — off by default)
🏗 Infrastructure       (7 toggles)
🌊 Maritime & Trade     (3 toggles)
🌐 Environment & People (8 toggles)
🏙 Economic Overlays    (3 toggles)
📡 Signals & Space      (4 toggles)
```

---

## Live API Integration

To replace mock conflict data with live feeds, the `CONFLICTS` dict schema is designed to accept live API data directly. Minimum required fields per theatre match the ACLED, GDELT, and ReliefWeb response schemas:

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

### ACLED — Armed Conflict Location & Event Data

```python
@st.cache_data(ttl=300, show_spinner=False)
def fetch_acled(country: str, api_key: str, email: str) -> pd.DataFrame:
    url = "https://api.acleddata.com/acled/read"
    params = {
        "key": api_key, "email": email, "country": country, "limit": 50,
        "fields": "event_date|event_type|location|latitude|longitude|fatalities|notes",
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return pd.DataFrame(r.json()["data"])
```

### GDELT Project (already integrated for live events and instability blending)

The app already uses GDELT for the live events layer (90s TTL), conflict-scoped news (2min TTL), and the country instability blending (1h TTL). To extend GDELT conflict tracking, see `fetch_gdelt_conflict()` and `fetch_live_instability()` in `app.py`.

### ReliefWeb API (UN humanitarian data)

```python
@st.cache_data(ttl=600, show_spinner=False)
def fetch_reliefweb(country: str) -> list:
    url = "https://api.reliefweb.int/v1/reports"
    params = {
        "filter[field]": "country.name", "filter[value]": country,
        "limit": 10, "fields[include][]": ["title", "body", "date", "source"],
    }
    r = requests.get(url, params=params, timeout=10)
    return r.json().get("data", [])
```

---

## Deployment

### Streamlit Community Cloud (free, simplest)

1. Push to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → select `app.py` → deploy

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

### Railway

```bash
npm install -g @railway/cli
railway login && railway init && railway up
```

Add a `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

---

## Project Structure

```
geo-locator/
├── app.py              # Entire application (~6,400 lines)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

The application is intentionally single-file for Streamlit deployment simplicity. For a production split:

```
geo-locator/
├── app.py
├── requirements.txt
├── data/
│   ├── conflicts.py      # CONFLICTS dict + ACLED fetcher
│   ├── earth.py          # USGS, EONET, NOAA, FIRMS fetchers
│   ├── instability.py    # COUNTRY_INSTABILITY + GDELT blending
│   ├── intel.py          # Static intel overlays (bases, nuclear, cyber…)
│   ├── news.py           # RSS sources + fetch_rss()
│   ├── markets.py        # Yahoo Finance + CoinGecko fetchers
│   └── historical.py     # HISTORICAL_EVENTS + HLS_CHANNELS
├── ui/
│   ├── charts.py         # All Plotly chart builders
│   ├── maps.py           # build_global_map() + layer helpers
│   ├── intel_panel.py    # _render_intelligence_panel()
│   ├── econ_tab.py       # Economic & Markets HTML component
│   └── styles.py         # CSS string
└── config.py             # Constants, colour palette, layer groups
```

---

## Roadmap

Features planned for v8:

- [ ] **Live ACLED integration** — real conflict event data replacing mock incidents
- [ ] **AIS vessel tracking** — live ship positions (AISStream.io)
- [ ] **OpenSky Network** — live airspace / military aviation overlay
- [ ] **Telegram channel monitor** — open-source conflict reporting channels
- [ ] **Export to PDF** — one-click situation report export
- [ ] **User authentication** — persistent session data, saved map configurations
- [ ] **Alert webhooks** — push notifications for CRITICAL events to Slack / Discord
- [ ] **Historical playback** — scrub through conflict timelines with animated map
- [ ] **Additional conflict theatres** — Sahel, South China Sea, Taiwan Strait
- [ ] **FRED API integration** — replace static economic indicators with live FRED data

---

## Disclaimer

The Geo-Locator is an educational and analytical tool built on open-source intelligence. Conflict data is a combination of public OSINT and structured baseline data. Casualty and displacement figures are approximations drawn from public reporting and should not be used as authoritative counts. Economic data combines live feeds (Yahoo Finance, CoinGecko) with structured baseline values. Country instability scores are a model output, not official assessments.

---

## License

MIT — see `LICENSE` for details.

---

<p align="center">
  Built with Streamlit · PyDeck · Plotly · GDELT · USGS · NASA EONET · NOAA SWPC
  <br/>
  <sub>THE GEO-LOCATOR v7 — Global Intelligence Operations Center</sub>
</p>
