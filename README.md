# 🌐 The Geo-Locator v7

> A real-time global intelligence dashboard built with Streamlit — tracking conflicts, signals intelligence, live markets, earth events, and geopolitical risk in a single interface.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)
![pydeck](https://img.shields.io/badge/pydeck-0.8+-0066CC)
![License](https://img.shields.io/badge/License-Research%20Use-lightgrey)

---

## Overview

The Geo-Locator is a 8,300-line single-file Streamlit application that aggregates live data from 25+ external APIs into seven specialized intelligence dashboards. It is designed for open-source researchers, analysts, and anyone who needs a real-time picture of global geopolitical, economic, and signals intelligence in one place.

The app runs entirely in a browser via Streamlit, with no database required. All live data is fetched server-side using Python's `requests` library and cached with `@st.cache_data` TTLs ranging from 45 seconds (AIS vessels) to 60 minutes (country instability scores).

---

## Quick Start

```bash
# 1. Install dependencies
pip install streamlit pydeck plotly pandas numpy requests streamlit-autorefresh

# 2. Run
streamlit run app.py
```

Python 3.10 or later is required. The app runs fully without any API keys — several data sources have optional keys that unlock higher-quality or higher-rate-limit feeds (see [API Keys](#optional-api-keys)).

---

## Tabs & Features

### ⚔ Conflict Dashboard

Real-time conflict tracking across seven active theatres:

| Theatre | Region |
|---|---|
| Ukraine–Russia War | Eastern Europe |
| Gaza Conflict | Middle East |
| Israel–Iran War | Middle East |
| Sudan Civil War | Sub-Saharan Africa |
| Myanmar Civil War | Southeast Asia |
| Pakistan–Afghanistan Conflict | South Asia |
| Haiti Gang War | Caribbean |

Each theatre includes:

- **Live GDELT feed** — Articles fetched from GDELT Doc API 2.0, filtered to the conflict start date, with recency badges (NEW / RECENT)
- **RSS fallback** — Server-side Python RSS parsing (ISW, Reuters, BBC, Al Jazeera) when GDELT is unavailable
- **Live ACLED events** — Armed Conflict Location & Event Data filtered by theatre country, showing event type, actor, and fatality count
- **Theatre incident map** — pydeck ScatterplotLayer with per-incident severity colouring and tooltips
- **Order of battle** — Faction tracker with territory control %, weapons systems, and external support networks
- **Conflict timeline** — Key events from conflict start to present
- **Escalation gauge** — 0–100 index with CRITICAL/HIGH/ELEVATED/MODERATE thresholds
- **Live conflict clock** — JavaScript countdown showing duration to the second
- **📋 Situation Report Export** — One-click SitRep generation in Markdown, Plain Text, or HTML formats including ACLED live data, order of battle, incident log, and escalation assessment

---

### 🌍 Earth Signals

Global geophysical and environmental monitoring:

- **Live seismic events** — USGS Earthquake Hazards API, significant events and M4.5+ feed with magnitude-proportional markers
- **EONET natural events** — NASA EONET API for wildfires, volcanic activity, severe storms, and other hazards
- **KP Index / Space Weather** — NOAA SWPC 1-minute planetary K-index with 24h bar chart
- **Solar activity** — NOAA SWPC solar flare and geomagnetic storm data
- **Active fire count** — NASA FIRMS satellite fire detection aggregated by region
- **Climate anomalies** — Arctic warming, drought belts, SST anomalies, permafrost events
- **Weather alerts** — Cyclones, floods, droughts, and severe weather by region

---

### ✊ Civil Movements

Global protest, strike, and civil unrest tracker:

- 12 active movements (2025–2026) including Georgia pro-EU protests, Bangladesh economic unrest, Serbia anti-government rallies, Myanmar anti-junta uprisings
- Each entry has type (protest/strike/civil), scale index (0–100), size estimate, and age
- Map layer with sentiment-based colouring (CRIT/HIGH/MED)
- Farmers' Protest removed as a resolved case; updated to current 2025–2026 events

---

### 📡 Live News

Three-panel news intelligence feed:

**📺 Live TV Streams** — 10 HLS channels with multi-source fallbacks:
Bloomberg TV, Sky News, Euronews, DW, CNBC, CNN International, France 24, Al Arabiya, Al Jazeera

**📰 Article Feeds** — Server-side RSS aggregation (no CORS proxy) across six categories:

| Category | Sources |
|---|---|
| Global | Reuters, BBC World, Al Jazeera, AP News |
| Conflict | ISW, ACLED, CSIS, Defense One |
| Geopolitics | Foreign Policy, The Diplomat, Defense One |
| Science | NASA JPL, USGS, Phys.org |
| Climate | Carbon Brief |
| Space Weather | SpaceWeather.com, NOAA SWPC |

**📋 Source Directory** — Full metadata for all news sources and HLS streams.

---

### 🛰 Intel Dashboard

Geopolitical intelligence overview rendered as a full-width HTML dashboard:

- **Country Instability Index** — Scored 0–100 with U/C/S/I sub-components, region pill filters, trend arrows
- **Strategic Risk Overview** — Live-scored via GDELT Tone API across 6 domains (Military, Cyber, Economic, Political, Climate, Pandemic) with SVG ring gauge
- **Intelligence Feed** — Live GDELT conflict + geopolitics articles with source badges
- **Force Posture Matrix** — Active military postures with signal counts and risk scores
- **Infrastructure Cascade** — Submarine cables, pipelines, ports, and power grid risk by region
- **Nuclear Sites & WMD Posture** — NUKE_ALERTS with status and WMD doctrine tracker
- **Chokepoints** — Global maritime and land chokepoints with week-on-week change
- **Outages** — Live internet and infrastructure outage feed

---

### 📻 SIGINT Dashboard

Signals intelligence dashboard with a dark glassmorphic design (Orbitron + JetBrains Mono + Barlow typefaces):

**Static intelligence databases:**

| Panel | Data |
|---|---|
| COMINT | 6 active communications intercepts (GRU, IRGC, DPRK, MSS, SVR, Houthi) |
| ELINT | 8 tracked radar/EW systems (Nebo-M, S-400, Don-2N, Type 346, Krasukha-4, Murmansk-BN) |
| MASINT | 6 measurement/signature events (seismic, nuclear radiation, acoustic, chemical, thermal) |
| Threat Actors | 8 state actors with threat level 0–100, domain tags, attribution confidence, active operations |
| Collection Priorities | P1–P8 intelligence gaps with platform assignments and intel gap assessments |
| GPS Jamming Zones | 8 active GNSS jamming zones with radius and attributed source |
| Orbital ISR | 8 satellite systems (KH-13, Lacrosse SAR, Yaogan-41, Cosmos-2558, Planet Labs, Maxar, Starlink ISR, Ofek-16) |
| Cyber Threats | APT29, APT41, Lazarus, IRGC Cyber, Sandworm, Volt Typhoon |
| OSINT Platforms | 10 collection platforms with coverage and resolution specs |
| CII Risk | Critical infrastructure instability by country/sector, sorted by risk score |

**Live panels (client-side polling every 60 seconds):**
- Live OSINT/SIGINT feed — GDELT Doc API (war/conflict + geopolitics queries)
- Cyber signals — GDELT (cyber/espionage query)
- Seismic MASINT — USGS significant hourly feed
- KP Space Weather — NOAA SWPC 1-minute K-index with 24h bar history
- Sticky topbar — global risk score, KP value, active jam count, live UTC timestamp, countdown to next poll

---

### 📊 Economic & Markets

Full-width economic intelligence dashboard (rendered as an embedded HTML/JS component):

**Live data (Yahoo Finance, CoinGecko, FRED):**

| Panel | Data | Refresh |
|---|---|---|
| KPI Strip | Brent/WTI crude, Fed Funds Rate, Bitcoin price, Pizza Index score | 5 min |
| Global Indices | S&P 500, Nasdaq, Dow, FTSE, DAX, CAC40, Nikkei, Hang Seng, Shanghai, Sensex, Bovespa, VIX | 5 min |
| Forex | 12 currency pairs including EUR/USD, GBP/USD, USD/CNY, USD/INR, USD/TRY | 5 min |
| Commodities | Gold, Silver, Copper, Platinum, WTI, Brent, NatGas, Wheat, Corn, Soybeans | 5 min |
| Defense Stocks | RTX, LMT, NOC, GD, BA, HII, Rheinmetall, Saab, BAE Systems, Airbus | 10 min |
| Crypto | BTC, ETH, SOL, XRP, BNB, TON with market cap (CoinGecko) | 5 min |
| Sector Heatmap | 12 ETFs: XLK, XLF, XLE, XLV, XLY, XLI, XLP, XLU, XLB, XLRE, XLC, SMH | 5 min |
| Market Posture | Dynamic label (RISK ON/CAUTION/RISK OFF/CASH) derived from live VIX + sector breadth | 5 min |
| BTC ETF Tracker | Net flow, estimated flow, inflow/outflow badge | Static |

**Static intelligence panels:**
- Economic Indicators (FRED: Fed Funds Rate, Unemployment, 10Y-2Y Spread, Fed Balance Sheet, Real GDP Growth, CPI)
- Trade Policy (WTO tariff restrictions and applied rates)
- Supply Chain (chokepoint status, shipping rates, critical minerals)
- Sanctions Tracker (10 sanctioned entities with detail)
- Currency Crisis Monitor (10 countries with YoY devaluation %)
- Geopolitical Risk Premiums (Red Sea, Hormuz, Black Sea, Taiwan, Suez, etc.)
- 🍕 Pizza Index — commodity stress gauge tracking wheat futures, energy, mozzarella, tomato paste, and retail pizza prices in 8 cities; components updated live via Yahoo Finance
- Layoffs Tracker
- Fires by Region (NASA FIRMS aggregated)
- AI/ML sector feed (live via GDELT)

---

## Global Map Layers

The sidebar exposes 37 toggle-able map layers built on **pydeck** (Mapbox GL / CARTO Dark basemap):

### Intelligence & Military
| Toggle | Data |
|---|---|
| 🏛 Military Bases | 61 bases across USA, UK, Russia, China, NATO, India, Pakistan, Israel, Saudi Arabia |
| ☢ Nuclear Sites | 37 sites: weapons complexes, NPPs, enrichment facilities, test sites (USA, Russia, UK, France, China, India, Pakistan, DPRK, Iran) |
| ⚠ Gamma Irradiators | Medical/industrial radiation sources |
| 🛡 Cyber Threat Actors | APT group geolocations with targeting info |
| 🛰 Orbital Surveillance | ISR satellite ground tracks |
| 📡 GPS Jamming Zones | Radius circles with severity colouring |
| 🎯 Intel Hotspots | Analyst-tagged geopolitical flashpoints |
| ⚔ Conflict Zones | Active conflict perimeters |

### Live Intelligence (new)
| Toggle | Source | Notes |
|---|---|---|
| 🚢 AIS Vessel Tracking | AISStream.io / VesselFinder fallback | 45s cache, classifies Tanker/Military/Cargo |
| ✈ OpenSky Airspace | OpenSky Network (anonymous) | 60s cache, military callsign + emergency squawk detection |
| ⚔ ACLED Conflict Events | ACLED REST API / GDELT GEO fallback | 2 min cache, dot size proportional to fatalities |

### Maritime & Transport
| Toggle | Data |
|---|---|
| 🚢 Ship Traffic Zones | 12 zones as PathLayer lines with traffic status colour |
| ⚓ Trade Route Arcs | 8 multi-waypoint routes (Suez, Cape reroute, Trans-Pacific, etc.) as PathLayer |
| ⚓ Strategic Waterways | 12 waterways as PathLayer lines (red=disrupted, amber=reduced, cyan=normal) |
| ✈ Military Activity | 10 active carrier strike groups, exercise zones, and strike packages |
| ✈ Aviation Status | Airport status (open/closed/congested) |

### Infrastructure
| Toggle | Data |
|---|---|
| 🔌 Undersea Cables | 8 cables with risk score and status |
| 🛢 Pipelines | 8 pipelines including Nord Stream (sabotaged), Druzhba (reduced) |
| 🖥 AI Data Centers | 11 facilities: AWS, Azure, Meta, Google, xAI, Alibaba, Anthropic |
| 🚀 Spaceports | 12 active launch facilities |
| 📡 Internet Outages | Live outage detections |
| 💰 Economic Centers | Major financial hubs with GDP |
| 🌎 CII Instability | Critical infrastructure risk by country/sector |

### Natural & Climate
| Toggle | Data |
|---|---|
| 🟦 Seismic Events | USGS live feed, magnitude-scaled dots |
| 🟠 Volcanic / EONET | NASA EONET natural events |
| 🌡 Heatmap | Seismic energy density HeatmapLayer |
| 🌫 Climate Anomalies | Arctic warming, SST, drought belts, permafrost |
| ⛈ Weather Alerts | Active cyclones, floods, droughts |
| 🔥 Active Fire Zones | NASA FIRMS satellite fire detections |
| 👥 Displacement Flows | 7 displacement corridors as ArcLayer |
| 💎 Critical Minerals | DRC cobalt, Chile lithium, China REE, etc. |
| 📢 Protests | Active civil movement markers |

---

## Architecture

```
app.py  (8,372 lines, ~524 KB)
│
├── Data constants (lines 1–460)
│   └── 55 static data structures (CONFLICTS, MILITARY_BASES, NUCLEAR_SITES,
│       COMINT_SIGNALS, THREAT_ACTORS, COUNTRY_INSTABILITY, …)
│
├── Live fetchers (lines 910–1700)
│   ├── fetch_usgs()                   USGS seismic    ttl=60s
│   ├── fetch_eonet()                  NASA EONET      ttl=300s
│   ├── fetch_kp()                     NOAA SWPC KP    ttl=180s
│   ├── fetch_rss_conflict()           Multi-source RSS ttl=120s
│   ├── fetch_gdelt_conflict()         GDELT Doc API   ttl=120s
│   ├── fetch_live_global_events()     GDELT Doc API   ttl=90s
│   ├── fetch_solar()                  NOAA Solar      ttl=300s
│   ├── fetch_firms_count()            NASA FIRMS      ttl=600s
│   ├── fetch_outage_feed()            Outage RSS      ttl=180s
│   ├── fetch_acled_events()           ACLED / GDELT   ttl=120s  ← new
│   ├── fetch_ais_vessels()            AISStream.io    ttl=45s   ← new
│   ├── fetch_opensky_flights()        OpenSky Network ttl=60s   ← new
│   ├── fetch_news_rss()               Multi-cat RSS   ttl=300s
│   ├── fetch_live_strategic_risk()    GDELT Tone API  ttl=1800s
│   ├── fetch_live_pizza_index()       Yahoo Finance   ttl=600s
│   ├── fetch_live_indices()           Yahoo Finance   ttl=300s
│   ├── fetch_live_commodities()       Yahoo Finance   ttl=300s
│   ├── fetch_live_forex()             Yahoo Finance   ttl=300s
│   ├── fetch_live_defense()           Yahoo Finance   ttl=600s
│   └── fetch_live_crypto()            CoinGecko       ttl=300s
│
├── Map builder (lines 2028–2520)
│   ├── build_global_map()     37-layer pydeck map
│   └── build_theatre_map()    Per-conflict incident map
│
├── Sidebar (lines 2600–2800)
│   └── 37 layer toggles in 8 expanders
│
└── Tabs (lines 4010–8105)
    ├── tab_conflict      Conflict Dashboard + SitRep export
    ├── tab_earth         Earth Signals
    ├── tab_civil         Civil Movements
    ├── tab_news          Live News (TV + Articles + Directory)
    ├── tab_intel         Intel Dashboard (HTML component)
    ├── tab_sigint        SIGINT Dashboard (HTML component)
    └── tab_econ          Economic & Markets (HTML component)
```

### Rendering approach

The app uses two rendering strategies:

1. **Native Streamlit** — Conflict Dashboard, Earth Signals, Civil Movements, Live News. All use `st.markdown`, `st.columns`, `st.pydeck_chart`, `st.metric`, `st.expander`.

2. **Embedded HTML components** — Intel Dashboard, SIGINT, and Economic & Markets tabs use `streamlit.components.v1.html()` to render full HTML/CSS/JS dashboards. This allows custom fonts, CSS variables, animations, and client-side live polling via `fetch()` + `setInterval()`. Data is passed from Python to JavaScript as a JSON-serialized payload injected into a `const D = {...}` declaration.

---

## External APIs

| API | Usage | Auth | Rate Limit |
|---|---|---|---|
| USGS Earthquake Hazards | Seismic events | None | Unlimited |
| NASA EONET | Natural events | None | Unlimited |
| NOAA SWPC | KP index, space weather alerts | None | Unlimited |
| NOAA SWPC Solar | Solar flare data | None | Unlimited |
| NASA FIRMS | Active fire counts | None | Unlimited |
| NASA JPL RSS | Space science news | None | Unlimited |
| GDELT Doc API v2 | Conflict articles, OSINT signals | None | ~10 req/min |
| GDELT Tone API | Strategic risk scoring | None | ~10 req/min |
| GDELT GEO API | Conflict event geolocation (ACLED fallback) | None | ~10 req/min |
| OpenSky Network | Live aircraft positions | None (anonymous) | 10 req/min |
| Yahoo Finance (yfinance) | Indices, forex, commodities, crypto | None | Soft limit |
| CoinGecko | Crypto prices + market cap | None | 30 req/min |
| FRED (Federal Reserve) | Economic indicators | None | 120 req/min |
| ACLED REST API | Conflict events with fatalities | **Key required** | By plan |
| AISStream.io | Live vessel AIS positions | **Key required** | By plan |
| Reuters RSS | Global news | None | Fair use |
| BBC World RSS | Global news | None | Fair use |
| Al Jazeera RSS | Global/Middle East news | None | Fair use |
| AP News RSS | Breaking news | None | Fair use |
| ISW RSS | Ukraine/conflict analysis | None | Fair use |
| Foreign Policy RSS | Geopolitics | None | Fair use |
| The Diplomat RSS | Asia-Pacific | None | Fair use |
| Defense One RSS | Military/defense | None | Fair use |
| CSIS RSS | Strategic studies | None | Fair use |
| Carbon Brief RSS | Climate | None | Fair use |
| SpaceWeather.com RSS | Solar/aurora | None | Fair use |
| 10× HLS streams | Live TV (Bloomberg, Sky News, DW, CNN, etc.) | None | CDN |

---

## Optional API Keys

Create `.streamlit/secrets.toml` in the project root to enable premium data sources:

```toml
# ACLED — Armed Conflict Location & Event Data
# Free registration at: https://acleddata.com/access-data/
ACLED_KEY   = "your_acled_api_key"
ACLED_EMAIL = "your@email.com"

# AISStream.io — Live AIS vessel tracking
# Free tier at: https://aisstream.io/
AISSTREAM_KEY = "your_aisstream_api_key"

# OpenSky Network — No key required
# Anonymous access: 10 requests/min, sufficient for 60s polling
```

Without keys the app falls back gracefully:
- **ACLED** → GDELT GEO API conflict event geolocation
- **AISStream** → VesselFinder public endpoint (limited vessel count)
- **OpenSky** → Works without a key (anonymous rate limit)

---

## Dependencies

```txt
streamlit>=1.35.0
pydeck>=0.8.0
plotly>=5.18.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
streamlit-autorefresh>=1.0.0
```

Install all at once:

```bash
pip install streamlit pydeck plotly pandas numpy requests streamlit-autorefresh
```

---

## Deployment (Streamlit Cloud)

1. Push `app.py` to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Select your repo and `app.py`
4. In **Advanced settings → Secrets**, add your API keys:
   ```toml
   ACLED_KEY     = "..."
   ACLED_EMAIL   = "..."
   AISSTREAM_KEY = "..."
   ```
5. Deploy — the app cold-starts in ~30–45 seconds

The app auto-refreshes every 300 seconds via `streamlit-autorefresh`. Individual data sources have their own cache TTLs so data is never more stale than the TTL of the slowest source.

---

## Data Freshness

| Data Type | Source | TTL | Fallback |
|---|---|---|---|
| Seismic | USGS | 60s | Static empty |
| Space weather | NOAA SWPC | 180s | Static KP 3.7 |
| GDELT articles | GDELT Doc API | 120s | Server-side RSS |
| ACLED events | ACLED REST | 120s | GDELT GEO API |
| AIS vessels | AISStream.io | 45s | VesselFinder |
| Airspace | OpenSky | 60s | Empty layer |
| Market indices | Yahoo Finance | 300s | Static baseline |
| Crypto prices | CoinGecko | 300s | Static prices |
| Sector ETFs | Yahoo Finance | 300s | Static heatmap |
| Strategic risk | GDELT Tone | 1800s | Static score 58 |
| Pizza Index | Yahoo Finance | 600s | Static values |
| Country instability | GDELT Tone | 3600s | Baseline scores |
| TV streams | HLS CDN | Live | Direct site link |
| News RSS | Multiple | 300s | Source directory |

---

## Situation Report Export

Located at the bottom of every Conflict Dashboard theatre. Generates a full intelligence brief in three formats:

**Markdown** — Suitable for wikis, GitHub, Obsidian. Includes executive summary, timeline, order of battle, recent incidents, ACLED data, intelligence sources, and assessment.

**Plain Text** — Clean monospaced format for secure messaging, email, or printing.

**HTML** — Styled print-ready document with KPI grid, colour-coded severity tables, faction matrix, and a watermark. Open in browser and use Print → Save as PDF.

Reports are auto-named: `sitrep_ukraine_russia_war_20260320_1145.md`

---

## Design Notes

**Map** — CARTO Dark basemap via pydeck. Layer types used: `ScatterplotLayer` (32 instances), `ArcLayer` (6), `PathLayer` (3), `HeatmapLayer` (2). Trade routes and waterways use PathLayer with multi-waypoint geographic paths rather than straight ArcLayer arcs.

**Intel Dashboard** — Native Streamlit with `streamlit.components.v1.html()` for the dashboard panels. Font: IBM Plex Mono + system font stack.

**SIGINT Dashboard** — Orbitron (display numerals), JetBrains Mono (system text), Barlow (body). Scanline overlay via CSS `repeating-linear-gradient`. Sticky topbar with backdrop-filter blur. Cards use CSS animation `rise` staggered by nth-child.

**Economic & Markets** — Orbitron + JetBrains Mono. KPI strip uses `gap:1px` seamless grid. finPanel sits in its own full-width row split 50/50 (crypto left, sector heatmap + market posture right).

---

## License & Usage

This application is built for **research and educational use only**. All conflict data, intelligence assessments, and geopolitical analysis are derived from open sources (GDELT, ACLED, USGS, NOAA, RSS feeds, and publicly available datasets) and should not be used for operational military, law enforcement, or commercial intelligence purposes.

Live stream links are provided for public broadcast channels only. No proprietary or classified data is used or implied.

---

## Changelog

| Version | Key Changes |
|---|---|
| v7 | SIGINT tab, ACLED integration, AIS vessel tracking, OpenSky airspace, SitRep export, PathLayer maritime routes, 61 military bases, 37 nuclear sites, live Pizza Index, live sector heatmap |
| v6 | Economic & Markets tab, live Yahoo Finance/CoinGecko feeds, Intel Dashboard redesign, live strategic risk |
| v5 | SIGINT data structures, live news RSS server-side, conflict tab GDELT integration |
| v4 | Pakistan-Afghanistan conflict, Haiti Gang War, updated civil movements |
| v3 | Earth Signals tab, NOAA space weather, NASA FIRMS, HLS live TV |
| v2 | Multi-theatre conflict dashboard, faction tracker, supply line arcs |
| v1 | Global map with seismic + conflict layers |
