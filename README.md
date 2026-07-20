<div align="center">

# 🌐 THE GEO-LOCATOR
### v8

**A real-time global intelligence dashboard — conflicts, signals intelligence, live markets, earth events, and geopolitical risk, in one command console.**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37%2B-FF4B4B?logo=streamlit&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=0a0a0a)
![pydeck](https://img.shields.io/badge/pydeck-0.9%2B-4B8BBE)
![plotly](https://img.shields.io/badge/plotly-5.18%2B-3F4F75)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>

---

## 🖥 What you're looking at

```mermaid
flowchart LR
    U["🧑‍💻 You"] --> APP["🛰 THE GEO-LOCATOR<br/>Streamlit app"]
    APP --> T1["⚔ Conflict"]
    APP --> T2["🌍 Earth Signals"]
    APP --> T3["✊ Civil Movements"]
    APP --> T4["📡 Live News"]
    APP --> T5["🛰 Intel"]
    APP --> T6["📻 SIGINT · React"]
    APP --> T7["📊 Econ & Markets · React"]
    APP --> T8["🏭 Facility Map"]
    APP --> GLOBE["🌐 Global Command Globe<br/>Cobe WebGL · 37 layers"]

    style APP fill:#0a1525,stroke:#00d4ff,color:#dce8f5
    style GLOBE fill:#0a1525,stroke:#fb6415,color:#dce8f5
    style T6 fill:#0a1525,stroke:#61dafb,color:#dce8f5
    style T7 fill:#0a1525,stroke:#61dafb,color:#dce8f5
```

Only the **active tab's code runs** on any given interaction — a v8 fix for a Streamlit quirk where `st.tabs()` normally re-executes every tab's API calls on every click, no matter which one you're looking at.

---

## 🌐 Global Command Globe

The centerpiece: a rotating 3D WebGL globe ([Cobe](https://cobe.vercel.app/)) with **37 toggleable data layers**, click-to-pin sticky notes, and a hard split between what's genuinely live and what's a curated reference baseline.

```mermaid
flowchart TB
    subgraph LIVE["🟢 LIVE — refetched on every load"]
        direction LR
        L1["Seismic<br/>USGS"]
        L2["Wildfires<br/>NASA EONET"]
        L3["Cyber Threats<br/>GDELT-enriched"]
        L4["GDELT Events"]
        L5["AIS Vessels"]
        L6["Flights<br/>OpenSky"]
        L7["ACLED Events"]
    end
    subgraph REFERENCE["⚪ REFERENCE — curated baselines"]
        direction LR
        R1["Military Bases"]
        R2["Nuclear Sites"]
        R3["Undersea Cables"]
        R4["Pipelines"]
        R5["+ 26 more categories…"]
    end
    LIVE --> GLOBE(("🌐"))
    REFERENCE --> GLOBE

    style LIVE fill:#08160f,stroke:#00e5a0,color:#dce8f5
    style REFERENCE fill:#0d1220,stroke:#5a7a95,color:#dce8f5
    style GLOBE fill:#050a12,stroke:#fb6415,color:#fb6415
```

**Interactions:**
- 🖱 **Drag** to rotate · **hover** any dot for a quick preview
- 📌 **Click** a marker to pin a sticky note (title + category + key details) — multiple notes can stay open at once, each closable individually
- 🎛 37 layers grouped into 7 sidebar categories: Core, Intelligence, Infrastructure, Military & Traffic, Live Intelligence, Human & Social, Natural & Climate

---

## 📊 Feature Map

| Tab | Highlights | Stack |
|---|---|---|
| ⚔ **Conflict Dashboard** | Live-duration tracker per conflict, GDELT news overlay, casualty/timeline charts | Streamlit + Plotly |
| 🌍 **Earth Signals** | USGS earthquakes, NASA EONET, Kp-index space weather | Streamlit + pydeck |
| ✊ **Civil Movements** | Global protest/unrest tracking | Streamlit |
| 📡 **Live News** | Live TV embeds, RSS aggregation | Streamlit + `hls.js` |
| 🛰 **Intel Dashboard** | GPS jamming, cyber threats, country instability index | Streamlit |
| 📻 **SIGINT** | 12 live-polling intel panels (COMINT/ELINT/MASINT/cyber/seismic/KP) | **React 18**, precompiled |
| 📊 **Economic & Markets** | 16 panels: indices, forex, crypto, sanctions, pizza index, supply chain | **React 18**, precompiled |
| 🏭 **Facility Map** | Refineries, SPR sites, satellite tile imagery | Streamlit + pydeck |
| 🌐 **Global Command Globe** | 37-layer rotating 3D globe, click-to-pin sticky notes | Cobe (WebGL canvas) |

> **Why React only on two tabs?** SIGINT and Econ build entire UIs from JSON payloads — exactly what React is for. Everywhere else, plain Streamlit/pydeck/Plotly is simpler and better-suited, so that's what's used. See [Architecture notes](#-architecture-notes).

---

## 🚀 Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Python 3.9+. Runs fully without any API keys — optional keys unlock higher-quality data for four sources (see [Configuration](#-configuration-all-optional)).

> ⚠️ **Repo requirement:** `app.py` and `data_constants.py` must live in the same directory and be committed together — `app.py` does `from data_constants import *` at startup.

---

## 📁 Repository Structure

```
.
├── app.py                # Main app — UI, tabs, live fetchers, globe, React dashboards
├── data_constants.py     # Static reference datasets (pure data, no imports)
├── requirements.txt      # Python dependencies
└── README.md
```

---

## ⚙️ Configuration (all optional)

Fully functional out of the box on public, keyless endpoints. Add these in `.streamlit/secrets.toml` (local) or **App settings → Secrets** (Streamlit Cloud) to unlock more:

```toml
ACLED_KEY = "..."            # + ACLED_EMAIL — live ACLED conflict events
AISSTREAM_KEY = "..."        # full live AIS vessel feed
SUPABASE_URL = "..."         # + SUPABASE_KEY — persisted history/cache backend
ALERT_WEBHOOK_URL = "..."    # Slack/Discord webhook — plain HTTP, no AI involved
```

| Secret | Unlocks | Without it |
|---|---|---|
| `ACLED_KEY` + `ACLED_EMAIL` | Live ACLED conflict events | Falls back to GDELT scraping |
| `AISSTREAM_KEY` | Full live AIS vessel feed | Reduced/static set |
| `SUPABASE_URL` + `SUPABASE_KEY` | Persisted history/cache backend | In-session cache only |
| `ALERT_WEBHOOK_URL` | 🔔 Push alerts (critical conflicts, Kp≥5 storms) | Sidebar shows "🔕 off" |

---

## 🏗 Architecture Notes

```mermaid
flowchart LR
    A["Click anywhere<br/>in the app"] --> B{"Which tab is<br/>active?"}
    B -->|"only this one runs"| C["Active tab's<br/>fetch calls"]
    B -.->|"skipped entirely"| D["7 inactive tabs<br/>(v7: these ALL ran too)"]
    C --> E["st.cache_data<br/>60–90s TTL"]
    E --> F["Render"]

    style D stroke-dasharray: 5 5,color:#5a7a95
    style C fill:#08160f,stroke:#00e5a0
```

- **Lazy tab loading** — `st.tabs()` normally executes every tab's code on every rerun; a session-state selector fixed that.
- **Precompiled React** — SIGINT & Econ JSX is compiled to plain JS *ahead of time* (via Babel/Node), not transpiled live in-browser. Removes a multi-MB Babel-Standalone dependency and was the fix for slow/failed loads on the largest tab.
- **Caching & fallbacks** — every live fetch has a per-source TTL and a static-baseline fallback, so a flaky third-party API degrades gracefully.
- **Logging** — high-traffic fetcher failures are logged via Python's `logging` module instead of failing silently.
- **Module split (phase 1)** — static reference datasets live in `data_constants.py`; fetchers/UI remain in `app.py`.

---

---

## 🧰 Tech Stack

<div align="center">

| Layer | Technology | Used for |
|---|---|---|
| App framework | ![Streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?logo=streamlit&logoColor=white) | Tabs, sidebar, widgets, session state, caching |
| Language | ![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white) | Fetchers, data wrangling, orchestration |
| Maps | ![pydeck](https://img.shields.io/badge/-pydeck-4B8BBE) | Facility Map, Earth Signals map |
| 3D globe | ![WebGL](https://img.shields.io/badge/-Cobe%20%2F%20WebGL-000000?logo=webgl&logoColor=white) | Global Command Globe (37-layer rotating globe) |
| Charts | ![Plotly](https://img.shields.io/badge/-Plotly-3F4F75?logo=plotly&logoColor=white) | Timelines, casualty/media-bias charts |
| Dashboards | ![React](https://img.shields.io/badge/-React%2018-61DAFB?logo=react&logoColor=0a0a0a) | SIGINT & Economic tabs (precompiled, no runtime Babel) |
| Data | ![Pandas](https://img.shields.io/badge/-Pandas-150458?logo=pandas&logoColor=white) ![NumPy](https://img.shields.io/badge/-NumPy-013243?logo=numpy&logoColor=white) | DataFrames, numeric ops on live feeds |
| Networking | ![Requests](https://img.shields.io/badge/-Requests-000000?logo=python&logoColor=white) | USGS, GDELT, EONET, ACLED, AIS, Yahoo, CoinGecko, NOAA, Supabase |
| Video | ![hls.js](https://img.shields.io/badge/-hls.js-E113A7) | Live TV stream embeds |
| Images | ![Pillow](https://img.shields.io/badge/-Pillow-3776AB?logo=python&logoColor=white) | Satellite tile mosaic stitching |
| Persistence (optional) | ![Supabase](https://img.shields.io/badge/-Supabase-3ECF8E?logo=supabase&logoColor=white) | History/cache backend via REST API |
| Alerts (optional) | ![Slack](https://img.shields.io/badge/-Slack%20%2F%20Discord-4A154B?logo=slack&logoColor=white) | Webhook push alerts — plain HTTP, no AI |

</div>

### External data sources

<div align="center">

![USGS](https://img.shields.io/badge/-USGS-000000) ![NASA EONET](https://img.shields.io/badge/-NASA%20EONET-0B3D91) ![GDELT](https://img.shields.io/badge/-GDELT-1a1a1a) ![ACLED](https://img.shields.io/badge/-ACLED-c0392b) ![NOAA SWPC](https://img.shields.io/badge/-NOAA%20SWPC-0073CF) ![Yahoo Finance](https://img.shields.io/badge/-Yahoo%20Finance-6001D2) ![CoinGecko](https://img.shields.io/badge/-CoinGecko-8dc63f) ![AISStream](https://img.shields.io/badge/-AISStream.io-00A3E0) ![OpenSky](https://img.shields.io/badge/-OpenSky%20Network-004A99)

</div>

---

## 🧭 Known Limitations

- Curated baselines (military postures, nuclear-site status, instability index) are a point-in-time snapshot, not continuously verified.
- "SIGINT"-flavored panels (MASINT/ELINT/COMINT) are derived/illustrative signal blends, not real classified feeds.
- The globe's line-shaped datasets (cables, pipelines, trade routes) render as endpoints, not true connecting arcs — a real trade-off of the WebGL-canvas approach vs. the old pydeck `ArcLayer`.
- Free-tier public APIs (GDELT, ACLED without a key, EONET, USGS) are rate-limited under heavy concurrent use.

---

## 📄 License

Released under the [MIT License](LICENSE) — free to use, modify, and distribute, including commercially, with attribution and no warranty.

<div align="center">

---

*Built with Streamlit · pydeck · Plotly · React · Cobe*

</div>
