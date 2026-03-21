# 🌐 The Geo-Locator v7

> A real-time global intelligence dashboard built with Streamlit — tracking conflicts, signals intelligence, live markets, earth events, and geopolitical risk across eight specialised tabs.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)
![pydeck](https://img.shields.io/badge/pydeck-0.8+-0066CC)
![plotly](https://img.shields.io/badge/plotly-5.18+-3F4F75)
![License](https://img.shields.io/badge/License-Research%20Use-lightgrey)

---

## Quick Start

```bash
pip install streamlit pydeck plotly pandas numpy requests yfinance \
            streamlit-autorefresh pillow
streamlit run app.py
```

Python 3.10+ required. The app runs fully without any API keys — optional keys unlock higher-quality data for four sources (see [Optional API Keys](#optional-api-keys)).

---

## Tabs

| # | Tab | Core purpose |
|---|-----|-------------|
| 1 | ⚔ Conflict Dashboard | Live conflict tracking across 7 active theatres with ACLED/GDELT feeds and SitRep export |
| 2 | 🌍 Earth Signals | Geophysical monitoring — USGS seismic, NASA EONET, NOAA space weather, FIRMS fires |
| 3 | ✊ Civil Movements | Global protest and civil unrest tracker across 12 active movements |
| 4 | 📡 Live News | 10 HLS live TV streams + server-side RSS aggregation across 6 categories |
| 5 | 🛰 Intel Dashboard | Country instability index, strategic risk, force posture, WMD tracker |
| 6 | 📻 SIGINT | Signals intelligence dashboard — COMINT, ELINT, MASINT, threat actors, space weather |
| 7 | 📊 Economic & Markets | Live market indices, commodities, forex, crypto, defence stocks, Pizza Index |
| 8 | 🏭 Facility Map | Global refinery/storage/pipeline map with per-facility live weather, satellite, and AIS |

---

## Tab Reference

### ⚔ Conflict Dashboard

Seven active conflict theatres, each with its own incident map, order of battle, timeline, escalation gauge, and live feeds:

| Theatre | Region | Escalation |
|---------|--------|-----------|
| Ukraine–Russia War | Eastern Europe | CRITICAL |
| Gaza Conflict | Middle East | CRITICAL |
| Israel–Iran War | Middle East | HIGH |
| Sudan Civil War | Sub-Saharan Africa | HIGH |
| Myanmar Civil War | Southeast Asia | HIGH |
| Pakistan–Afghanistan Conflict | South Asia | ELEVATED |
| Haiti Gang War | Caribbean | HIGH |

**Per-theatre features:**
- Live GDELT Doc API feed filtered to conflict start date, with NEW/RECENT badges
- Server-side RSS fallback (ISW, Reuters, BBC, Al Jazeera) when GDELT unavailable
- **Live ACLED events** — Armed Conflict Location & Event Data filtered by theatre country, showing event type, actor, and fatality count; falls back to GDELT GEO API without a key
- Theatre incident map (pydeck ScatterplotLayer, severity-coloured)
- Faction tracker with territory %, weapons systems, and external support
- JavaScript conflict duration clock (live to the second)
- **Situation Report Export** — one-click SitRep in Markdown, Plain Text, or HTML including ACLED data, order of battle, incident log, and escalation assessment; auto-named `sitrep_ukraine_russia_war_20260320_1145.md`

---

### 🌍 Earth Signals

- **USGS seismic** — M2.5+ daily feed, magnitude-scaled map dots, depth profile chart
- **NASA EONET** — natural events (wildfires, volcanoes, severe storms)
- **KP Index** — NOAA SWPC 1-minute planetary K-index, 24h bar chart
- **Solar activity** — NOAA SWPC solar wind speed and 10cm flux
- **NASA FIRMS** — active fire count via EONET proxy
- **Climate anomalies** — Arctic warming, SST anomalies, drought belts, permafrost
- **Weather alerts** — active cyclones, floods, and droughts

---

### ✊ Civil Movements

12 active movements (2025–2026 events): Georgia pro-EU protests, Bangladesh economic unrest, Serbia anti-government rallies, Myanmar anti-junta uprising, Kenya cost-of-living protests, Haiti gang violence, and others. Each entry carries type, scale index (0–100), size estimate, sentiment colouring, and age.

---

### 📡 Live News

**Live TV (10 HLS streams with CDN fallbacks):**
Bloomberg TV, Sky News, Euronews, Deutsche Welle, CNBC, CNN International, France 24, Al Arabiya, Al Jazeera English

**Article feeds — server-side RSS (no CORS proxy, 5-min cache):**

| Category | Sources |
|----------|---------|
| Global | Reuters, BBC World, Al Jazeera, AP News |
| Conflict | ISW, ACLED, CSIS, Defense One |
| Geopolitics | Foreign Policy, The Diplomat, Defense One |
| Science | NASA JPL, USGS, Phys.org |
| Climate | Carbon Brief |
| Space Weather | SpaceWeather.com, NOAA SWPC |

---

### 🛰 Intel Dashboard

Full-width HTML component rendered via `streamlit.components.v1.html()`:

- **Country Instability Index** — 47 countries scored 0–100, region filters, trend arrows, GDELT-blended live updates
- **Strategic Risk Overview** — live GDELT Tone API across 6 domains (Military, Cyber, Economic, Political, Climate, Pandemic); SVG ring gauge; 30-min cache
- **Intelligence Feed** — live GDELT conflict + geopolitics articles
- **Force Posture Matrix** — active military postures with signal counts
- **Infrastructure Cascade** — submarine cables, pipelines, ports, power grid risk
- **Nuclear Sites & WMD Posture** — status tracker across 37 tracked facilities
- **Chokepoints** — global maritime and land chokepoints with week-on-week change
- **Outages** — live internet outage feed

---

### 📻 SIGINT Dashboard

Dark glassmorphic design (Orbitron + JetBrains Mono + Barlow). Static intelligence databases plus client-side live polling every 60 seconds.

**Static databases:**

| Panel | Entries | Notes |
|-------|---------|-------|
| COMINT | 6 | GRU, IRGC, DPRK, MSS, SVR, Houthi intercepts |
| ELINT | 8 | Nebo-M, S-400, Don-2N, Type 346, Krasukha-4, Murmansk-BN |
| MASINT | 6 | Seismic, nuclear radiation, acoustic, chemical, thermal events |
| Threat Actors | 8 | State actors scored 0–100 with attribution confidence |
| Collection Priorities | 8 | P1–P8 with platform assignments and intel gaps |
| GPS Jamming Zones | 8 | Active GNSS jamming with radius and source |
| Orbital ISR | 8 | KH-13, Lacrosse, Yaogan, Cosmos, Planet Labs, Ofek-16 |
| Cyber Threats | 6 | APT29, APT41, Lazarus, IRGC Cyber, Sandworm, Volt Typhoon |
| OSINT Platforms | 10 | Coverage and resolution specs |
| CII Risk | 12+ | Critical infrastructure by country/sector |

**Live panels (60-second client-side polling):**
GDELT conflict + geopolitics feeds, USGS significant seismic, NOAA SWPC KP index. Sticky topbar shows global risk score, KP value, active jam count, UTC timestamp, and countdown to next poll.

---

### 📊 Economic & Markets

Full-width HTML component with 6 parallel live fetches (Yahoo Finance + CoinGecko):

| Panel | Tickers / Data | Refresh |
|-------|---------------|---------|
| KPI Strip | Brent, WTI, Fed Funds, Bitcoin, Pizza Index score | 5 min |
| Global Indices | S&P 500, Nasdaq, Dow, FTSE, DAX, CAC40, Nikkei, Hang Seng, Shanghai, Sensex, Bovespa, VIX | 5 min |
| Forex | 12 pairs — EUR/USD, GBP/USD, USD/CNY, USD/INR, USD/TRY and others | 5 min |
| Commodities | Gold, Silver, Copper, WTI, Brent, NatGas, Wheat, Corn, Soybeans | 5 min |
| Defence Stocks | RTX, LMT, NOC, GD, BA, HII, Rheinmetall, Saab, BAE, Airbus | 10 min |
| Crypto | BTC, ETH, SOL, XRP, BNB, TON with market cap (CoinGecko) | 5 min |
| Sector Heatmap | XLK, XLF, XLE, XLV, XLY, XLI, XLP, XLU, XLB, XLRE, XLC, SMH | 5 min |
| Market Posture | Dynamic label derived from live VIX + sector breadth | 5 min |

Static panels: FRED economic indicators, trade policy, supply chain chokepoints, sanctions tracker, currency crisis monitor, geopolitical risk premiums, layoffs tracker, AI/ML feed.

**🍕 Pizza Index** — commodity stress gauge tracking wheat futures, energy, mozzarella, tomato paste, and retail pizza prices in 8 cities. Wheat and energy components updated live via Yahoo Finance.

---

### 🏭 Facility Map

Global oil & gas infrastructure intelligence powered by Plotly Scattergeo:

**Dataset:**
- 62 refineries across 7 regions (North America, Europe, Middle East, Asia Pacific, Russia/CIS, Africa, South America)
- 18 storage terminals and SPRs (including US Strategic Petroleum Reserve sites)
- 15 pipeline routes as arc lines colour-coded by product type (crude=amber, LNG=red, products=teal)

**Map controls:** projection selector, region filter, status filter (Operational / Commissioning / Partial / Reduced), layer toggles for refineries, storage, and pipelines. Dot size scales with capacity — Jamnagar at 1,240 kb/d renders noticeably larger than a 100 kb/d facility.

**Facility Intelligence Panel** — select any facility from the dropdown to open four sub-tabs:

| Sub-tab | Data source | Notes |
|---------|------------|-------|
| 🌤 Weather | Open-Meteo | Current conditions + 24h wind/precip forecast. No key. |
| 🔥 NASA FIRMS | NASA FIRMS NRT CSV | VIIRS + MODIS thermal anomalies within 50km. Falls back to FIRMS interactive map embed. |
| 🛰 Satellite | Esri World Imagery | 3×3 tile mosaic stitched with PIL. Configurable zoom 10–17. Links to Google Maps, Esri Wayback, Google Earth Timelapse. |
| 🚢 AIS Tracking | MarineTraffic embed | Live vessel positions centred on facility. |

---

## Global Map Layers

37 toggle-able layers on the pydeck CARTO Dark basemap. Two are on by default:

| Default | Toggle | Data |
|---------|--------|------|
| **ON** | 🟦 Seismic Events | USGS M2.5+ live feed |
| **ON** | 🔴 Conflict Incidents | Per-theatre incident points |
| off | 🟠 Volcanic / EONET | NASA EONET natural events |
| off | 🟣 Civil Movements | Active movement markers |
| off | ⟶ Supply Arc Lines | Per-conflict supply corridors |
| off | 📅 Historical Events 2022+ | ~51 dated events |
| off | ⚡ Live Events (GDELT) | Real-time article geolocations |
| off | 🎯 Intel Hotspots | Analyst-tagged flashpoints |
| off | ⚔ Conflict Zones | Active conflict perimeters |
| off | 🏛 Military Bases | 61 bases — USA, UK, Russia, China, NATO, India, Pakistan, Israel, Saudi Arabia |
| off | ☢ Nuclear Sites | 37 sites — weapons complexes, NPPs, enrichment, test sites |
| off | ⚠ Gamma Irradiators | Medical/industrial radiation sources |
| off | 🛡 Cyber Threat Actors | APT group geolocations |
| off | 🛰 Orbital Surveillance | ISR satellite ground tracks |
| off | 📡 GPS Jamming Zones | Radius circles with severity |
| off | 🌎 CII Instability | Critical infrastructure risk |
| off | 🚢 **AIS Vessel Tracking (Live)** | AISStream.io / VesselFinder fallback, 45s cache |
| off | ✈ **OpenSky Airspace (Live)** | OpenSky Network, military callsign + emergency squawk detection |
| off | ⚔ **ACLED Conflict Events (Live)** | ACLED REST API / GDELT GEO fallback, dot size ∝ fatalities |
| off | 🚀 Spaceports | 12 active launch facilities |
| off | 🔌 Undersea Cables | 8 cables with risk score |
| off | 🛢 Pipelines | 8 pipelines including sabotaged/reduced |
| off | 🖥 AI Data Centers | 11 facilities — AWS, Azure, Meta, Google, xAI, Alibaba, Anthropic |
| off | ✈ Aviation Status | Airport status (open/closed/congested) |
| off | ⚓ Strategic Waterways | 12 waterways as PathLayer lines |
| off | 🚢 Ship Traffic Zones | 12 corridors as PathLayer lines |
| off | ⚓ Trade Route Arcs | 8 multi-waypoint routes as PathLayer |
| off | 📢 Protests | Active civil movement markers |
| off | 👥 Displacement Flows | 7 displacement corridors as ArcLayer |
| off | 💎 Critical Minerals | DRC cobalt, Chile lithium, China REE |
| off | 🔥 Active Fire Zones | NASA FIRMS detections |
| off | 🌫 Climate Anomalies | Arctic, SST, drought, permafrost |
| off | ⛈ Weather Alerts | Active cyclones, floods, droughts |

pydeck layer types in use: `ScatterplotLayer` ×32, `ArcLayer` ×6, `PathLayer` ×3, `HeatmapLayer` ×2.

---

## Architecture

```
app.py  (9,713 lines, ~604 KB)
│
├── Data constants (lines 1–3,550)
│   └── 55+ static structures:
│       CONFLICTS (7 theatres), MILITARY_BASES (61), NUCLEAR_SITES (37),
│       COUNTRY_INSTABILITY (47), HISTORICAL_EVENTS (51), MOVEMENTS (12),
│       COMINT_SIGNALS (6), ELINT_SIGNALS (8), MASINT_EVENTS (6),
│       THREAT_ACTORS (8), GPS_JAMMING_ZONES (8), ORBITAL_SURVEILLANCE (8),
│       COLLECTION_PRIORITIES (8), REFINERIES (62), STORAGE (18),
│       PIPELINES (15), and 40+ more
│
├── Persistence layer — Supabase (lines 143–260)
│   ├── _sb_creds()          reads SUPABASE_URL + SUPABASE_KEY
│   ├── _persist(table, rows) fire-and-forget POST, strips map fields, cleans numpy types
│   └── load_persisted(table) GET with 5-min cache, used as live-source fallback
│
├── Facility map dependencies (lines 261–560)
│   └── Ported from oil_gas_research.py:
│       THEME, PALETTE, rgba(), apply_theme(), err_box(), dl_button(),
│       fetch_nasa_firms(), fetch_weather(), fetch_satellite_mosaic(),
│       google_maps_satellite_url(), marinetraffic_url()
│
├── Live fetchers — 25 functions (lines 561–3,550)
│   └── All @st.cache_data decorated, TTLs 45s–3600s
│
├── Map builder (lines 3,551–2,880)
│   ├── build_global_map()   37-layer pydeck map
│   └── build_theatre_map()  per-conflict incident map
│
├── Startup (lines 3,563–4,920)
│   ├── _startup_fetch()     ThreadPoolExecutor(6) — USGS×2, EONET, KP, Solar, FIRMS
│   ├── Sidebar              37 layer toggles, 8 expanders
│   └── Global map + click panel
│
└── Tabs (lines 4,921–9,713)
    ├── tab_conflict     ACLED feed, GDELT, theatre map, SitRep export
    ├── tab_earth        Seismic charts, EONET, KP, solar
    ├── tab_civil        Civil movements map and cards
    ├── tab_news         HLS TV + RSS articles + source directory
    ├── tab_intel        HTML component — ThreadPoolExecutor(4)
    ├── tab_sigint       HTML component — ThreadPoolExecutor(9)
    ├── tab_econ         HTML component — ThreadPoolExecutor(6)
    └── tab_facility     Plotly Scattergeo + facility intelligence panel
```

### Rendering strategy

**Native Streamlit** — Conflict Dashboard, Earth Signals, Civil Movements, Live News, Facility Map. Standard `st.markdown`, `st.columns`, `st.pydeck_chart`, `st.metric`, `st.expander`.

**Embedded HTML components** — Intel Dashboard, SIGINT, and Economic & Markets use `streamlit.components.v1.html()` to render full HTML/CSS/JS dashboards. Data is injected as `const D = {...}` at render time; client-side `fetch()` + `setInterval()` handle live polling within those panels.

---

## Performance Architecture

Six `ThreadPoolExecutor` pools eliminate serial HTTP bottlenecks across the app:

| Pool | Workers | Location | Fetches |
|------|---------|----------|---------|
| `_startup_fetch()` | 6 | Module level | USGS, EONET, KP, Solar, FIRMS×2 |
| `_TPE_i` | 4 | `with tab_intel:` | Outage, risk, conflict feed, cyber feed |
| `_TPE_s` | 9 | `with tab_sigint:` | News×2, events, outage, risk, KP, USGS, cyber |
| `_TPE_e` | 6 | `with tab_econ:` | Indices, commodities, forex, defence, crypto, pizza |
| `_TPE_f` | 2 | Facility panel | Weather, NASA FIRMS |
| `ThreadPoolExecutor(9)` | 9 | `fetch_satellite_mosaic()` | 3×3 Esri tile grid |

**Additional optimisations:**
- `_HIST_SORTED` — `HISTORICAL_EVENTS` pre-sorted once at startup, referenced everywhere instead of re-sorting on each render
- GDELT live events feed deferred to second page load via `st.session_state._map_loaded`
- Intro animation sleep reduced from 10s to 3s
- Global autorefresh at 600s (10 min) — caches handle per-source freshness
- Default map layers reduced from 7 active to 2 (Seismic + Conflict); all others opt-in

---

## Persistence — Supabase Integration

Optional. Enables time-series history, dark-ship detection (AIS), and resilience against API downtime.

### Setup

**Step 1 — Create tables** (run once in Supabase SQL editor):

```sql
create table if not exists acled_events (
  id          bigserial primary key,
  inserted_at timestamptz default now(),
  event_date text, event_type text, sub_type text,
  actor1 text, actor2 text, country text, location text,
  lat float8, lon float8, fatalities int, notes text, source text
);
create table if not exists ais_positions (
  id          bigserial primary key,
  inserted_at timestamptz default now(),
  mmsi text, name text, lat float8, lon float8,
  speed float8, heading float8, type text, flag text
);
create table if not exists seismic_events (
  id          bigserial primary key,
  inserted_at timestamptz default now(),
  title text, mag float8, place text,
  depth_km float8, lon float8, lat float8, url text
);
create table if not exists gdelt_events (
  id          bigserial primary key,
  inserted_at timestamptz default now(),
  title text, source text, url text unique, time text
);
```

**Step 2 — Add to `.streamlit/secrets.toml`:**

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "your-anon-key"
```

### How it works

Every successful live fetch writes to Supabase via `_persist()` — a fire-and-forget POST that never raises or blocks the fetcher. When the live source fails, `load_persisted()` serves the most recent stored rows. The sidebar shows a green "Supabase persistence active" pill when credentials are configured.

**What gets stored and why:**

| Table | Source | Value of history |
|-------|--------|-----------------|
| `acled_events` | ACLED REST / GDELT GEO | Enables conflict trend lines and comparative SitReps |
| `ais_positions` | AISStream.io | Enables dark-ship detection (vessel stops transmitting near a chokepoint) |
| `seismic_events` | USGS | Enables regional swarm analysis over 30-day windows |
| `gdelt_events` | GDELT Doc API | Resilience against GDELT downtime; dedup on `url` column |

---

## Optional API Keys

Add to `.streamlit/secrets.toml` to enable premium data:

```toml
# ACLED — Armed Conflict Location & Event Data
# Free registration: https://acleddata.com/access-data/
ACLED_KEY   = "your_key"
ACLED_EMAIL = "your@email.com"

# AISStream.io — Live AIS vessel tracking
# Free tier: https://aisstream.io/
AISSTREAM_KEY = "your_key"

# Supabase — Persistence layer
# Free tier (500 MB): https://supabase.com
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "your-anon-key"
```

**Fallback behaviour without keys:**

| Key | Fallback |
|-----|----------|
| `ACLED_KEY` | GDELT GEO API conflict geolocations |
| `AISSTREAM_KEY` | VesselFinder public endpoint (limited count) |
| `SUPABASE_*` | No persistence; sidebar shows grey pill |
| OpenSky | No key needed — anonymous, 10 req/min |

---

## External APIs

| API | Usage | Auth | Cache TTL |
|-----|-------|------|-----------|
| USGS Earthquake Hazards | M2.5+ seismic + significant events | None | 60s / 120s |
| NASA EONET | Natural events | None | 300s |
| NOAA SWPC | KP index, space weather, solar wind | None | 300s |
| NASA FIRMS NRT CSV | Thermal anomalies (facility map) | None | 3600s |
| Open-Meteo | Current weather + 24h forecast | None | 1800s |
| Esri World Imagery | Satellite tile mosaic | None | 3600s |
| GDELT Doc API v2 | Conflict articles, OSINT signals | None | 90–120s |
| GDELT Tone API | Strategic risk scoring | None | 1800s |
| GDELT GEO API | Conflict event geolocation | None | 120s |
| OpenSky Network | Live aircraft positions | None (anon) | 60s |
| Yahoo Finance | Indices, forex, commodities, defence | None | 300–600s |
| CoinGecko | Crypto prices + market cap | None | 300s |
| MarineTraffic | AIS vessel tracking embed | None (embed) | — |
| ACLED REST API | Conflict events with fatalities | **Key required** | 120s |
| AISStream.io | Live vessel AIS positions | **Key required** | 45s |
| Supabase REST | Persistence read/write | **Key required** | 300s |
| Reuters RSS | Global news | None | 300s |
| BBC World RSS | Global news | None | 300s |
| Al Jazeera RSS | Global / Middle East | None | 300s |
| AP News RSS | Breaking news | None | 300s |
| ISW RSS | Ukraine / conflict analysis | None | 300s |
| Foreign Policy RSS | Geopolitics | None | 300s |
| The Diplomat RSS | Asia-Pacific | None | 300s |
| Defense One RSS | Military / defence | None | 300s |
| CSIS RSS | Strategic studies | None | 300s |
| 10× HLS streams | Live TV | None | CDN |

---

## Dependencies

```txt
streamlit>=1.35.0
pydeck>=0.8.0
plotly>=5.18.0
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
yfinance>=0.2.0
streamlit-autorefresh>=1.0.0
pillow>=9.0.0
```

```bash
pip install streamlit pydeck plotly pandas numpy requests \
            yfinance streamlit-autorefresh pillow
```

---

## Deployment

### Streamlit Cloud

1. Push `app.py` to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select repo and `app.py`
3. In **Advanced settings → Secrets** add your keys (ACLED, AISStream, Supabase)
4. Deploy — cold start typically 25–40 seconds

### Local

```bash
git clone https://github.com/your-repo/geo-locator
cd geo-locator
pip install -r requirements.txt
# Optional: create .streamlit/secrets.toml with your keys
streamlit run app.py
```

---

## Intro Animation

On first load the app shows a 10-second full-screen intro animation (pure HTML/CSS/JS, no video file). It displays:

- Rotating globe with 7 active conflict hotspots (Ukraine, Gaza, Iran, Sudan, Myanmar, Pakistan-Afghanistan, Haiti)
- Two orbital rings representing AIS vessels (amber dot) and OpenSky aircraft (cyan dot) with comet trails
- Feature chip grid: Conflict Dashboard, SIGINT, Economic & Markets, ACLED Live Events, AIS Vessel Tracking, OpenSky Airspace, SitRep Export, Supabase Persistence, 61 Military Bases, 37 Nuclear Sites, Pizza Index, and more
- Four HUD corners: system status, 25+ live feeds, active theatres, Supabase persistence status
- Live-scrolling ticker with current conflict headlines
- Skip button; Python sleep reduced to 3s so the server thread stays responsive

After the intro, `st.session_state["intro_shown"]` is set and the animation never re-runs for that session.

---

## Design Notes

**Background** — Four composited CSS layers: a directional `linear-gradient` deep-space base, two `radial-gradient` aurora bands animating on 18s and 26s opposing cycles (`aurora-drift` / `aurora-drift2`), a 30-point CSS star field with a 34s `stars-twinkle` pulse, and a fine `repeating-linear-gradient` scanline texture. Sidebar and tab bar use `backdrop-filter: blur(24px/16px)` glassmorphism.

**Map** — CARTO Dark basemap via pydeck. Maritime trade routes and strategic waterways use `PathLayer` with multi-waypoint geographic paths rather than straight `ArcLayer` arcs.

**SIGINT Dashboard** — Orbitron (display numerals, 900 weight), JetBrains Mono (system text), Barlow (body). Sticky topbar with backdrop-filter blur; cards use staggered `rise` CSS animation.

**Economic & Markets** — KPI strip uses `gap:1px` seamless grid with shared background. The financial panel is full-width, split 50/50 between crypto list and sector heatmap + market posture.

**Facility Map** — Scoped CSS for `.sh`, `.err-box`, `.info-box`, `.prov` injected inside `with tab_facility:` to avoid polluting the global stylesheet.

---

## Situation Report Export

At the bottom of every Conflict Dashboard theatre view. Generates a complete intelligence brief in three formats:

- **Markdown (.md)** — for wikis, GitHub, Obsidian; includes executive summary, timeline, order of battle, incidents, ACLED data, source reliability table, and assessment
- **Plain Text (.txt)** — monospaced, suitable for secure messaging or printing
- **HTML (.html)** — styled print-ready document with KPI grid, colour-coded severity tables, and watermark; open in browser → Print → Save as PDF

Reports auto-named: `sitrep_ukraine_russia_war_20260320_1145.md`

---

## Changelog

| Version | Key additions |
|---------|--------------|
| v7 | 🏭 Facility Map tab (62 refineries, 18 storage, 15 pipelines, per-facility weather/satellite/AIS/FIRMS); ACLED live integration; AIS vessel tracking; OpenSky airspace; SitRep export; Supabase persistence; parallel fetch pools across all tabs; aurora background; updated intro animation; 61 military bases; 37 nuclear sites; live Pizza Index; SIGINT redesign |
| v6 | Economic & Markets tab; live Yahoo Finance/CoinGecko; Intel Dashboard redesign; live strategic risk |
| v5 | SIGINT data structures; server-side RSS; conflict tab GDELT integration |
| v4 | Pakistan-Afghanistan conflict; Haiti Gang War; updated civil movements |
| v3 | Earth Signals tab; NOAA space weather; NASA FIRMS; HLS live TV |
| v2 | Multi-theatre conflict dashboard; faction tracker; supply line arcs |
| v1 | Global map with seismic + conflict layers |

---

## License & Usage

For **research and educational use only**. All conflict data, intelligence assessments, and geopolitical analysis derive from open sources (GDELT, ACLED, USGS, NOAA, RSS feeds, and public datasets) and must not be used for operational military, law enforcement, or commercial intelligence purposes. Live stream links point to public broadcast channels only.
