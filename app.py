"""
THE GEO-LOCATOR v7
==============
Changes from v5:
  - FIXED: YT_CAT_NAMES, CAT_TABS_NEWS, CAT_NAMES_ART were undefined → defined properly
  - REMOVED: AI Provider sidebar section
  - REMOVED: Analyst Profile sidebar section
  - REMOVED: Training Arena tab
  - REMOVED: AI Analyst tab
  - REMOVED: AI Situation Report Generator from Conflict Dashboard
  - REMOVED: call_ai() and all AI-related session state

Run:
    pip install streamlit pydeck plotly pandas numpy requests streamlit-autorefresh
    streamlit run app.py
"""

# ── Pre-defined data constants (defined early to prevent NameError on any line) ──
SHIPPING_RATES = [
    {"route":"Shanghai → Rotterdam","type":"Container","rate":4820,"unit":"$/FEU","change":12.4,"status":"Elevated","note":"Red Sea rerouting via Cape"},
    {"route":"Shanghai → Los Angeles","type":"Container","rate":3140,"unit":"$/FEU","change":4.1,"status":"Normal","note":"Trans-Pacific stable"},
    {"route":"Rotterdam → New York","type":"Container","rate":1850,"unit":"$/FEU","change":2.8,"status":"Normal","note":"North Atlantic corridor"},
    {"route":"Arabian Gulf → Japan","type":"VLCC Oil","rate":52000,"unit":"$/day","change":-3.2,"status":"Reduced","note":"Hormuz risk premium easing"},
    {"route":"W.Africa → US Gulf","type":"Suezmax Oil","rate":38500,"unit":"$/day","change":1.5,"status":"Normal","note":"WAF corridor steady"},
    {"route":"Baltic Dry Index","type":"BDI","rate":1842,"unit":"points","change":5.8,"status":"Rising","note":"Iron ore and grain demand"},
    {"route":"LNG Spot (JKM Asia)","type":"LNG","rate":12.40,"unit":"$/MMBtu","change":8.2,"status":"Elevated","note":"Winter demand residual"},
    {"route":"SCFI Composite","type":"Index","rate":1620,"unit":"points","change":11.6,"status":"Rising","note":"Container freight composite"},
]

CRIT_MIN_DATA = [
    {"mineral":"Lithium",  "price":13.50,"unit":"$/kg","change":-18.4,"supply_risk":72,"top_producer":"Australia 46%","use":"EV batteries","col":"#34d399"},
    {"mineral":"Cobalt",   "price":26.80,"unit":"$/kg","change":-8.2, "supply_risk":85,"top_producer":"DRC 70%",      "use":"Battery cathodes","col":"#38bdf8"},
    {"mineral":"REE (Nd)", "price":68.00,"unit":"$/kg","change":4.1,  "supply_risk":88,"top_producer":"China 60%",    "use":"EV motors / wind","col":"#fbbf24"},
    {"mineral":"Nickel",   "price":15.40,"unit":"$/kg","change":-12.1,"supply_risk":55,"top_producer":"Indonesia 37%","use":"Battery anodes","col":"#a78bfa"},
    {"mineral":"Graphite", "price":0.48, "unit":"$/kg","change":-22.0,"supply_risk":91,"top_producer":"China 79%",    "use":"Battery anodes","col":"#fb923c"},
    {"mineral":"Uranium",  "price":106.5,"unit":"$/lb","change":0.5,  "supply_risk":48,"top_producer":"Kazakhstan 43%","use":"Nuclear fuel","col":"#f87171"},
    {"mineral":"Copper",   "price":8.92, "unit":"$/kg","change":3.2,  "supply_risk":42,"top_producer":"Chile 28%",   "use":"Grid / EVs / electronics","col":"#fb923c"},
    {"mineral":"Gallium",  "price":320,  "unit":"$/kg","change":45.0, "supply_risk":95,"top_producer":"China 80%",   "use":"Semiconductors","col":"#f87171"},
]

NUKE_ALERTS = [
    {"site":"Natanz (Iran)","status":"STRUCK","level":"CRITICAL","detail":"Destroyed by IDF Mar 2026 — centrifuge halls collapsed","col":"#ff3d5a"},
    {"site":"Fordow (Iran)","status":"DESTROYED","level":"CRITICAL","detail":"Bunker-buster strike Feb 2026 — enrichment halted","col":"#ff3d5a"},
    {"site":"Zaporizhzhia NPP","status":"OCCUPIED","level":"CRITICAL","detail":"Russian occupation continues — IAEA monitoring disrupted","col":"#ff3d5a"},
    {"site":"Yongbyon (DPRK)","status":"ACTIVE","level":"HIGH","detail":"Plutonium reactor operational — recent satellite imagery confirms","col":"#ff8c42"},
    {"site":"Khushab (Pakistan)","status":"ACTIVE","level":"HIGH","detail":"Plutonium production ongoing — arsenal est. 165 warheads","col":"#ff8c42"},
    {"site":"Dimona (Israel)","status":"UNDECLARED","level":"MED","detail":"Estimated 90 warheads — not IAEA member","col":"#ffb400"},
    {"site":"Bushehr NPP (Iran)","status":"OPERATIONAL","level":"MED","detail":"1000MW — IAEA monitored but access reduced post-strikes","col":"#ffb400"},
    {"site":"Seversk (Russia)","status":"ACTIVE","level":"HIGH","detail":"Pu-239 production — expanded capacity 2025","col":"#ff8c42"},
]

WMD_POSTURE = [
    {"actor":"Iran","type":"Ballistic Missiles","status":"Elevated","assets":"Shahab-3, Fattah-2 hypersonic","risk":82,"col":"#ff3d5a"},
    {"actor":"Russia","type":"Nuclear Posture","status":"Elevated","assets":"ICBM + tactical — doctrine lowered threshold","risk":78,"col":"#ff3d5a"},
    {"actor":"DPRK","type":"ICBM/Nuclear","status":"Active","assets":"Hwasong-17/18 — 50+ warheads est.","risk":70,"col":"#ff8c42"},
    {"actor":"Israel","type":"Second Strike","status":"Alert","assets":"Jericho III ICBM — submarines — ~90 warheads","risk":45,"col":"#ffb400"},
    {"actor":"Pakistan","type":"Nuclear","status":"Normal","assets":"~165 warheads — India-Pakistan tension elevated","risk":55,"col":"#ff8c42"},
    {"actor":"China","type":"Nuclear Buildup","status":"Expanding","assets":"400 to 1500 warhead expansion programme","risk":50,"col":"#ff8c42"},
    {"actor":"USA","type":"Nuclear Readiness","status":"Normal","assets":"STRATCOM — 1700 deployed warheads","risk":20,"col":"#00c8ff"},
]

# ── Country Instability (also defined here so it is available early) ──
# Country Instability Index — 50 countries, 4-component model (U=Unrest, C=Conflict, S=Security, I=Information)
# Scores 0-100. Components are already on 0-100 scale. Baseline March 2026.
COUNTRY_INSTABILITY = [
    # Active war zones
    {"country":"Sudan",        "score":91,"trend":"↑","U":92,"C":88,"S":82,"I":76,"region":"Africa"},
    {"country":"Gaza",         "score":98,"trend":"↑","U":99,"C":99,"S":95,"I":80,"region":"Middle East"},
    {"country":"Myanmar",      "score":85,"trend":"→","U":82,"C":88,"S":78,"I":74,"region":"Asia"},
    {"country":"Yemen",        "score":83,"trend":"→","U":80,"C":88,"S":70,"I":72,"region":"Middle East"},
    {"country":"Haiti",        "score":84,"trend":"↑","U":88,"C":80,"S":74,"I":72,"region":"Americas"},
    {"country":"Somalia",      "score":79,"trend":"→","U":76,"C":82,"S":72,"I":66,"region":"Africa"},
    {"country":"DR Congo",     "score":78,"trend":"↑","U":74,"C":84,"S":68,"I":64,"region":"Africa"},
    {"country":"Libya",        "score":76,"trend":"→","U":70,"C":78,"S":70,"I":68,"region":"Africa"},
    {"country":"Ethiopia",     "score":72,"trend":"↑","U":68,"C":76,"S":66,"I":60,"region":"Africa"},
    {"country":"Mali",         "score":71,"trend":"↑","U":72,"C":72,"S":60,"I":60,"region":"Africa"},
    {"country":"Afghanistan",  "score":70,"trend":"→","U":68,"C":72,"S":60,"I":62,"region":"Asia"},
    {"country":"Syria",        "score":74,"trend":"↓","U":64,"C":72,"S":76,"I":70,"region":"Middle East"},
    # Active conflict participants
    {"country":"Ukraine",      "score":88,"trend":"→","U":70,"C":98,"S":84,"I":72,"region":"Europe"},
    {"country":"Russia",       "score":76,"trend":"↑","U":62,"C":90,"S":72,"I":88,"region":"Europe/Asia"},
    {"country":"Israel",       "score":78,"trend":"↑","U":66,"C":94,"S":76,"I":68,"region":"Middle East"},
    {"country":"Iran",         "score":80,"trend":"↑","U":72,"C":82,"S":78,"I":90,"region":"Middle East"},
    {"country":"Lebanon",      "score":72,"trend":"↑","U":68,"C":76,"S":66,"I":62,"region":"Middle East"},
    {"country":"Iraq",         "score":63,"trend":"↓","U":58,"C":64,"S":56,"I":54,"region":"Middle East"},
    # High-tension states
    {"country":"North Korea",  "score":74,"trend":"→","U":40,"C":64,"S":82,"I":98,"region":"Asia"},
    {"country":"Venezuela",    "score":62,"trend":"→","U":66,"C":54,"S":58,"I":68,"region":"Americas"},
    {"country":"Pakistan",     "score":64,"trend":"↑","U":62,"C":68,"S":58,"I":54,"region":"Asia"},
    {"country":"China",        "score":55,"trend":"→","U":52,"C":38,"S":58,"I":80,"region":"Asia"},
    {"country":"Turkey",       "score":54,"trend":"→","U":54,"C":56,"S":48,"I":60,"region":"Middle East/Europe"},
    {"country":"Saudi Arabia", "score":48,"trend":"→","U":42,"C":50,"S":44,"I":64,"region":"Middle East"},
    {"country":"Egypt",        "score":52,"trend":"→","U":54,"C":44,"S":48,"I":68,"region":"Africa"},
    {"country":"Nigeria",      "score":66,"trend":"↑","U":64,"C":72,"S":60,"I":52,"region":"Africa"},
    {"country":"Kenya",        "score":48,"trend":"→","U":48,"C":42,"S":44,"I":42,"region":"Africa"},
    {"country":"Indonesia",    "score":38,"trend":"→","U":38,"C":28,"S":36,"I":44,"region":"Asia"},
    {"country":"Philippines",  "score":44,"trend":"→","U":46,"C":44,"S":40,"I":42,"region":"Asia"},
    {"country":"India",        "score":46,"trend":"→","U":48,"C":42,"S":42,"I":54,"region":"Asia"},
    {"country":"Bangladesh",   "score":55,"trend":"↑","U":58,"C":44,"S":52,"I":60,"region":"Asia"},
    {"country":"Thailand",     "score":44,"trend":"→","U":44,"C":36,"S":42,"I":50,"region":"Asia"},
    # Elevated instability
    {"country":"Brazil",       "score":46,"trend":"↑","U":50,"C":46,"S":46,"I":40,"region":"Americas"},
    {"country":"Mexico",       "score":56,"trend":"→","U":52,"C":62,"S":54,"I":44,"region":"Americas"},
    {"country":"Colombia",     "score":50,"trend":"↓","U":46,"C":56,"S":48,"I":42,"region":"Americas"},
    {"country":"Ecuador",      "score":54,"trend":"↑","U":52,"C":58,"S":52,"I":44,"region":"Americas"},
    {"country":"Peru",         "score":48,"trend":"→","U":50,"C":42,"S":44,"I":44,"region":"Americas"},
    # Relatively stable but monitored
    {"country":"USA",          "score":38,"trend":"↑","U":46,"C":18,"S":36,"I":42,"region":"Americas"},
    {"country":"UK",           "score":32,"trend":"→","U":34,"C":14,"S":30,"I":36,"region":"Europe"},
    {"country":"France",       "score":34,"trend":"↑","U":42,"C":14,"S":28,"I":36,"region":"Europe"},
    {"country":"Germany",      "score":28,"trend":"→","U":30,"C":10,"S":26,"I":30,"region":"Europe"},
    {"country":"Japan",        "score":24,"trend":"→","U":20,"C":12,"S":28,"I":24,"region":"Asia"},
    {"country":"South Korea",  "score":36,"trend":"↑","U":36,"C":28,"S":34,"I":40,"region":"Asia"},
    {"country":"Australia",    "score":18,"trend":"→","U":18,"C":6, "S":20,"I":20,"region":"Pacific"},
    {"country":"Canada",       "score":22,"trend":"↑","U":24,"C":8, "S":20,"I":24,"region":"Americas"},
    {"country":"Singapore",    "score":16,"trend":"→","U":14,"C":8, "S":18,"I":22,"region":"Asia"},
    {"country":"New Zealand",  "score":14,"trend":"→","U":14,"C":4, "S":16,"I":16,"region":"Pacific"},
]
# Build a fast lookup dict
_CI_LOOKUP = {c["country"].lower(): c for c in COUNTRY_INSTABILITY}
GOV_BONDS = [
    {"name":"US 10Y","yield":4.42,"change":+0.03,"rating":"AAA","col":"#38bdf8"},
    {"name":"US 2Y", "yield":4.71,"change":-0.01,"rating":"AAA","col":"#38bdf8"},
    {"name":"UK 10Y","yield":4.18,"change":+0.05,"rating":"AA", "col":"#34d399"},
    {"name":"DE 10Y","yield":2.41,"change":+0.02,"rating":"AAA","col":"#34d399"},
    {"name":"JP 10Y","yield":1.52,"change":+0.08,"rating":"A+", "col":"#fbbf24"},
    {"name":"IT 10Y","yield":3.74,"change":+0.04,"rating":"BBB","col":"#fb923c"},
    {"name":"IN 10Y","yield":6.83,"change":-0.02,"rating":"BBB-","col":"#fb923c"},
    {"name":"CN 10Y","yield":2.28,"change":-0.01,"rating":"A+", "col":"#fbbf24"},
    {"name":"TR 10Y","yield":28.4, "change":+0.60,"rating":"B+", "col":"#f87171"},
    {"name":"NG 10Y","yield":19.6, "change":+0.30,"rating":"B-", "col":"#f87171"},
]


import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json, requests, re, html as html_lib, time
from datetime import datetime, timezone, timedelta


# ══════════════════════════════════════════════════════════════
# OIL & GAS FACILITY MAP — DEPENDENCIES
# ══════════════════════════════════════════════════════════════
import plotly.graph_objects as _go
from plotly.subplots import make_subplots as _make_subplots

THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(10,14,22,0.75)",
    font=dict(family="Barlow Condensed, sans-serif", color="#5a7898", size=11),
    xaxis=dict(gridcolor="#1a2438", zerolinecolor="#1a2438", showgrid=True,
               linecolor="#1e2d46", tickfont=dict(family="Barlow Condensed", size=10)),
    yaxis=dict(gridcolor="#1a2438", zerolinecolor="#1a2438", showgrid=True,
               linecolor="#1e2d46", tickfont=dict(family="Barlow Condensed", size=10)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, family="Barlow Condensed")),
    hoverlabel=dict(bgcolor="#101520", font_family="Barlow Condensed, sans-serif",
                    font_size=12, bordercolor="#243450"),
)

PALETTE = {
    "WTI":        "#d4963a",
    "Brent":      "#2eb8a0",
    "NatGas":     "#e05858",
    "Gasoline":   "#9060d8",
    "HeatingOil": "#4a8cc8",
    "green":      "#38b86a",
    "red":        "#e05050",
    "purple":     "#9060d8",
    "white":      "#c8d8e8",
}

def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def apply_theme(fig, title="", height=380, margin=None):
    m = margin or dict(l=55, r=20, t=38, b=38)
    fig.update_layout(
        **THEME,
        title=dict(text=title, font=dict(color="#c8a060", size=12)),
        height=height,
        margin=m,
    )
    return fig

def err_box(msg: str):
    st.markdown(f"<div class='err-box'>⚠ {msg}</div>", unsafe_allow_html=True)

def dl_button(df: pd.DataFrame, filename: str):
    if not df.empty:
        st.download_button(
            f"⬇ Download {filename}", df.to_csv(),
            file_name=filename, mime="text/csv", use_container_width=True,
        )

# ═══════════════════════════════════════════════════════════════
# DATA FETCHERS  (all cache-wrapped, with provenance metadata)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_nasa_firms(lat: float, lon: float, radius_km: int = 50) -> dict:
    """
    Fetch thermal anomaly data from NASA FIRMS.
    Strategy:
      1. Try FIRMS public NRT CSV download (no key, last 24h global file, filter by bbox)
      2. Fall back to FIRMS active fire count via their public summary JSON
    Both endpoints are completely public — no API key required.
    """
    from io import StringIO
    deg = radius_km / 111.0
    lat_min, lat_max = lat - deg, lat + deg
    lon_min, lon_max = lon - deg, lon + deg

    # ── Method 1: FIRMS public NRT CSV (last 24h, global, no key) ──
    # These are the genuinely open NRT CSV files NASA publishes daily
    NRT_SOURCES = [
        ("VIIRS_SNPP", "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_Global_24h.csv"),
        ("MODIS",      "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_24h.csv"),
        ("VIIRS_NOAA", "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_Global_24h.csv"),
    ]

    for sensor_name, csv_url in NRT_SOURCES:
        try:
            r = requests.get(csv_url, timeout=15,
                             headers={"User-Agent": "OilGasResearchDashboard/1.0"})
            if r.status_code != 200:
                continue
            df = pd.read_csv(StringIO(r.text))
            if df.empty or "latitude" not in df.columns:
                continue
            df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
            df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
            df = df.dropna(subset=["latitude","longitude"])
            # Filter to facility bounding box
            nearby = df[
                (df["latitude"]  >= lat_min) & (df["latitude"]  <= lat_max) &
                (df["longitude"] >= lon_min) & (df["longitude"] <= lon_max)
            ].copy()
            # Normalise column names across MODIS / VIIRS
            frp_col  = next((c for c in ["frp","FRP"] if c in nearby.columns), None)
            date_col = next((c for c in ["acq_date","ACQ_DATE"] if c in nearby.columns), None)
            time_col = next((c for c in ["acq_time","ACQ_TIME"] if c in nearby.columns), None)
            bright_col = next((c for c in ["bright_ti4","bright_t31","brightness","BRIGHT_TI4","BRIGHTNESS"] if c in nearby.columns), None)
            conf_col = next((c for c in ["confidence","CONFIDENCE"] if c in nearby.columns), None)

            out = pd.DataFrame()
            out["latitude"]   = nearby["latitude"]
            out["longitude"]  = nearby["longitude"]
            out["frp"]        = pd.to_numeric(nearby[frp_col],    errors="coerce") if frp_col    else np.nan
            out["acq_date"]   = nearby[date_col].astype(str)                        if date_col   else "N/A"
            out["acq_time"]   = nearby[time_col].astype(str)                        if time_col   else "N/A"
            out["bright_ti4"] = pd.to_numeric(nearby[bright_col], errors="coerce") if bright_col else np.nan
            out["confidence"] = nearby[conf_col].astype(str)                        if conf_col   else "N/A"
            out = out.dropna(subset=["latitude","longitude"])

            return {
                "ok": True, "df": out, "count": len(out),
                "sensor": sensor_name,
                "source": f"NASA FIRMS {sensor_name} NRT (24h global, no key)",
                "fetched_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "embed_url": (
                    f"https://firms.modaps.eosdis.nasa.gov/map/#d:2017-05-14..2017-05-15;"
                    f"@{lon:.3f},{lat:.3f},10z"
                ),
            }
        except Exception:
            continue

    # ── Method 2: FIRMS public map embed (always works, visual only) ──
    embed_url = (
        f"https://firms.modaps.eosdis.nasa.gov/map/"
        f"#d:24hrs;@{lon:.4f},{lat:.4f},11z"
    )
    return {
        "ok": False,
        "error": "NRT CSV download unavailable on this network — use embed viewer below",
        "df": pd.DataFrame(), "count": 0,
        "embed_url": embed_url,
        "source": "NASA FIRMS (map embed fallback)",
        "fetched_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }


# ── Open-Meteo — live weather at facility coordinates ─────────

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current weather + 24h forecast via Open-Meteo. No key needed."""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,wind_direction_10m,"
                           "relative_humidity_2m,weather_code,visibility,surface_pressure",
                "hourly": "temperature_2m,wind_speed_10m,precipitation_probability",
                "forecast_days": 2,
                "wind_speed_unit": "kmh",
                "timezone": "UTC",
            },
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        curr = data.get("current", {})
        hourly = data.get("hourly", {})
        # Build 24h forecast df
        fcast_df = pd.DataFrame({
            "time":     pd.to_datetime(hourly.get("time", [])),
            "temp_c":   hourly.get("temperature_2m", []),
            "wind_kmh": hourly.get("wind_speed_10m", []),
            "precip_pct": hourly.get("precipitation_probability", []),
        }).head(24)
        WMO_CODES = {
            0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
            45:"Foggy",48:"Rime fog",51:"Light drizzle",53:"Drizzle",
            61:"Light rain",63:"Rain",71:"Light snow",73:"Snow",
            80:"Rain showers",81:"Heavy showers",95:"Thunderstorm",
            99:"Thunderstorm w/ hail",
        }
        return {
            "ok": True,
            "temp_c":      curr.get("temperature_2m"),
            "wind_kmh":    curr.get("wind_speed_10m"),
            "wind_dir":    curr.get("wind_direction_10m"),
            "humidity":    curr.get("relative_humidity_2m"),
            "pressure":    curr.get("surface_pressure"),
            "visibility":  curr.get("visibility"),
            "condition":   WMO_CODES.get(curr.get("weather_code", 0), "Unknown"),
            "fcast_df":    fcast_df,
            "source":      "Open-Meteo (no key)",
            "fetched_at":  datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Satellite imagery URL builders (Sentinel deprecated 20 Mar 2026) ─────────

def google_maps_satellite_url(lat: float, lon: float, zoom: int = 14) -> str:
    """Google Maps satellite embed — free, no key for basic embed."""
    return (
        f"https://maps.google.com/maps"
        f"?q={lat:.5f},{lon:.5f}&z={zoom}&output=embed&t=k"
    )

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_satellite_mosaic(lat: float, lon: float, zoom: int = 14) -> dict:
    """
    Fetch a 3×3 mosaic of Esri World Imagery tiles centred on facility.
    All 9 tiles fetched concurrently — ~9× faster than serial.
    """
    import math
    from concurrent.futures import ThreadPoolExecutor, as_completed
    try:
        n = 2 ** zoom
        cx = int((lon + 180) / 360 * n)
        cy = int((1 - math.log(math.tan(math.radians(lat)) +
                  1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)

        def _fetch_tile(dy, dx):
            tx, ty = cx + dx, cy + dy
            url = (f"https://server.arcgisonline.com/ArcGIS/rest/services"
                   f"/World_Imagery/MapServer/tile/{zoom}/{ty}/{tx}")
            r = requests.get(url, timeout=8,
                             headers={"User-Agent": "OilGasResearchDashboard/1.0"})
            if r.status_code == 200:
                return (dy + 1, dx + 1, r.content)
            return None

        coords = [(dy, dx) for dy in range(-1, 2) for dx in range(-1, 2)]
        tiles = []
        with ThreadPoolExecutor(max_workers=9) as pool:
            futs = {pool.submit(_fetch_tile, dy, dx): (dy, dx) for dy, dx in coords}
            for fut in as_completed(futs):
                result = fut.result()
                if result:
                    tiles.append(result)
        # Sort into row-major order for PIL stitching
        tiles.sort(key=lambda t: (t[0], t[1]))
        return {
            "ok": bool(tiles),
            "tiles": tiles,
            "source": "Esri World Imagery (ArcGIS Online — free, no key)",
            "fetched_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "tiles": []}


# ── MarineTraffic AIS embed URL builder ───────────────────────

def marinetraffic_url(lat: float, lon: float, zoom: int = 10) -> str:
    """Build MarineTraffic live vessel tracking embed URL."""
    return (
        f"https://www.marinetraffic.com/en/ais/embed/zoom:{zoom}"
        f"/centery:{lat:.3f}/centerx:{lon:.3f}"
        f"/maptype:1/shownames:false/mmsi:0/shipid:0/fleet:/fleet_id:/vtypes:/selectedMapType:0"
    )


# ── RSS feeds (kept below) ────────────────────────────────────

# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
# PERSISTENCE LAYER — Supabase (fire-and-forget)
# ══════════════════════════════════════════════════════════════
# Configure in .streamlit/secrets.toml:
#   SUPABASE_URL = "https://xxxx.supabase.co"
#   SUPABASE_KEY = "your-anon-key"
#
# Required tables (run once in Supabase SQL editor):
#
#   create table if not exists acled_events (
#     id          bigserial primary key,
#     inserted_at timestamptz default now(),
#     event_date  text, event_type text, sub_type text,
#     actor1 text, actor2 text, country text, location text,
#     lat float8, lon float8, fatalities int, notes text, source text
#   );
#   create table if not exists ais_positions (
#     id          bigserial primary key,
#     inserted_at timestamptz default now(),
#     mmsi text, name text, lat float8, lon float8,
#     speed float8, heading float8, type text, flag text
#   );
#   create table if not exists seismic_events (
#     id          bigserial primary key,
#     inserted_at timestamptz default now(),
#     title text, mag float8, place text,
#     depth_km float8, lon float8, lat float8, url text
#   );
#   create table if not exists gdelt_events (
#     id          bigserial primary key,
#     inserted_at timestamptz default now(),
#     title text, source text, url text unique, time text
#   );

def _sb_creds() -> tuple:
    """Return (url, key) or (None, None) if not configured."""
    try:
        url = st.secrets.get("SUPABASE_URL", None)
        key = st.secrets.get("SUPABASE_KEY", None)
        return (url, key) if url and key else (None, None)
    except Exception:
        return (None, None)


def _persist(table: str, rows: list) -> None:
    """
    Fire-and-forget insert to Supabase REST API.
    - Never raises; never blocks the calling fetcher.
    - Deduplicates on 'url' column for gdelt_events (Prefer: resolution=ignore-duplicates).
    - Strips non-serialisable types (DataFrames, numpy values) before sending.
    """
    url, key = _sb_creds()
    if not url or not key or not rows:
        return
    try:
        import json as _json

        def _clean(v):
            """Make a value JSON-safe."""
            if v is None:
                return None
            if isinstance(v, (int, float, str, bool)):
                return v
            try:
                import numpy as np
                if isinstance(v, (np.integer,)):  return int(v)
                if isinstance(v, (np.floating,)): return float(v)
                if isinstance(v, (np.bool_,)):    return bool(v)
            except ImportError:
                pass
            return str(v)

        clean_rows = [
            {k: _clean(v) for k, v in row.items()
             if k not in ("tip", "_color", "_radius")}  # skip map-only fields
            for row in rows
        ]

        headers = {
            "apikey":        key,
            "Authorization": f"Bearer {key}",
            "Content-Type":  "application/json",
            "Prefer":        "resolution=ignore-duplicates",
        }
        requests.post(
            f"{url}/rest/v1/{table}",
            data=_json.dumps(clean_rows),
            headers=headers,
            timeout=5,
        )
    except Exception:
        pass  # always silent — persistence must never break the live feed


@st.cache_data(ttl=300, show_spinner=False)
def load_persisted(table: str, limit: int = 100) -> list:
    """
    Read the most recent rows from a Supabase table.
    Used as a fallback when the live API source fails.
    Returns [] if Supabase is not configured or the query fails.
    """
    url, key = _sb_creds()
    if not url or not key:
        return []
    try:
        r = requests.get(
            f"{url}/rest/v1/{table}",
            params={"order": "inserted_at.desc", "limit": limit},
            headers={
                "apikey":        key,
                "Authorization": f"Bearer {key}",
                "Accept":        "application/json",
            },
            timeout=6,
        )
        if r.status_code == 200:
            return r.json() or []
    except Exception:
        pass
    return []


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_instability(country: str, baseline: dict) -> dict:
    """Fetch live instability signal from GDELT and blend with baseline.
    
    GDELT GKG tone is negative = conflict/instability, positive = calm.
    We map tone to a 0-100 instability delta and blend with baseline score.
    """
    try:
        # GDELT Doc API — search last 24h for country name, get tone
        r = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query":      f"{country} conflict protest crisis war",
                "mode":       "tonechart",
                "timespan":   "1d",
                "format":     "json",
            },
            timeout=12,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if r.status_code != 200:
            return baseline

        data = r.json()
        # tone array: list of {date, tone, pos, neg, ...}
        tone_data = data.get("tonechart", [])
        if not tone_data:
            return baseline

        # Average tone over available data points (tone is -100 to +100)
        avg_tone = sum(float(t.get("tone", 0)) for t in tone_data) / len(tone_data)

        # Map tone to instability delta: very negative tone = higher instability
        # avg_tone typically ranges -10 to +5 for conflict countries
        # We map: -15 → +15 delta, 0 → 0, +5 → -5 delta
        tone_delta = max(-20, min(20, int(-avg_tone * 1.2)))

        # Blend: 70% baseline, 30% live signal
        live_score = int(baseline["score"] * 0.7 + (baseline["score"] + tone_delta) * 0.3)
        live_score = max(0, min(100, live_score))

        # Determine live trend from direction of tone delta
        if tone_delta > 3:
            live_trend = "↑"
        elif tone_delta < -3:
            live_trend = "↓"
        else:
            live_trend = baseline.get("trend", "→")

        return {**baseline, "score": live_score, "trend": live_trend, "_live": True}

    except Exception:
        return baseline


def get_instability_for_country(country: str) -> dict | None:
    """Get instability data for a country, with live GDELT blending."""
    c_lower = country.lower()
    baseline = _CI_LOOKUP.get(c_lower)
    if not baseline:
        # fuzzy match
        for key, val in _CI_LOOKUP.items():
            if c_lower in key or key in c_lower:
                baseline = val
                break
    if not baseline:
        return None
    # Try to get live data (cached 1h)
    return fetch_live_instability(country, baseline)




import pydeck as pdk
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="The Geo-Locator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-refresh ─────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60_000, key="auto60s")  # 60 s global refresh — keeps map+figures live
except ImportError:
    pass

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ═══════════════════════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════════════════════ */
:root {
  --void:#020509;--deep:#060d18;--panel:#080f1c;--card:#0b1524;
  --glass:rgba(8,15,28,.88);--border:rgba(0,200,255,.12);--bord2:rgba(0,200,255,.06);
  --cyan:#00c8ff;--amber:#ffb400;--red:#ff3d5a;--green:#00e676;
  --violet:#9d6eff;--orange:#ff8c42;--text:#e2ecf8;--text2:#a8c0d8;
  --muted:#4a6b85;--dim:#0f2035;
  --fd:'Bebas Neue','Impact',sans-serif;
  --fm:'IBM Plex Mono','Courier New',monospace;
  --fb:'DM Sans',system-ui,sans-serif;

  /* Aurora animation timing */
  --t1:18s; --t2:26s; --t3:34s; --t4:22s;
}

/* ═══════════════════════════════════════════════════════════
   BACKGROUND SYSTEM
   Three-layer composited background:
   1. Base deep-space gradient
   2. Aurora colour bands (CSS animated)
   3. Star field + scanline texture
   ═══════════════════════════════════════════════════════════ */

html, body, [class*="css"], .stApp {
  font-family: var(--fb) !important;
  color: var(--text) !important;
  background: var(--void) !important;
}

/* ── Layer 0: Base gradient — deep space blue-black ── */
.stApp {
  background:
    radial-gradient(ellipse 120% 60% at 50%  -5%, rgba(0,50,120,.28) 0%, transparent 65%),
    radial-gradient(ellipse  60% 80% at  0%  50%, rgba(10,30,80,.18) 0%, transparent 60%),
    radial-gradient(ellipse  50% 70% at 100% 60%, rgba(20,10,60,.16) 0%, transparent 60%),
    linear-gradient(175deg, #020509 0%, #03060f 40%, #020408 100%)
    !important;
}

/* ── Layer 1: Aurora bands — two animated pseudo-elements ── */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    /* Teal aurora band — top left diagonal */
    radial-gradient(ellipse 80% 35% at 20%  8%, rgba(0,180,220,.11) 0%, transparent 70%),
    /* Violet aurora band — top right */
    radial-gradient(ellipse 70% 28% at 80% 12%, rgba(80,20,180,.09) 0%, transparent 65%),
    /* Faint amber equatorial band */
    radial-gradient(ellipse 90% 18% at 50% 45%, rgba(120,70,0,.055) 0%, transparent 70%),
    /* Deep green trace — bottom left */
    radial-gradient(ellipse 55% 25% at  8% 80%, rgba(0,120,80,.06) 0%, transparent 65%);
  animation: aurora-drift var(--t1) ease-in-out infinite alternate;
}

@keyframes aurora-drift {
  0%   { transform: translate(0,    0)    scale(1);    opacity: 1; }
  30%  { transform: translate(18px,-12px) scale(1.03); opacity: .88; }
  60%  { transform: translate(-14px, 8px) scale(.97);  opacity: .94; }
  100% { transform: translate(10px, 16px) scale(1.02); opacity: .84; }
}

/* ── Layer 2: Second aurora pass — slow opposing drift ── */
.stApp::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    /* Slow violet bloom — upper centre */
    radial-gradient(ellipse 60% 40% at 55%  -8%, rgba(60,0,160,.08) 0%, transparent 70%),
    /* Cyan shimmer — right edge */
    radial-gradient(ellipse 35% 55% at 100% 30%, rgba(0,160,220,.07) 0%, transparent 65%),
    /* Warm magenta trace — far left */
    radial-gradient(ellipse 40% 30% at  0%  25%, rgba(140,0,100,.06) 0%, transparent 60%),
    /* Vignette — darken edges for depth */
    radial-gradient(ellipse 92% 88% at 50%  50%, transparent 45%, rgba(0,0,0,.55) 100%);
  animation: aurora-drift2 var(--t2) ease-in-out infinite alternate-reverse;
}

@keyframes aurora-drift2 {
  0%   { transform: translate(0,    0)    scale(1);    opacity: 1; }
  40%  { transform: translate(-20px,14px) scale(1.04); opacity: .82; }
  70%  { transform: translate(12px,-8px)  scale(.96);  opacity: .92; }
  100% { transform: translate(-8px,-18px) scale(1.01); opacity: .78; }
}

/* ── Layer 3: Star field — tiny CSS box-shadow stars ── */
#stDecoration {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 1;
  /* 60 pseudo-random stars via box-shadow — no JS needed */
  background: transparent;
  animation: stars-twinkle var(--t3) ease-in-out infinite alternate;
}
#stDecoration::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at  4%  8%, rgba(255,255,255,.55) 0%, transparent 100%),
    radial-gradient(1px 1px at 12% 22%, rgba(200,230,255,.45) 0%, transparent 100%),
    radial-gradient(1px 1px at 22%  5%, rgba(255,255,255,.38) 0%, transparent 100%),
    radial-gradient(1px 1px at 31% 15%, rgba(180,220,255,.4)  0%, transparent 100%),
    radial-gradient(1px 1px at 42%  3%, rgba(255,255,255,.5)  0%, transparent 100%),
    radial-gradient(1px 1px at 51% 18%, rgba(200,200,255,.35) 0%, transparent 100%),
    radial-gradient(1px 1px at 63%  9%, rgba(255,255,255,.42) 0%, transparent 100%),
    radial-gradient(1px 1px at 74% 25%, rgba(180,230,255,.38) 0%, transparent 100%),
    radial-gradient(1px 1px at 84%  6%, rgba(255,255,255,.48) 0%, transparent 100%),
    radial-gradient(1px 1px at 93% 14%, rgba(200,220,255,.4)  0%, transparent 100%),
    radial-gradient(1px 1px at  7% 35%, rgba(255,255,255,.32) 0%, transparent 100%),
    radial-gradient(1px 1px at 18% 48%, rgba(180,200,255,.28) 0%, transparent 100%),
    radial-gradient(1px 1px at 28% 38%, rgba(255,255,255,.36) 0%, transparent 100%),
    radial-gradient(1px 1px at 39% 52%, rgba(200,220,255,.3)  0%, transparent 100%),
    radial-gradient(1px 1px at 48% 41%, rgba(255,255,255,.44) 0%, transparent 100%),
    radial-gradient(1px 1px at 58% 55%, rgba(180,210,255,.32) 0%, transparent 100%),
    radial-gradient(1px 1px at 67% 44%, rgba(255,255,255,.38) 0%, transparent 100%),
    radial-gradient(1px 1px at 78% 58%, rgba(200,230,255,.26) 0%, transparent 100%),
    radial-gradient(1px 1px at 87% 47%, rgba(255,255,255,.34) 0%, transparent 100%),
    radial-gradient(1px 1px at 96% 39%, rgba(180,200,255,.28) 0%, transparent 100%),
    radial-gradient(1px 1px at  2% 62%, rgba(255,255,255,.3)  0%, transparent 100%),
    radial-gradient(1px 1px at 14% 72%, rgba(200,220,255,.24) 0%, transparent 100%),
    radial-gradient(1px 1px at 24% 65%, rgba(255,255,255,.28) 0%, transparent 100%),
    radial-gradient(1px 1px at 35% 78%, rgba(180,210,255,.22) 0%, transparent 100%),
    radial-gradient(1px 1px at 45% 68%, rgba(255,255,255,.32) 0%, transparent 100%),
    radial-gradient(1px 1px at 55% 82%, rgba(200,225,255,.2)  0%, transparent 100%),
    radial-gradient(1px 1px at 64% 73%, rgba(255,255,255,.26) 0%, transparent 100%),
    radial-gradient(1px 1px at 76% 86%, rgba(180,200,255,.18) 0%, transparent 100%),
    radial-gradient(1px 1px at 85% 76%, rgba(255,255,255,.24) 0%, transparent 100%),
    radial-gradient(1px 1px at 95% 88%, rgba(200,220,255,.2)  0%, transparent 100%);
}
@keyframes stars-twinkle {
  0%   { opacity: .6; }
  50%  { opacity: 1;  }
  100% { opacity: .7; }
}

/* ── Layer 4: Fine scanline texture ── */
#stDecoration::after {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent 0px,
    transparent 3px,
    rgba(0,0,0,.018) 3px,
    rgba(0,0,0,.018) 4px
  );
}

/* ── Sidebar — semi-transparent with blur ── */
section[data-testid="stSidebar"] {
  background: rgba(4,8,20,.82) !important;
  border-right: 1px solid rgba(0,200,255,.1) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p { color: var(--text) !important; }

/* ── Tab bar — glassy ── */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(4,8,20,.75) !important;
  border-bottom: 1px solid var(--border) !important;
  backdrop-filter: blur(16px) !important;
  gap: 0 !important;
  padding: 0 8px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-bottom: 3px solid transparent !important;
  font-family: var(--fb) !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  letter-spacing: .06em !important;
  color: var(--muted) !important;
  padding: 14px 20px !important;
}
.stTabs [aria-selected="true"] {
  color: var(--cyan) !important;
  border-bottom-color: var(--cyan) !important;
}

/* ═══════════════════════════════════════════════════════════
   SCROLLBAR
   ═══════════════════════════════════════════════════════════ */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--deep); }
::-webkit-scrollbar-thumb { background: rgba(0,200,255,.2); border-radius: 2px; }

/* ═══════════════════════════════════════════════════════════
   COMPONENT STYLES  (unchanged from original)
   ═══════════════════════════════════════════════════════════ */
div[data-testid="stMetric"]{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 20px!important;}
div[data-testid="stMetricValue"]{font-family:var(--fm)!important;font-size:24px!important;color:var(--cyan)!important;font-weight:500!important;}
div[data-testid="stMetricLabel"]{font-family:var(--fb)!important;font-size:11px!important;font-weight:600!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:var(--muted)!important;}
.stButton>button{background:transparent!important;border:1px solid var(--border)!important;color:var(--text)!important;font-family:var(--fb)!important;font-weight:600!important;font-size:13px!important;border-radius:8px!important;padding:10px 18px!important;transition:all .18s!important;}
.stButton>button:hover{border-color:var(--cyan)!important;color:var(--cyan)!important;background:rgba(0,200,255,.06)!important;box-shadow:0 0 16px rgba(0,200,255,.12)!important;}
.stSelectbox>div>div,.stTextInput>div>div>input,.stTextArea textarea{background:var(--card)!important;border:1px solid var(--border)!important;color:var(--text)!important;font-family:var(--fm)!important;font-size:13px!important;border-radius:8px!important;}
.stSelectbox label,.stTextInput label,.stTextArea label,.stCheckbox label,.stToggle label{color:var(--text2)!important;font-size:12px!important;font-weight:500!important;font-family:var(--fb)!important;}
.stRadio>div{gap:8px;flex-wrap:wrap;}
.stRadio>div>label{background:var(--card)!important;border:1px solid var(--bord2)!important;border-radius:8px!important;padding:7px 14px!important;font-size:12px!important;color:var(--text2)!important;text-transform:none!important;letter-spacing:0!important;font-weight:500!important;}
.stSuccess{background:rgba(0,230,118,.07)!important;border:1px solid rgba(0,230,118,.25)!important;color:var(--green)!important;border-radius:10px!important;font-size:13px!important;}
.stError{background:rgba(255,61,90,.07)!important;border:1px solid rgba(255,61,90,.25)!important;color:var(--red)!important;border-radius:10px!important;font-size:13px!important;}
.stInfo{background:rgba(0,200,255,.07)!important;border:1px solid rgba(0,200,255,.25)!important;color:var(--cyan)!important;border-radius:10px!important;font-size:13px!important;}
hr{border:none!important;border-top:1px solid var(--bord2)!important;margin:18px 0!important;}
.wordmark{font-family:var(--fd);font-size:30px;letter-spacing:.16em;line-height:1;color:var(--cyan);text-shadow:0 0 28px rgba(0,200,255,.45);}
.wordmark em{color:var(--amber);font-style:normal;}
.sec-label{font-family:var(--fb);font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:8px;margin-bottom:12px;}
.sec-label::after{content:'';flex:1;height:1px;background:var(--bord2);}
.status-row{display:flex;align-items:center;gap:20px;font-family:var(--fm);font-size:11px;color:var(--muted);padding:8px 0 14px;border-bottom:1px solid var(--bord2);margin-bottom:18px;flex-wrap:wrap;}
.pulse{width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:5px;animation:blink 2s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.p-cyan{background:var(--cyan);box-shadow:0 0 6px var(--cyan);}
.p-amber{background:var(--amber);box-shadow:0 0 6px var(--amber);}
.p-red{background:var(--red);box-shadow:0 0 6px var(--red);animation-duration:.8s;}
.p-green{background:var(--green);box-shadow:0 0 6px var(--green);}
.p-orange{background:var(--orange);box-shadow:0 0 6px var(--orange);}
.utc-clock{margin-left:auto;font-family:var(--fd);font-size:15px;letter-spacing:.12em;color:var(--cyan);}
.gcard{background:var(--glass);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-bottom:10px;position:relative;overflow:hidden;transition:border-color .2s,box-shadow .2s;}
.gcard:hover{border-color:rgba(0,200,255,.22);box-shadow:0 4px 24px rgba(0,200,255,.06);}
.gcard::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(0,200,255,.3),transparent);}
.gcard-crit{border-color:rgba(255,61,90,.35)!important;animation:crit-pulse 3s ease-in-out infinite;}
@keyframes crit-pulse{0%,100%{box-shadow:0 0 18px rgba(255,61,90,.06)}50%{box-shadow:0 0 28px rgba(255,61,90,.18)}}
.gcard-crit::before{background:linear-gradient(90deg,transparent,rgba(255,61,90,.45),transparent)!important;}
.conflict-card{background:var(--card);border:1px solid var(--bord2);border-radius:12px;overflow:hidden;margin-bottom:12px;transition:border-color .2s;}
.cc-header{padding:12px 16px;border-bottom:1px solid var(--bord2);display:flex;align-items:center;justify-content:space-between;}
.cc-body{padding:14px 16px;}
.cc-title{font-family:var(--fd);font-size:16px;letter-spacing:.07em;color:var(--text);}
.incident-row{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--bord2);transition:background .15s;}
.inc-icon{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;}
.inc-body{flex:1;min-width:0;}
.inc-title{font-size:13px;font-weight:600;color:var(--text);line-height:1.4;}
.inc-meta{font-family:var(--fm);font-size:11px;color:var(--muted);margin-top:3px;}
.inc-badge-row{display:flex;gap:5px;margin-top:6px;flex-wrap:wrap;}
.badge{display:inline-flex;align-items:center;padding:3px 9px;border-radius:5px;font-family:var(--fm);font-size:10px;font-weight:500;letter-spacing:.05em;border:1px solid;white-space:nowrap;}
.b-red{color:var(--red);border-color:rgba(255,61,90,.35);background:rgba(255,61,90,.10);}
.b-amber{color:var(--amber);border-color:rgba(255,180,0,.35);background:rgba(255,180,0,.10);}
.b-cyan{color:var(--cyan);border-color:rgba(0,200,255,.35);background:rgba(0,200,255,.10);}
.b-green{color:var(--green);border-color:rgba(0,230,118,.35);background:rgba(0,230,118,.10);}
.b-violet{color:var(--violet);border-color:rgba(157,110,255,.35);background:rgba(157,110,255,.10);}
.b-orange{color:var(--orange);border-color:rgba(255,140,66,.35);background:rgba(255,140,66,.10);}
.b-muted{color:var(--muted);border-color:rgba(74,107,133,.35);background:rgba(74,107,133,.10);}
.sig-title{font-size:14px;font-weight:600;color:var(--text);line-height:1.4;}
.sig-meta{font-family:var(--fm);font-size:11px;color:var(--muted);margin-top:4px;line-height:1.5;}
.scale-wrap{display:flex;align-items:center;gap:8px;margin-top:8px;}
.scale-track{flex:1;height:4px;background:var(--dim);border-radius:2px;overflow:hidden;}
.scale-fill{height:100%;border-radius:2px;}
.m-panel{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-bottom:10px;}
.m-label{font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:6px;}
.m-val{font-family:var(--fd);font-size:36px;letter-spacing:.04em;line-height:1;margin-bottom:4px;}
.m-sub{font-family:var(--fm);font-size:11px;color:var(--muted);}
.m-cyan{color:var(--cyan);text-shadow:0 0 20px rgba(0,200,255,.3);}
.m-amber{color:var(--amber);text-shadow:0 0 20px rgba(255,180,0,.2);}
.m-red{color:var(--red);text-shadow:0 0 20px rgba(255,61,90,.25);}
.m-green{color:var(--green);text-shadow:0 0 20px rgba(0,230,118,.2);}
.m-violet{color:var(--violet);text-shadow:0 0 20px rgba(157,110,255,.2);}
.news-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-bottom:12px;position:relative;overflow:hidden;transition:border-color .2s,transform .15s;}
.news-card:hover{border-color:rgba(0,200,255,.25);transform:translateY(-1px);box-shadow:0 4px 20px rgba(0,0,0,.3);}
.news-card::after{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;}
.nc-conflict::after{background:linear-gradient(180deg,#ff3d5a,transparent);}
.nc-global::after{background:linear-gradient(180deg,#ff8c42,transparent);}
.nc-science::after{background:linear-gradient(180deg,#00c8ff,transparent);}
.nc-geo::after{background:linear-gradient(180deg,#9d6eff,transparent);}
.nc-climate::after{background:linear-gradient(180deg,#00e676,transparent);}
.nc-space::after{background:linear-gradient(180deg,#ffb400,transparent);}
.nc-default::after{background:linear-gradient(180deg,#4a6b85,transparent);}
.news-headline{font-size:14px;font-weight:600;color:var(--text);line-height:1.45;margin:8px 0 6px;}
.news-snippet{font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px;}
.news-footer{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.news-time{font-family:var(--fm);font-size:10px;color:var(--muted);}
.news-link{display:inline-flex;align-items:center;gap:4px;font-family:var(--fm);font-size:10px;color:var(--cyan);text-decoration:none;padding:4px 10px;border:1px solid rgba(0,200,255,.25);border-radius:5px;transition:background .15s;}
.news-link:hover{background:rgba(0,200,255,.1);}
.src-directory-card{background:var(--card);border:1px solid var(--bord2);border-radius:10px;padding:14px 16px;margin-bottom:10px;transition:border-color .2s;}
.src-directory-card:hover{border-color:var(--border);}
.map-top-bar{background:var(--panel);border:1px solid var(--border);border-radius:14px 14px 0 0;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;}
.map-title-text{font-family:var(--fd);font-size:17px;letter-spacing:.14em;color:var(--cyan);text-shadow:0 0 16px rgba(0,200,255,.3);}
.map-legend{display:flex;gap:16px;align-items:center;font-family:var(--fm);font-size:10px;color:var(--muted);flex-wrap:wrap;}
.ticker-wrap{background:var(--deep);border-top:1px solid var(--border);border-bottom:1px solid var(--bord2);overflow:hidden;padding:8px 0;}
.ticker-inner{display:inline-block;white-space:nowrap;animation:ticker-scroll 90s linear infinite;font-family:var(--fm);font-size:11px;color:var(--muted);}
@keyframes ticker-scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.t-sep{color:var(--cyan);margin:0 16px;}.t-hi{color:var(--text);}.t-red{color:var(--red);}.t-amb{color:var(--amber);}
.helper{font-size:12px;color:var(--muted);line-height:1.6;padding:10px 14px;background:var(--dim);border-radius:8px;border-left:3px solid var(--bord2);margin-bottom:14px;}
.helper b{color:var(--text2);font-style:normal;}
.sb-div{height:1px;background:var(--bord2);margin:16px 0;}
.tl-item{position:relative;margin-bottom:16px;padding-left:22px;}
.tl-item::before{content:'';position:absolute;left:0;top:4px;width:9px;height:9px;border-radius:50%;border:2px solid var(--dim);}
.tl-date{font-family:var(--fm);font-size:10px;color:var(--muted);margin-bottom:3px;}
.tl-text{font-size:13px;color:var(--text);line-height:1.5;}
.tl-tag{font-family:var(--fm);font-size:9px;margin-top:2px;}
.live-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;background:rgba(255,61,90,.1);border:1px solid rgba(255,61,90,.3);border-radius:20px;font-family:var(--fm);font-size:9px;color:var(--red);}
.sec-l{font-family:var(--fb);font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:8px;margin-bottom:12px;}
.sec-l::after{content:'';flex:1;height:1px;background:var(--bord2);}

/* ═══════════════════════════════════════════════════════════
   MOBILE RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width:768px){
  .status-row{gap:10px!important;padding:6px 0 10px!important;font-size:10px!important;}
  .wordmark{font-size:22px!important;letter-spacing:.1em!important;}
  .map-top-bar{flex-direction:column!important;align-items:flex-start!important;gap:6px!important;padding:10px 14px!important;}
  .map-legend{gap:8px!important;font-size:9px!important;flex-wrap:wrap!important;}
  .map-title-text{font-size:14px!important;}
  div[data-testid="stMetric"]{padding:10px 12px!important;}
  div[data-testid="stMetricValue"]{font-size:18px!important;}
  div[data-testid="stMetricLabel"]{font-size:10px!important;}
  .stTabs [data-baseweb="tab"]{padding:10px 10px!important;font-size:11px!important;letter-spacing:.02em!important;}
  .gcard{padding:12px 14px!important;}
  .m-val{font-size:28px!important;}
  .ticker-inner{font-size:10px!important;}
  .stButton>button{padding:8px 14px!important;font-size:12px!important;}
  .helper{font-size:11px!important;}
  .js-plotly-plot{min-height:140px!important;}
}
@media (max-width:480px){
  .wordmark{font-size:18px!important;}
  .stTabs [data-baseweb="tab"]{padding:8px 7px!important;font-size:10px!important;}
  div[data-testid="stMetricValue"]{font-size:15px!important;}
  .m-val{font-size:22px!important;}
  .gcard{padding:10px 11px!important;margin-bottom:7px!important;}
  .live-badge{font-size:8px!important;padding:2px 7px!important;}
}
</style>
""", unsafe_allow_html=True)

# Inject star-field layer (CSS-only, no JS, ultra-lightweight)
st.markdown('<div id="stDecoration"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {
    "selected_conflict": "Ukraine–Russia War",
    "last_refresh": 0,
    "prev_eq_count": 0,
    "prev_active_conf": 0,
    "prev_total_cas": 0,
    "intro_shown": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def bg_chart():
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

def ax(color="#4a6b85", grid="#0f2035", sz=10):
    return dict(color=color, tickfont_size=sz, gridcolor=grid)

# ─────────────────────────────────────────────
# CONFLICT DATA
# ─────────────────────────────────────────────
CONFLICTS = {
"Ukraine–Russia War": {
  "status":"ACTIVE","intensity":"CRITICAL","start":"2022-02-24","region":"Eastern Europe",
  "escalation":87,"ceasefire":False,"casualties_total":350000,"displaced":14200000,
  "description":"Full-scale Russian invasion of Ukraine. Ongoing frontline combat across eastern and southern oblasts, with regular missile and drone attacks on civilian infrastructure.",
  "factions":[
    {"name":"Ukraine Armed Forces","side":"UA","color":"#1a9fff","territory_pct":68,"strength":"High","weapons":["F-16","HIMARS","M1 Abrams","Patriot PAC-3"],"support":["USA","NATO","EU"],"status":"Defending"},
    {"name":"Russian Federation","side":"RU","color":"#ff3d5a","territory_pct":20,"strength":"High","weapons":["T-90M","Kalibr","Iskander","Shahed-136"],"support":["Belarus","Iran","DPRK"],"status":"Advancing"},
    {"name":"Wagner/Volunteer Corps","side":"RU","color":"#ff8c42","territory_pct":4,"strength":"Med","weapons":["Artillery","Armour"],"support":["Russia"],"status":"Active"},
  ],
  "incidents":[
    {"type":"airstrike","title":"Missile salvo targets Kyiv energy grid","loc":"Kyiv Oblast","lat":50.45,"lon":30.52,"date":"2026-03-14","severity":"CRITICAL","casualties":12},
    {"type":"ground","title":"Frontal assault near Avdiivka sector","loc":"Donetsk Oblast","lat":47.97,"lon":37.74,"date":"2026-03-14","severity":"HIGH","casualties":45},
    {"type":"drone","title":"Shahed drone swarm intercepted","loc":"Zaporizhzhia","lat":47.84,"lon":35.14,"date":"2026-03-13","severity":"HIGH","casualties":3},
    {"type":"naval","title":"Black Sea tanker seized","loc":"Black Sea","lat":44.5,"lon":32.5,"date":"2026-03-13","severity":"MED","casualties":0},
    {"type":"airstrike","title":"Kharkiv residential district strike","loc":"Kharkiv","lat":49.99,"lon":36.23,"date":"2026-03-12","severity":"CRITICAL","casualties":28},
    {"type":"cyber","title":"Power grid SCADA intrusion detected","loc":"Western Ukraine","lat":49.8,"lon":24.0,"date":"2026-03-12","severity":"HIGH","casualties":0},
    {"type":"ground","title":"Counterattack recaptures village","loc":"Kherson Oblast","lat":46.65,"lon":32.62,"date":"2026-03-11","severity":"MED","casualties":8},
  ],
  "timeline":[
    {"date":"2022-02-24","event":"Full-scale invasion begins","type":"escalation"},
    {"date":"2022-03-28","event":"Kyiv assault repelled","type":"milestone"},
    {"date":"2022-11-11","event":"Kherson city liberated","type":"milestone"},
    {"date":"2023-06-04","event":"Ukrainian counteroffensive","type":"escalation"},
    {"date":"2024-02-17","event":"Avdiivka falls to Russia","type":"setback"},
    {"date":"2024-08-06","event":"Ukraine's Kursk incursion","type":"escalation"},
    {"date":"2025-11-20","event":"US authorises long-range strikes","type":"escalation"},
    {"date":"2026-03-10","event":"Largest missile salvo of 2026","type":"escalation"},
  ],
  "supply_lines":[
    {"from_lat":48.8,"from_lon":2.35,"to_lat":50.45,"to_lon":30.52,"type":"Military Aid","provider":"France"},
    {"from_lat":52.52,"from_lon":13.4,"to_lat":50.45,"to_lon":30.52,"type":"Military Aid","provider":"Germany"},
    {"from_lat":38.9,"from_lon":-77.0,"to_lat":50.45,"to_lon":30.52,"type":"Military Aid","provider":"USA"},
  ],
  "media_sources":[
    {"name":"Reuters","bias":"Centre","reliability":92},{"name":"BBC","bias":"Centre-Left","reliability":88},
    {"name":"RT","bias":"State/RU","reliability":28},{"name":"Kyiv Independent","bias":"Pro-UA","reliability":74},
  ],
},
"Gaza Conflict": {
  "status":"ACTIVE","intensity":"CRITICAL","start":"2023-10-07","region":"Middle East",
  "escalation":92,"ceasefire":False,"casualties_total":46000,"displaced":1900000,
  "description":"Israeli military operations in Gaza following Hamas October 7 attacks. Severe humanitarian crisis with ongoing ground and air operations.",
  "factions":[
    {"name":"Israel Defense Forces","side":"IL","color":"#1a9fff","territory_pct":72,"strength":"High","weapons":["F-35I","Iron Dome","Merkava IV"],"support":["USA","UK"],"status":"Offensive"},
    {"name":"Hamas","side":"HA","color":"#ff3d5a","territory_pct":20,"strength":"Med","weapons":["Rockets","Tunnels","IEDs"],"support":["Iran"],"status":"Defending"},
    {"name":"Palestinian Islamic Jihad","side":"HA","color":"#ff8c42","territory_pct":5,"strength":"Low","weapons":["Rockets","Mortars"],"support":["Iran"],"status":"Active"},
    {"name":"UNRWA / Aid Corridors","side":"HU","color":"#00e676","territory_pct":3,"strength":"N/A","weapons":[],"support":["UN","EU"],"status":"Constrained"},
  ],
  "incidents":[
    {"type":"airstrike","title":"IDF strikes Rafah crossing area","loc":"Rafah, Gaza","lat":31.28,"lon":34.25,"date":"2026-03-14","severity":"CRITICAL","casualties":35},
    {"type":"ground","title":"Ground forces advance in northern Gaza","loc":"Gaza City","lat":31.52,"lon":34.47,"date":"2026-03-14","severity":"HIGH","casualties":22},
    {"type":"humanitarian","title":"Aid convoy blocked at Kerem Shalom","loc":"Kerem Shalom","lat":31.23,"lon":34.3,"date":"2026-03-13","severity":"HIGH","casualties":0},
    {"type":"rocket","title":"Hezbollah rocket barrage — Northern Israel","loc":"Northern Israel","lat":33.0,"lon":35.5,"date":"2026-03-13","severity":"HIGH","casualties":4},
  ],
  "timeline":[
    {"date":"2023-10-07","event":"Hamas multi-front attack — 1,200 killed","type":"escalation"},
    {"date":"2023-10-27","event":"Israeli ground invasion begins","type":"escalation"},
    {"date":"2023-11-24","event":"Temporary ceasefire and hostage deal","type":"diplomatic"},
    {"date":"2024-05-07","event":"Rafah ground operation begins","type":"escalation"},
    {"date":"2025-01-19","event":"Ceasefire phase-1 agreement","type":"diplomatic"},
    {"date":"2025-03-18","event":"Ceasefire collapses — operations resume","type":"escalation"},
    {"date":"2026-03-14","event":"Ongoing operations — Rafah and north Gaza","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":30.06,"from_lon":31.24,"to_lat":31.52,"to_lon":34.47,"type":"Humanitarian","provider":"Egypt/UN"},
    {"from_lat":38.9,"from_lon":-77.0,"to_lat":31.77,"to_lon":35.21,"type":"Military Aid","provider":"USA"},
    {"from_lat":35.69,"from_lon":51.39,"to_lat":31.28,"to_lon":34.25,"type":"Arms/Funding","provider":"Iran→Hamas"},
  ],
  "media_sources":[
    {"name":"Al Jazeera","bias":"Pro-Palestinian","reliability":72},{"name":"Times of Israel","bias":"Pro-Israel","reliability":71},
    {"name":"Reuters","bias":"Centre","reliability":91},{"name":"Haaretz","bias":"Centre-Left","reliability":83},
  ],
},
"Israel–Iran War": {
  "status":"ACTIVE","intensity":"CRITICAL","start":"2024-04-13","region":"Middle East",
  "escalation":88,"ceasefire":False,"casualties_total":2800,"displaced":280000,
  "description":"Direct military confrontation between Israel and Iran, escalating from decades of proxy conflict. Iran's April 2024 drone/missile barrage marked the first direct Iranian attack on Israeli soil. Israel struck Iranian nuclear and military sites in response. Hezbollah, IRGC proxies, and Houthi forces in Yemen form a multi-front pressure network.",
  "factions":[
    {"name":"Israel Defense Forces","side":"IL","color":"#1a9fff","territory_pct":0,"strength":"High","weapons":["F-35I","Arrow-3","David's Sling","Jericho III ICBM"],"support":["USA","UK","Jordan (limited)"],"status":"Offensive"},
    {"name":"Islamic Republic of Iran (IRGC)","side":"IR","color":"#ff3d5a","territory_pct":0,"strength":"High","weapons":["Shahab-3","Fattah-2 hypersonic","Shahed-136","S-300 equivalent"],"support":["Russia","China (covert)","Hezbollah","Houthis"],"status":"Retaliatory"},
    {"name":"Hezbollah","side":"IR","color":"#ff8c42","territory_pct":0,"strength":"Med","weapons":["Burkan rockets","Kornets","Radwan UAVs"],"support":["Iran","Syria"],"status":"Active"},
    {"name":"Houthis (Yemen)","side":"IR","color":"#ffb400","territory_pct":0,"strength":"Med","weapons":["Ballistic missiles","Samad UAVs","Naval drones"],"support":["Iran","Russia"],"status":"Active"},
    {"name":"US CENTCOM","side":"US","color":"#00e676","territory_pct":0,"strength":"High","weapons":["F-15EX","B-2 Spirit","THAAD","Patriot PAC-3"],"support":["Israel","UK","Bahrain","UAE"],"status":"Defensive support"},
  ],
  "incidents":[
    {"type":"airstrike","title":"Israel strikes IRGC Quds Force HQ — Isfahan","loc":"Isfahan, Iran","lat":32.65,"lon":51.68,"date":"2026-03-13","severity":"CRITICAL","casualties":45},
    {"type":"airstrike","title":"Iranian ballistic missile salvo targets Tel Aviv","loc":"Tel Aviv, Israel","lat":32.08,"lon":34.78,"date":"2026-03-12","severity":"CRITICAL","casualties":18},
    {"type":"airstrike","title":"Hezbollah precision missile — Haifa industrial zone","loc":"Haifa, Israel","lat":32.82,"lon":34.99,"date":"2026-03-14","severity":"HIGH","casualties":7},
    {"type":"drone","title":"Houthi Samad-3 drone intercepted over Eilat","loc":"Eilat, Israel","lat":29.56,"lon":34.95,"date":"2026-03-14","severity":"HIGH","casualties":0},
    {"type":"airstrike","title":"IDF destroys Fordow enrichment facility","loc":"Fordow, Iran","lat":34.88,"lon":49.93,"date":"2026-03-11","severity":"CRITICAL","casualties":62},
    {"type":"naval","title":"IRGC seizes commercial vessel in Strait of Hormuz","loc":"Strait of Hormuz","lat":26.56,"lon":56.26,"date":"2026-03-10","severity":"HIGH","casualties":0},
    {"type":"cyber","title":"Stuxnet-class malware hits Iranian power grid","loc":"Tehran, Iran","lat":35.69,"lon":51.39,"date":"2026-03-09","severity":"HIGH","casualties":0},
    {"type":"airstrike","title":"Israel strikes Natanz nuclear site","loc":"Natanz, Iran","lat":33.72,"lon":51.73,"date":"2026-03-07","severity":"CRITICAL","casualties":28},
    {"type":"diplomatic","title":"UN Security Council convenes — US vetoes ceasefire resolution","loc":"New York","lat":40.75,"lon":-73.98,"date":"2026-03-08","severity":"INFO","casualties":0},
    {"type":"airstrike","title":"US B-2 strikes IRGC air defence network — Bushehr","loc":"Bushehr, Iran","lat":28.98,"lon":50.84,"date":"2026-03-06","severity":"CRITICAL","casualties":34},
  ],
  "timeline":[
    {"date":"2024-04-01","event":"Israel strikes Iranian consulate in Damascus","type":"escalation"},
    {"date":"2024-04-13","event":"Iran fires 300+ drones/missiles at Israel — 99% intercepted","type":"escalation"},
    {"date":"2024-04-19","event":"Israeli strike on Isfahan air defence radar","type":"escalation"},
    {"date":"2024-09-27","event":"IDF assassinates Hezbollah leader Nasrallah","type":"milestone"},
    {"date":"2024-10-01","event":"Iran fires ~180 ballistic missiles — most intercepted","type":"escalation"},
    {"date":"2024-10-26","event":"Israel strikes Iranian missile factories & air defences","type":"escalation"},
    {"date":"2025-06-13","event":"Israel strikes Iranian nuclear research facility","type":"escalation"},
    {"date":"2025-08-30","event":"Iran retaliates — major hypersonic missile salvo","type":"escalation"},
    {"date":"2025-12-01","event":"US CENTCOM deploys additional carrier strike groups","type":"escalation"},
    {"date":"2026-02-14","event":"IDF destroys Fordow uranium enrichment complex","type":"milestone"},
    {"date":"2026-03-07","event":"Natanz facility struck — nuclear programme set back 2+ years","type":"milestone"},
    {"date":"2026-03-14","event":"Active exchanges continue — war in full escalation","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":38.9,"from_lon":-77.0,"to_lat":32.08,"to_lon":34.78,"type":"Military Aid","provider":"USA→Israel"},
    {"from_lat":51.5,"from_lon":-0.1,"to_lat":32.08,"to_lon":34.78,"type":"Military Aid","provider":"UK→Israel"},
    {"from_lat":35.69,"from_lon":51.39,"to_lat":33.52,"to_lon":36.29,"type":"Arms/Funding","provider":"Iran→Hezbollah"},
    {"from_lat":35.69,"from_lon":51.39,"to_lat":15.35,"to_lon":44.21,"type":"Arms/Funding","provider":"Iran→Houthis"},
    {"from_lat":55.75,"from_lon":37.61,"to_lat":35.69,"to_lon":51.39,"type":"Military Aid","provider":"Russia→Iran (covert)"},
  ],
  "media_sources":[
    {"name":"Times of Israel","bias":"Pro-Israel","reliability":71},
    {"name":"Al Jazeera","bias":"Pro-Palestinian","reliability":72},
    {"name":"Reuters","bias":"Centre","reliability":91},
    {"name":"BBC","bias":"Centre","reliability":87},
    {"name":"Iranian Press TV","bias":"State/IR","reliability":21},
    {"name":"Jerusalem Post","bias":"Right/Israel","reliability":68},
  ],
},
"Sudan Civil War": {
  "status":"ACTIVE","intensity":"HIGH","start":"2023-04-15","region":"Sub-Saharan Africa",
  "escalation":74,"ceasefire":False,"casualties_total":15000,"displaced":8100000,
  "description":"Armed conflict between Sudanese Armed Forces (SAF) and Rapid Support Forces (RSF). Darfur faces atrocity risk; famine declared in multiple regions.",
  "factions":[
    {"name":"Sudanese Armed Forces","side":"SAF","color":"#1a9fff","territory_pct":55,"strength":"Med","weapons":["Su-25","T-72","Mi-24"],"support":["Egypt","Saudi Arabia"],"status":"Active"},
    {"name":"Rapid Support Forces","side":"RSF","color":"#ff3d5a","territory_pct":38,"strength":"High","weapons":["Technicals","ZU-23","Armour"],"support":["UAE","Wagner"],"status":"Advancing"},
    {"name":"Sudan Liberation Army","side":"SLA","color":"#ffb400","territory_pct":5,"strength":"Low","weapons":["Light arms"],"support":["None"],"status":"Active"},
  ],
  "incidents":[
    {"type":"airstrike","title":"SAF airstrike — Omdurman RSF position","loc":"Omdurman","lat":15.65,"lon":32.48,"date":"2026-03-14","severity":"HIGH","casualties":18},
    {"type":"ground","title":"RSF advances in El Fasher, North Darfur","loc":"El Fasher","lat":13.63,"lon":25.35,"date":"2026-03-13","severity":"CRITICAL","casualties":42},
    {"type":"humanitarian","title":"MSF hospital shelled — Khartoum North","loc":"Khartoum","lat":15.5,"lon":32.53,"date":"2026-03-12","severity":"CRITICAL","casualties":9},
    {"type":"diplomatic","title":"Jeddah peace talks collapse","loc":"Jeddah","lat":21.49,"lon":39.19,"date":"2026-03-10","severity":"MED","casualties":0},
  ],
  "timeline":[
    {"date":"2023-04-15","event":"Open fighting erupts in Khartoum","type":"escalation"},
    {"date":"2023-06-01","event":"RSF seizes most of Khartoum","type":"setback"},
    {"date":"2023-10-26","event":"Darfur atrocities — UN warning","type":"escalation"},
    {"date":"2024-03-13","event":"El Fasher siege begins","type":"escalation"},
    {"date":"2025-01-10","event":"SAF recaptures parts of Khartoum","type":"milestone"},
    {"date":"2026-03-14","event":"RSF advancing in Darfur — famine risk","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":25.2,"from_lon":55.27,"to_lat":15.65,"to_lon":32.48,"type":"RSF Support","provider":"UAE"},
    {"from_lat":30.06,"from_lon":31.24,"to_lat":15.65,"to_lon":32.48,"type":"SAF Support","provider":"Egypt"},
  ],
  "media_sources":[
    {"name":"Sudan Tribune","bias":"Local","reliability":67},{"name":"Reuters","bias":"Centre","reliability":91},
    {"name":"BBC","bias":"Centre","reliability":86},{"name":"Al Jazeera","bias":"Centre-Left","reliability":75},
  ],
},
"Myanmar Civil War": {
  "status":"ACTIVE","intensity":"HIGH","start":"2021-02-01","region":"Southeast Asia",
  "escalation":68,"ceasefire":False,"casualties_total":50000,"displaced":2600000,
  "description":"Armed resistance against Myanmar military junta (SAC/Tatmadaw) by People's Defence Force and Ethnic Resistance Organisations.",
  "factions":[
    {"name":"Tatmadaw / SAC","side":"JU","color":"#ff3d5a","territory_pct":45,"strength":"Med","weapons":["Yak-130","Mi-35","D30"],"support":["Russia","China"],"status":"Defending"},
    {"name":"People's Defence Force","side":"OP","color":"#00e676","territory_pct":35,"strength":"Med","weapons":["Drones","IEDs","Captured arms"],"support":["NUG","Diaspora"],"status":"Offensive"},
    {"name":"Ethnic Resistance Orgs","side":"OP","color":"#1a9fff","territory_pct":18,"strength":"Med","weapons":["Artillery","Infantry"],"support":["PDF","NUG"],"status":"Advancing"},
  ],
  "incidents":[
    {"type":"airstrike","title":"Junta airstrike on PDF-held village","loc":"Sagaing Region","lat":21.9,"lon":95.98,"date":"2026-03-14","severity":"HIGH","casualties":14},
    {"type":"ground","title":"3BHA captures Hsipaw town","loc":"Shan State","lat":22.6,"lon":97.3,"date":"2026-03-13","severity":"HIGH","casualties":20},
    {"type":"humanitarian","title":"IDP camp shelled — 30,000 displaced","loc":"Kayah State","lat":19.74,"lon":97.34,"date":"2026-03-12","severity":"CRITICAL","casualties":7},
  ],
  "timeline":[
    {"date":"2021-02-01","event":"Military coup overthrows NLD government","type":"escalation"},
    {"date":"2021-09-07","event":"NUG declares People's Defensive War","type":"escalation"},
    {"date":"2023-10-27","event":"Operation 1027 — major offensive","type":"milestone"},
    {"date":"2024-04-11","event":"Myawaddy falls to resistance","type":"milestone"},
    {"date":"2026-03-14","event":"Resistance controls 60%+ of territory","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":39.9,"from_lon":116.39,"to_lat":21.9,"to_lon":95.98,"type":"Junta Support","provider":"China"},
    {"from_lat":55.75,"from_lon":37.61,"to_lat":16.87,"to_lon":96.19,"type":"Arms Supply","provider":"Russia"},
  ],
  "media_sources":[
    {"name":"Irrawaddy","bias":"Pro-Resistance","reliability":75},{"name":"Myanmar Now","bias":"Pro-Resistance","reliability":70},
    {"name":"Reuters","bias":"Centre","reliability":91},{"name":"Global New Light","bias":"State/Junta","reliability":22},
  ],
},
"Pakistan-Afghanistan Conflict": {
  "status":"ACTIVE","intensity":"HIGH","start":"2024-03-15","region":"South Asia",
  "escalation":72,"ceasefire":False,"casualties_total":3200,"displaced":850000,
  "description":"Escalating cross-border conflict between Pakistan and Taliban-governed Afghanistan. Pakistan conducts regular airstrikes against TTP (Tehrik-i-Taliban Pakistan) hideouts in eastern Afghanistan. Taliban retaliates with cross-border incursions into KPK and Balochistan. Bilateral relations severed; IMF-backed Pakistan economy under stress from security costs.",
  "factions":[
    {"name":"Pakistan Armed Forces","side":"PK","color":"#1a9fff","territory_pct":0,"strength":"High","weapons":["F-16","JF-17 Thunder","Al-Khalid MBT","Shaheen MRBM"],"support":["China","Saudi Arabia","USA (limited)"],"status":"Offensive strikes"},
    {"name":"Tehrik-i-Taliban Pakistan (TTP)","side":"AF","color":"#ff3d5a","territory_pct":0,"strength":"Med","weapons":["Small arms","IEDs","Mortars","Captured equipment"],"support":["Afghan Taliban","Al-Qaeda affiliates"],"status":"Cross-border attacks"},
    {"name":"Afghan Taliban (IEA)","side":"AF","color":"#ff8c42","territory_pct":0,"strength":"High","weapons":["US-abandoned HMMWVs","Black Hawks","Captured M4s"],"support":["Pakistan (historical)","China (economic)"],"status":"Sheltering TTP / retaliatory"},
    {"name":"BLA / Baloch insurgents","side":"BL","color":"#ffb400","territory_pct":0,"strength":"Low","weapons":["IEDs","Small arms"],"support":["None confirmed"],"status":"Active in Balochistan"},
  ],
  "incidents":[
    {"type":"airstrike","title":"PAF F-16 strikes TTP compound — Paktika","loc":"Paktika, Afghanistan","lat":32.26,"lon":69.05,"date":"2026-03-12","severity":"HIGH","casualties":28},
    {"type":"ground","title":"TTP cross-border attack — Khyber Pakhtunkhwa","loc":"KPK, Pakistan","lat":33.91,"lon":70.84,"date":"2026-03-11","severity":"HIGH","casualties":15},
    {"type":"airstrike","title":"Pakistan drones strike Kunar Province","loc":"Kunar, Afghanistan","lat":34.85,"lon":71.1,"date":"2026-03-10","severity":"HIGH","casualties":22},
    {"type":"diplomatic","title":"Taliban closes border crossing at Torkham","loc":"Torkham","lat":34.1,"lon":71.1,"date":"2026-03-09","severity":"MED","casualties":0},
    {"type":"ground","title":"BLA ambush on Makran Coastal Highway","loc":"Balochistan, Pakistan","lat":25.86,"lon":62.72,"date":"2026-03-08","severity":"HIGH","casualties":9},
    {"type":"airstrike","title":"PAF strikes — Khost Province TTP network","loc":"Khost, Afghanistan","lat":33.33,"lon":69.92,"date":"2026-03-05","severity":"HIGH","casualties":31},
  ],
  "timeline":[
    {"date":"2021-08-15","event":"Taliban seize Kabul — TTP emboldened","type":"escalation"},
    {"date":"2022-04-01","event":"TTP attacks surge — 20 incidents/month","type":"escalation"},
    {"date":"2023-11-06","event":"Pakistan formally designates TTP terrorist","type":"milestone"},
    {"date":"2024-03-15","event":"Pakistan first major air strikes in Afghanistan","type":"escalation"},
    {"date":"2024-10-28","event":"Afghan Taliban formally backs TTP — Pakistan protests","type":"escalation"},
    {"date":"2025-02-14","event":"Pakistan expels Afghan ambassador","type":"diplomatic"},
    {"date":"2025-06-20","event":"Major PAF strike kills 80+ in Khost — Taliban retaliates","type":"escalation"},
    {"date":"2026-01-18","event":"Pakistan deployes additional corps to NW frontier","type":"escalation"},
    {"date":"2026-03-12","event":"Active exchanges — border closed at Torkham","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":33.73,"from_lon":73.06,"to_lat":33.91,"to_lon":70.84,"type":"Military Ops","provider":"Pakistan Armed Forces"},
    {"from_lat":31.52,"from_lon":74.35,"to_lat":33.91,"to_lon":70.84,"type":"Reinforcement","provider":"Pakistan"},
  ],
  "media_sources":[
    {"name":"Dawn","bias":"Pakistani mainstream","reliability":74},{"name":"The News International","bias":"Pakistani","reliability":68},
    {"name":"Tolo News","bias":"Afghan","reliability":61},{"name":"Reuters","bias":"Centre","reliability":91},
  ],
},
"Haiti Gang War": {
  "status":"ACTIVE","intensity":"HIGH","start":"2023-02-01","region":"Caribbean",
  "escalation":80,"ceasefire":False,"casualties_total":5800,"displaced":580000,
  "description":"Gang coalition Viv Ansanm controls 85%+ of Port-au-Prince. State has collapsed; PM resigned; Kenyan-led Multinational Security Support mission deployed but under-resourced. Famine declared in several regions.",
  "factions":[
    {"name":"Viv Ansanm (G9/GPEP coalition)","side":"GA","color":"#ff3d5a","territory_pct":85,"strength":"High","weapons":["Firearms","Armoured vehicles (captured)","50-cal. M2"],"support":["Diaspora funding","Criminal networks"],"status":"Controlling Port-au-Prince"},
    {"name":"Haiti National Police","side":"HG","color":"#1a9fff","territory_pct":10,"strength":"Low","weapons":["Light arms","Limited armour"],"support":["Kenya-led MSS","USA funding"],"status":"Overwhelmed"},
    {"name":"Kenyan-led MSS Mission","side":"IN","color":"#00e676","territory_pct":5,"strength":"Med","weapons":["Armoured vehicles","Helicopters"],"support":["USA","UN mandate"],"status":"Deployed — limited capacity"},
  ],
  "incidents":[
    {"type":"ground","title":"Gang siege — Pétion-Ville district","loc":"Port-au-Prince","lat":18.54,"lon":-72.34,"date":"2026-03-14","severity":"CRITICAL","casualties":32},
    {"type":"humanitarian","title":"MSF: 500,000 facing acute malnutrition","loc":"Haiti","lat":18.7,"lon":-72.5,"date":"2026-03-12","severity":"CRITICAL","casualties":0},
    {"type":"ground","title":"Gangs seize National Palace perimeter","loc":"Port-au-Prince","lat":18.55,"lon":-72.34,"date":"2026-03-10","severity":"CRITICAL","casualties":18},
  ],
  "timeline":[
    {"date":"2021-07-07","event":"President Jovenel Moïse assassinated","type":"escalation"},
    {"date":"2023-02-01","event":"Gang coalition Viv Ansanm forms","type":"escalation"},
    {"date":"2024-03-11","event":"PM Henry resigns — transitional council formed","type":"diplomatic"},
    {"date":"2024-06-25","event":"Kenya deploys 400 police to Haiti","type":"milestone"},
    {"date":"2025-01-01","event":"Gang control expands to 85% of PaP","type":"setback"},
    {"date":"2026-03-14","event":"Ongoing — state effectively collapsed","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":-1.28,"from_lon":36.82,"to_lat":18.54,"to_lon":-72.34,"type":"MSS Support","provider":"Kenya"},
    {"from_lat":38.9,"from_lon":-77.0,"to_lat":18.54,"to_lon":-72.34,"type":"Funding/Training","provider":"USA"},
  ],
  "media_sources":[
    {"name":"Haiti Libre","bias":"Local","reliability":58},{"name":"Reuters","bias":"Centre","reliability":91},
    {"name":"AP News","bias":"Centre","reliability":89},{"name":"Al Jazeera","bias":"Centre-Left","reliability":76},
  ],
},
}

INCIDENT_ICONS = {"airstrike":"💥","ground":"⚔️","drone":"🛸","naval":"⚓","rocket":"🚀","cyber":"💻","diplomatic":"🤝","humanitarian":"🏥"}
INCIDENT_COLORS = {
    "airstrike":"rgba(255,61,90,.18)","ground":"rgba(255,140,66,.15)","drone":"rgba(157,110,255,.15)",
    "naval":"rgba(0,200,255,.15)","rocket":"rgba(255,180,0,.15)","cyber":"rgba(0,200,255,.12)",
    "diplomatic":"rgba(0,230,118,.12)","humanitarian":"rgba(0,200,255,.1)",
}
SEV_BADGE = {"CRITICAL":"b-red","HIGH":"b-orange","MED":"b-amber","LOW":"b-green","INFO":"b-muted"}

MOVEMENTS = [
    # ── Active 2025-2026 Civil Movements ──────────────────────
    {"id":"mv1","type":"protest","title":"Anti-austerity protests","location":"Athens, Greece","country":"GR","size":"45,000+","sentiment":"HIGH","scale":80,"lat":37.98,"lon":23.73,"age_h":3},
    {"id":"mv2","type":"strike","title":"General strike — pension reform","location":"Paris, France","country":"FR","size":"National","sentiment":"HIGH","scale":72,"lat":48.85,"lon":2.35,"age_h":5},
    {"id":"mv3","type":"civil","title":"Pro-democracy vigils (post-impeachment)","location":"Seoul, South Korea","country":"KR","size":"80,000+","sentiment":"HIGH","scale":85,"lat":37.57,"lon":126.98,"age_h":2},
    {"id":"mv4","type":"civil","title":"Anti-junta uprising","location":"Yangon, Myanmar","country":"MM","size":"50,000+","sentiment":"CRIT","scale":92,"lat":16.87,"lon":96.19,"age_h":1},
    {"id":"mv5","type":"protest","title":"Cost-of-living demonstrations","location":"Nairobi, Kenya","country":"KE","size":"30,000+","sentiment":"HIGH","scale":78,"lat":-1.29,"lon":36.82,"age_h":4},
    {"id":"mv6","type":"strike","title":"Port workers strike","location":"Hamburg, Germany","country":"DE","size":"Port-wide","sentiment":"MED","scale":55,"lat":53.55,"lon":9.99,"age_h":12},
    {"id":"mv7","type":"protest","title":"Anti-government protests","location":"Tbilisi, Georgia","country":"GE","size":"100,000+","sentiment":"CRIT","scale":90,"lat":41.69,"lon":44.83,"age_h":6},
    {"id":"mv8","type":"civil","title":"Pro-EU demonstrations","location":"Belgrade, Serbia","country":"RS","size":"60,000+","sentiment":"HIGH","scale":82,"lat":44.82,"lon":20.46,"age_h":8},
    {"id":"mv9","type":"protest","title":"Economic protests","location":"Dhaka, Bangladesh","country":"BD","size":"200,000+","sentiment":"CRIT","scale":91,"lat":23.81,"lon":90.41,"age_h":2},
    {"id":"mv10","type":"protest","title":"IMF austerity protests","location":"Cairo, Egypt","country":"EG","size":"25,000","sentiment":"HIGH","scale":70,"lat":30.06,"lon":31.24,"age_h":14},
    {"id":"mv11","type":"civil","title":"Maduro opposition rallies","location":"Caracas, Venezuela","country":"VE","size":"40,000+","sentiment":"HIGH","scale":75,"lat":10.48,"lon":-66.87,"age_h":10},
    {"id":"mv12","type":"protest","title":"Gang violence protests","location":"Port-au-Prince, Haiti","country":"HT","size":"15,000","sentiment":"CRIT","scale":88,"lat":18.54,"lon":-72.34,"age_h":7},
]

# News sources registry
NEWS_SOURCES = [
    {"name":"Reuters",       "cat":"global",       "color":"#ff8c42", "site":"reuters.com",        "desc":"Global wire service, 170+ countries",          "rss":"https://feeds.reuters.com/reuters/worldNews"},
    {"name":"BBC World",     "cat":"global",       "color":"#bb1919", "site":"bbc.com",             "desc":"BBC international news",                       "rss":"http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name":"Al Jazeera",    "cat":"global",       "color":"#00873c", "site":"aljazeera.com",       "desc":"Middle East & Global South focus",             "rss":"https://www.aljazeera.com/xml/rss/all.xml"},
    {"name":"AP News",       "cat":"global",       "color":"#cc0000", "site":"apnews.com",          "desc":"Associated Press — breaking world news",       "rss":"https://apnews.com/rss"},
    {"name":"NASA JPL",      "cat":"science",      "color":"#0b3d91", "site":"jpl.nasa.gov",        "desc":"NASA Jet Propulsion Lab — Earth & space",      "rss":"https://www.jpl.nasa.gov/feeds/news"},
    {"name":"USGS",          "cat":"science",      "color":"#4caf50", "site":"usgs.gov",            "desc":"Earthquakes, volcanoes, hazards",               "rss":"https://www.usgs.gov/news/science-news/rss.xml"},
    {"name":"Phys.org",      "cat":"science",      "color":"#1a7fc1", "site":"phys.org",            "desc":"Earth science & geoscience research",          "rss":"https://phys.org/rss-feed/earth-news/"},
    {"name":"Foreign Policy","cat":"geopolitics",  "color":"#8b1a1a", "site":"foreignpolicy.com",   "desc":"International affairs & strategy",             "rss":"https://foreignpolicy.com/feed/"},
    {"name":"The Diplomat",  "cat":"geopolitics",  "color":"#1a3a5c", "site":"thediplomat.com",     "desc":"Asia-Pacific geopolitics & security",          "rss":"https://thediplomat.com/feed/"},
    {"name":"Defense One",   "cat":"geopolitics",  "color":"#444444", "site":"defenseone.com",      "desc":"US & global defence, security, military",      "rss":"https://www.defenseone.com/rss/all/"},
    {"name":"ISW",           "cat":"conflict",     "color":"#800020", "site":"understandingwar.org","desc":"Institute for the Study of War — daily updates","rss":"https://understandingwar.org/rss.xml"},
    {"name":"ACLED",         "cat":"conflict",     "color":"#cc0000", "site":"acleddata.com",       "desc":"Armed Conflict Location & Event Data",         "rss":"https://acleddata.com/feed/"},
    {"name":"CSIS",          "cat":"conflict",     "color":"#003366", "site":"csis.org",            "desc":"Center for Strategic & International Studies",  "rss":"https://www.csis.org/rss/analysis"},
    {"name":"Carbon Brief",  "cat":"climate",      "color":"#1b5e20", "site":"carbonbrief.org",     "desc":"Climate science & policy analysis",            "rss":"https://www.carbonbrief.org/feed"},
    {"name":"SpaceWeather",  "cat":"spaceweather", "color":"#4a148c", "site":"spaceweather.com",    "desc":"Solar activity, geomagnetic storms, aurora",   "rss":"https://spaceweather.com/index.xml"},
    {"name":"NOAA SWPC",     "cat":"spaceweather", "color":"#0d47a1", "site":"swpc.noaa.gov",       "desc":"NOAA Space Weather Prediction Center",         "rss":"https://www.swpc.noaa.gov/news/rss.xml"},
]

NEWS_CAT_COLOR = {
    "global":"#ff8c42","science":"#00c8ff","geopolitics":"#9d6eff",
    "conflict":"#ff3d5a","climate":"#00e676","spaceweather":"#ffb400",
}
NEWS_CAT_CARD = {
    "global":"nc-global","science":"nc-science","geopolitics":"nc-geo",
    "conflict":"nc-conflict","climate":"nc-climate","spaceweather":"nc-space",
}

# ── News category helpers (previously undefined) ──────────────
CAT_TABS_NEWS = ["ALL", "global", "geopolitics", "conflict", "science", "climate", "spaceweather"]
CAT_NAMES_ART = {
    "ALL":         "🌐 All",
    "global":      "🌍 Global",
    "geopolitics": "🏛 Geopolitics",
    "conflict":    "⚔ Conflict",
    "science":     "🔬 Science",
    "climate":     "🌿 Climate",
    "spaceweather":"🌌 Space Weather",
}

# ── HLS channel category name map (previously undefined) ──────
# Each channel carries multiple HLS fallback URLs tried in order by the browser player.
# If all HLS sources fail the player shows a direct link to the official live page.
HLS_CHANNELS = [
    {
        "name": "Bloomberg TV", "color": "#f04e23", "cat": "global",
        "web": "https://www.bloomberg.com/live",
        "desc": "Markets, finance & global business news 24/7",
        "hls": [
            "https://bloomberg-bloombergtv-5-eu.plex.wurl.tv/playlist.m3u8",
            "https://cdn-gl-prod.tsv2.amagi.tv/linear/amg01077-bloombergtv-bloombergtv-tubi/playlist.m3u8",
            "https://cdn-na1-prod.tsv2.amagi.tv/linear/amg01077-bloombergtv-bloombergtvus-samsung/playlist.m3u8",
            "https://bloomberg-1-eu.wurl.tv/playlist.m3u8",
        ],
    },
    {
        "name": "Sky News", "color": "#004f9f", "cat": "global",
        "web": "https://news.sky.com/watch-live",
        "desc": "UK breaking news & international coverage",
        "hls": [
            "https://linear-116.frequency.stream/dist/us/skynewsuk/playlist.m3u8",
            "https://skynewshduk-lh.akamaihd.net/i/skynewshduk_1@44098/master.m3u8",
            "https://d25w9q07b2mtmw.cloudfront.net/live/master.m3u8",
            "https://skynews-skynewsuk.hls.adaptive.level3.net/skynews/skynewsuk/playlist.m3u8",
        ],
    },
    {
        "name": "Euronews", "color": "#003399", "cat": "global",
        "web": "https://www.euronews.com/live",
        "desc": "Pan-European news in English — 24/7 live",
        "hls": [
            "https://euronews-1.cdn.euronews.com/live/euronews/euronewsen/playlist.m3u8",
            "https://euronews-2.cdn.euronews.com/live/euronews/euronewsen/playlist.m3u8",
            "https://euronews-euronews-euronewsen-1-eu.rakuten.wurl.tv/playlist.m3u8",
            "https://euronews-livepkgr.akamaized.net/hls/live/582849/euronewslive/euronewsen/playlist.m3u8",
        ],
    },
    {
        "name": "DW News", "color": "#003087", "cat": "global",
        "web": "https://www.dw.com/en/media-center/live-tv/l-150330",
        "desc": "Deutsche Welle English — German public broadcaster",
        "hls": [
            "https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/index.m3u8",
            "https://dwamdstream104.akamaized.net/hls/live/2015527/dwstream104/index.m3u8",
            "https://dwamdstream106.akamaized.net/hls/live/2015529/dwstream106/index.m3u8",
            "https://dwstream102-lh.akamaihd.net/i/dwstream102_1@326562/master.m3u8",
        ],
    },
    {
        "name": "CNBC", "color": "#004b87", "cat": "global",
        "web": "https://www.cnbc.com/live-tv",
        "desc": "US & global markets, business, breaking news",
        "hls": [
            "https://linear-55.frequency.stream/dist/us/cnbc-intl/playlist.m3u8",
            "https://cnbcnewsus-i.akamaihd.net/hls/live/686878/NBCNEWSUS/master.m3u8",
            "https://cnbc.cdn.turner.com/cnbc/big/live/master.m3u8",
            "https://linear-9.frequency.stream/dist/us/cnbc/playlist.m3u8",
        ],
    },
    {
        "name": "CNN International", "color": "#cc0000", "cat": "global",
        "web": "https://edition.cnn.com/live-tv",
        "desc": "CNN International 24/7 world news stream",
        "hls": [
            "https://ds2c506obo7m8.cloudfront.net/v1/master/3722c60a815c199d9c0ef36c5b73da68a62b09d1/cc-7zjq3tdqasbg8/index.m3u8",
            "https://arn-cnni.akamaized.net/hls/live/master.m3u8",
            "https://cnn-cnninternational.hls.adaptive.level3.net/cnn/cnn/cnn_intl/live/playlist.m3u8",
            "https://turner-cnni-live.akamaized.net/hls/live/master.m3u8",
        ],
    },
    {
        "name": "France 24", "color": "#002395", "cat": "global",
        "web": "https://www.france24.com/en/live-news",
        "desc": "French international broadcaster in English",
        "hls": [
            "https://static.france24.com/live/F24_EN_HI_HLS/live_tv.m3u8",
            "https://france24hls-i.akamaihd.net/hls/live/221892/F24_EN_HI/master.m3u8",
            "https://france24-lh.akamaihd.net/i/france24_en_1@116291/master.m3u8",
            "https://f24hls-i.akamaihd.net/hls/live/221892/F24_EN_LO/master.m3u8",
        ],
    },
    {
        "name": "Al Arabiya", "color": "#b8860b", "cat": "global",
        "web": "https://english.alarabiya.net/live",
        "desc": "Pan-Arab 24/7 news — English stream",
        "hls": [
            "https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8",
            "https://alarabiya-alarabiyaen.hls.adaptive.level3.net/alarabiya/alarabiyaen/playlist.m3u8",
            "https://alarabiya.cdn.arabiantelevision.net/live/alarabiya.m3u8",
            "https://alarabiya-lh.akamaihd.net/i/alarabiya_1@144411/master.m3u8",
        ],
    },
    {
        "name": "Al Jazeera English", "color": "#00873c", "cat": "global",
        "web": "https://www.aljazeera.com/live",
        "desc": "Qatar — 24/7 English, global & Middle East coverage",
        "hls": [
            "https://live-hls-web-aje.getaj.net/AJE/index.m3u8",
            "https://aljazeera-a.akamaihd.net/hls/live/256498/AJE-PHD@355396/master.m3u8",
            "https://aljazeera-eng-hd-aje.akamaized.net/hls/live/2014416/AJE/master.m3u8",
            "https://live-hls-aje-ak.getaj.net/AJE/index.m3u8",
        ],
    },
    {
        "name": "NDTV 24x7", "color": "#e31837", "cat": "global",
        "web": "https://www.ndtv.com/live-tv",
        "desc": "India's leading English news channel 24/7",
        "hls": [
            "https://ndtv24x7elemarchana.akamaized.net/hls/live/2003678/ndtv24x7/ndtv24x7master.m3u8",
            "https://ndtvstre1-lh.akamaihd.net/i/ndtvindia_1@21017/master.m3u8",
            "https://ndtv24x7-lh.akamaihd.net/i/ndtv24x7_1@189730/master.m3u8",
            "https://ndtv-ndtv24x7.hls.adaptive.level3.net/ndtv/ndtv24x7/master.m3u8",
        ],
    },
]

HLS_CAT_NAMES = {
    "ALL":    "🌐 All",
    "global": "🌍 Global",
}

# ─────────────────────────────────────────────
# LIVE DATA FETCHERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def fetch_usgs():
    try:
        r = requests.get(
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
            timeout=8)
        r.raise_for_status()
        rows = []
        for f in r.json()["features"][:50]:
            p, c = f["properties"], f["geometry"]["coordinates"]
            rows.append({
                "title": p.get("title","—"), "mag": round(p.get("mag",0),1),
                "place": p.get("place","?"), "depth_km": round(c[2],1),
                "lon": c[0], "lat": c[1], "type": "seismic",
                "time": datetime.fromtimestamp(p["time"]/1000,tz=timezone.utc).strftime("%H:%Mz"),
                "url": p.get("url",""),
            })
        _persist("seismic_events", rows)
        return pd.DataFrame(rows)
    except:
        # ── Last resort: rebuild DataFrame from persisted rows ──
        _stored_q = load_persisted("seismic_events", limit=50)
        if _stored_q:
            try:
                return pd.DataFrame(_stored_q)
            except Exception:
                pass
        return _sq()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_eonet():
    try:
        r = requests.get("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=20", timeout=8)
        r.raise_for_status()
        rows = []
        for e in r.json()["events"]:
            cat = e["categories"][0]["title"] if e["categories"] else "Other"
            if e["geometry"]:
                geo = e["geometry"][-1]
                if geo["type"] == "Point":
                    rows.append({"title":e["title"],"cat":cat,"date":geo["date"][:10],
                                 "lon":geo["coordinates"][0],"lat":geo["coordinates"][1],"type":"eonet"})
        return pd.DataFrame(rows) if rows else _se()
    except:
        return _se()

@st.cache_data(ttl=60, show_spinner=False)
def fetch_kp():
    try:
        r = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=6)
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, list) or not data:
            raise ValueError("Unexpected KP data shape")
        series = []
        for row in data[-24:]:
            try:
                if isinstance(row, (list, tuple)) and len(row) > 1:
                    series.append(float(row[1]))
                elif isinstance(row, dict):
                    series.append(float(row.get("Kp") or row.get("kp_index") or 0))
            except (TypeError, ValueError):
                pass
        latest = series[-1] if series else 3.7
        return {"kp": round(latest, 1), "series": series}
    except Exception:
        return {"kp": 3.7, "series": [1,2,1.5,2.3,3.1,3.7,2.8,2.1,1.8,2.5,3,3.7]*2}

# ── GDELT conflict-scoped fetcher ────────────────────────────
CONFLICT_QUERIES = {
    "Ukraine–Russia War":  ["Ukraine Russia war shelling missile", "Ukraine war frontline", "Russia Ukraine attack"],
    "Gaza Conflict":       ["Gaza Israel war strikes", "Gaza humanitarian IDF Hamas", "Gaza ceasefire"],
    "Israel–Iran War":     ["Israel Iran war strike nuclear", "Israel Iran missiles IRGC", "Hezbollah Israel attack"],
    "Sudan Civil War":     ["Sudan RSF SAF war Darfur", "Sudan civil war Khartoum", "Sudan famine conflict"],
    "Myanmar Civil War":   ["Myanmar junta resistance PDF war", "Myanmar military coup resistance", "Myanmar Tatmadaw"],
}

@st.cache_data(ttl=60, show_spinner=False)
def _parse_age(dt: datetime) -> tuple:
    """Return (age_s, dt_str, is_recent, is_new) from a datetime."""
    age   = datetime.now(tz=timezone.utc) - dt
    age_h = age.total_seconds() / 3600
    if age_h < 1:
        age_s = f"{int(age.total_seconds()//60)}m ago"
    elif age_h < 24:
        age_s = f"{int(age_h)}h ago"
    else:
        age_s = f"{int(age_h//24)}d ago"
    return age_s, dt.strftime("%Y-%m-%d %H:%Mz"), age_h < 6, age_h < 1


@st.cache_data(ttl=120, show_spinner=False)
def fetch_rss_conflict(theatre: str) -> list:
    """Fetch conflict news via server-side RSS parsing — no CORS proxies needed."""
    import xml.etree.ElementTree as ET

    # Per-theatre keyword filters applied to RSS titles
    keywords = {
        "Ukraine\u2013Russia War": ["ukraine","russia","kyiv","kremlin","zelenskyy","putin","donbas","kharkiv","kherson","kursk","nato","zaporizhzhia"],
        "Gaza Conflict":           ["gaza","hamas","israel","rafah","west bank","idf","netanyahu","ceasefire","hostage","palestin"],
        "Israel\u2013Iran War":    ["iran","israel","tehran","natanz","idf","hezbollah","mossad","irgc","nuclear","missile strike"],
        "Sudan Civil War":         ["sudan","rsf","khartoum","darfur","el fasher","saf","hemeti","al-burhan"],
        "Myanmar Civil War":       ["myanmar","burma","tatmadaw","junta","nug","pdf","mandalay","yangon","ethnic armed"],
    }
    kws = keywords.get(theatre, [theatre.lower().split("\u2013")[0].strip()])

    # RSS sources — tried in order, first success wins enough articles
    rss_sources = [
        ("Reuters",    "https://feeds.reuters.com/reuters/worldNews"),
        ("Reuters",    "http://feeds.reuters.com/reuters/worldNews"),
        ("Sky News",   "https://feeds.skynews.com/feeds/rss/world.xml"),
        ("VOA",        "https://www.voanews.com/api/ztjq_eit_pgm/rss"),
        ("France 24",  "https://www.france24.com/en/rss"),
        ("UN News",    "https://news.un.org/feed/subscribe/en/news/all/rss.xml"),
        ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("NYT World",  "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"),
        ("BBC World",  "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ]

    articles = []
    seen = set()
    headers = {"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"}

    for source_name, url in rss_sources:
        if len(articles) >= 15:
            break
        try:
            r = requests.get(url, timeout=10, headers=headers)
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            # Handle both RSS <item> and Atom <entry>
            items = root.findall(".//item") or root.findall(".//atom:entry", ns)
            for item in items[:30]:
                def gtext(tag):
                    el = item.find(tag)
                    if el is None: return ""
                    return (el.text or "").strip()
                title   = gtext("title") or gtext("atom:title")
                link    = gtext("link")  or gtext("atom:link")
                pub     = gtext("pubDate") or gtext("published") or gtext("atom:published")
                desc    = gtext("description") or gtext("summary") or ""
                # Keyword filter
                combined = (title + " " + desc).lower()
                if not any(kw in combined for kw in kws):
                    continue
                if not title or title in seen:
                    continue
                seen.add(title)
                # Parse date
                age_s, dt_str, is_recent, is_new = "recent", "", False, False
                for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                            "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
                    try:
                        dt = datetime.strptime(pub.strip(), fmt)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        age_s, dt_str, is_recent, is_new = _parse_age(dt)
                        break
                    except:
                        continue
                articles.append({
                    "title":     title[:140],
                    "url":       link,
                    "source":    source_name,
                    "time":      age_s,
                    "dt_str":    dt_str,
                    "is_recent": is_recent,
                    "is_new":    is_new,
                })
        except Exception:
            continue

    return articles


@st.cache_data(ttl=60, show_spinner=False)
def fetch_gdelt_conflict(theatre: str, max_records: int = 30) -> list:
    """Fetch GDELT Doc 2.0 news — tries multiple query strategies with fallback to RSS."""
    queries = CONFLICT_QUERIES.get(theatre, [theatre])

    # Try multiple timespans — longer ones are more likely to return results
    timespans = ["1d", "3d", "7d"]
    all_articles = []
    seen_urls = set()

    for timespan in timespans:
        if len(all_articles) >= 10:
            break
        for query in queries[:2]:
            if len(all_articles) >= 10:
                break
            try:
                r = requests.get(
                    "https://api.gdeltproject.org/api/v2/doc/doc",
                    params={
                        "query": query + " sourcelang:english",
                        "mode": "artlist",
                        "maxrecords": max_records,
                        "format": "json",
                        "timespan": timespan,
                        "sort": "DateDesc",
                    },
                    timeout=14,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if r.status_code != 200:
                    continue
                articles = r.json().get("articles", [])
                for a in articles:
                    url = a.get("url", "")
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    raw_dt = str(a.get("seendate", ""))
                    age_s, dt_str, is_recent, is_new = "recent", "", False, False
                    try:
                        dt = datetime.strptime(raw_dt[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                        age_s, dt_str, is_recent, is_new = _parse_age(dt)
                    except:
                        pass
                    all_articles.append({
                        "title":     a.get("title", "")[:140],
                        "url":       url,
                        "source":    a.get("domain", ""),
                        "time":      age_s,
                        "dt_str":    dt_str,
                        "is_recent": is_recent,
                        "is_new":    is_new,
                        "lang":      a.get("language", ""),
                    })
            except Exception:
                continue

    # Sort by recency
    def sort_key(x):
        try:
            return datetime.strptime(x["dt_str"], "%Y-%m-%d %H:%Mz") if x["dt_str"] else datetime.min.replace(tzinfo=timezone.utc)
        except:
            return datetime.min.replace(tzinfo=timezone.utc)

    all_articles.sort(key=sort_key, reverse=True)
    return all_articles[:max_records]


def _sq():
    rng = np.random.default_rng(42)
    lats = rng.uniform(-55,70,30); lons = rng.uniform(-170,170,30)
    mags = rng.uniform(2.5,6.8,30); d = rng.uniform(5,120,30)
    pl = ["California","Japan","Indonesia","Chile","Turkey","Philippines","Papua New Guinea","Peru","Mexico","Greece"]
    return pd.DataFrame({
        "title":    [f"M{m:.1f} — {pl[i%len(pl)]}" for i,m in enumerate(mags)],
        "mag":      np.round(mags,1), "place": [pl[i%len(pl)] for i in range(30)],
        "depth_km": np.round(d,1), "lon": np.round(lons,3), "lat": np.round(lats,3),
        "time":     [f"{rng.integers(0,24):02d}:{rng.integers(0,60):02d}z" for _ in range(30)],
        "type":"seismic", "url":"",
    })

def _se():
    return pd.DataFrame([
        {"title":"Kilauea — Active Lava","cat":"Volcanoes","date":"2026-03-14","lon":-155.2,"lat":19.4,"type":"eonet"},
        {"title":"Etna — SO₂ Plume","cat":"Volcanoes","date":"2026-03-13","lon":15.0,"lat":37.8,"type":"eonet"},
        {"title":"Texas Wildfires","cat":"Wildfires","date":"2026-03-12","lon":-101.0,"lat":32.5,"type":"eonet"},
    ])

# ─────────────────────────────────────────────
# MAP BUILDER
# ─────────────────────────────────────────────
CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

def _sev_colors():
    return {
        "CRITICAL": [255,40,70,230], "HIGH": [255,120,40,200],
        "MED":      [255,170,0,170], "LOW":  [0,220,110,150], "INFO": [0,190,255,120],
    }


# ═══════════════════════════════════════════════════════════════
# STATIC GEODATA FOR MAP LAYERS
# ═══════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════
# HISTORICAL EVENTS SINCE 2022  (for Global Command Map)
# ═══════════════════════════════════════════════════════════════

HISTORICAL_EVENTS = [
    # ── Ukraine–Russia War ──────────────────────────────────────
    {"date":"2022-02-24","lat":50.45,"lon":30.52,"type":"invasion","severity":"CRITICAL","title":"Russia begins full-scale invasion of Ukraine","tip":"2022-02-24 | INVASION\nRussia begins full-scale invasion of Ukraine\nKyiv Oblast — Critical"},
    {"date":"2022-03-28","lat":50.45,"lon":30.52,"type":"milestone","severity":"HIGH","title":"Russian forces repelled from Kyiv","tip":"2022-03-28 | MILESTONE\nRussian forces repelled from Kyiv\nUkrainian counter-push succeeds"},
    {"date":"2022-04-07","lat":48.74,"lon":37.57,"type":"atrocity","severity":"CRITICAL","title":"Bucha massacre revealed — war crimes evidence","tip":"2022-04-07 | WAR CRIME\nBucha massacre revealed after Russian withdrawal\nICC opens investigation"},
    {"date":"2022-09-11","lat":49.99,"lon":36.23,"type":"counteroffensive","severity":"HIGH","title":"Ukrainian forces liberate Kharkiv Oblast","tip":"2022-09-11 | COUNTEROFFENSIVE\nUkraine liberates Kharkiv Oblast\nRussian forces routed in NE Ukraine"},
    {"date":"2022-11-11","lat":46.65,"lon":32.62,"type":"milestone","severity":"HIGH","title":"Kherson city liberated","tip":"2022-11-11 | LIBERATION\nKherson city liberated by Ukrainian forces\nOnly regional capital recaptured from Russia"},
    {"date":"2022-09-26","lat":55.0,"lon":15.5,"type":"sabotage","severity":"CRITICAL","title":"Nord Stream pipelines sabotaged","tip":"2022-09-26 | SABOTAGE\nNord Stream 1 & 2 pipelines destroyed\nBaltic Sea — Attributed to state actor"},
    {"date":"2023-06-06","lat":47.05,"lon":33.48,"type":"disaster","severity":"CRITICAL","title":"Kakhovka Dam destroyed — massive flooding","tip":"2023-06-06 | ENVIRONMENTAL\nKakhovka Dam destroyed\nMassive flooding — Kherson region"},
    {"date":"2023-06-04","lat":47.97,"lon":37.74,"type":"counteroffensive","severity":"HIGH","title":"Ukrainian summer counteroffensive begins","tip":"2023-06-04 | OFFENSIVE\nUkrainian summer counteroffensive\nSouthern and eastern fronts"},
    {"date":"2024-02-17","lat":47.97,"lon":37.74,"type":"setback","severity":"HIGH","title":"Avdiivka falls to Russian forces","tip":"2024-02-17 | SETBACK\nAvdiivka captured by Russia\nDonetsk Oblast — months-long siege ends"},
    {"date":"2024-08-06","lat":51.73,"lon":35.38,"type":"incursion","severity":"CRITICAL","title":"Ukraine launches Kursk incursion into Russia","tip":"2024-08-06 | INCURSION\nUkraine invades Kursk Oblast, Russia\nFirst foreign force on Russian soil since WW2"},
    {"date":"2025-11-20","lat":50.45,"lon":30.52,"type":"escalation","severity":"HIGH","title":"US authorises ATACMS long-range strikes into Russia","tip":"2025-11-20 | ESCALATION\nUS authorises Ukraine to strike inside Russia\nATACMS long-range missiles approved"},
    {"date":"2026-03-10","lat":50.45,"lon":30.52,"type":"airstrike","severity":"CRITICAL","title":"Largest Russian missile salvo of 2026","tip":"2026-03-10 | AIRSTRIKE\nLargest Russian missile salvo of 2026\nKyiv & infrastructure nationwide"},
    # ── Gaza & Israel–Hamas ─────────────────────────────────────
    {"date":"2023-10-07","lat":31.4,"lon":34.47,"type":"attack","severity":"CRITICAL","title":"Hamas launches October 7 attack — 1,200 killed","tip":"2023-10-07 | ATTACK\nHamas multi-front attack on Israel\n1,200 killed, 251 hostages taken"},
    {"date":"2023-10-27","lat":31.52,"lon":34.47,"type":"invasion","severity":"CRITICAL","title":"Israeli ground invasion of Gaza begins","tip":"2023-10-27 | INVASION\nIsraeli ground forces enter Gaza\nOperation Swords of Iron expands"},
    {"date":"2023-11-24","lat":31.4,"lon":34.47,"type":"diplomatic","severity":"MED","title":"Temporary ceasefire — hostage release deal","tip":"2023-11-24 | CEASEFIRE\nTemporary ceasefire agreed\nFirst hostages released — Qatar-brokered"},
    {"date":"2024-05-07","lat":31.28,"lon":34.25,"type":"offensive","severity":"CRITICAL","title":"Israel begins Rafah ground operation","tip":"2024-05-07 | OFFENSIVE\nIsraeli forces enter Rafah\nUS expresses concern — 1.4M civilians sheltering"},
    {"date":"2025-01-19","lat":31.4,"lon":34.47,"type":"diplomatic","severity":"HIGH","title":"Gaza ceasefire Phase 1 agreement","tip":"2025-01-19 | CEASEFIRE\nGaza Phase 1 ceasefire agreement\nHostage-prisoner exchange begins"},
    {"date":"2025-03-18","lat":31.4,"lon":34.47,"type":"escalation","severity":"CRITICAL","title":"Ceasefire collapses — operations resume","tip":"2025-03-18 | COLLAPSE\nGaza ceasefire collapses\nIsraeli operations resume — Phase 2 failed"},
    # ── Israel–Iran Direct Conflict ─────────────────────────────
    {"date":"2024-04-01","lat":33.52,"lon":36.29,"type":"strike","severity":"HIGH","title":"Israel strikes Iranian consulate Damascus","tip":"2024-04-01 | STRIKE\nIsrael strikes Iranian consulate in Damascus\n7 IRGC officers killed — major escalation"},
    {"date":"2024-04-13","lat":32.08,"lon":34.78,"type":"attack","severity":"CRITICAL","title":"Iran fires 300+ drones/missiles at Israel","tip":"2024-04-13 | MISSILE ATTACK\nIran fires 300+ drones & ballistic missiles\n~99% intercepted by Israel + allies"},
    {"date":"2024-04-19","lat":32.65,"lon":51.68,"type":"strike","severity":"HIGH","title":"Israeli retaliatory strike on Isfahan","tip":"2024-04-19 | RETALIATION\nIsrael strikes Isfahan air defence radar\nFirst direct Israeli strike on Iran"},
    {"date":"2024-09-27","lat":33.89,"lon":35.5,"type":"assassination","severity":"CRITICAL","title":"IDF assassinates Hezbollah leader Nasrallah","tip":"2024-09-27 | ASSASSINATION\nHassan Nasrallah killed in Beirut strike\nHezbollah secretary-general for 32 years"},
    {"date":"2024-10-01","lat":32.08,"lon":34.78,"type":"attack","severity":"CRITICAL","title":"Iran fires 180+ ballistic missiles at Israel","tip":"2024-10-01 | MISSILE ATTACK\nIran fires ~180 ballistic missiles\nMost intercepted — Israel vows response"},
    {"date":"2024-10-26","lat":35.69,"lon":51.39,"type":"strike","severity":"CRITICAL","title":"Israel strikes Iranian missile factories & air defences","tip":"2024-10-26 | STRIKE\nIsrael strikes Iranian missile production\nAir defence systems degraded"},
    {"date":"2025-06-13","lat":33.72,"lon":51.73,"type":"strike","severity":"CRITICAL","title":"Israel strikes Iranian nuclear research facility","tip":"2025-06-13 | NUCLEAR STRIKE\nIsrael strikes Iranian nuclear site\nSignificant setback to programme"},
    {"date":"2026-02-14","lat":34.88,"lon":49.93,"type":"strike","severity":"CRITICAL","title":"IDF destroys Fordow uranium enrichment complex","tip":"2026-02-14 | NUCLEAR STRIKE\nFordow enrichment facility destroyed\nDeep bunker-buster strike"},
    {"date":"2026-03-07","lat":33.72,"lon":51.73,"type":"strike","severity":"CRITICAL","title":"Natanz nuclear facility struck — programme set back 2yrs","tip":"2026-03-07 | NUCLEAR STRIKE\nNatanz struck again\nCentrifuge halls destroyed — 2yr setback"},
    # ── Sudan Civil War ─────────────────────────────────────────
    {"date":"2023-04-15","lat":15.55,"lon":32.53,"type":"invasion","severity":"CRITICAL","title":"RSF-SAF fighting erupts in Khartoum","tip":"2023-04-15 | OUTBREAK\nRSF vs SAF fighting erupts across Khartoum\nSudan civil war begins"},
    {"date":"2023-06-01","lat":15.55,"lon":32.53,"type":"setback","severity":"HIGH","title":"RSF seizes most of Khartoum","tip":"2023-06-01 | SETBACK\nRSF seizes control of most of Khartoum\nGovernment forces pushed to outskirts"},
    {"date":"2024-03-13","lat":13.63,"lon":25.35,"type":"siege","severity":"CRITICAL","title":"El Fasher siege begins — last major SAF hold in Darfur","tip":"2024-03-13 | SIEGE\nEl Fasher siege begins\nLast major SAF stronghold in Darfur — atrocity risk"},
    # ── Myanmar ─────────────────────────────────────────────────
    {"date":"2021-02-01","lat":16.87,"lon":96.19,"type":"coup","severity":"CRITICAL","title":"Military coup overthrows elected government","tip":"2021-02-01 | COUP\nTatmadaw seizes power\nAung San Suu Kyi arrested — NLD government ousted"},
    {"date":"2023-10-27","lat":22.6,"lon":97.3,"type":"offensive","severity":"HIGH","title":"Operation 1027 — resistance major offensive","tip":"2023-10-27 | OFFENSIVE\nOperation 1027 begins\nThree Brotherhood Alliance captures key towns"},
    {"date":"2024-04-11","lat":16.44,"lon":98.58,"type":"milestone","severity":"HIGH","title":"Myawaddy falls to resistance forces","tip":"2024-04-11 | MILESTONE\nMyawaddy border town falls\nMajor commercial crossing seized from junta"},
    # ── Red Sea / Houthi ────────────────────────────────────────
    {"date":"2023-10-19","lat":14.5,"lon":43.5,"type":"attack","severity":"HIGH","title":"Houthi attacks on Red Sea shipping begin","tip":"2023-10-19 | MARITIME ATTACK\nHouthis begin targeting commercial shipping\nRed Sea — in solidarity with Gaza"},
    {"date":"2024-01-12","lat":15.35,"lon":44.21,"type":"strike","severity":"HIGH","title":"US & UK strike Houthi targets in Yemen","tip":"2024-01-12 | COALITION STRIKE\nUS & UK strike 60+ Houthi targets in Yemen\nOperation Prosperity Guardian response"},
    {"date":"2024-11-18","lat":14.5,"lon":43.5,"type":"attack","severity":"HIGH","title":"Houthi hypersonic missile reaches central Israel","tip":"2024-11-18 | ESCALATION\nHouthi hypersonic missile reaches central Israel\nSurpasses Iron Dome — first time"},
    # ── Major Natural & Climate Events 2022-2026 ────────────────
    {"date":"2022-09-25","lat":27.0,"lon":68.3,"type":"natural","severity":"CRITICAL","title":"Pakistan megaflood — 1/3 of country submerged","tip":"2022-09-25 | MEGAFLOOD\nPakistan megaflood — 33% of country submerged\n1,700 killed, 33M affected"},
    {"date":"2023-02-06","lat":37.17,"lon":36.83,"type":"natural","severity":"CRITICAL","title":"Turkey-Syria earthquake M7.8 — 56,000 killed","tip":"2023-02-06 | EARTHQUAKE M7.8\nTurkey-Syria earthquake\n56,000 killed — deadliest in region since 1939"},
    {"date":"2023-09-08","lat":31.06,"lon":-8.44,"type":"natural","severity":"HIGH","title":"Morocco earthquake M6.8 — 2,900 killed","tip":"2023-09-08 | EARTHQUAKE M6.8\nMorocco earthquake\n2,900 killed — Atlas Mountains"},
    {"date":"2023-09-11","lat":27.11,"lon":13.18,"type":"natural","severity":"CRITICAL","title":"Libya floods — 10,000+ killed in Derna","tip":"2023-09-11 | CATASTROPHIC FLOOD\nLibya floods — Derna dam collapse\n10,000+ killed in seconds"},
    {"date":"2024-01-01","lat":37.5,"lon":137.2,"type":"natural","severity":"HIGH","title":"Japan Noto earthquake M7.5","tip":"2024-01-01 | EARTHQUAKE M7.5\nNoto Peninsula, Japan earthquake\n241 killed — New Year's Day"},
    {"date":"2024-08-10","lat":29.5,"lon":61.5,"type":"natural","severity":"HIGH","title":"Pakistan-Iran border earthquake M7.1","tip":"2024-08-10 | EARTHQUAKE M7.1\nPakistan-Iran border\n154 killed — remote region"},
    {"date":"2024-10-24","lat":14.0,"lon":36.0,"type":"natural","severity":"CRITICAL","title":"Sudan & Ethiopia floods — 650,000+ displaced","tip":"2024-10-24 | MEGA FLOOD\nSudan & Ethiopia catastrophic floods\n650,000+ displaced amid civil war"},
    {"date":"2025-03-28","lat":-8.5,"lon":115.0,"type":"natural","severity":"CRITICAL","title":"Myanmar-Thailand earthquake M7.7 — 1,700 killed","tip":"2025-03-28 | EARTHQUAKE M7.7\nMyanmar-Thailand earthquake\n1,700+ killed — Mandalay devastated"},
    # ── Geopolitical Milestones 2022-2026 ────────────────────────
    {"date":"2022-10-04","lat":40.0,"lon":127.0,"type":"provocation","severity":"HIGH","title":"DPRK ICBM test over Japan","tip":"2022-10-04 | ICBM TEST\nNorth Korea fires ICBM over Japan\nEEZ violation — maximum range test"},
    {"date":"2023-08-24","lat":-25.9,"lon":28.2,"type":"diplomatic","severity":"MED","title":"BRICS expands — Saudi Arabia, UAE, Iran join","tip":"2023-08-24 | GEOPOLITICAL\nBRICS expansion announced\nSaudi Arabia, UAE, Iran, Egypt, Ethiopia join"},
    {"date":"2024-06-26","lat":41.0,"lon":29.0,"type":"diplomatic","severity":"HIGH","title":"NATO summit — Ukraine membership pathway agreed","tip":"2024-06-26 | NATO\nNATO Washington summit\nUkraine irreversible path to membership agreed"},
    {"date":"2024-11-05","lat":38.9,"lon":-77.0,"type":"political","severity":"HIGH","title":"US election — Trump wins presidency","tip":"2024-11-05 | US ELECTION\nDonald Trump wins US Presidential Election\nMajor geopolitical shift for NATO & Ukraine"},
    {"date":"2025-01-20","lat":38.9,"lon":-77.0,"type":"political","severity":"HIGH","title":"Trump inaugurated — signals Ukraine peace push","tip":"2025-01-20 | INAUGURATION\nTrump inaugurated\nSignals Ukraine ceasefire push — NATO tension"},
    {"date":"2025-02-18","lat":48.85,"lon":2.35,"type":"diplomatic","severity":"HIGH","title":"Paris Ukraine summit — Europe commits to defence","tip":"2025-02-18 | SUMMIT\nEurope Ukraine defence summit — Paris\nEU commits €100B+ defence spending increase"},
    {"date":"2026-01-15","lat":55.75,"lon":37.61,"type":"political","severity":"HIGH","title":"Russia declares wartime economy — conscription expanded","tip":"2026-01-15 | RUSSIA\nRussia expands conscription\nFull wartime economy declared — 500k more troops"},
]

# Pre-sorted once at startup — avoids repeated sort() inside render loops
_HIST_SORTED = sorted(HISTORICAL_EVENTS, key=lambda x: x["date"], reverse=True)


# Severity colour map for historical events
HIST_SEV_COLORS = {
    "CRITICAL": [255, 30, 60, 220],
    "HIGH":     [255, 120, 40, 190],
    "MED":      [255, 180, 0,  160],
    "LOW":      [0,  200, 255, 130],
}

HIST_TYPE_ICONS = {
    "invasion":"🔴","attack":"💥","strike":"✈","airstrike":"✈","counteroffensive":"⚔",
    "milestone":"⭐","setback":"📉","diplomatic":"🤝","ceasefire":"🕊","escalation":"⬆",
    "sabotage":"💣","disaster":"🌊","incursion":"🚨","offensive":"⚔","assassination":"🎯",
    "siege":"🔒","coup":"🏛","natural":"🌍","provocation":"⚠","political":"🗳",
    "atrocity":"⛔","maritime":"⚓",
}

# ── Live Events GDELT fetcher ──────────────────────────────────────────────
@st.cache_data(ttl=90, show_spinner=False)
def fetch_live_global_events(max_records: int = 20) -> list:
    """Fetch the very latest global events from GDELT Doc API."""
    queries = [
        "war attack military strike airstrike conflict 2026",
        "Ukraine Russia frontline offensive Avdiivka Kharkiv",
        "Israel Iran Gaza strike missile Hezbollah Houthi",
        "Pakistan Afghanistan TTP Taliban border strike",
        "Sudan RSF SAF Darfur famine displaced",
        "Haiti gang violence coup insecurity",
        "earthquake flood disaster volcanic eruption",
        "nuclear missile launch threat ballistic ICBM DPRK",
        "Myanmar Tatmadaw junta PDF resistance offensive",
    ]
    all_arts = []
    seen = set()
    for q in queries:
        try:
            r = requests.get("https://api.gdeltproject.org/api/v2/doc/doc",
                             params={"query": q, "mode": "artlist", "maxrecords": 10,
                                     "format": "json", "timespan": "1h", "sort": "DateDesc"},
                             timeout=10)
            r.raise_for_status()
            for a in r.json().get("articles", []):
                url = a.get("url", "")
                if url in seen: continue
                seen.add(url)
                raw_dt = str(a.get("seendate",""))
                try:
                    dt  = datetime.strptime(raw_dt[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                    age = datetime.now(tz=timezone.utc) - dt
                    age_s = f"{int(age.total_seconds()//60)}m ago" if age.total_seconds() < 3600 else f"{int(age.total_seconds()//3600)}h ago"
                except:
                    age_s = "recent"
                all_arts.append({
                    "title":  a.get("title","")[:100],
                    "source": a.get("domain",""),
                    "url":    url,
                    "time":   age_s,
                })
        except:
            pass
    if all_arts:
        _persist("gdelt_events", all_arts[:max_records])
        return all_arts[:max_records]

    # ── Last resort: return last persisted GDELT events ─────────
    _stored_g = load_persisted("gdelt_events", limit=max_records)
    if _stored_g:
        return _stored_g

    return []


# ── Live NOAA solar wind / X-ray flux ─────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_solar():
    try:
        r = requests.get("https://services.swpc.noaa.gov/products/summary/solar-wind-speed.json", timeout=6)
        r.raise_for_status()
        d = r.json()
        speed = float(d.get("WindSpeed", 400))
        
        r2 = requests.get("https://services.swpc.noaa.gov/products/summary/10cm-flux.json", timeout=6)
        r2.raise_for_status()
        d2 = r2.json()
        flux = float(d2.get("Flux", 100))
        return {"speed": speed, "flux": flux}
    except:
        return {"speed": 420.0, "flux": 112.0}

# ── FIRMS active fire count from NASA EONET ───────────────────
@st.cache_data(ttl=600, show_spinner=False)
def fetch_firms_count():
    """Get active wildfire count from EONET (proxy for FIRMS)."""
    try:
        r = requests.get(
            "https://eonet.gsfc.nasa.gov/api/v3/events?category=wildfires&status=open&limit=50",
            timeout=8)
        r.raise_for_status()
        events = r.json().get("events", [])
        return len(events)
    except:
        return 0

# ── NetBlocks / IODA internet outage feed ─────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def fetch_outage_feed():
    """Fetch internet outage alerts from IODA via GDELT."""
    try:
        r = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={"query": "internet outage shutdown censorship",
                    "mode": "artlist", "maxrecords": 8,
                    "format": "json", "timespan": "6h", "sort": "DateDesc"},
            timeout=10)
        r.raise_for_status()
        arts = r.json().get("articles", [])
        out = []
        for a in arts:
            raw_dt = str(a.get("seendate",""))
            try:
                dt    = datetime.strptime(raw_dt[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                age   = datetime.now(tz=timezone.utc) - dt
                age_s = f"{int(age.total_seconds()//60)}m ago" if age.total_seconds() < 3600 else f"{int(age.total_seconds()//3600)}h ago"
            except:
                age_s = ""
            out.append({"title": a.get("title","")[:90], "source": a.get("domain",""),
                        "url": a.get("url",""), "time": age_s})
        return out
    except:
        return []

# ── Earthquake depth profile for Earth Signals ────────────────
# ══════════════════════════════════════════════════════════════
# LIVE INTEGRATION FETCHERS
# ══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# Geopolitical live-enrichment fetchers
# These replace or augment the hardcoded baselines for the map
# overlays and the SIGINT / Econ dashboard payloads.
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_live_nuke_alerts() -> list:
    """
    Enrich NUKE_ALERTS with GDELT news signals for each site.
    Adds `live_hits`, `live_headline`, `last_updated`.
    Escalates `level` from HIGH → CRITICAL if ≥3 fresh GDELT hits exist.
    Falls back to NUKE_ALERTS baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc = datetime.now(tz=timezone.utc)
    results = []

    for alert in NUKE_ALERTS:
        enriched = dict(alert)
        try:
            site_kw = alert.get("site", "").replace("(", "").replace(")", "")
            query = urllib.parse.quote(
                f"{site_kw} nuclear strike attack radiation enrichment reactor")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=6"
                "&format=json&timespan=48h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                hits = len(arts)
                enriched["live_hits"]    = hits
                enriched["last_updated"] = now_utc.strftime("%Y-%m-%d %H:%M UTC")
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
                # Escalate if significant fresh coverage
                if hits >= 3 and enriched.get("level") == "HIGH":
                    enriched["level"] = "CRITICAL"
                    enriched["col"]   = "#ff3d5a"
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0
        results.append(enriched)

    return results if results else NUKE_ALERTS


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_live_wmd_posture() -> list:
    """
    Enrich WMD_POSTURE with GDELT article volume + tone for each actor.
    High article volume → nudge `risk` up by up to 6 pts.
    Adds `live_hits`, `live_headline`, `last_updated`.
    Falls back to WMD_POSTURE baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc = datetime.now(tz=timezone.utc)
    results = []

    for posture in WMD_POSTURE:
        enriched = dict(posture)
        try:
            actor_kw = posture.get("actor", "").replace("(", "").replace(")", "")
            type_kw  = posture.get("type", "")
            assets_kw = " ".join(posture.get("assets", "").split()[:4])
            query = urllib.parse.quote(
                f"{actor_kw} {type_kw} {assets_kw} missile nuclear weapon posture")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=6"
                "&format=json&timespan=48h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                hits = len(arts)
                enriched["live_hits"]    = hits
                enriched["last_updated"] = now_utc.strftime("%Y-%m-%d %H:%M UTC")
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
                # Nudge risk score with article volume (cap +6)
                bump = min(6, hits)
                enriched["risk"] = min(99, posture.get("risk", 50) + bump)
                # Escalate status if risk crosses threshold
                new_risk = enriched["risk"]
                if new_risk >= 85 and enriched.get("status") not in ("Elevated", "Active"):
                    enriched["status"] = "Elevated"
                    enriched["col"]    = "#ff8c42"
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0
        results.append(enriched)

    return results if results else WMD_POSTURE

@st.cache_data(ttl=600, show_spinner=False)
def fetch_live_gps_jamming() -> list:
    """
    Enrich GPS_JAMMING_ZONES with live GDELT article hits for each zone.
    High hit-count → escalate severity; zero hits → downgrade to 'Low'.
    Also appends any newly-reported jamming zones detected in GDELT last 24 h
    that don't overlap an existing zone (rough 5° grid dedup).
    Falls back to GPS_JAMMING_ZONES baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc  = datetime.now(tz=timezone.utc)
    results  = []
    used_locs = set()  # (round lat/5)*5, (round lon/5)*5 used for dedup

    for zone in GPS_JAMMING_ZONES:
        enriched = dict(zone)
        grid_key = (round(zone["lat"] / 5) * 5, round(zone["lon"] / 5) * 5)
        used_locs.add(grid_key)
        try:
            src = zone.get("source", "")
            name = zone.get("name", "")
            query = urllib.parse.quote(
                f"GPS jamming GNSS spoofing {src} {name} navigation interference")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=8"
                "&format=json&timespan=24h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts   = r.json().get("articles", [])
                hits   = len(arts)
                enriched["live_hits"] = hits
                if hits >= 4:
                    enriched["severity"] = "High"
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
                elif hits == 0 and zone.get("severity") == "Med":
                    enriched["severity"] = "Low"
                elif hits > 0:
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0
        results.append(enriched)

    # Scan GDELT for new jamming events not in baseline
    try:
        import urllib.parse as _up
        r2 = requests.get(
            "https://api.gdeltproject.org/api/v2/geo/geo",
            params={"query": "GPS jamming GNSS spoofing navigation interference",
                    "mode": "pointdata", "maxpoints": 20,
                    "format": "json", "timespan": "24h"},
            timeout=8)
        if r2.status_code == 200:
            for feat in r2.json().get("features", []):
                props = feat.get("properties", {})
                geo   = feat.get("geometry", {}).get("coordinates", [0, 0])
                glat, glon = float(geo[1]) if len(geo) > 1 else 0.0, float(geo[0]) if len(geo) > 0 else 0.0
                if not glat and not glon:
                    continue
                grid_key = (round(glat / 5) * 5, round(glon / 5) * 5)
                if grid_key in used_locs:
                    continue
                used_locs.add(grid_key)
                results.append({
                    "name":       props.get("name", "Emerging jamming zone"),
                    "lat":        glat,
                    "lon":        glon,
                    "radius_km":  150,
                    "source":     "GDELT-detected",
                    "severity":   "Med",
                    "live_hits":  1,
                    "live_headline": props.get("title", "")[:120],
                    "tip": (f"📡 GPS JAMMING | {props.get('name','Unknown area')} | "
                            f"GDELT-detected | {now_utc.strftime('%Y-%m-%d')}"),
                })
    except Exception:
        pass

    return results if results else GPS_JAMMING_ZONES


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_cyber_threats() -> list:
    """
    Enrich CYBER_THREATS_GEO with live GDELT article data for each APT/actor.
    Adds `live_hits`, `live_headline`, `last_active`.
    Also appends up to 3 new geo-located cyber events from GDELT last 6 h
    that don't overlap an existing actor location.
    Falls back to CYBER_THREATS_GEO baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc  = datetime.now(tz=timezone.utc)
    results  = []
    used_locs = set()

    for threat in CYBER_THREATS_GEO:
        enriched = dict(threat)
        grid_key = (round(threat["lat"] / 3) * 3, round(threat["lon"] / 3) * 3)
        used_locs.add(grid_key)
        try:
            actor_kw  = threat.get("actor", "").replace("/", " ")
            name_kw   = threat.get("name", "").replace("—", "").replace("-", " ")
            targets_kw = threat.get("targets", "")
            query = urllib.parse.quote(
                f"{name_kw} {actor_kw} cyber espionage hacking {targets_kw}")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=6"
                "&format=json&timespan=6h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                enriched["live_hits"] = len(arts)
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
                    enriched["last_active"]   = now_utc.strftime("%Y-%m-%d %H:%M UTC")
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0
        results.append(enriched)

    # Append new GDELT-detected cyber events
    try:
        r3 = requests.get(
            "https://api.gdeltproject.org/api/v2/geo/geo",
            params={"query": "cyber attack hacking breach malware ransomware APT",
                    "mode": "pointdata", "maxpoints": 15,
                    "format": "json", "timespan": "6h"},
            timeout=8)
        added = 0
        if r3.status_code == 200:
            for feat in r3.json().get("features", []):
                if added >= 3:
                    break
                props = feat.get("properties", {})
                geo   = feat.get("geometry", {}).get("coordinates", [0, 0])
                glat  = float(geo[1]) if len(geo) > 1 else 0.0
                glon  = float(geo[0]) if len(geo) > 0 else 0.0
                if not glat and not glon:
                    continue
                grid_key = (round(glat / 3) * 3, round(glon / 3) * 3)
                if grid_key in used_locs:
                    continue
                used_locs.add(grid_key)
                title = props.get("title", props.get("name", ""))[:120]
                results.append({
                    "name":         props.get("name", "Emerging cyber event"),
                    "lat":          glat,
                    "lon":          glon,
                    "actor":        "GDELT-detected",
                    "targets":      title[:60],
                    "live_hits":    1,
                    "live_headline": title,
                    "last_active":  now_utc.strftime("%Y-%m-%d"),
                    "tip": (f"🛡 CYBER THREAT | {props.get('name','?')} | "
                            f"GDELT-detected | {now_utc.strftime('%Y-%m-%d')}"),
                })
                added += 1
    except Exception:
        pass

    return results if results else CYBER_THREATS_GEO


@st.cache_data(ttl=600, show_spinner=False)
def fetch_live_cii() -> list:
    """
    Enrich CII_INSTABILITY by querying GDELT for news about each country's
    critical infrastructure sector.  High article volume or negative tone
    nudges `risk` upward by up to 8 pts.  Adds `live_hits`, `live_headline`.
    Falls back to CII_INSTABILITY baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc = datetime.now(tz=timezone.utc)
    results = []

    for entry in CII_INSTABILITY:
        enriched = dict(entry)
        try:
            country_kw = entry.get("country", "")
            sector_kw  = entry.get("sector", "")
            query = urllib.parse.quote(
                f"{country_kw} {sector_kw} infrastructure attack outage blackout failure")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=6"
                "&format=json&timespan=24h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                hits = len(arts)
                enriched["live_hits"] = hits
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
                # Escalate risk proportionally to hit count (cap at +8)
                bump = min(8, hits * 2)
                enriched["risk"] = min(100, entry.get("risk", 50) + bump)
                enriched["last_updated"] = now_utc.strftime("%Y-%m-%d %H:%M UTC")
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0
        results.append(enriched)

    return results if results else CII_INSTABILITY


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_internet_outages() -> list:
    """
    Enrich INTERNET_OUTAGES with:
    - Live GDELT article counts for each location's shutdown/censorship news
    - NetBlocks-style GDELT query for new country-level shutdowns not in baseline
    Severity mapping: >=4 GDELT hits → Total/Disrupted escalation.
    Falls back to INTERNET_OUTAGES baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc  = datetime.now(tz=timezone.utc)
    results  = []
    used_countries = {e.get("name", "").split("—")[0].strip() for e in INTERNET_OUTAGES}

    for entry in INTERNET_OUTAGES:
        enriched = dict(entry)
        try:
            loc_kw   = entry.get("name", "").split("—")[0].strip()
            cause_kw = entry.get("cause", "")
            query = urllib.parse.quote(
                f"{loc_kw} internet shutdown outage censorship {cause_kw}")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=5"
                "&format=json&timespan=12h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                hits = len(arts)
                enriched["live_hits"] = hits
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
                if hits >= 4 and enriched.get("severity") not in ("Total",):
                    enriched["severity"] = "Disrupted"
                enriched["last_updated"] = now_utc.strftime("%Y-%m-%d %H:%M UTC")
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0
        results.append(enriched)

    # Scan for newly-reported outages via GDELT geo
    try:
        r4 = requests.get(
            "https://api.gdeltproject.org/api/v2/geo/geo",
            params={"query": "internet shutdown outage censorship blocked",
                    "mode": "pointdata", "maxpoints": 10,
                    "format": "json", "timespan": "12h"},
            timeout=8)
        if r4.status_code == 200:
            for feat in r4.json().get("features", []):
                props  = feat.get("properties", {})
                geo    = feat.get("geometry", {}).get("coordinates", [0, 0])
                glat   = float(geo[1]) if len(geo) > 1 else 0.0
                glon   = float(geo[0]) if len(geo) > 0 else 0.0
                ctry   = props.get("countrycode", "") or props.get("name", "")[:20]
                if ctry in used_countries or (not glat and not glon):
                    continue
                used_countries.add(ctry)
                results.append({
                    "name":          props.get("name", ctry),
                    "lat":           glat,
                    "lon":           glon,
                    "severity":      "Disrupted",
                    "cause":         "GDELT-detected",
                    "live_hits":     1,
                    "live_headline": props.get("title", "")[:120],
                    "last_updated":  now_utc.strftime("%Y-%m-%d"),
                    "tip": (f"📡 INTERNET OUTAGE | {props.get('name','?')} | "
                            f"GDELT-detected | {now_utc.strftime('%Y-%m-%d')}"),
                })
    except Exception:
        pass

    return results if results else INTERNET_OUTAGES


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_military_activity() -> list:
    """
    Enrich MILITARY_ACTIVITY with live GDELT article hits for each unit/operation.
    Adds `live_hits`, `live_headline`, `last_active`.
    Also appends up to 4 new geo-located military events from GDELT last 6 h
    that are not near any existing marker.
    Falls back to MILITARY_ACTIVITY baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc  = datetime.now(tz=timezone.utc)
    results  = []
    used_locs = set()

    for act in MILITARY_ACTIVITY:
        enriched = dict(act)
        grid_key = (round(act["lat"] / 4) * 4, round(act["lon"] / 4) * 4)
        used_locs.add(grid_key)
        try:
            name_kw    = act.get("name", "").replace("/", " ")
            type_kw    = act.get("type", "")
            country_kw = act.get("country", "")
            query = urllib.parse.quote(
                f"{name_kw} {country_kw} {type_kw} military operation strike naval")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=6"
                "&format=json&timespan=6h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                enriched["live_hits"] = len(arts)
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
                    enriched["last_active"]   = now_utc.strftime("%Y-%m-%d %H:%M UTC")
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0
        results.append(enriched)

    # Append new GDELT-detected military events
    try:
        r5 = requests.get(
            "https://api.gdeltproject.org/api/v2/geo/geo",
            params={"query": "airstrike military attack offensive troops naval",
                    "mode": "pointdata", "maxpoints": 20,
                    "format": "json", "timespan": "6h"},
            timeout=8)
        added = 0
        if r5.status_code == 200:
            for feat in r5.json().get("features", []):
                if added >= 4:
                    break
                props = feat.get("properties", {})
                geo   = feat.get("geometry", {}).get("coordinates", [0, 0])
                glat  = float(geo[1]) if len(geo) > 1 else 0.0
                glon  = float(geo[0]) if len(geo) > 0 else 0.0
                if not glat and not glon:
                    continue
                grid_key = (round(glat / 4) * 4, round(glon / 4) * 4)
                if grid_key in used_locs:
                    continue
                used_locs.add(grid_key)
                title = props.get("title", props.get("name", ""))[:120]
                results.append({
                    "name":         props.get("name", "New military event"),
                    "lat":          glat,
                    "lon":          glon,
                    "type":         "GDELT-detected",
                    "country":      props.get("countrycode", "Unknown"),
                    "live_hits":    1,
                    "live_headline": title,
                    "last_active":  now_utc.strftime("%Y-%m-%d"),
                    "tip": (f"✈ MIL ACTIVITY | {props.get('name','?')} | "
                            f"GDELT-detected | {now_utc.strftime('%Y-%m-%d')}"),
                })
                added += 1
    except Exception:
        pass

    return results if results else MILITARY_ACTIVITY


@st.cache_data(ttl=900, show_spinner=False)
def fetch_live_shipping_rates() -> list:
    """
    Update SHIPPING_RATES by querying Yahoo Finance for Baltic Dry Index (BDI)
    and the Freightos Baltic Container Index (FBX) proxy tickers, and GDELT
    for route-specific disruption signals.

    - BDI: ^BDI (Yahoo) → updates the 'Baltic Dry Index' row
    - FBX composite proxy: HAFNIA.OL, ZIM, MATX → sentiment proxy for container rates
    - GDELT: per-route keyword search → updates `status` and `note`
    Falls back to SHIPPING_RATES baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc = datetime.now(tz=timezone.utc)
    results = []

    # Pull Yahoo tickers for BDI proxy + container shipping proxies
    yahoo_data = _yahoo_batch(("^BDI", "ZIM", "MATX", "HAFNIA.OL", "DSX"))

    for rate in SHIPPING_RATES:
        enriched = dict(rate)
        route    = rate.get("route", "")
        rtype    = rate.get("type",  "")

        # BDI direct update
        if rtype == "BDI" and "^BDI" in yahoo_data:
            bdi = yahoo_data["^BDI"]
            enriched["rate"]   = int(bdi["price"])
            enriched["change"] = round(bdi["chg_pct"], 1)
            enriched["status"] = ("Rising" if bdi["chg_pct"] > 1 else
                                  "Falling" if bdi["chg_pct"] < -1 else "Stable")
            enriched["live"]   = True

        # Container rates: use ZIM sentiment proxy
        elif rtype == "Container" and "ZIM" in yahoo_data:
            zim_chg = yahoo_data["ZIM"]["chg_pct"]
            # ZIM stock directionally tracks container spot rates
            if abs(zim_chg) > 0.5:
                enriched["change"] = round(
                    rate.get("change", 0) + zim_chg * 0.4, 1)
                enriched["status"] = "Elevated" if zim_chg > 2 else (
                                     "Rising"   if zim_chg > 0.5 else
                                     "Reduced"  if zim_chg < -2 else "Normal")
                enriched["live"] = True

        # VLCC / Suezmax oil tankers: use DSX proxy
        elif rtype in ("VLCC Oil", "Suezmax Oil") and "DSX" in yahoo_data:
            dsx_chg = yahoo_data["DSX"]["chg_pct"]
            enriched["change"] = round(rate.get("change", 0) + dsx_chg * 0.3, 1)
            enriched["live"] = True

        # GDELT disruption signal for this route
        try:
            route_parts = route.replace("→", "").replace("→", "")
            query = urllib.parse.quote(
                f"shipping {route_parts} disruption reroute freight rate")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=4"
                "&format=json&timespan=24h&sort=DateDesc"
            )
            r = requests.get(url, timeout=6,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                enriched["live_hits"] = len(arts)
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:100]
                    # Flagging keywords → escalate status
                    headline_lower = arts[0].get("title", "").lower()
                    if any(kw in headline_lower for kw in
                           ("attack", "disruption", "blocked", "seized", "reroute")):
                        enriched["status"] = "Elevated"
        except Exception:
            pass

        results.append(enriched)

    return results if results else SHIPPING_RATES


@st.cache_data(ttl=900, show_spinner=False)
def fetch_live_critical_minerals() -> list:
    """
    Update CRIT_MIN_DATA using Yahoo Finance spot-price proxies and GDELT
    supply-chain / export-control signals.

    Ticker map:
      Lithium → LTHM (Livent), ALB (Albemarle)
      Cobalt  → COBF (proxy), CMC
      Nickel  → NICKEL=F (Yahoo futures) or VALE
      Copper  → HG=F (COMEX futures)
      Uranium → URA ETF
      REE     → MP (MP Materials — Nd/Pr)
      Graphite → NOVG.OL (proxy)
    Falls back to CRIT_MIN_DATA baseline on failure.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc = datetime.now(tz=timezone.utc)

    MINERAL_TICKERS = {
        "Lithium":  ("ALB",    0.15),   # Albemarle — directional proxy
        "Cobalt":   ("VALE",   0.08),   # VALE cobalt by-product proxy
        "REE (Nd)": ("MP",     0.20),   # MP Materials
        "Nickel":   ("VALE",   0.12),
        "Graphite": ("SYRA.AX",0.10),   # Syrah Resources ASX proxy
        "Uranium":  ("URA",    0.25),   # Global X Uranium ETF
        "Copper":   ("HG=F",   1.00),   # COMEX copper futures (direct)
        "Gallium":  ("INTC",   0.05),   # Proxy: Intel (Ga consumer)
    }

    tickers_needed = tuple(set(v[0] for v in MINERAL_TICKERS.values()))
    yahoo_data = _yahoo_batch(tickers_needed)

    results = []
    for mineral_rec in CRIT_MIN_DATA:
        enriched = dict(mineral_rec)
        mineral_name = mineral_rec.get("mineral", "")
        ticker, weight = MINERAL_TICKERS.get(mineral_name, (None, 0))

        if ticker and ticker in yahoo_data and weight > 0:
            proxy_chg = yahoo_data[ticker]["chg_pct"]
            # Blend proxy % change with baseline price directionally
            enriched["change"] = round(
                mineral_rec.get("change", 0) * 0.6 + proxy_chg * weight * 0.4, 1)
            enriched["live"] = True
            enriched["proxy_ticker"] = ticker

        # GDELT supply-chain signal
        try:
            query = urllib.parse.quote(
                f"{mineral_name} supply export restriction mine production")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=4"
                "&format=json&timespan=24h&sort=DateDesc"
            )
            r = requests.get(url, timeout=6,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                enriched["live_hits"] = len(arts)
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:100]
                    headline_lower = arts[0].get("title", "").lower()
                    if any(kw in headline_lower for kw in
                           ("ban", "restriction", "sanction", "shortage", "cut")):
                        enriched["supply_risk"] = min(99,
                            mineral_rec.get("supply_risk", 50) + 5)
        except Exception:
            pass

        results.append(enriched)

    return results if results else CRIT_MIN_DATA


# ─────────────────────────────────────────────────────────────
# SIGINT live-enrichment fetchers
# Each function uses the hardcoded baseline as a fallback and
# blends in signals pulled from GDELT / USGS / open feeds.
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_comint() -> list:
    """
    Enrich COMINT_SIGNALS with live GDELT article counts + tone.
    For each signal, query GDELT for the actor keyword in the last 6 h.
    If GDELT returns articles, update `last_active`, `confidence` (±5 pts),
    and add a `live_hits` count.  Falls back to baseline on any error.
    """
    import urllib.parse
    from datetime import datetime, timezone, timedelta

    results = []
    now_utc = datetime.now(tz=timezone.utc)

    for sig in COMINT_SIGNALS:
        enriched = dict(sig)
        try:
            actor_kw = sig.get("actor", "").replace("/", " ").replace("(", "").replace(")", "")
            target_kw = sig.get("target", "")
            query = urllib.parse.quote(f"{actor_kw} {target_kw} signal intercept communication")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=5"
                "&format=json&timespan=6h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                hit_count = len(arts)
                if hit_count > 0:
                    # Nudge confidence up by 1 pt per article hit (cap ±5)
                    delta = min(5, hit_count)
                    enriched["confidence"] = min(99, sig.get("confidence", 75) + delta)
                    enriched["intercept"]  = "Active"
                    enriched["last_active"] = now_utc.strftime("%Y-%m-%d")
                    enriched["live_hits"]   = hit_count
                    enriched["live_headline"] = arts[0].get("title", "")[:120] if arts else ""
                else:
                    enriched["live_hits"] = 0
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0
        results.append(enriched)

    return results if results else COMINT_SIGNALS


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_elint() -> list:
    """
    Enrich ELINT_SIGNALS with GDELT article hits for each system/actor.
    Also checks USGS seismic feed for nuclear-test indicators near known
    ELINT-monitored sites (Punggye-ri, Lop Nur) — flags anomalies.
    Falls back to ELINT_SIGNALS baseline on any error.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc = datetime.now(tz=timezone.utc)
    results = []

    # Pull recent USGS seismic data once for the whole call
    usgs_quakes = []
    try:
        r_usgs = requests.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/query",
            params={"format": "geojson", "minmagnitude": 2.8,
                    "limit": 50, "orderby": "time"},
            timeout=8)
        if r_usgs.status_code == 200:
            for feat in r_usgs.json().get("features", []):
                c = feat.get("geometry", {}).get("coordinates", [0, 0, 0])
                usgs_quakes.append({
                    "lat": float(c[1]), "lon": float(c[0]),
                    "depth": float(c[2]),
                    "mag": float(feat["properties"].get("mag", 0) or 0),
                    "place": feat["properties"].get("place", ""),
                })
    except Exception:
        pass

    for sig in ELINT_SIGNALS:
        enriched = dict(sig)
        try:
            system_kw = sig.get("system", "").replace("-", " ")
            actor_kw  = sig.get("actor", "")
            query = urllib.parse.quote(f"{system_kw} {actor_kw} radar electronic warfare")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=5"
                "&format=json&timespan=12h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                enriched["live_hits"] = len(arts)
                if arts:
                    enriched["status"] = "Active"
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
                    enriched["last_seen"] = now_utc.strftime("%Y-%m-%d %H:%M UTC")
            else:
                enriched["live_hits"] = 0

            # Seismic anomaly check — flag if any shallow quake within 150 km
            sig_lat = sig.get("lat", 0)
            sig_lon = sig.get("lon", 0)
            for q in usgs_quakes:
                dlat = abs(q["lat"] - sig_lat)
                dlon = abs(q["lon"] - sig_lon)
                approx_km = ((dlat ** 2 + dlon ** 2) ** 0.5) * 111
                if approx_km < 150 and q["depth"] < 10:
                    enriched["seismic_flag"] = True
                    enriched["seismic_detail"] = (
                        f"M{q['mag']:.1f} shallow quake {int(approx_km)} km away — "
                        f"{q['place']}"
                    )
                    break

        except Exception:
            enriched["live_hits"] = 0

        results.append(enriched)

    return results if results else ELINT_SIGNALS


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_masint() -> list:
    """
    Enrich MASINT_EVENTS with real USGS seismic events and CTBTO-correlated
    nuclear/explosion signals.

    Strategy:
    - For Seismic-type events: query USGS for recent quakes near the baseline
      lat/lon (within 200 km).  Replace confidence / date with live data if a
      matching event is found.
    - For all types: query GDELT for related keywords and surface the headline.
    - Append any NEW USGS shallow quakes (depth < 12 km, mag > 3.0) near known
      nuclear sites as dynamically-generated MASINT entries.
    Falls back to MASINT_EVENTS baseline on any error.
    """
    from datetime import datetime, timezone
    import urllib.parse

    now_utc = datetime.now(tz=timezone.utc)
    NUCLEAR_SITE_COORDS = [
        (41.27, 129.08, "Punggye-ri DPRK"),
        (33.72, 51.73,  "Natanz Iran"),
        (39.81, 125.75, "Yongbyon DPRK"),
        (40.06, 93.7,   "Lop Nur China"),
        (69.0,  33.0,   "Kola Russia"),
        (35.0,  32.5,   "Incirlik Turkey"),
    ]

    # Pull USGS seismic data
    usgs_all = []
    try:
        r_usgs = requests.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/query",
            params={"format": "geojson", "minmagnitude": 2.5,
                    "limit": 100, "orderby": "time"},
            timeout=8)
        if r_usgs.status_code == 200:
            for feat in r_usgs.json().get("features", []):
                c = feat.get("geometry", {}).get("coordinates", [0, 0, 0])
                ts = feat["properties"].get("time", 0) or 0
                usgs_all.append({
                    "lat":   float(c[1]),
                    "lon":   float(c[0]),
                    "depth": float(c[2]),
                    "mag":   float(feat["properties"].get("mag", 0) or 0),
                    "place": feat["properties"].get("place", ""),
                    "date":  datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d")
                             if ts else now_utc.strftime("%Y-%m-%d"),
                })
    except Exception:
        pass

    results = []
    used_usgs_idxs = set()

    for ev in MASINT_EVENTS:
        enriched = dict(ev)
        ev_lat = ev.get("lat", 0)
        ev_lon = ev.get("lon", 0)

        # For seismic-type events try to match a real USGS event nearby
        if ev.get("type") == "Seismic":
            best_match = None
            best_dist  = 999
            for i, q in enumerate(usgs_all):
                dlat = abs(q["lat"] - ev_lat)
                dlon = abs(q["lon"] - ev_lon)
                dist = ((dlat ** 2 + dlon ** 2) ** 0.5) * 111
                if dist < 200 and q["depth"] < 20:
                    if dist < best_dist:
                        best_dist  = dist
                        best_match = (i, q)
            if best_match:
                i, q = best_match
                used_usgs_idxs.add(i)
                enriched["confidence"]   = min(92, ev.get("confidence", 55) + 15)
                enriched["date"]         = q["date"]
                enriched["depth_km"]     = round(q["depth"], 1)
                enriched["live_source"]  = "USGS real-time"
                enriched["live_detail"]  = (
                    f"USGS: M{q['mag']:.1f} @ {q['depth']:.1f} km depth — "
                    f"{q['place']} — {int(best_dist)} km from baseline site"
                )

        # GDELT keyword enrichment for all MASINT types
        try:
            loc_kw = ev.get("location", "").split(",")[0]
            type_kw = ev.get("type", "")
            query = urllib.parse.quote(
                f"{loc_kw} {type_kw} explosion radiation nuclear seismic signature")
            url = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=4"
                "&format=json&timespan=48h&sort=DateDesc"
            )
            r = requests.get(url, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code == 200:
                arts = r.json().get("articles", [])
                enriched["live_hits"] = len(arts)
                if arts:
                    enriched["live_headline"] = arts[0].get("title", "")[:120]
            else:
                enriched["live_hits"] = 0
        except Exception:
            enriched["live_hits"] = 0

        results.append(enriched)

    # Append new USGS shallow events near nuclear sites not already matched
    new_id_counter = len(MASINT_EVENTS) + 1
    for i, q in enumerate(usgs_all):
        if i in used_usgs_idxs:
            continue
        if q["depth"] > 12 or q["mag"] < 3.0:
            continue
        for site_lat, site_lon, site_name in NUCLEAR_SITE_COORDS:
            dlat = abs(q["lat"] - site_lat)
            dlon = abs(q["lon"] - site_lon)
            dist = ((dlat ** 2 + dlon ** 2) ** 0.5) * 111
            if dist < 250:
                results.append({
                    "id":         f"M{900 + new_id_counter:03d}",
                    "type":       "Seismic",
                    "event":      f"USGS shallow event near {site_name}",
                    "location":   q["place"] or site_name,
                    "lat":        q["lat"],
                    "lon":        q["lon"],
                    "magnitude":  q["mag"],
                    "depth_km":   q["depth"],
                    "confidence": 45,
                    "date":       q["date"],
                    "detail":     (
                        f"USGS real-time: M{q['mag']:.1f} shallow quake "
                        f"({q['depth']:.1f} km depth) detected {int(dist)} km "
                        f"from {site_name}. Monitoring for UGT indicators."
                    ),
                    "live_source": "USGS real-time",
                    "live_hits":   0,
                })
                new_id_counter += 1
                break  # only assign each quake to one site

    return results if results else MASINT_EVENTS


@st.cache_data(ttl=600, show_spinner=False)
def fetch_live_threat_actors() -> list:
    """
    Enrich THREAT_ACTORS with live GDELT article volume and tone.
    For each actor, query GDELT for news in the last 24 h.
    High article volume → raise threat_level by up to 8 pts.
    Negative GDELT tone → raise threat_level by up to 4 pts.
    Adds `live_hits`, `live_headline`, `live_tone`, and `last_seen` fields.
    Falls back to THREAT_ACTORS baseline on any error.
    """
    import urllib.parse
    from datetime import datetime, timezone

    now_utc = datetime.now(tz=timezone.utc)
    results = []

    for actor in THREAT_ACTORS:
        enriched = dict(actor)
        try:
            actor_kw = (actor.get("actor", "") + " " +
                        actor.get("unit", "")).replace("/", " ")
            query = urllib.parse.quote(
                f"{actor_kw} cyber espionage attack hacking intelligence")

            # Article volume
            url_art = (
                "https://api.gdeltproject.org/api/v2/doc/doc"
                f"?query={query}&mode=artlist&maxrecords=10"
                "&format=json&timespan=24h&sort=DateDesc"
            )
            r_art = requests.get(url_art, timeout=8,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            hit_count = 0
            headline  = ""
            if r_art.status_code == 200:
                arts = r_art.json().get("articles", [])
                hit_count = len(arts)
                headline  = arts[0].get("title", "")[:120] if arts else ""

            # Tone series (negativity → higher threat)
            url_tone = (
                "https://api.gdeltproject.org/api/v2/tv/tv"
                f"?query={query}&mode=timelinetone&format=json&timespan=24h"
            )
            avg_neg_tone = 0.0
            try:
                r_tone = requests.get(url_tone, timeout=8,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
                if r_tone.status_code == 200:
                    tl = r_tone.json().get("timeline", [{}])
                    pts = tl[0].get("data", []) if tl else []
                    neg_vals = [abs(float(p.get("value", 0)))
                                for p in pts if float(p.get("value", 0) or 0) < 0]
                    avg_neg_tone = sum(neg_vals) / len(neg_vals) if neg_vals else 0.0
            except Exception:
                pass

            # Blend into threat_level
            base_tl  = actor.get("threat_level", 50)
            vol_bump = min(8, hit_count // 2)        # max +8 from volume
            tone_bump = min(4, int(avg_neg_tone * 0.8))  # max +4 from tone
            new_tl   = min(99, base_tl + vol_bump + tone_bump)

            enriched["threat_level"]    = new_tl
            enriched["live_hits"]       = hit_count
            enriched["live_headline"]   = headline
            enriched["live_tone"]       = round(avg_neg_tone, 2)
            enriched["last_seen"]       = now_utc.strftime("%Y-%m-%d %H:%M UTC")

            # Escalate status label if live signals are strong
            if new_tl >= 92:
                enriched["status"] = "CRITICAL"
            elif new_tl >= 85 and enriched.get("status") not in ("Highly Active", "CRITICAL"):
                enriched["status"] = "Highly Active"

        except Exception:
            pass

        results.append(enriched)

    return results if results else THREAT_ACTORS


@st.cache_data(ttl=120, show_spinner=False)
def fetch_acled_events(limit: int = 50) -> list:
    """
    ACLED (Armed Conflict Location & Event Data) via their free public API.
    Returns recent conflict events with lat/lon, actor, event type, fatalities.
    API key can be set in st.secrets['ACLED_KEY'] — falls back to scraping GDELT
    if no key is configured.
    """
    import xml.etree.ElementTree as ET
    from datetime import datetime, timezone, timedelta

    # ── Attempt ACLED REST API (requires free account key) ────
    acled_key  = None
    acled_mail = None
    try:
        acled_key  = st.secrets.get("ACLED_KEY",  None)
        acled_mail = st.secrets.get("ACLED_EMAIL", None)
    except Exception:
        pass

    if acled_key and acled_mail:
        try:
            from_date = (datetime.now(tz=timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
            url = (
                f"https://api.acleddata.com/acled/read?"
                f"key={acled_key}&email={acled_mail}"
                f"&event_date={from_date}&event_date_where=BETWEEN"
                f"&event_date_end={datetime.now(tz=timezone.utc).strftime('%Y-%m-%d')}"
                f"&limit={limit}&fields=event_date|event_type|sub_event_type"
                f"|actor1|actor2|country|location|latitude|longitude|fatalities|notes|source"
            )
            r = requests.get(url, timeout=10,
                headers={"User-Agent": "GeoLocator/1.0 (research)"})
            if r.status_code == 200:
                data = r.json()
                events = data.get("data", []) or []
                result = []
                for ev in events:
                    try:
                        result.append({
                            "date":        ev.get("event_date", ""),
                            "event_type":  ev.get("event_type", ""),
                            "sub_type":    ev.get("sub_event_type", ""),
                            "actor1":      ev.get("actor1", "Unknown"),
                            "actor2":      ev.get("actor2", ""),
                            "country":     ev.get("country", ""),
                            "location":    ev.get("location", ""),
                            "lat":         float(ev.get("latitude",  0) or 0),
                            "lon":         float(ev.get("longitude", 0) or 0),
                            "fatalities":  int(ev.get("fatalities",  0) or 0),
                            "notes":       (ev.get("notes", "") or "")[:200],
                            "source":      ev.get("source", "ACLED"),
                            "tip": (f"⚔ ACLED | {ev.get('event_type','')} | "
                                    f"{ev.get('location','')}, {ev.get('country','')} | "
                                    f"{ev.get('event_date','')} | "
                                    f"Fatalities: {ev.get('fatalities',0)} | "
                                    f"Actor: {ev.get('actor1','')}")
                        })
                    except (ValueError, TypeError):
                        continue
                if result:
                    _persist("acled_events", result)
                    return result
        except Exception:
            pass

    # ── Fallback: GDELT GEO API for conflict events ────────────
    try:
        from_ts = (datetime.now(tz=timezone.utc) - timedelta(days=7)).strftime("%Y%m%d%H%M%S")
        query = "war battle attack killed airstrike shelling explosion"
        url = (
            f"https://api.gdeltproject.org/api/v2/geo/geo?"
            f"query={requests.utils.quote(query)}"
            f"&mode=pointdata&maxpoints={limit}&format=json"
            f"&startdatetime={from_ts}&timespan=7d"
        )
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            points = data.get("features", []) or []
            result = []
            for pt in points:
                try:
                    props = pt.get("properties", {})
                    geo   = pt.get("geometry", {}).get("coordinates", [0, 0])
                    result.append({
                        "date":       props.get("dateadded", "")[:10],
                        "event_type": "Conflict",
                        "sub_type":   "Armed clash",
                        "actor1":     props.get("name", "Unknown"),
                        "country":    props.get("countrycode", ""),
                        "location":   props.get("name", ""),
                        "lat":        float(geo[1]) if len(geo) > 1 else 0,
                        "lon":        float(geo[0]) if len(geo) > 0 else 0,
                        "fatalities": 0,
                        "notes":      (props.get("title", ""))[:200],
                        "source":     "GDELT GEO",
                        "tip": (f"⚔ CONFLICT EVENT | {props.get('name','')} | "
                                f"{props.get('dateadded','')[:10]} | GDELT")
                    })
                except (ValueError, TypeError, KeyError):
                    continue
            _persist("acled_events", result[:limit])
            return result[:limit]
    except Exception:
        pass

    # ── Last resort: return last persisted records ──────────────
    _stored = load_persisted("acled_events", limit=limit)
    if _stored:
        return _stored

    return []


@st.cache_data(ttl=45, show_spinner=False)
def fetch_ais_vessels(bbox: tuple = (-180, -90, 180, 90), limit: int = 80) -> list:
    """
    Live AIS vessel positions via AISStream.io WebSocket REST endpoint.
    Falls back to MarineTraffic public data / VesselFinder if API key absent.
    Set st.secrets['AISSTREAM_KEY'] for full live feed.
    """
    ais_key = None
    try:
        ais_key = st.secrets.get("AISSTREAM_KEY", None)
    except Exception:
        pass

    # ── Try AISStream.io HTTP snapshot ─────────────────────────
    if ais_key:
        try:
            url = "https://api.aisstream.io/v0/vessels"
            params = {
                "BoundingBoxes": [[bbox[1], bbox[0], bbox[3], bbox[2]]],
                "FilterMessageTypes": ["PositionReport"],
            }
            r = requests.post(url, json=params, timeout=10,
                headers={"Authorization": f"Bearer {ais_key}"})
            if r.status_code == 200:
                vessels = r.json().get("vessels", []) or r.json() or []
                result = []
                for v in vessels[:limit]:
                    try:
                        ship_type = v.get("ShipType", 0)
                        type_lbl  = ("Tanker" if 80 <= ship_type <= 89
                                     else "Cargo" if 70 <= ship_type <= 79
                                     else "Military" if ship_type == 35
                                     else "Passenger" if 60 <= ship_type <= 69
                                     else "Other")
                        result.append({
                            "mmsi":    v.get("MMSI", ""),
                            "name":    v.get("ShipName", "Unknown").strip(),
                            "lat":     float(v.get("Latitude",  0)),
                            "lon":     float(v.get("Longitude", 0)),
                            "speed":   float(v.get("Sog", 0)),
                            "heading": float(v.get("TrueHeading", 0)),
                            "type":    type_lbl,
                            "flag":    v.get("Destination", ""),
                            "tip": (f"🚢 AIS VESSEL | {v.get('ShipName','').strip()} | "
                                    f"MMSI: {v.get('MMSI','')} | "
                                    f"Type: {type_lbl} | Speed: {v.get('Sog',0)} kn | "
                                    f"Heading: {v.get('TrueHeading',0)}°")
                        })
                    except (ValueError, TypeError):
                        continue
                if result:
                    _persist("ais_positions", result)
                    return result
        except Exception:
            pass

    # ── Fallback: VesselFinder open endpoint (limited public data) ──
    try:
        url = "https://www.myshiptracking.com/requests/vesselsonmap.php?type=json&minlat=-90&maxlat=90&minlng=-180&maxlng=180&zoom=2"
        r = requests.get(url, timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (compatible; research)"})
        if r.status_code == 200 and r.text.strip().startswith("["):
            vessels = r.json() or []
            result = []
            for v in vessels[:limit]:
                try:
                    result.append({
                        "mmsi":    str(v.get("mmsi", v.get("i", ""))),
                        "name":    str(v.get("name", v.get("n", "Unknown"))).strip(),
                        "lat":     float(v.get("lat",  v.get("y", 0))),
                        "lon":     float(v.get("lon",  v.get("x", 0))),
                        "speed":   float(v.get("speed", v.get("s", 0)) or 0),
                        "heading": float(v.get("course", v.get("c", 0)) or 0),
                        "type":    str(v.get("type",  v.get("t", ""))),
                        "flag":    str(v.get("flag",  v.get("f", ""))),
                        "tip": (f"🚢 AIS | {str(v.get('name', v.get('n','Unknown'))).strip()} | "
                                f"Speed: {v.get('speed', v.get('s',0))} kn")
                    })
                except (ValueError, TypeError):
                    continue
            _persist("ais_positions", result)
            return result
    except Exception:
        pass

    # ── Last resort: return last persisted positions ────────────
    _stored_ais = load_persisted("ais_positions", limit=80)
    if _stored_ais:
        return _stored_ais

    return []


@st.cache_data(ttl=60, show_spinner=False)
def fetch_opensky_flights(bbox: tuple = (-180, -90, 180, 90), limit: int = 120) -> list:
    """
    Live aircraft positions from OpenSky Network free anonymous API.
    Filters for military-interest callsigns and anomalous patterns.
    No API key required — anonymous rate limit is 10 req/min.
    """
    try:
        url = (
            f"https://opensky-network.org/api/states/all"
            f"?lamin={bbox[1]}&lomin={bbox[0]}&lamax={bbox[3]}&lomax={bbox[2]}"
        )
        r = requests.get(url, timeout=12,
            headers={"User-Agent": "GeoLocator/1.0 (open research)"})
        if r.status_code != 200:
            return []
        data    = r.json()
        states  = data.get("states", []) or []

        # Field index mapping for OpenSky state vector
        # [icao, callsign, origin, time_pos, last_contact, lon, lat, geo_alt,
        #  on_ground, velocity, true_track, vert_rate, sensors, baro_alt,
        #  squawk, spi, position_source]
        MIL_PREFIXES = {
            "RCH","RRR","CTAM","SAM","USAF","UAF","NATO","RCHT","LNT","FORTE",
            "JAKE","DOOM","BUCK","GRIM","HAVOC","SHADOW","DARKSTAR","NIGHT",
            "REAPER","HAWG","VIPER","EAGLE","LANCE","SABER","DRAGON","TIGER",
        }
        SPECIAL_SQUAWKS = {"7500", "7600", "7700"}

        result = []
        for s in states:
            if not s or len(s) < 8:
                continue
            try:
                callsign = (s[1] or "").strip().upper()
                lon      = s[5]
                lat      = s[6]
                alt      = s[7] or s[13] or 0
                on_gnd   = s[8]
                speed    = s[9] or 0
                heading  = s[10] or 0
                squawk   = (s[14] or "").strip()
                icao     = (s[0] or "").upper()

                if on_gnd or not lat or not lon:
                    continue

                # Classify
                is_mil     = any(callsign.startswith(p) for p in MIL_PREFIXES)
                is_emrg    = squawk in SPECIAL_SQUAWKS
                is_no_call = not callsign
                is_anomaly = is_mil or is_emrg

                if not is_anomaly and not is_no_call and len(result) < limit:
                    if len(result) >= limit // 3:
                        continue  # Only take a third of regular flights

                category = ("MILITARY" if is_mil
                            else "EMERGENCY" if is_emrg
                            else "UNKNOWN" if is_no_call
                            else "CIVIL")
                col_map  = {
                    "MILITARY":  [255, 80,  30, 230],
                    "EMERGENCY": [255, 30,  80, 255],
                    "UNKNOWN":   [200, 200,  0, 180],
                    "CIVIL":     [0,  180, 255, 100],
                }
                result.append({
                    "icao":     icao,
                    "callsign": callsign or "N/A",
                    "lat":      float(lat),
                    "lon":      float(lon),
                    "alt_m":    int(float(alt or 0)),
                    "speed_ms": float(speed),
                    "heading":  float(heading),
                    "squawk":   squawk,
                    "category": category,
                    "_color":   col_map.get(category, [0,180,255,100]),
                    "_radius":  20000 if is_anomaly else 10000,
                    "tip": (f"{'🪖 MILITARY' if is_mil else '🚨 EMERGENCY' if is_emrg else '✈ CIVIL'}"
                            f" | {callsign or 'No callsign'} | ICAO: {icao}"
                            f" | Alt: {int(float(alt or 0))}m | Speed: {int(float(speed or 0))} m/s"
                            f" | Squawk: {squawk or 'none'}")
                })
                if len(result) >= limit:
                    break
            except (ValueError, TypeError, IndexError):
                continue

        # Sort: military and emergencies first
        result.sort(key=lambda x: 0 if x["category"] in ("MILITARY","EMERGENCY") else 1)
        return result[:limit]

    except Exception:
        return []


@st.cache_data(ttl=300, show_spinner=False)
def fetch_news_rss(category: str) -> list:
    """Server-side RSS fetch for news tab categories — bypasses CORS entirely."""
    import xml.etree.ElementTree as ET
    from datetime import datetime, timezone

    CATEGORY_FEEDS = {
        "conflict": [
            "https://understandingwar.org/rss.xml",
            "https://www.csis.org/rss/analysis",
            "https://acleddata.com/feed/",
            "https://www.defenseone.com/rss/all/",
            "https://feeds.reuters.com/reuters/worldNews",
        ],
        "geopolitics": [
            "https://foreignpolicy.com/feed/",
            "https://thediplomat.com/feed/",
            "https://www.defenseone.com/rss/all/",
            "https://www.csis.org/rss/analysis",
            "https://feeds.reuters.com/reuters/worldNews",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
        ],
        "spaceweather": [
            "https://spaceweather.com/index.xml",
            "https://www.swpc.noaa.gov/news/rss.xml",
            "https://www.jpl.nasa.gov/feeds/news",
            "https://science.nasa.gov/feeds/rss/news.rss",
            "https://phys.org/rss-feed/earth-news/",
        ],
        "global": [
            "https://feeds.reuters.com/reuters/worldNews",
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.aljazeera.com/xml/rss/all.xml",
            "https://apnews.com/rss",
        ],
        "science": [
            "https://www.jpl.nasa.gov/feeds/news",
            "https://www.usgs.gov/news/science-news/rss.xml",
            "https://phys.org/rss-feed/earth-news/",
        ],
        "climate": [
            "https://www.carbonbrief.org/feed",
        ],
    }

    feeds = CATEGORY_FEEDS.get(category, CATEGORY_FEEDS["global"])
    articles = []

    def _parse_date(s):
        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                    "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]:
            try: return datetime.strptime(s.strip(), fmt).replace(tzinfo=timezone.utc)
            except: pass
        return datetime.now(timezone.utc)


    for url in feeds:
        try:
            r = requests.get(url, timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            # Detect feed source name from URL
            parts = url.split("/")
            src_name = parts[2].replace("www.","").replace("feeds.","").split(".")[0].upper()
            feed_arts = []
            # RSS 2.0 items
            for item in root.findall(".//item")[:8]:
                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link") or "").strip()
                pub   = (item.findtext("pubDate") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                if not title and desc:
                    title = re.sub(r"<[^>]+>", "", desc)[:120].strip()
                if not title:
                    continue
                dt = _parse_date(pub) if pub else datetime.now(timezone.utc)
                age_s = int((datetime.now(timezone.utc) - dt).total_seconds())
                if age_s < 60:      age = f"{age_s}s ago"
                elif age_s < 3600:  age = f"{age_s//60}m ago"
                elif age_s < 86400: age = f"{age_s//3600}h ago"
                else:               age = f"{age_s//86400}d ago"
                feed_arts.append({"title": title, "url": link, "time": age,
                                   "source": src_name, "ts": dt.timestamp()})
            articles.extend(feed_arts)
            if articles:
                break  # Standard behaviour: stop at first working feed
        except Exception:
            continue

    # Deduplicate by title (first 60 chars)
    seen, unique = set(), []
    for a in articles:
        key = a["title"][:60].lower()
        if key not in seen:
            seen.add(key)
            unique.append(a)

    # Sort newest first
    unique.sort(key=lambda x: -x.get("ts", 0))
    return unique[:30]


@st.cache_data(ttl=120, show_spinner=False)
def fetch_usgs_significant():
    """M5.0+ events in the last 30 days for depth profile chart."""
    try:
        r = requests.get(
            "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/5.0_month.geojson",
            timeout=10)
        r.raise_for_status()
        rows = []
        for f in r.json()["features"][:80]:
            p, c = f["properties"], f["geometry"]["coordinates"]
            rows.append({
                "mag": round(p.get("mag", 0), 1),
                "place": p.get("place", "?"),
                "depth_km": round(c[2], 1),
                "lon": c[0], "lat": c[1],
                "time": datetime.fromtimestamp(p["time"]/1000, tz=timezone.utc).strftime("%Y-%m-%d"),
                "url": p.get("url",""),
                "tip": "🌍 SIGNIFICANT SEISMIC  M" + str(round(p.get("mag",0),1)) + "\n" +
                       p.get("place","?") + "\nDepth: " + str(round(c[2],1)) + " km",
            })
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except:
        return pd.DataFrame()


# ── Country Intelligence lookup for click-to-analyse feature ─────────────────
# Maps country name → coordinates + intel data
COUNTRY_INTEL = {
    "Ukraine":       {"lat":49.0, "lon":31.0,  "flag":"🇺🇦", "code":"UA", "region":"Europe"},
    "Russia":        {"lat":61.0, "lon":105.0, "flag":"🇷🇺", "code":"RU", "region":"Europe/Asia"},
    "Israel":        {"lat":31.5, "lon":34.8,  "flag":"🇮🇱", "code":"IL", "region":"Middle East"},
    "Iran":          {"lat":32.0, "lon":53.0,  "flag":"🇮🇷", "code":"IR", "region":"Middle East"},
    "Gaza":          {"lat":31.4, "lon":34.4,  "flag":"🇵🇸", "code":"PS", "region":"Middle East"},
    "Sudan":         {"lat":12.0, "lon":30.0,  "flag":"🇸🇩", "code":"SD", "region":"Africa"},
    "Myanmar":       {"lat":17.0, "lon":96.0,  "flag":"🇲🇲", "code":"MM", "region":"Asia"},
    "China":         {"lat":35.0, "lon":104.0, "flag":"🇨🇳", "code":"CN", "region":"Asia"},
    "USA":           {"lat":38.0, "lon":-97.0, "flag":"🇺🇸", "code":"US", "region":"Americas"},
    "North Korea":   {"lat":40.0, "lon":127.0, "flag":"🇰🇵", "code":"KP", "region":"Asia"},
    "South Korea":   {"lat":36.0, "lon":127.5, "flag":"🇰🇷", "code":"KR", "region":"Asia"},
    "Japan":         {"lat":36.0, "lon":138.0, "flag":"🇯🇵", "code":"JP", "region":"Asia"},
    "India":         {"lat":20.0, "lon":78.0,  "flag":"🇮🇳", "code":"IN", "region":"Asia"},
    "Pakistan":      {"lat":30.0, "lon":69.0,  "flag":"🇵🇰", "code":"PK", "region":"Asia"},
    "Yemen":         {"lat":15.0, "lon":48.0,  "flag":"🇾🇪", "code":"YE", "region":"Middle East"},
    "Syria":         {"lat":34.8, "lon":38.0,  "flag":"🇸🇾", "code":"SY", "region":"Middle East"},
    "Iraq":          {"lat":33.0, "lon":43.0,  "flag":"🇮🇶", "code":"IQ", "region":"Middle East"},
    "Lebanon":       {"lat":33.8, "lon":35.8,  "flag":"🇱🇧", "code":"LB", "region":"Middle East"},
    "Saudi Arabia":  {"lat":24.0, "lon":45.0,  "flag":"🇸🇦", "code":"SA", "region":"Middle East"},
    "Turkey":        {"lat":39.0, "lon":35.0,  "flag":"🇹🇷", "code":"TR", "region":"Middle East/Europe"},
    "Libya":         {"lat":25.0, "lon":17.0,  "flag":"🇱🇾", "code":"LY", "region":"Africa"},
    "Somalia":       {"lat":5.0,  "lon":46.0,  "flag":"🇸🇴", "code":"SO", "region":"Africa"},
    "Ethiopia":      {"lat":9.0,  "lon":40.0,  "flag":"🇪🇹", "code":"ET", "region":"Africa"},
    "DRC":           {"lat":-4.0, "lon":24.0,  "flag":"🇨🇩", "code":"CD", "region":"Africa"},
    "DR Congo":      {"lat":-4.0, "lon":24.0,  "flag":"🇨🇩", "code":"CD", "region":"Africa"},
    "Venezuela":     {"lat":8.0,  "lon":-66.0, "flag":"🇻🇪", "code":"VE", "region":"Americas"},
    "Haiti":         {"lat":19.0, "lon":-72.0, "flag":"🇭🇹", "code":"HT", "region":"Americas"},
    "Afghanistan":   {"lat":33.0, "lon":65.0,  "flag":"🇦🇫", "code":"AF", "region":"Asia"},
    "UK":            {"lat":54.0, "lon":-2.0,  "flag":"🇬🇧", "code":"GB", "region":"Europe"},
    "France":        {"lat":46.0, "lon":2.0,   "flag":"🇫🇷", "code":"FR", "region":"Europe"},
    "Germany":       {"lat":51.0, "lon":10.0,  "flag":"🇩🇪", "code":"DE", "region":"Europe"},
    "NATO/USA":      {"lat":49.0, "lon":7.6,   "flag":"🇺🇸", "code":"US", "region":"Europe"},
    "USA/Afghan":    {"lat":34.9, "lon":69.3,  "flag":"🇺🇸", "code":"US", "region":"Asia"},
    "USA/NATO":      {"lat":35.5, "lon":24.0,  "flag":"🇺🇸", "code":"US", "region":"Europe"},
    "Singapore":     {"lat":1.35, "lon":103.8, "flag":"🇸🇬", "code":"SG", "region":"Asia"},
    "Mali":          {"lat":17.0, "lon":-4.0,  "flag":"🇲🇱", "code":"ML", "region":"Africa"},
}

def get_country_from_tip(tip: str) -> str:
    """Extract country name from a tip string."""
    # Try to find a country match in the tip
    for country in COUNTRY_INTEL:
        if country.lower() in tip.lower():
            return country
    return ""

def get_all_signals_for_country(country: str) -> dict:
    """Gather all data signals for a country from live + static datasets."""
    c_lower = country.lower()
    signals = {
        "military_bases": [],
        "nuclear_sites": [],
        "conflicts": [],
        "military_activity": [],
        "intel_hotspots": [],
        "historical_events": [],
        "instability": None,
        "nuke_alerts": [],
        "wmd": None,
    }
    # Military bases
    for b in MILITARY_BASES:
        if c_lower in b.get("country","").lower() or c_lower in b.get("name","").lower():
            signals["military_bases"].append(b["name"])
    # Nuclear sites
    for n in NUCLEAR_SITES:
        if c_lower in n.get("country","").lower():
            signals["nuclear_sites"].append({"name":n["name"],"status":n.get("status","")})
    # Active conflicts
    for cname, cdata in CONFLICTS.items():
        factions = " ".join(str(f) for f in cdata.get("factions",[]))
        if c_lower in cname.lower() or c_lower in factions.lower():
            signals["conflicts"].append(cname)
    # Military activity — use live-enriched data (cached, so no extra HTTP cost)
    try:
        _mil_src = fetch_live_military_activity()
    except Exception:
        _mil_src = MILITARY_ACTIVITY
    for m in _mil_src:
        if c_lower in m.get("country","").lower() or c_lower in m.get("name","").lower():
            signals["military_activity"].append(m["name"])
    # Historical events (recent 5)
    for e in _HIST_SORTED:
        if c_lower in e.get("title","").lower() or c_lower in e.get("tip","").lower():
            signals["historical_events"].append(e)
            if len(signals["historical_events"]) >= 5:
                break
    # Instability index — uses live GDELT-blended data
    signals["instability"] = get_instability_for_country(country)
    # Nuke alerts — use live-enriched data
    try:
        _nuke_src = fetch_live_nuke_alerts()
    except Exception:
        _nuke_src = NUKE_ALERTS
    for na in _nuke_src:
        if c_lower in na["site"].lower():
            signals["nuke_alerts"].append(na)
    # WMD posture — use live-enriched data
    try:
        _wmd_src = fetch_live_wmd_posture()
    except Exception:
        _wmd_src = WMD_POSTURE
    for wp in _wmd_src:
        if c_lower in wp["actor"].lower():
            signals["wmd"] = wp
            break
    return signals

INTEL_HOTSPOTS = [
    {"name":"Strait of Hormuz","lat":26.56,"lon":56.26,"type":"Naval Chokepoint","risk":88,"tip":"🎯 INTEL HOTSPOT | Strait of Hormuz | Iran blockade risk | Risk: 88"},
    {"name":"Bab el-Mandeb","lat":12.58,"lon":43.38,"type":"Naval Chokepoint","risk":82,"tip":"🎯 INTEL HOTSPOT | Bab el-Mandeb | Houthi threat | Risk: 82"},
    {"name":"South China Sea","lat":14.5,"lon":113.5,"type":"Territorial Dispute","risk":75,"tip":"🎯 INTEL HOTSPOT | South China Sea | PLA expansion | Risk: 75"},
    {"name":"Taiwan Strait","lat":24.5,"lon":119.5,"type":"Flashpoint","risk":78,"tip":"🎯 INTEL HOTSPOT | Taiwan Strait | PLA pressure | Risk: 78"},
    {"name":"Kashmir LoC","lat":34.5,"lon":74.5,"type":"Border Dispute","risk":65,"tip":"🎯 INTEL HOTSPOT | Kashmir LoC | India-Pakistan tension | Risk: 65"},
    {"name":"Korean DMZ","lat":38.3,"lon":127.0,"type":"Border","risk":60,"tip":"🎯 INTEL HOTSPOT | Korean DMZ | DPRK provocation | Risk: 60"},
    {"name":"Zaporizhzhia NPP","lat":47.5,"lon":34.6,"type":"Nuclear Risk","risk":90,"tip":"🎯 INTEL HOTSPOT | Zaporizhzhia NPP | Active frontline | Risk: 90"},
    {"name":"Kerch Strait","lat":45.35,"lon":36.62,"type":"Naval Chokepoint","risk":72,"tip":"🎯 INTEL HOTSPOT | Kerch Strait | Russia-Ukraine conflict | Risk: 72"},
    {"name":"Niger Delta","lat":5.0,"lon":6.2,"type":"Resource Conflict","risk":62,"tip":"🎯 INTEL HOTSPOT | Niger Delta | Pipeline sabotage risk | Risk: 62"},
    {"name":"Sahel Belt","lat":13.5,"lon":2.0,"type":"Insurgency Zone","risk":74,"tip":"🎯 INTEL HOTSPOT | Sahel | JNIM/ISGS insurgency | Risk: 74"},
]

CONFLICT_ZONES = [
    {"name":"Donetsk Front","lat":48.0,"lon":37.8,"status":"Active","intensity":"Critical","tip":"⚔ CONFLICT ZONE | Donetsk Front | Active frontline combat | Critical"},
    {"name":"Gaza Strip","lat":31.4,"lon":34.4,"status":"Active","intensity":"Critical","tip":"⚔ CONFLICT ZONE | Gaza Strip | IDF operations | Critical"},
    {"name":"Southern Lebanon","lat":33.3,"lon":35.5,"status":"Active","intensity":"High","tip":"⚔ CONFLICT ZONE | S. Lebanon | Hezbollah-Israel exchanges | High"},
    {"name":"Western Iran","lat":33.5,"lon":48.0,"status":"Active","intensity":"Critical","tip":"⚔ CONFLICT ZONE | W. Iran | Israeli strike operations | Critical"},
    {"name":"North Darfur","lat":14.0,"lon":25.3,"status":"Active","intensity":"Critical","tip":"⚔ CONFLICT ZONE | North Darfur | RSF-SAF combat | Critical"},
    {"name":"Sagaing Myanmar","lat":22.0,"lon":95.9,"status":"Active","intensity":"High","tip":"⚔ CONFLICT ZONE | Sagaing | Junta vs PDF | High"},
    {"name":"Tigray Ethiopia","lat":13.5,"lon":38.5,"status":"Frozen","intensity":"Med","tip":"⚔ CONFLICT ZONE | Tigray | Post-ceasefire tension | Med"},
    {"name":"Cabo Delgado","lat":-12.3,"lon":39.5,"status":"Active","intensity":"High","tip":"⚔ CONFLICT ZONE | Cabo Delgado | ISIL-Mozambique | High"},
    {"name":"NE Nigeria","lat":12.0,"lon":13.5,"status":"Active","intensity":"High","tip":"⚔ CONFLICT ZONE | NE Nigeria | Boko Haram / ISWAP | High"},
    {"name":"Rakhine Myanmar","lat":20.1,"lon":93.0,"status":"Active","intensity":"High","tip":"⚔ CONFLICT ZONE | Rakhine | AA-Tatmadaw | High"},
    {"name":"Khartoum","lat":15.5,"lon":32.5,"status":"Active","intensity":"Critical","tip":"⚔ CONFLICT ZONE | Khartoum | RSF urban warfare | Critical"},
    {"name":"Kharkiv Oblast","lat":50.0,"lon":36.3,"status":"Active","intensity":"High","tip":"⚔ CONFLICT ZONE | Kharkiv | Russian shelling | High"},
]

MILITARY_BASES = [
    # ── USA Global Network ──────────────────────────────────────
    {"name":"Diego Garcia (BIOT)","country":"US/UK","lat":-7.3,"lon":72.4,"type":"Naval/Air","tip":"🏛 MILITARY BASE | Diego Garcia | US/UK | Naval-Air | Indian Ocean strategic hub"},
    {"name":"Ramstein AFB","country":"USA","lat":49.44,"lon":7.6,"type":"Air","tip":"🏛 MILITARY BASE | Ramstein AFB | Germany | USAF Air Command | NATO Europe HQ"},
    {"name":"Al Udeid AFB","country":"USA","lat":25.11,"lon":51.31,"type":"Air","tip":"🏛 MILITARY BASE | Al Udeid | Qatar | USAF | CENTCOM forward HQ | 10,000 personnel"},
    {"name":"Kadena AFB","country":"USA","lat":26.36,"lon":127.77,"type":"Air","tip":"🏛 MILITARY BASE | Kadena | Okinawa | Largest USAF base in Asia | F-15C/D"},
    {"name":"Camp Lemonnier","country":"USA","lat":11.55,"lon":43.15,"type":"Naval/Air","tip":"🏛 MILITARY BASE | Camp Lemonnier | Djibouti | USA | Horn of Africa hub | JSOC"},
    {"name":"Guantanamo Bay","country":"USA","lat":19.9,"lon":-75.1,"type":"Naval","tip":"🏛 MILITARY BASE | Guantanamo Bay | Cuba | USA | Caribbean naval station & detention"},
    {"name":"Okinawa MCAS","country":"USA","lat":26.18,"lon":127.65,"type":"Air","tip":"🏛 MILITARY BASE | MCAS Futenma | Okinawa | USMC | Japan | F-35B capable"},
    {"name":"Camp Humphreys","country":"USA","lat":36.98,"lon":127.03,"type":"Army","tip":"🏛 MILITARY BASE | Camp Humphreys | South Korea | USFK HQ | Largest US overseas base"},
    {"name":"Yokosuka Naval Base","country":"USA","lat":35.28,"lon":139.67,"type":"Naval","tip":"🏛 MILITARY BASE | Yokosuka | Japan | 7th Fleet HQ | USS Ronald Reagan homeport"},
    {"name":"Misawa AFB","country":"USA","lat":40.7,"lon":141.37,"type":"Air","tip":"🏛 MILITARY BASE | Misawa | Japan | F-16 | ISR | Electronic warfare"},
    {"name":"Andersen AFB","country":"USA","lat":13.58,"lon":144.93,"type":"Air","tip":"🏛 MILITARY BASE | Andersen | Guam | USAF | B-2 bomber forward base | Pacific hub"},
    {"name":"Naval Base Guam","country":"USA","lat":13.44,"lon":144.65,"type":"Naval","tip":"🏛 MILITARY BASE | NB Guam | USA | Submarine & surface fleet | Pacific deterrence"},
    {"name":"Incirlik AFB","country":"NATO/USA","lat":37.0,"lon":35.4,"type":"Air","tip":"🏛 MILITARY BASE | Incirlik | Turkey | NATO/USA | B61 nuclear weapons hosted"},
    {"name":"Suda Bay","country":"USA/NATO","lat":35.49,"lon":24.14,"type":"Naval","tip":"🏛 MILITARY BASE | Suda Bay | Crete | US/NATO | Mediterranean operations hub"},
    {"name":"Al-Dhafra AFB","country":"USA","lat":24.25,"lon":54.55,"type":"Air","tip":"🏛 MILITARY BASE | Al-Dhafra | UAE | USAF | F-35A | RQ-4 Global Hawk ISR"},
    {"name":"Ali Al Salem AFB","country":"USA","lat":29.35,"lon":47.52,"type":"Air","tip":"🏛 MILITARY BASE | Ali Al Salem | Kuwait | USAF | Pre-positioned armour"},
    {"name":"NSA Bahrain","country":"USA","lat":26.22,"lon":50.59,"type":"Naval","tip":"🏛 MILITARY BASE | NSA Bahrain | 5th Fleet HQ | Gulf maritime operations"},
    {"name":"AFRICOM Djibouti","country":"USA","lat":11.55,"lon":43.1,"type":"Joint","tip":"🏛 MILITARY BASE | AFRICOM fwd | Djibouti | Drone ops | CT Africa"},
    {"name":"Thule Air Base","country":"USA","lat":76.53,"lon":-68.7,"type":"Air","tip":"🏛 MILITARY BASE | Pituffik | Greenland | USA | Ballistic missile warning | Arctic"},
    {"name":"Fort Wainwright","country":"USA","lat":64.83,"lon":-147.63,"type":"Army","tip":"🏛 MILITARY BASE | Fort Wainwright | Alaska | Arctic combat training | 25th Infantry"},
    {"name":"NAS Sigonella","country":"USA","lat":37.4,"lon":14.92,"type":"Naval/Air","tip":"🏛 MILITARY BASE | NAS Sigonella | Sicily | USA/NATO | P-8 Poseidon | Med hub"},
    {"name":"NSGA Molesworth","country":"USA","lat":52.37,"lon":-0.44,"type":"Intel","tip":"🏛 MILITARY BASE | Molesworth | UK | USAF | EUCOM Intel fusion centre"},
    # ── UK ──────────────────────────────────────────────────────
    {"name":"Portsmouth Naval","country":"UK","lat":50.8,"lon":-1.1,"type":"Naval","tip":"🏛 MILITARY BASE | Portsmouth | UK | RN surface fleet HQ | Queen Elizabeth carriers"},
    {"name":"HMNB Clyde (Faslane)","country":"UK","lat":56.07,"lon":-4.82,"type":"Naval","tip":"🏛 MILITARY BASE | Faslane | Scotland | Trident nuclear submarine base"},
    {"name":"RAF Brize Norton","country":"UK","lat":51.75,"lon":-1.58,"type":"Air","tip":"🏛 MILITARY BASE | RAF Brize Norton | UK | Air Transport | Tankers | A400M"},
    {"name":"RAF Akrotiri","country":"UK","lat":34.59,"lon":32.98,"type":"Air","tip":"🏛 MILITARY BASE | RAF Akrotiri | Cyprus | UK sovereign base | Med operations"},
    # ── Russia ──────────────────────────────────────────────────
    {"name":"Tartus Naval","country":"Russia","lat":34.9,"lon":35.9,"type":"Naval","tip":"🏛 MILITARY BASE | Tartus | Syria | Russia | Only Mediterranean naval base"},
    {"name":"Hmeimim AFB","country":"Russia","lat":35.4,"lon":35.95,"type":"Air","tip":"🏛 MILITARY BASE | Hmeimim | Syria | Russia | Su-35/Su-30 | Syrian campaign hub"},
    {"name":"Sevastopol Fleet","country":"Russia","lat":44.6,"lon":33.5,"type":"Naval","tip":"🏛 MILITARY BASE | Sevastopol | Crimea | Russia | Black Sea Fleet HQ | Contested"},
    {"name":"Kaliningrad Base","country":"Russia","lat":54.7,"lon":20.5,"type":"Joint","tip":"🏛 MILITARY BASE | Kaliningrad | Russia | Baltic exclave | Iskander missiles"},
    {"name":"Kant AFB","country":"Russia","lat":42.85,"lon":74.84,"type":"Air","tip":"🏛 MILITARY BASE | Kant | Kyrgyzstan | Russia | CSTO forward base | Central Asia"},
    {"name":"Khmeimim Wagner Hub","country":"Russia","lat":16.0,"lon":-0.5,"type":"Air","tip":"🏛 MILITARY BASE | Mali/CAR | Russia (Africa Corps) | Wagner successor operations"},
    {"name":"Nova Kakhovka (frontline)","country":"Russia","lat":46.76,"lon":33.36,"type":"Ground","tip":"🏛 MILITARY BASE | Nova Kakhovka area | Russia/Ukraine frontline | Occupied territory"},
    # ── China ──────────────────────────────────────────────────
    {"name":"Djibouti PLA Base","country":"China","lat":11.6,"lon":43.2,"type":"Naval","tip":"🏛 MILITARY BASE | PLA Base Djibouti | China | First overseas base | Logistics hub"},
    {"name":"Woody Island (Paracel)","country":"China","lat":16.83,"lon":112.34,"type":"Air/Naval","tip":"🏛 MILITARY BASE | Woody Island | South China Sea | PLA | Runway | SAM batteries"},
    {"name":"Fiery Cross Reef","country":"China","lat":9.55,"lon":114.23,"type":"Air/Naval","tip":"🏛 MILITARY BASE | Fiery Cross Reef | Spratly Islands | PLA | 3km runway | contested"},
    {"name":"Mischief Reef","country":"China","lat":9.9,"lon":115.53,"type":"Naval","tip":"🏛 MILITARY BASE | Mischief Reef | Spratlys | PLA | Naval base | SCS control hub"},
    {"name":"Subi Reef","country":"China","lat":10.93,"lon":114.08,"type":"Air/Naval","tip":"🏛 MILITARY BASE | Subi Reef | Spratlys | PLA | Runway + hangers | ADIZ enforcement"},
    # ── Other Nations ───────────────────────────────────────────
    {"name":"Changi Naval Base","country":"Singapore","lat":1.4,"lon":104.0,"type":"Naval","tip":"🏛 MILITARY BASE | Changi | Singapore | RSN + US access | Strait of Malacca key"},
    {"name":"RAAF Tindal","country":"Australia","lat":-14.52,"lon":132.37,"type":"Air","tip":"🏛 MILITARY BASE | RAAF Tindal | Northern Territory | B-52 capable | AUKUS hub"},
    {"name":"Pine Gap","country":"USA/Australia","lat":-23.8,"lon":133.74,"type":"Intel","tip":"🏛 MILITARY BASE | Pine Gap | Australia | CIA/NSA signals intelligence | SIGINT"},
    {"name":"CFB Trenton","country":"Canada","lat":44.12,"lon":-77.53,"type":"Air","tip":"🏛 MILITARY BASE | CFB Trenton | Canada | Largest RCAF base | Strategic airlift"},
    {"name":"Lajes Field","country":"USA/Portugal","lat":38.76,"lon":-27.09,"type":"Air","tip":"🏛 MILITARY BASE | Lajes | Azores | Portugal/USA | Atlantic crossroads | NATO"},
    {"name":"Bagram (inactive)","country":"USA/Afghan","lat":34.94,"lon":69.27,"type":"Air","tip":"🏛 MILITARY BASE | Bagram | Afghanistan | Abandoned by USA Aug 2021 | Now Taliban"},
    {"name":"NSG Aden (UAE)","country":"UAE","lat":12.79,"lon":45.04,"type":"Naval","tip":"🏛 MILITARY BASE | Aden | Yemen | UAE naval hub | Red Sea operations"},
    {"name":"French Djibouti (Camp Lemonier)","country":"France","lat":11.52,"lon":43.08,"type":"Joint","tip":"🏛 MILITARY BASE | Camp de la Paix | Djibouti | France | Legionnaire base | Africa ops"},
    {"name":"French Polynesia (Mururoa legacy)","country":"France","lat":-21.86,"lon":-138.88,"type":"Nuclear legacy","tip":"🏛 MILITARY BASE | Mururoa Atoll | French Polynesia | Nuclear test site legacy | monitored"},
    {"name":"Israeli Air Force Tel Nof","country":"Israel","lat":31.84,"lon":34.82,"type":"Air","tip":"🏛 MILITARY BASE | Tel Nof | Israel | IAF HQ | F-35I | Nuclear-capable squadron"},
    {"name":"Nevatim AFB","country":"Israel","lat":31.21,"lon":35.01,"type":"Air","tip":"🏛 MILITARY BASE | Nevatim | Israel | F-35I Adir | Primary IAF strike base"},
    {"name":"INS Karwar (Project Seabird)","country":"India","lat":14.81,"lon":74.12,"type":"Naval","tip":"🏛 MILITARY BASE | INS Karwar | India | Largest naval base in Asia under expansion"},
    {"name":"INS Varsha (Visakhapatnam)","country":"India","lat":17.69,"lon":83.22,"type":"Naval","tip":"🏛 MILITARY BASE | INS Varsha | India | Nuclear submarine base | Strategic Command"},
    {"name":"Gwangju Air Base","country":"South Korea","lat":35.12,"lon":126.81,"type":"Air","tip":"🏛 MILITARY BASE | Gwangju | South Korea | ROKAF | F-35A | Combined ops with USAF"},
    {"name":"JGSDF Camp Kengun","country":"Japan","lat":32.84,"lon":130.89,"type":"Army","tip":"🏛 MILITARY BASE | Camp Kengun | Kumamoto | JGSDF | Amphibious rapid deployment"},
    {"name":"Turkish Naval Aksaz","country":"Turkey","lat":36.93,"lon":28.3,"type":"Naval","tip":"🏛 MILITARY BASE | Naval Base Aksaz | Turkey | NATO | Aegean submarine hub"},
    {"name":"Pakistani GHQ Rawalpindi","country":"Pakistan","lat":33.59,"lon":73.06,"type":"Army HQ","tip":"🏛 MILITARY BASE | GHQ Rawalpindi | Pakistan | Army HQ | Nuclear command authority"},
    {"name":"Nur Khan AFB","country":"Pakistan","lat":33.62,"lon":73.1,"type":"Air","tip":"🏛 MILITARY BASE | PAF Nur Khan | Pakistan | VVIP airlift | Strategic transport"},
    {"name":"KAF Sargodha","country":"Pakistan","lat":32.05,"lon":72.67,"type":"Air","tip":"🏛 MILITARY BASE | PAF Sargodha | Pakistan | F-16 | Nuclear-capable airbase"},
    {"name":"Al-Shaybah (Saudi)","country":"Saudi Arabia","lat":22.51,"lon":53.97,"type":"Air","tip":"🏛 MILITARY BASE | Al-Shaybah | Saudi Arabia | RSAF | Patriot batteries | SE Arabia"},
    {"name":"King Abdulaziz Naval Base","country":"Saudi Arabia","lat":27.42,"lon":49.57,"type":"Naval","tip":"🏛 MILITARY BASE | King Abdulaziz | Jubail | Saudi Arabia | Eastern Fleet HQ"},
    {"name":"Al-Anad Air Base","country":"Yemen (Houthi zone)","lat":13.18,"lon":44.78,"type":"Air","tip":"🏛 MILITARY BASE | Al-Anad | Yemen | Former US drone hub | Now contested/Houthi zone"},
    {"name":"HMNB Gibraltar","country":"UK","lat":36.14,"lon":-5.36,"type":"Naval","tip":"🏛 MILITARY BASE | HMNB Gibraltar | UK | Strait of Gibraltar | Submarine support"},
]

NUCLEAR_SITES = [
    # ── Active Conflict / Struck Sites ─────────────────────────
    {"name":"Natanz","country":"Iran","lat":33.72,"lon":51.73,"type":"Enrichment","status":"Struck","tip":"☢ NUCLEAR | Natanz | Iran | Main enrichment facility | Struck by IDF Mar 2026 | ~19,000 centrifuges destroyed"},
    {"name":"Fordow","country":"Iran","lat":34.88,"lon":49.93,"type":"Enrichment","status":"Destroyed","tip":"☢ NUCLEAR | Fordow | Iran | Underground enrichment bunker | Destroyed by B-2/BLU-57 Feb 2026"},
    {"name":"Bushehr NPP","country":"Iran","lat":28.98,"lon":50.84,"type":"Power Plant","status":"Operational","tip":"☢ NUCLEAR | Bushehr NPP | Iran | 1000MW VVER reactor | Russian-built | IAEA monitored"},
    {"name":"Isfahan Nuclear Tech","country":"Iran","lat":32.63,"lon":51.66,"type":"Research/Conversion","status":"Struck","tip":"☢ NUCLEAR | Isfahan | Iran | UF6 conversion facility | Struck by IDF strikes 2026"},
    {"name":"Zaporizhzhia NPP","country":"Ukraine","lat":47.5,"lon":34.6,"type":"Power Plant","status":"Occupied","tip":"☢ NUCLEAR | Zaporizhzhia | Ukraine (occupied) | 6×950MW VVER | Frontline risk | IAEA monitoring disrupted"},
    {"name":"Chornobyl (exclusion)","country":"Ukraine","lat":51.39,"lon":30.1,"type":"Legacy/Decommissioned","status":"Monitored","tip":"☢ NUCLEAR | Chornobyl | Ukraine | 1986 disaster site | New safe confinement 2016 | Russian-occupied Feb-Mar 2022"},
    # ── DPRK ───────────────────────────────────────────────────
    {"name":"Yongbyon","country":"N.Korea","lat":39.81,"lon":125.75,"type":"Weapons Complex","status":"Active","tip":"☢ NUCLEAR | Yongbyon | DPRK | 5MW plutonium reactor + centrifuge hall | Satellite-confirmed expansion 2025"},
    {"name":"Punggye-ri","country":"N.Korea","lat":41.27,"lon":129.08,"type":"Test Site","status":"Active","tip":"☢ NUCLEAR | Punggye-ri | DPRK | Underground nuclear test site | 6 tests 2006-2017 | Tunnel activity observed 2024"},
    {"name":"Kangson","country":"N.Korea","lat":38.87,"lon":125.83,"type":"Enrichment (suspected)","status":"Active","tip":"☢ NUCLEAR | Kangson | DPRK | Suspected covert centrifuge enrichment | Identified 2018"},
    # ── Russia ─────────────────────────────────────────────────
    {"name":"Seversk","country":"Russia","lat":56.6,"lon":84.86,"type":"Weapons Production","status":"Active","tip":"☢ NUCLEAR | Seversk | Russia | Pu-239 production | Closed city | Rosatom"},
    {"name":"Sarov (Arzamas-16)","country":"Russia","lat":54.93,"lon":43.32,"type":"Weapons Design","status":"Active","tip":"☢ NUCLEAR | Sarov | Russia | Main nuclear weapons design lab | VNIIEF | 4,000+ warhead designs"},
    {"name":"Snezhinsk (Chelyabinsk-70)","country":"Russia","lat":56.08,"lon":60.74,"type":"Weapons Design","status":"Active","tip":"☢ NUCLEAR | Snezhinsk | Russia | 2nd nuclear warhead design lab | VNIITF"},
    {"name":"Novaya Zemlya","country":"Russia","lat":73.4,"lon":55.0,"type":"Test Site","status":"Active","tip":"☢ NUCLEAR | Novaya Zemlya | Russia | Arctic test site | Last test 1990 | Monitoring infrastructure active"},
    {"name":"Ozersk (Mayak)","country":"Russia","lat":55.77,"lon":60.63,"type":"Reprocessing","status":"Active","tip":"☢ NUCLEAR | Mayak | Ozersk | Russia | Plutonium reprocessing + weapons-grade material | Site of 1957 Kyshtym disaster"},
    # ── USA ─────────────────────────────────────────────────────
    {"name":"Cheyenne Mountain","country":"USA","lat":38.74,"lon":-104.85,"type":"Command","status":"Active","tip":"☢ NUCLEAR | Cheyenne Mountain | Colorado | USA | NORAD/USNORTHCOM | Nuclear-hardened command bunker"},
    {"name":"Y-12 National Security","country":"USA","lat":36.04,"lon":-84.09,"type":"Weapons Production","status":"Active","tip":"☢ NUCLEAR | Y-12 | Oak Ridge | USA | HEU storage + component manufacture | Main warhead production site"},
    {"name":"Pantex Plant","country":"USA","lat":35.26,"lon":-101.52,"type":"Weapons Assembly","status":"Active","tip":"☢ NUCLEAR | Pantex | Texas | USA | Only US nuclear warhead assembly/disassembly plant"},
    {"name":"Savannah River Site","country":"USA","lat":33.35,"lon":-81.72,"type":"Production/Tritium","status":"Active","tip":"☢ NUCLEAR | Savannah River | South Carolina | USA | Tritium production for warheads | Pu processing"},
    {"name":"Nevada Test Site","country":"USA","lat":37.1,"lon":-116.05,"type":"Test Site (legacy)","status":"Monitored","tip":"☢ NUCLEAR | Nevada | USA | 928 nuclear tests 1951-1992 | Now Nevada National Security Site | Subcritical tests"},
    {"name":"Los Alamos NL","country":"USA","lat":35.88,"lon":-106.3,"type":"Weapons Design","status":"Active","tip":"☢ NUCLEAR | Los Alamos | New Mexico | USA | Primary nuclear weapons design lab | Manhattan Project origin"},
    # ── Israel (undeclared) ─────────────────────────────────────
    {"name":"Dimona","country":"Israel","lat":31.0,"lon":35.15,"type":"Weapons Research","status":"Active","tip":"☢ NUCLEAR | Dimona | Israel | Negev Nuclear Research Center | Undeclared ~90 warheads | Not IAEA signatory"},
    # ── Pakistan ─────────────────────────────────────────────────
    {"name":"Khushab I-IV","country":"Pakistan","lat":32.05,"lon":71.9,"type":"Weapons Complex","status":"Active","tip":"☢ NUCLEAR | Khushab | Pakistan | 4 plutonium production reactors | ~165 warheads est. | Expanding capacity"},
    {"name":"Kahuta (KRL)","country":"Pakistan","lat":33.64,"lon":73.37,"type":"Enrichment","status":"Active","tip":"☢ NUCLEAR | Kahuta | Pakistan | Main HEU enrichment plant | A.Q. Khan Research Laboratories"},
    {"name":"Dera Ghazi Khan","country":"Pakistan","lat":30.04,"lon":70.62,"type":"Uranium Processing","status":"Active","tip":"☢ NUCLEAR | Dera Ghazi Khan | Pakistan | Uranium conversion + yellowcake processing"},
    # ── India ──────────────────────────────────────────────────
    {"name":"Tarapur NPP","country":"India","lat":19.83,"lon":72.66,"type":"Power Plant","status":"Active","tip":"☢ NUCLEAR | Tarapur | Maharashtra | India | 2×160MW BWR + 2×540MW PHWR | Oldest Indian NPP"},
    {"name":"Kaiga NPP","country":"India","lat":14.87,"lon":74.44,"type":"Power Plant","status":"Active","tip":"☢ NUCLEAR | Kaiga | Karnataka | India | 4×220MW PHWR | Operational | IAEA safeguards"},
    {"name":"Kalpakkam (IGCAR)","country":"India","lat":12.56,"lon":80.18,"type":"Research/Fast Reactor","status":"Active","tip":"☢ NUCLEAR | Kalpakkam | Tamil Nadu | India | Fast breeder reactor + IGCAR research | PFBR 500MW"},
    {"name":"Bhabha ARC","country":"India","lat":19.02,"lon":72.87,"type":"Research","status":"Active","tip":"☢ NUCLEAR | BARC | Mumbai | India | Nuclear research + weapons design authority | CIRUS/Apsara reactors"},
    {"name":"Trombay (BARC)","country":"India","lat":19.02,"lon":72.92,"type":"Reprocessing","status":"Active","tip":"☢ NUCLEAR | Trombay | Mumbai | India | Plutonium reprocessing | Unsafeguarded | Weapons-grade Pu source"},
    # ── China ──────────────────────────────────────────────────
    {"name":"Lop Nor","country":"China","lat":40.85,"lon":89.5,"type":"Test Site","status":"Monitored","tip":"☢ NUCLEAR | Lop Nor | Xinjiang | China | 45 nuclear tests 1964-1996 | Activity detected 2020-2024"},
    {"name":"Jianmen 404 Complex","country":"China","lat":38.88,"lon":101.83,"type":"Production","status":"Active","tip":"☢ NUCLEAR | Plant 404 | Gansu | China | Pu production + reprocessing | Warhead component manufacture"},
    {"name":"Guangyuan NPP","country":"China","lat":32.35,"lon":105.81,"type":"Power Plant","status":"Active","tip":"☢ NUCLEAR | Guangyuan | Sichuan | China | 2×650MW PWR | IAEA safeguarded"},
    {"name":"CNNC Baotou","country":"China","lat":40.62,"lon":109.84,"type":"Fuel/Weapons","status":"Active","tip":"☢ NUCLEAR | Baotou | Inner Mongolia | China | Nuclear fuel element factory + HEU enrichment"},
    # ── France ─────────────────────────────────────────────────
    {"name":"CEA Valduc","country":"France","lat":47.57,"lon":4.97,"type":"Weapons Production","status":"Active","tip":"☢ NUCLEAR | Valduc | Burgundy | France | Primary nuclear warhead production & maintenance | ~290 warheads"},
    {"name":"Île Longue","country":"France","lat":48.37,"lon":-4.57,"type":"Submarine Base","status":"Active","tip":"☢ NUCLEAR | Île Longue | Brittany | France | SSBN base | 4 Le Triomphant-class | SLBM M51 missiles"},
    # ── UK ─────────────────────────────────────────────────────
    {"name":"AWE Aldermaston","country":"UK","lat":51.38,"lon":-1.18,"type":"Weapons Design","status":"Active","tip":"☢ NUCLEAR | AWE Aldermaston | Berkshire | UK | Trident warhead design + manufacture | ~225 warheads"},
    {"name":"Coulport RNAD","country":"UK","lat":56.05,"lon":-4.86,"type":"Warhead Storage","status":"Active","tip":"☢ NUCLEAR | RNAD Coulport | Scotland | UK | Trident SLBM + warhead storage | Adjacent to Faslane SSBN base"},
]

GAMMA_IRRADIATORS = [
    {"name":"Cairo Medical Irradiator","country":"Egypt","lat":30.06,"lon":31.24,"type":"Medical","tip":"⚠ GAMMA IRRADIATOR | Cairo | Egypt | Medical sterilisation | IAEA reg."},
    {"name":"Lagos Industrial","country":"Nigeria","lat":6.45,"lon":3.4,"type":"Industrial","tip":"⚠ GAMMA IRRADIATOR | Lagos | Nigeria | Food irradiation facility"},
    {"name":"Tehran Isotope Centre","country":"Iran","lat":35.72,"lon":51.39,"type":"Research","tip":"⚠ GAMMA IRRADIATOR | Tehran | Iran | Research reactor isotopes"},
    {"name":"Dhaka Radiation Centre","country":"Bangladesh","lat":23.81,"lon":90.41,"type":"Medical","tip":"⚠ GAMMA IRRADIATOR | Dhaka | Bangladesh | Cancer treatment"},
    {"name":"Abuja Med Physics","country":"Nigeria","lat":9.07,"lon":7.4,"type":"Medical","tip":"⚠ GAMMA IRRADIATOR | Abuja | Nigeria | Medical use | IAEA monitored"},
    {"name":"Tbilisi Research","country":"Georgia","lat":41.69,"lon":44.83,"type":"Research","tip":"⚠ GAMMA IRRADIATOR | Tbilisi | Georgia | Legacy Soviet source"},
    {"name":"Caracas Industrial","country":"Venezuela","lat":10.48,"lon":-66.87,"type":"Industrial","tip":"⚠ GAMMA IRRADIATOR | Caracas | Venezuela | Sterilisation plant"},
    {"name":"Nairobi Med Centre","country":"Kenya","lat":-1.29,"lon":36.82,"type":"Medical","tip":"⚠ GAMMA IRRADIATOR | Nairobi | Kenya | Radiotherapy unit"},
]

SPACEPORTS = [
    {"name":"Kennedy Space Center","country":"USA","lat":28.52,"lon":-80.65,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | KSC | USA | SpaceX/NASA | LEO & deep space"},
    {"name":"Baikonur Cosmodrome","country":"Russia/Kazakhstan","lat":45.92,"lon":63.34,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | Baikonur | Russia | Historic Soviet facility | Soyuz"},
    {"name":"Jiuquan (JSLC)","country":"China","lat":40.96,"lon":100.29,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | Jiuquan | China | PLA & CNSA | LEO launches"},
    {"name":"Wenchang Space Centre","country":"China","lat":19.61,"lon":110.95,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | Wenchang | China | Long March 5 | Lunar missions"},
    {"name":"Kourou (ESA)","country":"France/ESA","lat":5.24,"lon":-52.77,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | Kourou | ESA/France | Ariane 6 | GTO launches"},
    {"name":"Tanegashima","country":"Japan","lat":30.4,"lon":131.02,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | Tanegashima | JAXA | H-IIA/H3 launch site"},
    {"name":"Sriharikota (ISRO)","country":"India","lat":13.73,"lon":80.23,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | SDSC-SHAR | India | ISRO | PSLV/GSLV launches"},
    {"name":"Vandenberg SFB","country":"USA","lat":34.74,"lon":-120.57,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | Vandenberg | USA | SpaceX Falcon 9 | Polar orbits"},
    {"name":"Plesetsk Cosmodrome","country":"Russia","lat":62.93,"lon":40.46,"type":"Military","active":True,"tip":"🚀 SPACEPORT | Plesetsk | Russia | Military launches | Angara"},
    {"name":"Naro Space Centre","country":"South Korea","lat":34.43,"lon":127.54,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | Naro | South Korea | KSLV-II Nuri"},
    {"name":"Palmachim AFB","country":"Israel","lat":31.9,"lon":34.69,"type":"Military","active":True,"tip":"🚀 SPACEPORT | Palmachim | Israel | Shavit launcher | Retrograde orbit"},
    {"name":"SpaceX Starbase","country":"USA","lat":25.99,"lon":-97.16,"type":"Launch","active":True,"tip":"🚀 SPACEPORT | Starbase Texas | USA | SpaceX Starship | Superheavy"},
]

UNDERSEA_CABLES = [
    {"name":"SEA-ME-WE 4","from_lat":1.35,"from_lon":103.8,"to_lat":50.85,"to_lon":4.35,"status":"Degraded","risk":72,"tip":"🔌 CABLE | SEA-ME-WE 4 | Singapore→Europe | Degraded | Risk: 72"},
    {"name":"Africa Coast to Europe","from_lat":6.45,"from_lon":3.4,"to_lat":43.35,"to_lon":-8.4,"status":"Cut","risk":88,"tip":"🔌 CABLE | ACE | W.Africa→Europe | CUT | Risk: 88"},
    {"name":"PEACE Cable","from_lat":25.07,"from_lon":55.15,"to_lat":14.0,"to_lon":42.0,"status":"Degraded","risk":65,"tip":"🔌 CABLE | PEACE | ME→Africa | Degraded | Risk: 65"},
    {"name":"Trans-Pacific Express","from_lat":37.77,"from_lon":-122.4,"to_lat":35.68,"to_lon":139.69,"status":"Active","risk":18,"tip":"🔌 CABLE | TPE | USA→Japan | Active | Risk: 18"},
    {"name":"FLAG Atlantic-1","from_lat":51.5,"from_lon":-0.1,"to_lat":40.71,"to_lon":-74.0,"status":"Active","risk":22,"tip":"🔌 CABLE | FLAG Atlantic-1 | UK→USA | Active | Risk: 22"},
    {"name":"AAE-1","from_lat":22.57,"from_lon":88.36,"to_lat":48.86,"to_lon":2.35,"status":"Active","risk":40,"tip":"🔌 CABLE | AAE-1 | Asia→Europe | Active | Risk: 40"},
    {"name":"MAREA","from_lat":51.5,"from_lon":-0.1,"to_lat":40.71,"to_lon":-74.0,"status":"Active","risk":15,"tip":"🔌 CABLE | MAREA | Microsoft/Facebook | UK→USA | Risk: 15"},
    {"name":"SJC2","from_lat":35.68,"from_lon":139.69,"to_lat":1.35,"to_lon":103.8,"status":"Active","risk":25,"tip":"🔌 CABLE | SJC2 | Japan→Singapore | Active | Risk: 25"},
]

PIPELINES = [
    {"name":"Nord Stream (sabotaged)","from_lat":59.9,"from_lon":24.9,"to_lat":54.15,"to_lon":12.1,"status":"Sabotaged","risk":95},
    {"name":"Druzhba Pipeline","from_lat":55.75,"from_lon":37.6,"to_lat":52.22,"to_lon":21.0,"status":"Reduced","risk":62},
    {"name":"Trans-Arabian Pipeline","from_lat":26.3,"from_lon":50.2,"to_lat":33.5,"to_lon":35.5,"status":"Suspended","risk":78},
    {"name":"TANAP","from_lat":40.0,"from_lon":49.8,"to_lat":41.7,"to_lon":26.6,"status":"Active","risk":30},
    {"name":"East African Crude","from_lat":-0.3,"from_lon":32.6,"to_lat":-4.9,"to_lon":39.6,"status":"Under Construction","risk":45},
    {"name":"Kazakhstan-China","from_lat":45.0,"from_lon":51.0,"to_lat":43.8,"to_lon":87.6,"status":"Active","risk":22},
    {"name":"Sumed Pipeline","from_lat":30.06,"from_lon":31.24,"to_lat":30.9,"to_lon":32.55,"status":"Active","risk":38},
    {"name":"Iran-Iraq-Syria","from_lat":35.69,"from_lon":51.39,"to_lat":33.3,"to_lon":44.4,"status":"Disrupted","risk":81},
]

AI_DATA_CENTERS = [
    {"name":"Microsoft Azure — Dublin","lat":53.33,"lon":-6.25,"operator":"Microsoft","tip":"🖥 AI DATA CENTER | Azure Dublin | Microsoft | EU West Hub | 200+ MW"},
    {"name":"Google DeepMind — London","lat":51.52,"lon":-0.08,"operator":"Google","tip":"🖥 AI DATA CENTER | GCP London | Google | AI training workloads"},
    {"name":"AWS — Northern Virginia","lat":38.9,"lon":-77.4,"operator":"Amazon","tip":"🖥 AI DATA CENTER | AWS US-East | Amazon | Largest cloud region globally"},
    {"name":"Microsoft — Des Moines","lat":41.58,"lon":-93.62,"operator":"Microsoft","tip":"🖥 AI DATA CENTER | Azure Iowa | Microsoft | OpenAI training cluster"},
    {"name":"Meta — Fort Worth","lat":32.74,"lon":-97.33,"operator":"Meta","tip":"🖥 AI DATA CENTER | Meta Texas | Meta AI | LLaMA training | 1GW+"},
    {"name":"Anthropic — San Francisco","lat":37.79,"lon":-122.4,"operator":"Anthropic","tip":"🖥 AI DATA CENTER | Anthropic SF | AWS-backed | Claude training"},
    {"name":"Baidu AI Cloud — Beijing","lat":39.9,"lon":116.4,"operator":"Baidu","tip":"🖥 AI DATA CENTER | Baidu Beijing | Ernie Bot | State-backed AI"},
    {"name":"Alibaba Cloud — Hangzhou","lat":30.27,"lon":120.15,"operator":"Alibaba","tip":"🖥 AI DATA CENTER | Alibaba Hangzhou | Qwen AI | China Tier-1"},
    {"name":"xAI — Memphis","lat":35.14,"lon":-90.05,"operator":"xAI/Tesla","tip":"🖥 AI DATA CENTER | xAI Memphis | Elon Musk | Colossus supercluster 200k H100"},
    {"name":"AWS — Singapore","lat":1.35,"lon":103.82,"operator":"Amazon","tip":"🖥 AI DATA CENTER | AWS Singapore | Amazon | APAC hub | Strict data laws"},
    {"name":"UAE AI Campus","lat":24.45,"lon":54.38,"operator":"G42/Microsoft","tip":"🖥 AI DATA CENTER | UAE AI | G42+Microsoft | $1.5B investment | MENA hub"},
]

MILITARY_ACTIVITY = [
    {"name":"USS Eisenhower CSG","type":"Carrier Strike Group","lat":35.5,"lon":32.0,"country":"USA","tip":"✈ MIL ACTIVITY | USS Eisenhower CSG | USA | E. Mediterranean | Surge posture"},
    {"name":"USS Gerald Ford","type":"Carrier Strike Group","lat":37.0,"lon":15.0,"country":"USA","tip":"✈ MIL ACTIVITY | USS Gerald Ford CSG | USA | Med | Redeployed Feb 2026"},
    {"name":"PLA PLAN Exercise","type":"Naval Exercise","lat":24.0,"lon":122.0,"country":"China","tip":"✈ MIL ACTIVITY | PLA PLAN | China | Taiwan Strait exercise | Elevated"},
    {"name":"NATO Air Policing","type":"Air Patrol","lat":56.0,"lon":24.0,"country":"NATO","tip":"✈ MIL ACTIVITY | NATO Air Policing | Baltic States | F-35/Typhoon CAP"},
    {"name":"Israeli Air Operations","type":"Strike Package","lat":33.0,"lon":44.0,"country":"Israel","tip":"✈ MIL ACTIVITY | IDF Air Ops | Israel | Iran strikes ongoing"},
    {"name":"IRGC Missile Posture","type":"Missile Alert","lat":32.0,"lon":50.0,"country":"Iran","tip":"✈ MIL ACTIVITY | IRGC | Iran | Elevated launch posture | Ballistic"},
    {"name":"Russian VKS Ukraine","type":"Air Strike Ops","lat":51.5,"lon":31.0,"country":"Russia","tip":"✈ MIL ACTIVITY | Russian VKS | Kalibr/Iskander ops | Ukraine"},
    {"name":"Houthi Naval/Drone","type":"Anti-Ship Ops","lat":14.5,"lon":43.5,"country":"Yemen/Houthi","tip":"✈ MIL ACTIVITY | Houthi | Red Sea | Anti-ship drone/missile ops"},
    {"name":"DPRK KN-25 Posture","type":"Artillery Alert","lat":39.0,"lon":125.5,"country":"DPRK","tip":"✈ MIL ACTIVITY | DPRK | KN-25 MLRS posture | Near DMZ"},
    {"name":"PLAAF Taiwan ADIZ","type":"Air Incursion","lat":22.0,"lon":120.5,"country":"China","tip":"✈ MIL ACTIVITY | PLA Air | Taiwan ADIZ | J-16/H-6K sorties"},
]

SHIP_TRAFFIC_ZONES = [
    # Each entry has a "path" list of [lon, lat] waypoints for PathLayer rendering
    {"name":"Strait of Malacca","lat":3.0,"lon":101.0,"traffic":"Extreme","vessels_day":300,
     "path":[[102.8,1.2],[101.5,2.5],[100.3,3.8],[99.5,5.5]],
     "tip":"🚢 SHIP TRAFFIC | Strait of Malacca | 300+ vessels/day | 25% global trade"},
    {"name":"Strait of Hormuz","lat":26.56,"lon":56.26,"traffic":"Critical/Reduced","vessels_day":21,
     "path":[[56.0,24.5],[56.26,25.8],[56.7,26.56],[57.8,27.2]],
     "tip":"🚢 SHIP TRAFFIC | Hormuz | ~21 tankers/day | 20% global oil | DISRUPTED"},
    {"name":"Suez Canal","lat":30.42,"lon":32.35,"traffic":"Reduced","vessels_day":44,
     "path":[[32.55,30.9],[32.4,30.42],[32.2,29.9],[32.6,29.2],[32.55,28.0]],
     "tip":"🚢 SHIP TRAFFIC | Suez Canal | ~44 ships/day | Down 35% vs baseline"},
    {"name":"Bab el-Mandeb","lat":12.58,"lon":43.38,"traffic":"Critical/Disrupted","vessels_day":32,
     "path":[[43.0,11.5],[43.38,12.58],[43.6,13.5],[44.0,14.5]],
     "tip":"🚢 SHIP TRAFFIC | Bab el-Mandeb | Houthi attacks | 32 vessels/day"},
    {"name":"English Channel","lat":51.0,"lon":1.5,"traffic":"Heavy","vessels_day":500,
     "path":[[-5.5,48.0],[-2.0,49.5],[1.5,51.0],[3.5,51.5],[7.0,52.8]],
     "tip":"🚢 SHIP TRAFFIC | English Channel | World's busiest sea lane | 500+/day"},
    {"name":"Cape of Good Hope Reroute","lat":-34.36,"lon":18.48,"traffic":"Increasing","vessels_day":85,
     "path":[[10.0,-31.0],[18.48,-34.36],[25.0,-33.5],[30.0,-28.0]],
     "tip":"🚢 SHIP TRAFFIC | Cape of Good Hope | +65% vs 2023 | Suez rerouting"},
    {"name":"Taiwan Strait","lat":24.5,"lon":119.5,"traffic":"Monitored","vessels_day":180,
     "path":[[121.5,22.0],[120.5,23.5],[119.5,24.5],[119.0,26.0],[120.0,28.0]],
     "tip":"🚢 SHIP TRAFFIC | Taiwan Strait | 180/day | PLA exercise risk"},
    {"name":"Kerch Strait","lat":45.35,"lon":36.62,"traffic":"Blocked","vessels_day":3,
     "path":[[35.8,44.8],[36.3,45.0],[36.62,45.35],[37.0,45.6]],
     "tip":"🚢 SHIP TRAFFIC | Kerch | Near-blocked | War zone"},
    {"name":"Singapore / Malacca Gateway","lat":1.25,"lon":103.7,"traffic":"Extreme","vessels_day":1000,
     "path":[[103.5,1.0],[103.7,1.25],[104.0,1.5],[104.5,2.0]],
     "tip":"🚢 SHIP TRAFFIC | Singapore | World's 2nd busiest port | 1000+ vessels"},
    {"name":"Panama Canal","lat":8.97,"lon":-79.53,"traffic":"Reduced","vessels_day":28,
     "path":[[-79.9,8.4],[-79.53,8.97],[-79.2,9.3]],
     "tip":"🚢 SHIP TRAFFIC | Panama Canal | 28/day | Drought reducing capacity 2024"},
    {"name":"Black Sea Western Entry","lat":43.2,"lon":30.5,"traffic":"Reduced","vessels_day":18,
     "path":[[28.0,41.8],[30.0,42.5],[31.5,43.0],[33.0,44.2]],
     "tip":"🚢 SHIP TRAFFIC | Black Sea W Entry | Turkish Straits | Reduced war traffic"},
    {"name":"Lombok / Sunda Strait Alt","lat":-8.5,"lon":115.87,"traffic":"Normal","vessels_day":40,
     "path":[[113.5,-8.0],[115.87,-8.5],[116.5,-8.7]],
     "tip":"🚢 SHIP TRAFFIC | Lombok Strait | Indonesia | Malacca alternate route"},
]

TRADE_ROUTE_ARCS = [
    # Multi-waypoint paths — each "path" is [[lon, lat], ...] for PathLayer
    {"name":"Asia-Europe via Suez","from_lat":1.35,"from_lon":103.8,"to_lat":51.5,"to_lon":-0.1,
     "type":"Container","status":"Rerouted",
     "path":[[103.8,1.35],[99.5,3.5],[87.0,7.0],[72.8,18.9],[56.26,12.5],[43.38,12.58],[32.4,30.42],[29.9,31.2],[12.5,37.5],[-0.1,51.5]],
     "tip":"⚓ TRADE | Asia→Europe via Suez | REROUTED — Houthi disruption | Container"},
    {"name":"Cape of Good Hope Reroute","from_lat":1.35,"from_lon":103.8,"to_lat":51.5,"to_lon":-0.1,
     "type":"Container","status":"Active",
     "path":[[103.8,1.35],[99.0,2.0],[87.0,-2.0],[70.0,-12.0],[50.0,-20.0],[35.0,-26.0],[18.48,-34.36],[0.0,-32.0],[-12.0,-25.0],[-10.0,-3.0],[-9.0,15.0],[-9.5,35.0],[-0.1,51.5]],
     "tip":"⚓ TRADE | Cape Reroute | Asia→Europe avoiding Red Sea | +$1500/container | Container"},
    {"name":"Trans-Pacific (Asia→USA)","from_lat":31.23,"from_lon":121.47,"to_lat":33.74,"to_lon":-118.2,
     "type":"Container","status":"Active",
     "path":[[121.47,31.23],[135.0,34.0],[150.0,38.0],[165.0,40.0],[180.0,40.5],[-165.0,38.0],[-150.0,35.0],[-130.0,34.5],[-118.2,33.74]],
     "tip":"⚓ TRADE | Trans-Pacific | Shanghai→LA | 14-16 days | Container"},
    {"name":"N. Atlantic (USA→Europe)","from_lat":40.71,"from_lon":-74.0,"to_lat":51.5,"to_lon":-0.1,
     "type":"Container","status":"Active",
     "path":[[-74.0,40.71],[-60.0,43.0],[-45.0,46.0],[-30.0,48.0],[-15.0,50.0],[-0.1,51.5]],
     "tip":"⚓ TRADE | N. Atlantic | New York→London | 7-8 days | Container"},
    {"name":"ME Oil to Asia","from_lat":26.56,"from_lon":56.26,"to_lat":35.68,"to_lon":139.69,
     "type":"Oil Tanker","status":"Disrupted",
     "path":[[56.26,26.56],[65.0,22.0],[72.8,18.9],[80.0,12.0],[87.0,5.0],[100.5,3.5],[103.8,1.35],[115.0,10.0],[120.0,20.0],[126.0,28.0],[130.0,32.5],[135.0,34.5],[139.69,35.68]],
     "tip":"⚓ TRADE | ME Oil→Asia | DISRUPTED Hormuz | Tanker | 20% global oil"},
    {"name":"West Africa Oil to USA","from_lat":6.45,"from_lon":3.4,"to_lat":40.71,"to_lon":-74.0,
     "type":"Oil Tanker","status":"Active",
     "path":[[3.4,6.45],[-5.0,5.0],[-15.0,8.0],[-25.0,12.0],[-40.0,18.0],[-55.0,25.0],[-65.0,32.0],[-74.0,40.71]],
     "tip":"⚓ TRADE | W. Africa Oil→USA | Nigeria/Angola→Gulf Coast | Oil Tanker"},
    {"name":"Australia-China Iron Ore","from_lat":-31.95,"from_lon":115.86,"to_lat":31.23,"to_lon":121.47,
     "type":"Bulk","status":"Active",
     "path":[[115.86,-31.95],[118.0,-25.0],[118.0,-15.0],[118.0,-5.0],[115.0,5.0],[115.0,12.0],[118.0,20.0],[120.0,26.0],[121.47,31.23]],
     "tip":"⚓ TRADE | Australia→China | Iron ore/coal | 700Mt/yr | Bulk"},
    {"name":"Russia-China Energy Corridor","from_lat":55.75,"from_lon":37.61,"to_lat":39.9,"to_lon":116.39,
     "type":"Oil Tanker","status":"Active",
     "path":[[37.61,55.75],[55.0,52.0],[65.0,54.0],[80.0,55.0],[100.0,50.0],[110.0,45.0],[116.39,39.9]],
     "tip":"⚓ TRADE | Russia→China Energy | Power of Siberia 2 | War sanctions bypass | Oil Tanker"},
]

GPS_JAMMING_ZONES = [
    {"name":"Eastern Baltic","lat":57.0,"lon":24.0,"radius_km":400,"source":"Russia","severity":"High","tip":"📡 GPS JAMMING | Eastern Baltic | Russia | GNSS spoofing confirmed | Aviation alerts"},
    {"name":"Eastern Mediterranean","lat":35.0,"lon":34.0,"radius_km":350,"source":"Multiple","severity":"High","tip":"📡 GPS JAMMING | E. Mediterranean | Israel/Turkey ops | FAA NOTAM active"},
    {"name":"Black Sea","lat":44.5,"lon":33.0,"radius_km":300,"source":"Russia","severity":"High","tip":"📡 GPS JAMMING | Black Sea | Russia | Persistent spoofing since 2022"},
    {"name":"Finnish-Russian Border","lat":61.5,"lon":28.5,"radius_km":200,"source":"Russia","severity":"Med","tip":"📡 GPS JAMMING | Finland border | Russia | Intermittent jamming"},
    {"name":"Syrian Airspace","lat":35.0,"lon":38.0,"radius_km":250,"source":"Russia/Syria","severity":"High","tip":"📡 GPS JAMMING | Syria | Russia | Persistent | Affects Lebanon/Cyprus"},
    {"name":"Iran Airspace","lat":32.5,"lon":51.0,"radius_km":500,"source":"Iran","severity":"High","tip":"📡 GPS JAMMING | Iran | IRGC | Widespread spoofing | Conflict-driven"},
    {"name":"South China Sea","lat":12.0,"lon":114.0,"radius_km":600,"source":"China","severity":"Med","tip":"📡 GPS JAMMING | SCS | China | Intermittent near artificial islands"},
    {"name":"Korean Peninsula","lat":38.0,"lon":127.0,"radius_km":300,"source":"DPRK","severity":"High","tip":"📡 GPS JAMMING | Korean Peninsula | DPRK | Chronic interference"},
]

ORBITAL_SURVEILLANCE = [
    {"name":"Keyhole KH-13 (NRO)","lat":0.0,"lon":-60.0,"operator":"USA/NRO","type":"Optical IMINT","tip":"🛰 ORBITAL | KH-13 | USA NRO | Sub-20cm resolution optical IMINT"},
    {"name":"Lacrosse SAR Cluster","lat":0.0,"lon":30.0,"operator":"USA/NRO","type":"SAR","tip":"🛰 ORBITAL | Lacrosse SAR | USA | All-weather radar imaging"},
    {"name":"Yaogan-41","lat":0.0,"lon":80.0,"operator":"China PLA","type":"ELINT/IMINT","tip":"🛰 ORBITAL | Yaogan-41 | China PLA | ELINT + optical cluster"},
    {"name":"Cosmos-2558","lat":0.0,"lon":160.0,"operator":"Russia GRU","type":"Inspector","tip":"🛰 ORBITAL | Cosmos-2558 | Russia | Shadowing US satellites"},
    {"name":"Planet Labs Constellation","lat":0.0,"lon":-120.0,"operator":"Commercial","type":"Commercial IMINT","tip":"🛰 ORBITAL | Planet Labs | 200+ Doves | Daily global coverage"},
    {"name":"Maxar WorldView-4","lat":0.0,"lon":-30.0,"operator":"Commercial","type":"Commercial IMINT","tip":"🛰 ORBITAL | Maxar WV-4 | 31cm resolution | Commercial"},
    {"name":"Starlink ISR","lat":0.0,"lon":100.0,"operator":"SpaceX/USA","type":"Comms/ISR","tip":"🛰 ORBITAL | Starlink ISR | SpaceX/DoD | Ukraine battlefield comms"},
    {"name":"Israeli Ofek-16","lat":0.0,"lon":50.0,"operator":"Israel/IAI","type":"SAR","tip":"🛰 ORBITAL | Ofek-16 | Israel | SAR satellite | Iran coverage"},
]

CII_INSTABILITY = [
    {"name":"Ukraine Power Grid","country":"Ukraine","lat":49.0,"lon":32.0,"sector":"Energy","risk":95,"tip":"🌎 CII | Ukraine Power Grid | Under attack | 95/100 instability"},
    {"name":"Sudan Internet/Telecom","country":"Sudan","lat":15.5,"lon":32.5,"sector":"Telecom","risk":88,"tip":"🌎 CII | Sudan Telecom | Conflict disruption | 88/100"},
    {"name":"Myanmar Banking","country":"Myanmar","lat":16.87,"lon":96.19,"sector":"Finance","risk":82,"tip":"🌎 CII | Myanmar Banking | Junta sanctions + conflict | 82/100"},
    {"name":"Iran Financial CII","country":"Iran","lat":35.69,"lon":51.39,"sector":"Finance","risk":80,"tip":"🌎 CII | Iran Financial | SWIFT exclusion + cyber attacks | 80/100"},
    {"name":"Gaza Telecom","country":"Palestine","lat":31.4,"lon":34.4,"sector":"Telecom","risk":98,"tip":"🌎 CII | Gaza Telecom | Nearly destroyed | 98/100"},
    {"name":"Haiti Institutions","country":"Haiti","lat":18.54,"lon":-72.34,"sector":"Government","risk":91,"tip":"🌎 CII | Haiti Gov | Gang control of infrastructure | 91/100"},
    {"name":"Venezuelan Grid","country":"Venezuela","lat":10.48,"lon":-66.87,"sector":"Energy","risk":78,"tip":"🌎 CII | Venezuela Grid | Chronic blackouts | 78/100"},
    {"name":"Pakistan Power Sector","country":"Pakistan","lat":33.73,"lon":73.09,"sector":"Energy","risk":68,"tip":"🌎 CII | Pakistan Energy | IMF crisis + grid failures | 68/100"},
]

DISPLACEMENT_FLOWS = [
    {"from_lat":31.4,"from_lon":34.4,"to_lat":30.06,"to_lon":31.24,"pop":1900000,"cause":"Gaza War","tip":"👥 DISPLACEMENT | Gaza → Egypt border | 1.9M displaced | Ongoing"},
    {"from_lat":50.45,"from_lon":30.52,"to_lat":52.23,"to_lon":21.01,"pop":6000000,"cause":"Ukraine War","tip":"👥 DISPLACEMENT | Ukraine → Poland/EU | 6M refugees | Ongoing"},
    {"from_lat":15.5,"from_lon":32.5,"to_lat":15.55,"to_lon":32.53,"pop":8100000,"cause":"Sudan Civil War","tip":"👥 DISPLACEMENT | Sudan internal | 8.1M IDP | World's largest"},
    {"from_lat":16.87,"from_lon":96.19,"to_lat":20.17,"to_lon":92.9,"pop":2600000,"cause":"Myanmar Coup","tip":"👥 DISPLACEMENT | Myanmar → Bangladesh/China | 2.6M IDP"},
    {"from_lat":12.0,"from_lon":43.0,"to_lat":11.55,"to_lon":43.15,"pop":1200000,"cause":"Yemen War","tip":"👥 DISPLACEMENT | Yemen → Djibouti/Horn | 1.2M fled"},
    {"from_lat":13.5,"from_lon":25.3,"to_lat":12.36,"to_lon":23.32,"pop":900000,"cause":"Darfur RSF","tip":"👥 DISPLACEMENT | Darfur → Chad | 900K fled since 2023"},
    {"from_lat":33.52,"from_lon":36.29,"to_lat":37.06,"to_lon":37.38,"pop":3000000,"cause":"Syria War (cumulative)","tip":"👥 DISPLACEMENT | Syria → Turkey | 3M in Turkey | Ongoing"},
]

CLIMATE_ANOMALIES = [
    {"name":"Extreme Arctic Warming","lat":80.0,"lon":0.0,"anomaly":"+4.2°C","type":"Temperature","tip":"🌫 CLIMATE | Arctic | +4.2°C anomaly | Record sea ice minimum 2026"},
    {"name":"Australian Coral Bleaching","lat":-18.0,"lon":147.0,"anomaly":"Mass bleaching","type":"Ocean","tip":"🌫 CLIMATE | Great Barrier Reef | 4th mass bleaching event | Critical"},
    {"name":"N.Africa Drought Belt","lat":15.0,"lon":10.0,"anomaly":"-45% rainfall","type":"Drought","tip":"🌫 CLIMATE | Sahel drought | -45% rainfall | 21M food insecure"},
    {"name":"S.Asia Heat Dome","lat":28.0,"lon":78.0,"anomaly":"+51°C max","type":"Heatwave","tip":"🌫 CLIMATE | South Asia | 51°C peak 2026 | Heat mortality elevated"},
    {"name":"Siberian Permafrost","lat":65.0,"lon":100.0,"anomaly":"Record thaw","type":"Permafrost","tip":"🌫 CLIMATE | Siberia | Permafrost thaw accelerating | Methane release"},
    {"name":"Amazon Dieback","lat":-5.0,"lon":-58.0,"anomaly":"Tipping point","type":"Ecosystem","tip":"🌫 CLIMATE | Amazon | Dieback threshold approached | CO2 source now"},
    {"name":"N.Atlantic SST Anomaly","lat":50.0,"lon":-30.0,"anomaly":"+2.1°C","type":"SST","tip":"🌫 CLIMATE | N.Atlantic | AMOC weakening signal | SST +2.1°C"},
]

WEATHER_ALERTS = [
    {"name":"Cyclone Hidaya","lat":-12.0,"lon":42.0,"type":"Cyclone","severity":"CAT 3","tip":"⛈ WEATHER ALERT | Cyclone Hidaya | CAT 3 | Mozambique Channel"},
    {"name":"Texas Drought","lat":31.0,"lon":-98.0,"type":"Drought","severity":"Exceptional","tip":"⛈ WEATHER ALERT | Texas | Exceptional drought | D4 classification"},
    {"name":"Pakistan Flood Watch","lat":29.0,"lon":70.0,"type":"Flood","severity":"High","tip":"⛈ WEATHER ALERT | Pakistan | Pre-monsoon flood risk | High"},
    {"name":"Arctic Storm Epsilon","lat":72.0,"lon":15.0,"type":"Storm","severity":"Severe","tip":"⛈ WEATHER ALERT | Arctic | Storm Epsilon | Barents Sea | Force 11"},
    {"name":"W.Africa Harmattan","lat":12.0,"lon":-2.0,"type":"Dust Storm","severity":"Moderate","tip":"⛈ WEATHER ALERT | W.Africa | Harmattan dust | Aviation impact"},
    {"name":"Bangladesh Flood","lat":24.0,"lon":90.0,"type":"Flood","severity":"High","tip":"⛈ WEATHER ALERT | Bangladesh | Flash flooding | 800k affected"},
]

INTERNET_OUTAGES = [
    {"name":"Gaza — Total Blackout","lat":31.4,"lon":34.4,"severity":"Total","cause":"Infrastructure destruction","tip":"📡 INTERNET OUTAGE | Gaza | TOTAL | Infrastructure destroyed | Conflict"},
    {"name":"Sudan — Partial","lat":15.5,"lon":32.5,"severity":"Partial","cause":"Conflict/Power","tip":"📡 INTERNET OUTAGE | Sudan | Partial | 40% connectivity loss | Conflict"},
    {"name":"Myanmar — Targeted Shutdown","lat":16.87,"lon":96.19,"severity":"Targeted","cause":"Junta censorship","tip":"📡 INTERNET OUTAGE | Myanmar | Junta-ordered shutdowns | Targeted"},
    {"name":"Iran — Throttled","lat":35.69,"lon":51.39,"severity":"Throttled","cause":"Government restriction","tip":"📡 INTERNET OUTAGE | Iran | Throttled 60% | Post-strike security"},
    {"name":"Russia — Selective Block","lat":55.75,"lon":37.61,"severity":"Selective","cause":"Censorship","tip":"📡 INTERNET OUTAGE | Russia | VPN blocks | Social media restricted"},
    {"name":"Ukraine — Disrupted","lat":50.45,"lon":30.52,"severity":"Disrupted","cause":"Missile strikes","tip":"📡 INTERNET OUTAGE | Ukraine | Post-strike disruptions | Recovering"},
]

CYBER_THREATS_GEO = [
    {"name":"APT29 — Russia","lat":55.75,"lon":37.61,"actor":"Russia/SVR","targets":"NATO/Ukraine Gov","tip":"🛡 CYBER THREAT | APT29 | Russia SVR | Active campaigns | NATO/Ukraine"},
    {"name":"APT41 — China","lat":39.9,"lon":116.4,"actor":"China MSS","targets":"SE Asia Defence/Tech","tip":"🛡 CYBER THREAT | APT41 | China MSS | SE Asia defence contractors"},
    {"name":"Lazarus Group — DPRK","lat":39.0,"lon":125.75,"actor":"DPRK RGB","targets":"Crypto/Finance Global","tip":"🛡 CYBER THREAT | Lazarus | DPRK | Crypto theft $1.7B 2025"},
    {"name":"IRGC Cyber — Iran","lat":35.69,"lon":51.39,"actor":"Iran IRGC","targets":"Israel/US Critical Infra","tip":"🛡 CYBER THREAT | IRGC Cyber | Iran | CII attacks | Wiper malware"},
    {"name":"Sandworm — GRU","lat":55.75,"lon":37.61,"actor":"Russia GRU","targets":"Ukraine Power/Telecom","tip":"🛡 CYBER THREAT | Sandworm | GRU | Ukraine grid attacks | Industroyer"},
    {"name":"Volt Typhoon — China","lat":39.9,"lon":116.39,"actor":"China PLA","targets":"US Military/Logistics","tip":"🛡 CYBER THREAT | Volt Typhoon | China | US mil logistics pre-positioning"},
]

ECONOMIC_CENTERS = [
    {"name":"New York","lat":40.71,"lon":-74.0,"gdp_t":2.0,"role":"Global Finance","tip":"💰 ECONOMIC | New York | NYSE/NASDAQ | $2T metro GDP | Global finance hub"},
    {"name":"London","lat":51.5,"lon":-0.1,"gdp_t":1.1,"role":"Finance/FX","tip":"💰 ECONOMIC | London | LME/LSE | FX market leader | $1.1T metro"},
    {"name":"Tokyo","lat":35.68,"lon":139.69,"gdp_t":1.5,"role":"Finance/Industry","tip":"💰 ECONOMIC | Tokyo | TSE | $1.5T | BOJ policy hub"},
    {"name":"Shanghai","lat":31.23,"lon":121.47,"gdp_t":0.7,"role":"Trade/Finance","tip":"💰 ECONOMIC | Shanghai | SSE | China's financial capital | Port #1"},
    {"name":"Hong Kong","lat":22.32,"lon":114.17,"gdp_t":0.36,"role":"Gateway","tip":"💰 ECONOMIC | Hong Kong | HKEx | China gateway | Autonomy eroded"},
    {"name":"Singapore","lat":1.35,"lon":103.82,"gdp_t":0.5,"role":"Trade/Finance","tip":"💰 ECONOMIC | Singapore | MAS | SE Asia hub | Oil trading centre"},
    {"name":"Dubai","lat":25.2,"lon":55.27,"gdp_t":0.38,"role":"Trade/Logistics","tip":"💰 ECONOMIC | Dubai | DIFC | ME financial hub | Logistics centre"},
    {"name":"Frankfurt","lat":50.11,"lon":8.68,"gdp_t":0.4,"role":"EU Finance","tip":"💰 ECONOMIC | Frankfurt | ECB/Deutsche Börse | EU financial capital"},
]

CRITICAL_MINERALS = [
    {"name":"DRC Cobalt Belt","lat":-10.5,"lon":25.5,"mineral":"Cobalt","share_pct":70,"tip":"💎 CRITICAL MINERAL | DRC Cobalt | 70% global supply | EV battery essential"},
    {"name":"Chile Lithium","lat":-23.6,"lon":-68.2,"mineral":"Lithium","share_pct":28,"tip":"💎 CRITICAL MINERAL | Atacama Chile | 28% global lithium | SQM/Codelco"},
    {"name":"China REE","lat":36.0,"lon":104.0,"mineral":"Rare Earth Elements","share_pct":60,"tip":"💎 CRITICAL MINERAL | China REE | 60% mining + 85% processing | Export controls"},
    {"name":"South Africa PGMs","lat":-25.7,"lon":27.1,"mineral":"Platinum Group","share_pct":75,"tip":"💎 CRITICAL MINERAL | S.Africa PGM | 75% global platinum | Autocatalysts"},
    {"name":"Indonesia Nickel","lat":-3.5,"lon":120.0,"mineral":"Nickel","share_pct":37,"tip":"💎 CRITICAL MINERAL | Indonesia | 37% global nickel | EV battery cathodes"},
    {"name":"Kazakhstan Uranium","lat":47.0,"lon":67.0,"mineral":"Uranium","share_pct":43,"tip":"💎 CRITICAL MINERAL | Kazakhstan | 43% global uranium | Nuclear fuel"},
    {"name":"Guinea Bauxite","lat":11.0,"lon":-10.7,"mineral":"Bauxite","share_pct":25,"tip":"💎 CRITICAL MINERAL | Guinea | 25% bauxite | Aluminium feedstock"},
    {"name":"Bolivia Lithium","lat":-20.1,"lon":-67.6,"mineral":"Lithium","share_pct":21,"tip":"💎 CRITICAL MINERAL | Bolivia Salar | 21% Li reserves | Underdeveloped"},
    {"name":"Australia Lithium","lat":-28.0,"lon":122.0,"mineral":"Lithium","share_pct":46,"tip":"💎 CRITICAL MINERAL | Pilbara Australia | 46% mined lithium | Spodumene"},
    {"name":"W.Africa Manganese","lat":5.5,"lon":-3.5,"mineral":"Manganese","share_pct":18,"tip":"💎 CRITICAL MINERAL | W.Africa Mn | Battery steel production"},
]

STRATEGIC_WATERWAYS = [
    {"name":"Strait of Hormuz","lat":26.56,"lon":56.26,"status":"red",
     "path":[[55.0,24.5],[55.8,25.5],[56.26,26.56],[57.2,27.0]],
     "tip":"⚓ STRATEGIC WATERWAY | Hormuz | 20% global oil | DISRUPTED | Iran-Israel war"},
    {"name":"Suez Canal","lat":30.42,"lon":32.35,"status":"amber",
     "path":[[32.55,31.2],[32.4,30.42],[32.3,29.5],[32.55,28.2]],
     "tip":"⚓ STRATEGIC WATERWAY | Suez | 12% global trade | Reduced traffic"},
    {"name":"Bab el-Mandeb","lat":12.58,"lon":43.38,"status":"red",
     "path":[[43.1,11.2],[43.38,12.58],[43.7,13.8]],
     "tip":"⚓ STRATEGIC WATERWAY | Bab el-Mandeb | Houthi zone | 9% global trade"},
    {"name":"Strait of Malacca","lat":3.0,"lon":101.0,"status":"green",
     "path":[[103.8,1.0],[102.0,2.5],[100.5,3.8],[99.5,5.5]],
     "tip":"⚓ STRATEGIC WATERWAY | Malacca | 25% global trade | Normal"},
    {"name":"Panama Canal","lat":8.97,"lon":-79.53,"status":"amber",
     "path":[[-79.95,8.3],[-79.53,8.97],[-79.1,9.35]],
     "tip":"⚓ STRATEGIC WATERWAY | Panama | Drought capacity − 30% | 3-5% global trade"},
    {"name":"Danish Straits","lat":57.44,"lon":10.0,"status":"green",
     "path":[[9.8,56.0],[10.0,57.44],[10.5,58.5]],
     "tip":"⚓ STRATEGIC WATERWAY | Danish Straits | Baltic access | NATO monitored"},
    {"name":"Kerch Strait","lat":45.35,"lon":36.62,"status":"red",
     "path":[[36.0,44.9],[36.62,45.35],[37.1,45.7]],
     "tip":"⚓ STRATEGIC WATERWAY | Kerch | Russian control | Near-blocked | War zone"},
    {"name":"Lombok Strait","lat":-8.5,"lon":115.87,"status":"green",
     "path":[[115.0,-8.1],[115.87,-8.5],[116.5,-8.9]],
     "tip":"⚓ STRATEGIC WATERWAY | Lombok | Indonesia | Malacca alternate"},
    {"name":"Taiwan / Formosa Strait","lat":24.5,"lon":119.5,"status":"amber",
     "path":[[121.8,22.0],[120.5,23.5],[119.5,24.5],[119.0,26.0]],
     "tip":"⚓ STRATEGIC WATERWAY | Formosa | PLA tensions | Semiconductor supply risk"},
    {"name":"Mozambique Channel","lat":-18.0,"lon":41.0,"status":"green",
     "path":[[34.5,-12.0],[36.0,-15.0],[41.0,-18.0],[43.5,-20.5]],
     "tip":"⚓ STRATEGIC WATERWAY | Mozambique Channel | LNG export route | East Africa"},
    {"name":"Turkish Straits (Bosphorus)","lat":41.1,"lon":29.05,"status":"amber",
     "path":[[28.97,40.9],[29.05,41.1],[29.1,41.4]],
     "tip":"⚓ STRATEGIC WATERWAY | Bosphorus | Black Sea access | Montreux Convention"},
    {"name":"Gibraltar Strait","lat":35.97,"lon":-5.45,"status":"green",
     "path":[[-6.0,35.8],[-5.45,35.97],[-4.8,36.2]],
     "tip":"⚓ STRATEGIC WATERWAY | Gibraltar | Atlantic-Med gateway | UK/Spain sovereign"},
]

def build_global_map(eq_df, eonet_df, show_seis, show_volc, show_mvmt, show_conf, show_supply, show_heat,
                      show_hist=False, show_live=False,
                      show_intel=False, show_czones=False, show_mbases=False, show_nuclear=False,
                      show_gamma=False, show_space=False, show_cables=False, show_pipes=False,
                      show_aidc=False, show_milact=False, show_ships=False, show_trade=False,
                      show_gps=False, show_orbital=False, show_cii=False, show_displaced=False,
                      show_climate=False, show_weather=False, show_outages=False, show_cyber=False,
                      show_econ=False, show_minerals=False, show_waterways=False, show_fires_layer=False,
                      show_protests=False, show_aviation=False,
                      show_ais=False, show_opensky=False, show_acled=False):
    layers = []

    _layer_id_counter = [0]

    def _scatter(data_list, col, radius, id_field="name", layer_id=None):
        if not data_list: return
        df = pd.DataFrame(data_list)
        if "lat" not in df.columns or "lon" not in df.columns: return
        df["_color"]  = [col]*len(df)
        df["_radius"] = radius
        if "tip" not in df.columns:
            df["tip"] = df.get(id_field, pd.Series([""] * len(df))).astype(str)
        _layer_id_counter[0] += 1
        lid = layer_id or f"scatter_{_layer_id_counter[0]}"
        layers.append(pdk.Layer("ScatterplotLayer", data=df, id=lid,
                                 get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color",
                                 get_line_color=[255,255,255,20], line_width_min_pixels=1,
                                 pickable=True, auto_highlight=True))

    def _icon_scatter(data_list, col, radius, layer_id=None):
        if not data_list: return
        df = pd.DataFrame(data_list)
        if "lat" not in df.columns or "lon" not in df.columns: return
        df["_color"]  = [col]*len(df)
        df["_radius"] = radius
        if "tip" not in df.columns:
            df["tip"] = df.get("name", pd.Series([""] * len(df))).astype(str)
        _layer_id_counter[0] += 1
        lid = layer_id or f"icon_{_layer_id_counter[0]}"
        layers.append(pdk.Layer("ScatterplotLayer", data=df, id=lid,
                                 get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color",
                                 pickable=True, auto_highlight=True))

    def _arc(data_list, color, width=2, layer_id=None):
        if not data_list: return
        df = pd.DataFrame(data_list)
        df["_color"] = [color]*len(df)
        if "tip" not in df.columns:
            df["tip"] = df.get("name", pd.Series([""] * len(df))).astype(str)
        _layer_id_counter[0] += 1
        lid = layer_id or f"arc_{_layer_id_counter[0]}"
        layers.append(pdk.Layer("ArcLayer", data=df, id=lid,
                                 get_source_position=["from_lon","from_lat"],
                                 get_target_position=["to_lon","to_lat"],
                                 get_source_color="_color", get_target_color="_color",
                                 get_width=width, pickable=True, auto_highlight=True))

    # ── Original layers ──────────────────────────────────────────
    if show_seis and not eq_df.empty:
        ep = eq_df.copy()
        ep["_color"]  = ep["mag"].apply(lambda m: [255,55,85,220] if m>=5.5 else [255,180,0,200] if m>=4.5 else [0,230,118,175] if m>=3.5 else [0,200,255,150])
        ep["_radius"] = (ep["mag"]**2.3 * 15000).clip(10000, 240000)
        ep["tip"]     = ep.apply(lambda r: f"\U0001f30d SEISMIC  M" + str(r['mag']) + "\n" + str(r['place']) + "\nDepth: " + str(r['depth_km']) + " km  |  " + str(r['time']), axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=ep, id="seismic",
                                 get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color",
                                 get_line_color=[255,255,255,30], line_width_min_pixels=1,
                                 pickable=True, auto_highlight=True))

    if show_volc and not eonet_df.empty:
        eo = eonet_df.copy(); eo["_color"] = [[255,110,40,200]]*len(eo); eo["_radius"] = 70000
        eo["tip"] = eo.apply(lambda r: f"🌋 EONET EVENT\n{r['title']}\nCategory: {r.get('cat','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=eo, id="eonet",
                                 get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_conf:
        rows = []
        for cname, c in CONFLICTS.items():
            for inc in c["incidents"]: rows.append({**inc, "conflict": cname})
        if rows:
            cdf = pd.DataFrame(rows); sc = _sev_colors()
            cdf["_color"]  = cdf["severity"].map(sc)
            cdf["_radius"] = cdf["severity"].map({"CRITICAL":100000,"HIGH":75000,"MED":55000,"LOW":40000,"INFO":30000})
            cdf["tip"]     = cdf.apply(lambda r: f"{r['conflict']}\n{INCIDENT_ICONS.get(r['type'],'●')} {r['title']}\n{r['loc']} · {r['date']}\nSeverity: {r['severity']} · Casualties: {r['casualties']}", axis=1)
            layers.append(pdk.Layer("ScatterplotLayer", data=cdf, id="conflicts",
                                     get_position=["lon","lat"],
                                     get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_mvmt:
        mdf = pd.DataFrame(MOVEMENTS)
        mdf["_color"]  = mdf["sentiment"].map({"CRIT":[200,60,255,200],"HIGH":[157,110,255,185],"MED":[120,80,220,165]})
        mdf["_radius"] = mdf["scale"] * 1800
        mdf["tip"]     = mdf.apply(lambda r: f"📢 CIVIL MOVEMENT\n{r['title']}\n{r['location']}\nSize: {r['size']} · Sentiment: {r['sentiment']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=mdf, id="movements",
                                 get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_supply:
        arc_rows = []
        for c in CONFLICTS.values(): arc_rows.extend(c["supply_lines"])
        if arc_rows:
            adf = pd.DataFrame(arc_rows)
            cmap = {"Military Aid":[255,61,90,160],"Arms/Funding":[255,61,90,160],
                    "RSF Support":[255,140,66,140],"SAF Support":[0,200,255,140],
                    "Junta Support":[255,61,90,140],"Arms Supply":[255,180,0,140],"Humanitarian":[0,230,118,150]}
            adf["_color"] = adf["type"].apply(lambda t: cmap.get(t,[74,107,133,120]))
            adf["tip"]   = adf.apply(lambda r: f"⟶ SUPPLY LINE\n{r['type']}\nProvider: {r['provider']}", axis=1)
            layers.append(pdk.Layer("ArcLayer", data=adf,
                                     get_source_position=["from_lon","from_lat"],
                                     get_target_position=["to_lon","to_lat"],
                                     get_source_color="_color", get_target_color="_color",
                                     get_width=2, pickable=True, auto_highlight=True))

    if show_heat and not eq_df.empty:
        # HeatmapLayer: pickable=False so hover never returns an object without tip
        layers.append(pdk.Layer("HeatmapLayer",
                                 data=eq_df[["lat","lon","mag"]].rename(columns={"mag":"weight"}),
                                 get_position=["lon","lat"], get_weight="weight",
                                 radiusPixels=50, opacity=0.45, pickable=False))

    # ── Historical Events layer (2022–present) ──────────────────
    if show_hist and HISTORICAL_EVENTS:
        hdf = pd.DataFrame(HISTORICAL_EVENTS)
        hdf["_color"] = hdf["severity"].apply(lambda s: HIST_SEV_COLORS.get(s, [157,110,255,170]))
        hdf["_radius"] = hdf["severity"].apply(lambda s: 90000 if s=="CRITICAL" else 70000 if s=="HIGH" else 55000 if s=="MED" else 40000)
        layers.append(pdk.Layer("ScatterplotLayer", data=hdf, id="historical",
                                 get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color",
                                 get_line_color=[255,255,255,30], line_width_min_pixels=1,
                                 pickable=True, auto_highlight=True))

    # ── Live Events layer (GDELT last 1h — lat/lon approximated from source) ─
    if show_live:
        live_arts = fetch_live_global_events(max_records=20)
        if live_arts:
            # Map to approximate coordinates using known news source locations
            # When GDELT doesn't provide coords, we distribute around conflict hotspots
            import random
            rng2 = random.Random(42)
            live_pts = []
            hotspot_coords = [
                (32.08,34.78),(50.45,30.52),(31.4,34.47),(35.69,51.39),
                (15.55,32.53),(16.87,96.19),(14.5,43.5),(39.9,116.4),(38.9,-77.0),
            ]
            for i, art in enumerate(live_arts):
                base_lat, base_lon = hotspot_coords[i % len(hotspot_coords)]
                live_pts.append({
                    "lat":   base_lat + rng2.uniform(-2, 2),
                    "lon":   base_lon + rng2.uniform(-2, 2),
                    "tip":   f"⚡ LIVE EVENT\n{art['source'].upper()}\n{art['title']}\n{art['time']}",
                    "_color": [0, 255, 200, 200],
                    "_radius": 60000,
                })
            live_df = pd.DataFrame(live_pts)
            layers.append(pdk.Layer("ScatterplotLayer", data=live_df, id="live_events",
                                     get_position=["lon","lat"],
                                     get_radius="_radius", get_fill_color="_color",
                                     get_line_color=[0,255,200,80], line_width_min_pixels=1,
                                     pickable=True, auto_highlight=True))

    # ── New layers ───────────────────────────────────────────────
    if show_intel:
        _scatter(INTEL_HOTSPOTS, [255,200,0,210], 90000)

    if show_czones:
        _scatter(CONFLICT_ZONES, [255,30,60,200], 110000)

    if show_mbases:
        base_df = pd.DataFrame(MILITARY_BASES)
        base_df["_color"] = base_df["country"].apply(lambda c:
            [0,200,255,200] if "USA" in c or "US" in c
            else [255,61,90,200] if "Russia" in c
            else [255,200,0,200] if "China" in c
            else [0,230,118,200] if any(x in c for x in ["UK","NATO","Israel","India","Japan","Singapore","S.Korea"])
            else [157,110,255,180])
        base_df["_radius"] = 55000
        if "tip" not in base_df.columns:
            base_df["tip"] = base_df.apply(lambda r: f"🏛 MILITARY BASE\n{r['name']}\n{r.get('country','')} · {r.get('type','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=base_df, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_nuclear:
        ndf = pd.DataFrame(NUCLEAR_SITES)
        ndf["_color"] = ndf["status"].apply(lambda s:
            [255,30,60,230] if s in ("Struck","Destroyed","Occupied")
            else [255,180,0,200] if s in ("Active","Operational")
            else [157,110,255,180])
        ndf["_radius"] = 70000
        if "tip" not in ndf.columns:
            ndf["tip"] = ndf.apply(lambda r: f"☢ NUCLEAR SITE\n{r['name']}\n{r.get('country','')} · {r.get('type','')}\nStatus: {r.get('status','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=ndf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_gamma:
        _scatter(GAMMA_IRRADIATORS, [255,165,0,180], 40000)

    if show_space:
        sdf = pd.DataFrame(SPACEPORTS)
        sdf["_color"] = sdf["type"].apply(lambda t: [0,200,255,210] if t=="Launch" else [255,61,90,200])
        sdf["_radius"] = 60000
        if "tip" not in sdf.columns:
            sdf["tip"] = sdf.apply(lambda r: f"🚀 SPACEPORT\n{r['name']}\n{r.get('country','')} · {r.get('type','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=sdf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_cables:
        cab_data = []
        status_colors = {"Cut":[255,30,60,200],"Degraded":[255,140,66,180],"Active":[0,200,255,140]}
        for c in UNDERSEA_CABLES:
            col = status_colors.get(c["status"],[74,107,133,120])
            cab_data.append({**c,"_color":col,"from_lat":c["from_lat"],"from_lon":c["from_lon"],"to_lat":c["to_lat"],"to_lon":c["to_lon"]})
        if cab_data:
            cdf2 = pd.DataFrame(cab_data)
            if "tip" not in cdf2.columns:
                cdf2["tip"] = cdf2.apply(lambda r: f"🔌 UNDERSEA CABLE\n{r.get('name','')}\nStatus: {r.get('status','')} · Risk: {r.get('risk','')}/100", axis=1)
            layers.append(pdk.Layer("ArcLayer", data=cdf2,
                                     get_source_position=["from_lon","from_lat"],
                                     get_target_position=["to_lon","to_lat"],
                                     get_source_color="_color", get_target_color="_color",
                                     get_width=2, pickable=True, auto_highlight=True))

    if show_pipes:
        pip_colors = {"Sabotaged":[255,30,60,200],"Disrupted":[255,61,90,180],"Suspended":[255,140,66,170],"Reduced":[255,180,0,160],"Active":[0,200,255,120],"Under Construction":[157,110,255,150]}
        pip_data = []
        for p in PIPELINES:
            col = pip_colors.get(p["status"],[74,107,133,100])
            pip_data.append({**p,"_color":col})
        if pip_data:
            pdf2 = pd.DataFrame(pip_data)
            if "tip" not in pdf2.columns:
                pdf2["tip"] = pdf2.apply(lambda r: f"🛢 PIPELINE\n{r.get('name','')}\nStatus: {r.get('status','')} · Risk: {r.get('risk','')}/100", axis=1)
            layers.append(pdk.Layer("ArcLayer", data=pdf2,
                                     get_source_position=["from_lon","from_lat"],
                                     get_target_position=["to_lon","to_lat"],
                                     get_source_color="_color", get_target_color="_color",
                                     get_width=3, pickable=True, auto_highlight=True))

    if show_aidc:
        aidf = pd.DataFrame(AI_DATA_CENTERS)
        aidf["_color"] = aidf["operator"].apply(lambda o:
            [0,200,255,210] if any(x in o for x in ["Microsoft","Azure"])
            else [255,180,0,200] if any(x in o for x in ["Google","Meta","Anthropic","xAI"])
            else [157,110,255,200] if any(x in o for x in ["Amazon","AWS"])
            else [255,140,66,180])
        aidf["_radius"] = 45000
        if "tip" not in aidf.columns:
            aidf["tip"] = aidf.apply(lambda r: f"🖥 AI DATA CENTER\n{r['name']}\nOperator: {r.get('operator','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=aidf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_milact:
        madf = pd.DataFrame(MILITARY_ACTIVITY)
        madf["_color"] = madf["country"].apply(lambda c:
            [0,200,255,210] if "USA" in c
            else [255,30,60,210] if any(x in c for x in ["Russia","Iran","Houthi","DPRK","China"])
            else [0,230,118,190] if any(x in c for x in ["Israel","NATO","Japan"])
            else [255,180,0,190])
        madf["_radius"] = 80000
        if "tip" not in madf.columns:
            madf["tip"] = madf.apply(lambda r: f"✈ MILITARY ACTIVITY\n{r.get('activity','')} — {r.get('country','')}\nType: {r.get('type','')}\nSignals: {r.get('signals','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=madf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_ships:
        _ship_path_data = []
        for _z in SHIP_TRAFFIC_ZONES:
            if "path" not in _z:
                continue
            _t = _z["traffic"]
            _col = ([255,30,60,210] if "Blocked" in _t or "Disrupted" in _t
                    else [255,140,66,190] if "Reduced" in _t or "Critical" in _t
                    else [0,200,255,170] if "Extreme" in _t or "Heavy" in _t
                    else [0,230,118,150])
            _w = 4 if "Extreme" in _t or "Heavy" in _t else 3 if "Blocked" in _t or "Disrupted" in _t else 2
            _ship_path_data.append({
                "path": _z["path"], "_color": _col, "_width": _w,
                "tip": _z.get("tip", f"🚢 {_z['name']} | {_z['vessels_day']} vessels/day"),
            })
        if _ship_path_data:
            _spdf = pd.DataFrame(_ship_path_data)
            layers.append(pdk.Layer("PathLayer", data=_spdf,
                                     get_path="path", get_color="_color", get_width="_width",
                                     width_min_pixels=2, width_max_pixels=8,
                                     pickable=True, auto_highlight=True, id="ship_traffic"))

    if show_trade:
        _t_colors = {"Container":[0,200,255,150],"Oil Tanker":[255,140,66,170],"Bulk":[157,110,255,150]}
        _trade_path_data = []
        for _r in TRADE_ROUTE_ARCS:
            _col = _t_colors.get(_r.get("type",[]), [74,107,133,120])
            if _r.get("status") in ("Rerouted","Disrupted"): _col = [255,61,90,180]
            _w = 3 if _r.get("status") in ("Rerouted","Disrupted") else 2
            if "path" in _r:
                _trade_path_data.append({
                    "path": _r["path"], "_color": _col, "_width": _w,
                    "tip": _r.get("tip", f"⚓ TRADE | {_r.get('name','')} | {_r.get('type','')} | {_r.get('status','')}"),
                })
        if _trade_path_data:
            _tpdf = pd.DataFrame(_trade_path_data)
            layers.append(pdk.Layer("PathLayer", data=_tpdf,
                                     get_path="path", get_color="_color", get_width="_width",
                                     width_min_pixels=1, width_max_pixels=6,
                                     pickable=True, auto_highlight=True, id="trade_routes"))

    if show_gps:
        gdf = pd.DataFrame(GPS_JAMMING_ZONES)
        gdf["_color"] = gdf["severity"].apply(lambda s: [255,61,90,80] if s=="High" else [255,180,0,60])
        gdf["_radius"] = gdf["radius_km"] * 1000
        if "tip" not in gdf.columns:
            gdf["tip"] = gdf.apply(lambda r: f"📡 GPS JAMMING\n{r['name']}\nSource: {r.get('source','')}\nSeverity: {r.get('severity','')}\nRadius: {r.get('radius_km','')} km", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=gdf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True,
                                 stroked=True, get_line_color=[255,61,90,120], line_width_min_pixels=1))

    if show_orbital:
        # Orbital surveillance shown as equatorial ring markers
        odf = pd.DataFrame(ORBITAL_SURVEILLANCE)
        odf["_color"] = odf["operator"].apply(lambda o:
            [0,200,255,160] if "USA" in o or "Commercial" in o
            else [255,61,90,160] if "Russia" in o
            else [255,200,0,160] if "China" in o
            else [0,230,118,160])
        odf["_radius"] = 150000
        if "tip" not in odf.columns:
            odf["tip"] = odf.apply(lambda r: f"🛰 ORBITAL SURVEILLANCE\n{r['name']}\nOperator: {r.get('operator','')}\nType: {r.get('type','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=odf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_cii:
        cii_df = pd.DataFrame(CII_INSTABILITY)
        cii_df["_color"] = cii_df["risk"].apply(lambda r: [255,30,60,200] if r>=85 else [255,140,66,180] if r>=65 else [255,180,0,160])
        cii_df["_radius"] = cii_df["risk"] * 1200
        if "tip" not in cii_df.columns:
            cii_df["tip"] = cii_df.apply(lambda r: f"🌎 CII INSTABILITY\n{r['name']}\nCountry: {r.get('country','')}\nSector: {r.get('sector','')}\nRisk: {r.get('risk','')}/100", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=cii_df, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_displaced:
        disp_data = []
        for d in DISPLACEMENT_FLOWS:
            disp_data.append({**d,"_color":[200,60,255,150]})
        if disp_data:
            ddf2 = pd.DataFrame(disp_data)
            if "tip" not in ddf2.columns:
                ddf2["tip"] = ddf2.apply(lambda r: f"👥 DISPLACEMENT\n{r.get('cause','')}\n{r.get('pop',0):,} displaced", axis=1)
            layers.append(pdk.Layer("ArcLayer", data=ddf2,
                                     get_source_position=["from_lon","from_lat"],
                                     get_target_position=["to_lon","to_lat"],
                                     get_source_color=[200,60,255,150], get_target_color=[200,60,255,80],
                                     get_width=2, pickable=True, auto_highlight=True))

    if show_climate:
        cldf = pd.DataFrame(CLIMATE_ANOMALIES)
        cldf["_color"] = cldf["type"].apply(lambda t:
            [0,200,80,160] if t in ("Temperature","Permafrost","Ecosystem","SST")
            else [255,180,0,160] if t=="Drought"
            else [0,180,255,160] if t=="Ocean"
            else [255,100,30,160])
        cldf["_radius"] = 450000
        if "tip" not in cldf.columns:
            cldf["tip"] = cldf.apply(lambda r: f"🌫 CLIMATE ANOMALY\n{r['name']}\nAnomaly: {r.get('anomaly','')}\nType: {r.get('type','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=cldf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_weather:
        wdf = pd.DataFrame(WEATHER_ALERTS)
        wdf["_color"] = wdf["type"].apply(lambda t:
            [0,100,255,180] if t in ("Flood","Storm")
            else [255,140,66,180] if t=="Drought"
            else [255,200,50,180] if t=="Dust Storm"
            else [157,110,255,200])
        wdf["_radius"] = 300000
        if "tip" not in wdf.columns:
            wdf["tip"] = wdf.apply(lambda r: f"⛈ WEATHER ALERT\n{r['name']}\nType: {r.get('type','')} · Severity: {r.get('severity','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=wdf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_outages:
        odf2 = pd.DataFrame(INTERNET_OUTAGES)
        odf2["_color"] = odf2["severity"].apply(lambda s:
            [255,30,60,220] if s=="Total"
            else [255,140,66,190] if s in ("Partial","Disrupted")
            else [255,180,0,170])
        odf2["_radius"] = 80000
        if "tip" not in odf2.columns:
            odf2["tip"] = odf2.apply(lambda r: f"📡 INTERNET OUTAGE\n{r['name']}\nSeverity: {r.get('severity','')}\nCause: {r.get('cause','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=odf2, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_cyber:
        cydf = pd.DataFrame(CYBER_THREATS_GEO)
        cydf["_color"] = cydf["actor"].apply(lambda a:
            [255,30,60,200] if "Russia" in a
            else [255,200,0,200] if "China" in a
            else [157,110,255,200] if "DPRK" in a
            else [255,140,66,200])
        cydf["_radius"] = 120000
        if "tip" not in cydf.columns:
            cydf["tip"] = cydf.apply(lambda r: f"🛡 CYBER THREAT\n{r['name']}\nActor: {r.get('actor','')}\nTargets: {r.get('targets','')}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=cydf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_econ:
        edf = pd.DataFrame(ECONOMIC_CENTERS)
        edf["_color"] = edf["role"].apply(lambda r: [255,180,0,200] if "Finance" in r else [0,200,255,180])
        edf["_radius"] = edf["gdp_t"].apply(lambda g: max(int(g * 180000), 60000))
        if "tip" not in edf.columns:
            edf["tip"] = edf.apply(lambda r: f"💰 ECONOMIC CENTER\n{r['name']}\nRole: {r.get('role','')}\nGDP: ${r.get('gdp_t','')}T", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=edf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_minerals:
        mdf2 = pd.DataFrame(CRITICAL_MINERALS)
        min_colors = {"Cobalt":[0,200,255,200],"Lithium":[0,230,118,200],"Rare Earth Elements":[255,200,0,200],
                      "Platinum Group":[200,200,200,200],"Nickel":[157,110,255,200],"Uranium":[255,60,60,200],
                      "Bauxite":[255,140,66,200],"Manganese":[255,180,0,200]}
        mdf2["_color"] = mdf2["mineral"].apply(lambda m: min_colors.get(m,[74,107,133,180]))
        mdf2["_radius"] = mdf2["share_pct"].apply(lambda s: int(s * 8000))
        if "tip" not in mdf2.columns:
            mdf2["tip"] = mdf2.apply(lambda r: f"💎 CRITICAL MINERAL\n{r['name']}\nMineral: {r.get('mineral','')}\nGlobal share: {r.get('share_pct','')}%", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=mdf2, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_waterways:
        _wway_path_data = []
        _ww_status_col = {"red":[255,30,60,220],"amber":[255,180,0,200],"green":[0,200,255,180]}
        for _w in STRATEGIC_WATERWAYS:
            if "path" not in _w:
                continue
            _wc = _ww_status_col.get(_w.get("status","green"), [0,200,255,180])
            _wway_path_data.append({
                "path": _w["path"], "_color": _wc, "_width": 4,
                "tip": _w.get("tip", f"⚓ WATERWAY | {_w['name']}"),
            })
        if _wway_path_data:
            _wwdf = pd.DataFrame(_wway_path_data)
            layers.append(pdk.Layer("PathLayer", data=_wwdf,
                                     get_path="path", get_color="_color", get_width="_width",
                                     width_min_pixels=2, width_max_pixels=10,
                                     pickable=True, auto_highlight=True, id="waterways"))
    if show_fires_layer:
        fire_pts = [{"lat":r["lat"],"lon":r["lon"],"fires":r["fires"]} for r in [
            {"lat":49.0,"lon":32.0,"fires":2162},{"lat":32.0,"lon":51.0,"fires":485},
            {"lat":15.5,"lon":32.5,"fires":1240},{"lat":-5.0,"lon":-52.0,"fires":3820},
            {"lat":0.5,"lon":115.0,"fires":910},{"lat":-30.0,"lon":135.0,"fires":340},
            {"lat":37.5,"lon":-119.0,"fires":180},
        ]]
        fdf = pd.DataFrame(fire_pts)
        fdf["_color"] = [[255,80,20,200]]*len(fdf)
        fdf["_radius"] = fdf["fires"].apply(lambda f: min(int(f*80), 300000))
        fdf["tip"] = fdf.apply(lambda r: f"🔥 ACTIVE FIRES\nFires: {r['fires']:,}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=fdf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_protests:
        prot_df = pd.DataFrame(MOVEMENTS)
        prot_df["_color"] = [[200,60,255,180]]*len(prot_df)
        prot_df["_radius"] = prot_df["scale"] * 2000
        prot_df["tip"] = prot_df.apply(lambda r: f"📢 PROTEST\n{r['title']}\n{r['location']}\nSize: {r['size']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=prot_df, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_aviation:
        av_pts = [
            {"lat":51.5,"lon":-0.1,"name":"Heathrow — congestion"},{"lat":40.63,"lon":-73.78,"name":"JFK — normal"},
            {"lat":35.68,"lon":139.78,"name":"Narita — normal"},{"lat":1.35,"lon":103.99,"name":"Changi — normal"},
            {"lat":25.25,"lon":55.36,"name":"Dubai Int — normal"},{"lat":48.36,"lon":11.79,"name":"Munich — normal"},
            {"lat":33.94,"lon":-118.41,"name":"LAX — normal"},{"lat":22.31,"lon":113.92,"name":"HKG — reduced"},
            {"lat":32.08,"lon":34.88,"name":"Ben Gurion — CLOSED"},{"lat":35.69,"lon":51.32,"name":"IKA Tehran — CLOSED"},
            {"lat":33.52,"lon":36.52,"name":"Damascus — CLOSED"},{"lat":15.59,"lon":32.55,"name":"Khartoum — CLOSED"},
            {"lat":31.51,"lon":34.41,"name":"Gaza — DESTROYED"},
        ]
        avdf = pd.DataFrame(av_pts)
        avdf["_color"] = avdf["name"].apply(lambda n:
            [255,30,60,230] if "CLOSED" in n or "DESTROYED" in n
            else [255,180,0,190] if "congestion" in n or "reduced" in n
            else [0,200,255,160])
        avdf["_radius"] = avdf["name"].apply(lambda n: 70000 if "CLOSED" in n or "DESTROYED" in n else 45000)
        avdf["tip"] = avdf["name"].apply(lambda n: f"✈ AVIATION STATUS\n{n}")
        layers.append(pdk.Layer("ScatterplotLayer", data=avdf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    # ── Live AIS vessel positions ──────────────────────────────
    if show_ais:
        _ais_vessels = fetch_ais_vessels()
        if _ais_vessels:
            _ais_df = pd.DataFrame(_ais_vessels)
            _ais_df["_color"] = _ais_df["type"].apply(lambda t:
                [255, 60, 30, 220] if "Tanker" in str(t)
                else [255, 180, 0, 200] if "Military" in str(t)
                else [0, 200, 255, 150])
            _ais_df["_radius"] = 22000
            _ais_df["tip"] = _ais_df.apply(
                lambda r: f"🚢 AIS | {r.get('name','Unknown')} | "
                          f"Type: {r.get('type','')} | Speed: {r.get('speed',0)} kn",
                axis=1)
            layers.append(pdk.Layer("ScatterplotLayer", data=_ais_df, id="ais_vessels",
                get_position=["lon","lat"], get_radius="_radius",
                get_fill_color="_color", get_line_color=[255,255,255,20],
                line_width_min_pixels=1, pickable=True, auto_highlight=True))

    # ── Live OpenSky airspace ───────────────────────────────────
    if show_opensky:
        _sky_flights = fetch_opensky_flights()
        if _sky_flights:
            _sky_df = pd.DataFrame(_sky_flights)
            # Already has _color and _radius per row
            layers.append(pdk.Layer("ScatterplotLayer", data=_sky_df, id="opensky",
                get_position=["lon","lat"], get_radius="_radius",
                get_fill_color="_color",
                get_line_color=[255,255,255,30], line_width_min_pixels=1,
                pickable=True, auto_highlight=True))

    # ── ACLED conflict events ───────────────────────────────────
    if show_acled:
        _acled_events = fetch_acled_events(limit=80)
        if _acled_events:
            _ae_df = pd.DataFrame(_acled_events)
            _ae_df["_color"] = _ae_df["event_type"].apply(lambda t:
                [255, 30, 60, 220]  if "Explosion" in str(t) or "Violence" in str(t)
                else [255, 120, 0, 200] if "Battle" in str(t) or "Conflict" in str(t)
                else [255, 200, 0, 180])
            _ae_df["_radius"] = _ae_df.get("fatalities", pd.Series([0]*len(_ae_df))).apply(
                lambda f: min(20000 + int(f or 0) * 1000, 120000))
            layers.append(pdk.Layer("ScatterplotLayer", data=_ae_df, id="acled",
                get_position=["lon","lat"], get_radius="_radius",
                get_fill_color="_color",
                get_line_color=[255, 60, 60, 60], line_width_min_pixels=1,
                pickable=True, auto_highlight=True))

    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=22, longitude=18, zoom=1.4, pitch=0),
        map_style=CARTO_DARK,
        tooltip={"text": "{tip}", "style": {"backgroundColor": "#080f1c", "color": "#e2ecf8", "border": "1px solid rgba(0,200,255,.3)", "fontFamily": "IBM Plex Mono, monospace", "fontSize": "12px", "padding": "10px 14px", "borderRadius": "8px", "boxShadow": "0 4px 24px rgba(0,0,0,.6)", "lineHeight": "1.7", "whiteSpace": "pre-line", "maxWidth": "320px"}},
        height=480,
    )

def build_theatre_map(conflict_key, show_supply):
    C = CONFLICTS[conflict_key]
    inc_df = pd.DataFrame(C["incidents"])
    sc = _sev_colors()
    inc_df["_fc"]  = inc_df["severity"].map(sc)
    inc_df["_rad"] = inc_df["severity"].map({"CRITICAL":60000,"HIGH":45000,"MED":35000,"LOW":25000,"INFO":20000})
    inc_df["tip"]  = inc_df.apply(lambda r:
        f"{INCIDENT_ICONS.get(r['type'],'?')} {r['title']}\n{r['loc']} · {r['date']}\nSeverity: {r['severity']} · Casualties: {r['casualties']}", axis=1)
    layers = [pdk.Layer("ScatterplotLayer", data=inc_df, get_position=["lon","lat"],
                          get_radius="_rad", get_fill_color="_fc",
                          get_line_color=[255,255,255,40], line_width_min_pixels=1,
                          pickable=True, auto_highlight=True)]
    if show_supply:
        adf = pd.DataFrame(C["supply_lines"])
        if not adf.empty:
            color_map = {
                "Military Aid":[255,61,90,160],"Arms/Funding":[255,61,90,160],
                "RSF Support":[255,140,66,140],"SAF Support":[0,200,255,140],
                "Junta Support":[255,61,90,140],"Arms Supply":[255,180,0,140],
                "Humanitarian":[0,230,118,150],
            }
            adf["_fc"]  = adf["type"].apply(lambda t: color_map.get(t,[74,107,133,120]))
            adf["tip"]  = adf.apply(lambda r: f"⟶ SUPPLY LINE\n{r['type']}\nProvider: {r['provider']}", axis=1)
            layers.append(pdk.Layer("ArcLayer", data=adf,
                get_source_position=["from_lon","from_lat"],
                get_target_position=["to_lon","to_lat"],
                get_source_color="_fc", get_target_color="_fc",
                get_width=2, pickable=True, auto_highlight=True))
    cx = np.mean([i["lon"] for i in C["incidents"]])
    cy = np.mean([i["lat"] for i in C["incidents"]])
    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=cy, longitude=cx, zoom=4, pitch=20),
        map_style=CARTO_DARK,
        tooltip={"text": "{tip}", "style": {"backgroundColor": "#080f1c", "color": "#e2ecf8", "border": "1px solid rgba(255,61,90,.35)", "fontFamily": "IBM Plex Mono, monospace", "fontSize": "12px", "padding": "10px 14px", "borderRadius": "8px", "boxShadow": "0 4px 24px rgba(0,0,0,.6)", "lineHeight": "1.7", "whiteSpace": "pre-line", "maxWidth": "300px"}},
        height=390,
    )

# ─────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────
def kp_chart(s):
    f = go.Figure()
    f.add_trace(go.Scatter(x=list(range(len(s))), y=s, mode="lines",
                            line=dict(color="#00c8ff",width=2),
                            fill="tozeroy", fillcolor="rgba(0,200,255,.07)"))
    f.add_hline(y=5,line_dash="dash",line_color="rgba(255,61,90,.5)",line_width=1.5,
                annotation_text="Storm (Kp5)",annotation_font=dict(color="#ff3d5a",size=9))
    f.update_layout(height=90,margin=dict(l=0,r=0,t=0,b=0),**bg_chart(),
                    showlegend=False,xaxis=dict(visible=False),yaxis=dict(visible=False,range=[0,9]))
    return f

def mag_hist(eq):
    f = go.Figure(go.Histogram(x=eq["mag"],nbinsx=14,marker_color="#00c8ff",opacity=.65,marker_line_width=0))
    f.update_layout(height=150,margin=dict(l=0,r=0,t=0,b=0),**bg_chart(),
                    xaxis=dict(**ax(),title="Magnitude"),yaxis=ax(),bargap=.08)
    return f

def mv_bar(mv):
    df = pd.DataFrame(mv).sort_values("scale",ascending=True)
    colors = df["sentiment"].map({"CRIT":"#ff3d5a","HIGH":"#ff8c42","MED":"#ffb400"})
    f = go.Figure(go.Bar(y=df["location"].str.split(",").str[0],x=df["scale"],orientation="h",
                          marker_color=colors,marker_line_width=0))
    f.update_layout(height=220,margin=dict(l=0,r=0,t=0,b=0),**bg_chart(),
                    xaxis=dict(**ax(),range=[0,100]),yaxis=dict(color="#dde8f5",tickfont_size=11))
    return f

def mag_donut(eq):
    b = {"M2.5–3.4":len(eq[(eq.mag>=2.5)&(eq.mag<3.5)]),
         "M3.5–4.4":len(eq[(eq.mag>=3.5)&(eq.mag<4.5)]),
         "M4.5–5.4":len(eq[(eq.mag>=4.5)&(eq.mag<5.5)]),
         "M5.5+":   len(eq[eq.mag>=5.5])}
    f = go.Figure(go.Pie(labels=list(b.keys()),values=list(b.values()),hole=.6,
                          marker_colors=["#00e676","#00c8ff","#ffb400","#ff3d5a"],
                          textfont_size=11,textinfo="label+percent"))
    f.update_layout(height=200,margin=dict(l=0,r=0,t=0,b=0),**bg_chart(),showlegend=False)
    return f

def escalation_gauge(val,label,color):
    f = go.Figure(go.Indicator(
        mode="gauge+number",value=val,
        gauge=dict(axis=dict(range=[0,100],tickcolor="#4a6b85",tickfont=dict(size=9,color="#4a6b85")),
                   bar=dict(color=color,thickness=.28),bgcolor="rgba(0,0,0,0)",borderwidth=0,
                   steps=[dict(range=[0,30],color="rgba(0,230,118,.07)"),
                           dict(range=[30,60],color="rgba(255,180,0,.07)"),
                           dict(range=[60,80],color="rgba(255,140,66,.07)"),
                           dict(range=[80,100],color="rgba(255,61,90,.07)")],
                   threshold=dict(line=dict(color=color,width=2),thickness=.75,value=val)),
        number=dict(font=dict(family="Bebas Neue",size=40,color=color)),
        title=dict(text=label,font=dict(family="IBM Plex Mono",size=9,color="#4a6b85")),
    ))
    f.update_layout(height=190,margin=dict(l=10,r=10,t=30,b=10),**bg_chart())
    return f

def conflict_timeline_chart(tl):
    tc = {"escalation":"#ff3d5a","milestone":"#00c8ff","diplomatic":"#00e676","setback":"#ffb400","ongoing":"#9d6eff"}
    colors = [tc.get(t["type"],"#4a6b85") for t in tl]
    f = go.Figure()
    f.add_trace(go.Scatter(x=[t["date"] for t in tl],y=[1]*len(tl),mode="lines",
                            line=dict(color="#0f2035",width=2),showlegend=False))
    f.add_trace(go.Scatter(x=[t["date"] for t in tl],y=[1]*len(tl),mode="markers+text",
                            text=[t["event"][:26]+"…" if len(t["event"])>26 else t["event"] for t in tl],
                            textposition="top center",textfont=dict(size=8,color="#4a6b85"),
                            marker=dict(size=11,color=colors,line=dict(width=1.5,color="#0f2035")),
                            hovertext=[t["event"] for t in tl],hoverinfo="text+x",showlegend=False))
    f.update_layout(height=180,margin=dict(l=0,r=0,t=30,b=0),**bg_chart(),showlegend=False,
                    xaxis=ax(),yaxis=dict(visible=False))
    return f

def casualty_chart():
    names  = [n.split("–")[0].split(" ")[0] for n in CONFLICTS]
    cas    = [c["casualties_total"] for c in CONFLICTS.values()]
    dis    = [c["displaced"]        for c in CONFLICTS.values()]
    f = go.Figure()
    f.add_trace(go.Bar(name="Casualties",x=names,y=cas,marker_color="#ff3d5a",opacity=.85,marker_line_width=0))
    f.add_trace(go.Bar(name="Displaced", x=names,y=dis,marker_color="#ffb400",opacity=.7, marker_line_width=0))
    f.update_layout(height=220,margin=dict(l=0,r=0,t=10,b=0),**bg_chart(),barmode="group",
                    legend=dict(font=dict(color="#4a6b85",size=10),bgcolor="rgba(0,0,0,0)"),
                    xaxis=ax(),yaxis=ax())
    return f

def media_bias_chart(sources):
    bias_colors = []
    for s in sources:
        b = s["bias"].lower()
        if "state" in b or "junta" in b: bias_colors.append("#ff3d5a")
        elif "pro-" in b:                 bias_colors.append("#ffb400")
        elif "centre" in b or "center" in b: bias_colors.append("#00c8ff")
        elif "left" in b:                 bias_colors.append("#9d6eff")
        elif "right" in b:                bias_colors.append("#ff8c42")
        else:                             bias_colors.append("#4a6b85")
    f = go.Figure(go.Bar(x=[s["name"] for s in sources],y=[s["reliability"] for s in sources],
                          marker_color=bias_colors,marker_line_width=0,opacity=.85,
                          text=[s["reliability"] for s in sources],
                          textfont=dict(size=9,color="#e2ecf8"),textposition="outside"))
    f.update_layout(height=180,margin=dict(l=0,r=0,t=10,b=30),**bg_chart(),
                    xaxis=dict(**ax(),tickangle=-30),yaxis=dict(**ax(),range=[0,105]))
    return f

# ─────────────────────────────────────────────
# FETCH LIVE DATA — parallel via ThreadPoolExecutor
# All 6 calls run concurrently; total wall-time ≈ slowest single request
# ─────────────────────────────────────────────
from concurrent.futures import ThreadPoolExecutor as _TPE, as_completed as _asc

def _startup_fetch():
    """Run all startup fetches in parallel, return results dict."""
    _tasks = {
        "eq":     fetch_usgs,
        "eonet":  fetch_eonet,
        "kp":     fetch_kp,
        "solar":  fetch_solar,
        "firms":  fetch_firms_count,
        "sig_eq": fetch_usgs_significant,
    }
    _results = {}
    with _TPE(max_workers=6) as _ex:
        _futs = {_ex.submit(fn): key for key, fn in _tasks.items()}
        for _fut in _asc(_futs):
            _results[_futs[_fut]] = _fut.result()
    return _results

_sd = _startup_fetch()
eq_df      = _sd["eq"]
eonet_df   = _sd["eonet"]
kp_data    = _sd["kp"]
solar_data = _sd["solar"]
firms_cnt  = _sd["firms"]
sig_eq_df  = _sd["sig_eq"]
utc_now    = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark" style="margin-bottom:4px">THE GEO-<em>LOCATOR</em></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:var(--muted);letter-spacing:.14em;font-weight:700;margin-bottom:16px">GLOBAL INTELLIGENCE PLATFORM v7</p>', unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    st.markdown("#### 🗺 Global Map Layers")
    st.caption("Groups: toggle categories on/off.")

    with st.expander("🌍 Core Layers", expanded=True):
        show_seis  = st.toggle("🟦 Seismic Events",       value=True,  key="lyr_seis")
        show_volc  = st.toggle("🟠 Volcanic / EONET",     value=False, key="lyr_volc")
        show_conf  = st.toggle("🔴 Conflict Incidents",    value=True,  key="lyr_conf")
        show_mvmt  = st.toggle("🟣 Civil Movements",      value=False, key="lyr_mvmt")
        show_supp  = st.toggle("⟶ Supply Arc Lines",      value=False, key="lyr_supp")
        show_heat  = st.toggle("🌡 Heatmap (Seismic)",    value=False, key="lyr_heat")
        show_hist  = st.toggle("📅 Historical Events 2022+", value=False, key="lyr_hist")
        show_live  = st.toggle("⚡ Live Events (GDELT)",  value=False, key="lyr_live")

    with st.expander("🎯 Intelligence", expanded=False):
        show_intel   = st.toggle("🎯 Intel Hotspots",       value=False, key="lyr_intel")
        show_czones  = st.toggle("⚔ Conflict Zones",       value=False, key="lyr_czones")
        show_mbases  = st.toggle("🏛 Military Bases",       value=False, key="lyr_mbases")
        show_nuclear = st.toggle("☢ Nuclear Sites",         value=False, key="lyr_nuc")
        show_gamma   = st.toggle("⚠ Gamma Irradiators",    value=False, key="lyr_gamma")
        show_cyber   = st.toggle("🛡 Cyber Threat Actors",  value=False, key="lyr_cyber")
        show_orbital = st.toggle("🛰 Orbital Surveillance", value=False, key="lyr_orbit")
        show_gps     = st.toggle("📡 GPS Jamming Zones",    value=False, key="lyr_gps")
        show_cii     = st.toggle("🌎 CII Instability",      value=False, key="lyr_cii")

    with st.expander("🚀 Infrastructure", expanded=False):
        show_space   = st.toggle("🚀 Spaceports",           value=False, key="lyr_space")
        show_cables  = st.toggle("🔌 Undersea Cables",      value=False, key="lyr_cables")
        show_pipes   = st.toggle("🛢 Pipelines",            value=False, key="lyr_pipes")
        show_aidc    = st.toggle("🖥 AI Data Centers",      value=False, key="lyr_aidc")
        show_outages = st.toggle("📡 Internet Outages",     value=False, key="lyr_outage")
        show_econ    = st.toggle("💰 Economic Centers",     value=False, key="lyr_econ")

    with st.expander("✈ Military & Traffic", expanded=False):
        show_milact  = st.toggle("✈ Military Activity",    value=False, key="lyr_milact")
        show_ships   = st.toggle("🚢 Ship Traffic Zones",  value=False, key="lyr_ships")
        show_trade   = st.toggle("⚓ Trade Route Arcs",    value=False, key="lyr_trade")
        show_aviation= st.toggle("✈ Aviation Status",      value=False, key="lyr_avia")
        show_waterways=st.toggle("⚓ Strategic Waterways", value=False, key="lyr_water")

    with st.expander("🛰 Live Intelligence", expanded=False):
        show_ais     = st.toggle("🚢 AIS Vessel Tracking (Live)",   value=False, key="lyr_ais")
        show_opensky = st.toggle("✈ OpenSky Airspace (Live)",       value=False, key="lyr_osky")
        show_acled   = st.toggle("⚔ ACLED Conflict Events (Live)",  value=False, key="lyr_acled")
        if show_ais or show_opensky or show_acled:
            st.caption("🔴 Live data — refreshes on rerun")

    with st.expander("📢 Human & Social", expanded=False):
        show_protests  = st.toggle("📢 Protests (all)",     value=False, key="lyr_prot")
        show_displaced = st.toggle("👥 Displacement Flows", value=False, key="lyr_disp")
        show_minerals  = st.toggle("💎 Critical Minerals",  value=False, key="lyr_min")

    with st.expander("🌋 Natural & Climate", expanded=False):
        show_fires_layer = st.toggle("🔥 Active Fire Zones", value=False, key="lyr_fire")
        show_climate     = st.toggle("🌫 Climate Anomalies", value=False, key="lyr_clim")
        show_weather     = st.toggle("⛈ Weather Alerts",    value=False, key="lyr_weath")

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    st.markdown("#### 📡 Live Data Status")

    # ── Supabase persistence status ──────────────────────────────
    _sb_url, _sb_key = _sb_creds()
    if _sb_url:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:7px;padding:6px 10px;'
            'background:rgba(0,230,118,.06);border:1px solid rgba(0,230,118,.2);'
            'border-radius:6px;margin-bottom:10px">'
            '<span style="width:7px;height:7px;border-radius:50%;background:#00e676;'
            'display:inline-block"></span>'
            '<span style="font-family:IBM Plex Mono,monospace;font-size:9px;color:#00e676">'
            'Supabase persistence active</span></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:7px;padding:6px 10px;'
            'background:rgba(74,107,133,.06);border:1px solid rgba(74,107,133,.2);'
            'border-radius:6px;margin-bottom:10px">'
            '<span style="width:7px;height:7px;border-radius:50%;background:#4a6b85;'
            'display:inline-block"></span>'
            '<span style="font-family:IBM Plex Mono,monospace;font-size:9px;color:#4a6b85">'
            'Persistence off — add SUPABASE_URL + SUPABASE_KEY to secrets</span></div>',
            unsafe_allow_html=True
        )

    feeds_ok = not eq_df.empty
    _kp_col = "p-red" if kp_data["kp"]>=5 else "p-amber" if kp_data["kp"]>=3 else "p-green"
    _sw_col = "p-red" if solar_data["speed"]>700 else "p-amber" if solar_data["speed"]>500 else "p-green"
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;gap:8px">
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse {'p-green' if feeds_ok else 'p-amber'}"></span>USGS Earthquakes</span>
        <span style="color:var(--muted);font-size:11px">{len(eq_df)} events</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse {'p-green' if not eonet_df.empty else 'p-amber'}"></span>NASA EONET</span>
        <span style="color:var(--muted);font-size:11px">{len(eonet_df)} events</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse {_kp_col}"></span>NOAA Kp-index</span>
        <span style="color:var(--muted);font-size:11px">Kp {kp_data['kp']:.1f}</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse {_sw_col}"></span>Solar Wind</span>
        <span style="color:var(--muted);font-size:11px">{solar_data['speed']:.0f} km/s</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse p-orange"></span>FIRMS Wildfires</span>
        <span style="color:var(--muted);font-size:11px">{firms_cnt} active</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse p-red"></span>Conflict Theatres</span>
        <span style="color:var(--muted);font-size:11px">{len(CONFLICTS)} tracked</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse p-cyan"></span>Hist. Events 2022+</span>
        <span style="color:var(--muted);font-size:11px">{len(HISTORICAL_EVENTS)} indexed</span>
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    if st.button("⟳  Refresh All Feeds", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# ─────────────────────────────────────────────

def _render_intelligence_panel(tip: str, name: str, country: str, obj: dict):
    """Render a rich country/point intelligence panel below the map when a marker is clicked."""
    import streamlit.components.v1 as _cp

    # Gather all signals
    signals    = get_all_signals_for_country(country) if country else {}
    ci         = signals.get("instability")
    wmd        = signals.get("wmd")
    conflicts  = signals.get("conflicts", [])
    mil_bases  = signals.get("military_bases", [])
    nuke_sites = signals.get("nuclear_sites", [])
    mil_acts   = signals.get("military_activity", [])
    hist_evts  = signals.get("historical_events", [])

    # Country metadata
    cmeta   = COUNTRY_INTEL.get(country, {})
    flag    = cmeta.get("flag", "🌍")
    code    = cmeta.get("code", "")
    region  = cmeta.get("region", "")

    # Instability scores
    ci_score = ci["score"] if ci else 0
    ci_U     = ci.get("U", 0) if ci else 0
    ci_C     = ci.get("C", 0) if ci else 0
    ci_S     = ci.get("S", 0) if ci else 0
    ci_I     = ci.get("I", 0) if ci else 0
    ci_trend = ci.get("trend","→") if ci else "→"
    ci_col   = "#ff3d5a" if ci_score>=70 else "#ff8c42" if ci_score>=50 else "#ffb400" if ci_score>=35 else "#00e676"

    # WMD risk
    wmd_risk = wmd["risk"] if wmd else 0
    wmd_col  = "#ff3d5a" if wmd_risk>=70 else "#ff8c42" if wmd_risk>=50 else "#ffb400" if wmd_risk>=35 else "#00e676"
    wmd_lbl  = wmd["status"] if wmd else "No data"

    # Historical events for 7-day-style timeline (last 7 days of our data)
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    _now = _dt.now(tz=_tz.utc)
    _7d_ago = _now - _td(days=365*4)  # Use all events since 2022 as our timeline
    tl_events = hist_evts[:6]

    # Nuke status
    nuke_html = ""
    for ns in nuke_sites[:3]:
        ns_col = "#ff3d5a" if "Struck" in ns["status"] or "Destroyed" in ns["status"] else "#ffb400" if "Occupied" in ns["status"] else "#00e676"
        nuke_html += f'<div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(0,200,255,.05)"><span style="font-size:11px;color:#e2ecf8">{ns["name"]}</span><span style="font-family:var(--fm,monospace);font-size:9px;color:{ns_col}">{ns["status"]}</span></div>'

    # Build intelligence brief text
    brief_lines = []
    if ci:
        trend_word = "rising" if ci_trend == "↑" else "declining" if ci_trend == "↓" else "stable"
        live_tag = " (live-updated)" if ci.get("_live") else ""
        brief_lines.append(f"Instability Index {ci_score}/100{live_tag} and {trend_word}. Primary drivers: Unrest ({ci_U}/100), Conflict ({ci_C}/100), Security ({ci_S}/100), Information ({ci_I}/100).")
    if conflicts:
        brief_lines.append(f"Active in {len(conflicts)} tracked conflict theatre(s): {', '.join(conflicts[:2])}.")
    if wmd:
        brief_lines.append(f"WMD posture: {wmd['type']} — Status {wmd['status']}. Assets: {wmd['assets'][:80]}.")
    if nuke_sites:
        brief_lines.append(f"Nuclear infrastructure: {len(nuke_sites)} site(s) tracked including {nuke_sites[0]['name']} ({nuke_sites[0]['status']}).")
    if mil_acts:
        brief_lines.append(f"Active military operations: {mil_acts[0]}.")
    if hist_evts:
        brief_lines.append(f"Most recent event: {hist_evts[0]['date']} — {hist_evts[0]['title'][:80]}.")
    if not brief_lines:
        brief_lines.append(f"Point of interest: {tip}. No detailed country profile available for this location.")

    brief_text = " ".join(brief_lines)

    # Signal count badges
    sig_count_html = ""
    sig_items = [
        (len(conflicts),    "⚔", "Conflicts",     "#ff3d5a"),
        (len(mil_bases),    "🏛", "Mil Bases",     "#ff8c42"),
        (len(nuke_sites),   "☢", "Nuclear Sites", "#ffb400"),
        (len(mil_acts),     "✈", "Mil Activity",  "#00c8ff"),
        (len(hist_evts),    "📅", "Events",        "#9d6eff"),
    ]
    for cnt, icon, label, col in sig_items:
        if cnt > 0:
            sig_count_html += f'<div style="display:flex;align-items:center;gap:6px;padding:6px 10px;background:#0b1524;border:1px solid rgba(0,200,255,.08);border-radius:8px"><span style="font-size:13px">{icon}</span><div><div style="font-family:monospace;font-size:15px;font-weight:700;color:{col};line-height:1">{cnt}</div><div style="font-size:8px;color:#4a6b85;text-transform:uppercase;letter-spacing:.1em">{label}</div></div></div>'

    # Timeline events
    tl_html = ""
    type_colors = {"invasion":"#ff3d5a","attack":"#ff3d5a","strike":"#ff8c42","airstrike":"#ff8c42",
                   "counteroffensive":"#ffb400","milestone":"#00c8ff","diplomatic":"#00e676",
                   "escalation":"#ff3d5a","setback":"#ffb400","natural":"#9d6eff","coup":"#ff3d5a",
                   "political":"#00c8ff","sabotage":"#ff8c42","disaster":"#9d6eff"}
    for ev in tl_events[:5]:
        ev_col = type_colors.get(ev.get("type",""), "#4a6b85")
        ev_title = ev.get("title","")[:70]
        tl_html += (
            f'<div style="display:flex;gap:10px;padding:8px 0;border-bottom:1px solid rgba(0,200,255,.05)">' +
            f'<div style="width:3px;background:{ev_col};border-radius:2px;flex-shrink:0"></div>' +
            f'<div><div style="font-family:monospace;font-size:9px;color:#4a6b85;margin-bottom:2px">{ev["date"]} · <span style="color:{ev_col};text-transform:uppercase">{ev.get("type","")}</span></div>' +
            f'<div style="font-size:11px;color:#e2ecf8;line-height:1.4">{ev_title}</div></div></div>'
        )
    if not tl_html:
        tl_html = '<div style="font-family:monospace;font-size:10px;color:#4a6b85;padding:12px 0">No tracked events for this location</div>'

    # Instability bars
    inst_bars = ""
    for label, val, bar_col in [
        ("Unrest",      ci_U, "#ff3d5a"),
        ("Conflict",    ci_C, "#ff8c42"),
        ("Security",    ci_S, "#ffb400"),
        ("Information", ci_I, "#9d6eff"),
    ]:
        inst_bars += (
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px">' +
            f'<div style="width:90px;font-size:10px;color:#a8c0d8">{label}</div>' +
            f'<div style="flex:1;height:5px;background:#0f2035;border-radius:3px;overflow:hidden">' +
            f'<div style="height:100%;width:{val}%;background:{bar_col};border-radius:3px"></div></div>' +
            f'<div style="font-family:monospace;font-size:11px;color:{bar_col};min-width:28px;text-align:right">{val}</div></div>'
        )

    # Title and label
    display_name = country if country else name[:40] if name else "Unknown Location"
    subtitle = f"{code} · {region}" if code and region else (tip[:50] if tip else "")

    # Render as components.html
    panel_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#02040a;font-family:'DM Sans',system-ui,sans-serif;color:#e2ecf8;padding:16px;}}
.header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;}}
.flag{{font-size:32px;margin-right:12px;}}
.title{{font-size:24px;font-weight:700;color:#e2ecf8;}}
.subtitle{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6b85;margin-top:2px;}}
.close-btn{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6b85;cursor:pointer;
           padding:4px 10px;border:1px solid rgba(74,107,133,.3);border-radius:5px;}}
.close-btn:hover{{color:#00c8ff;border-color:rgba(0,200,255,.3);}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;}}
.grid-3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px;}}
.panel{{background:#080f1c;border:1px solid rgba(0,200,255,.1);border-radius:10px;padding:14px 16px;}}
.panel-title{{font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:500;letter-spacing:.18em;
              text-transform:uppercase;color:#4a6b85;margin-bottom:10px;}}
.score{{font-family:'Bebas Neue',sans-serif;font-size:52px;line-height:1;}}
.trend{{font-family:'IBM Plex Mono',monospace;font-size:12px;color:#a8c0d8;margin-left:8px;}}
.signals{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;}}
.brief{{font-size:12px;color:#a8c0d8;line-height:1.75;padding:14px 16px;background:#080f1c;
        border:1px solid rgba(0,200,255,.1);border-radius:10px;margin-bottom:14px;}}
.brief-title{{font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:500;letter-spacing:.18em;
              text-transform:uppercase;color:#4a6b85;margin-bottom:8px;}}
.tip-box{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6b85;padding:10px 14px;
          background:#060d18;border:1px solid rgba(0,200,255,.06);border-radius:8px;line-height:1.6;
          margin-bottom:14px;}}
</style>
</head><body>
<div class="header">
  <div style="display:flex;align-items:center">
    <div class="flag">{flag}</div>
    <div>
      <div class="title">{display_name}</div>
      <div class="subtitle">{subtitle}</div>
    </div>
  </div>
  <div class="close-btn" onclick="window.parent.postMessage({{type:'streamlit:setComponentValue',value:'close'}},'*')">✕ Close</div>
</div>

<div class="tip-box">{tip[:120]}</div>

<div class="signals">{sig_count_html if sig_count_html else '<div style="font-family:monospace;font-size:10px;color:#4a6b85">No linked signal data</div>'}</div>

<div class="grid">
  <div class="panel">
    <div class="panel-title">Instability Index</div>
    <div style="display:flex;align-items:baseline;margin-bottom:12px">
      <span class="score" style="color:{ci_col}">{ci_score}</span>
      <span style="font-family:monospace;font-size:14px;color:#4a6b85">/100</span>
      <span class="trend">{ci_trend} {"rising" if ci_trend=="↑" else "declining" if ci_trend=="↓" else "stable"}</span>
      {"<span style=\"font-family:monospace;font-size:9px;color:#00e676;margin-left:8px;padding:1px 6px;background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.2);border-radius:4px\">⚡ LIVE</span>" if ci and ci.get("_live") else ""}
    </div>
    {inst_bars if ci else '<div style="font-family:monospace;font-size:10px;color:#4a6b85">No instability index available</div>'}
  </div>
  <div class="panel">
    <div class="panel-title">{"WMD / Nuclear Posture" if wmd or nuke_sites else "Point Data"}</div>
    {f'<div style="display:flex;align-items:baseline;gap:8px;margin-bottom:10px"><span class="score" style="color:{wmd_col};font-size:42px">{wmd_risk}</span><span style="font-family:monospace;font-size:11px;color:#4a6b85">/100 risk</span></div><div style="font-family:monospace;font-size:10px;color:{wmd_col};margin-bottom:8px">{wmd["type"] if wmd else ""} · {wmd_lbl}</div>' if wmd else ""}
    {nuke_html if nuke_html else ('<div style="font-family:monospace;font-size:10px;color:#4a6b85">No nuclear/WMD data</div>' if not wmd else "")}
  </div>
</div>

{"<div class='panel' style='margin-bottom:14px'><div class='panel-title'>Recent Historical Events</div>" + tl_html + "</div>" if tl_events else ""}

<div class="brief">
  <div class="brief-title">Intelligence Brief</div>
  {brief_text}
</div>

</body></html>"""

    # Render the panel in an expander for clean UX
    with st.expander(f"📍 Intelligence Profile — {display_name}", expanded=True):
        _cp.html(panel_html, height=750, scrolling=True)

# ═══════════════════════════════════════════════════════════════
# LIVE MARKET DATA FETCHERS  (Yahoo Finance · CoinGecko)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_live_strategic_risk() -> dict:
    """Derive a live Strategic Risk score from GDELT tone API + conflict data."""
    base = STRATEGIC_RISK.copy()
    try:
        # Fetch average tone for top conflict keywords from GDELT
        import urllib.parse
        queries = [
            ("war conflict military strike", "Military Conflict"),
            ("cyber attack hack breach", "Cyber Threats"),
            ("sanctions trade war economy", "Economic Disruption"),
            ("coup protest election fraud instability", "Political Instability"),
            ("earthquake flood drought wildfire climate", "Climate / Disaster"),
            ("pandemic virus outbreak disease", "Pandemic Risk"),
        ]
        component_scores = []
        for q, name in queries:
            try:
                url = ("https://api.gdeltproject.org/api/v2/tv/tv?query="
                       + urllib.parse.quote(q)
                       + "&mode=timelinetone&format=json&timespan=7d")
                r = requests.get(url, timeout=8)
                if r.status_code == 200:
                    data = r.json()
                    series = data.get("timeline", [{}])[0].get("data", []) if data.get("timeline") else []
                    if series:
                        tones = [abs(float(p.get("value", 0))) for p in series if p.get("value")]
                        avg_tone = sum(tones) / len(tones) if tones else 0
                        # Map tone magnitude (0-10) to risk score (0-100)
                        risk_score = min(int(avg_tone * 9), 95)
                        component_scores.append((name, risk_score))
                    else:
                        component_scores.append((name, None))
                else:
                    component_scores.append((name, None))
            except Exception:
                component_scores.append((name, None))

        # Blend live scores with baseline (70% baseline, 30% live)
        base_comp_map = {c["name"]: c for c in base["components"]}
        new_comps = []
        live_vals = []
        for name, live_val in component_scores:
            base_c = base_comp_map.get(name, {})
            base_val = base_c.get("val", 50)
            if live_val is not None:
                blended = round(base_val * 0.7 + live_val * 0.3)
                live_vals.append(blended)
            else:
                blended = base_val
            new_comps.append({
                "name": name, "val": blended, "col": base_c.get("col", "#ff8c42")
            })

        if live_vals:
            new_score = round(sum(live_vals) / len(live_vals))
            # Clamp to reasonable range
            new_score = max(30, min(92, new_score))
        else:
            new_score = base["score"]

        col = "#ff3d5a" if new_score >= 75 else "#ff8c42" if new_score >= 55 else "#ffb400" if new_score >= 35 else "#00e676"
        lbl = "CRITICAL" if new_score >= 75 else "ELEVATED" if new_score >= 55 else "MODERATE" if new_score >= 35 else "LOW"

        return {
            "score": new_score, "label": lbl, "color": col,
            "trend": base.get("trend", "→"),
            "components": new_comps if new_comps else base["components"],
            "is_live": bool(live_vals),
        }
    except Exception:
        return {**base, "is_live": False}


@st.cache_data(ttl=300, show_spinner=False)
def _yahoo_batch(symbols: tuple) -> dict:
    """Batch-fetch Yahoo Finance quotes. Returns {sym: {price, chg_pct, name, currency}}."""
    out = {}
    hdrs = {"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"}
    for sym in symbols:
        try:
            r = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                params={"interval": "1d", "range": "2d"},
                headers=hdrs, timeout=8)
            if r.status_code != 200:
                continue
            meta  = r.json()["chart"]["result"][0]["meta"]
            price = float(meta.get("regularMarketPrice") or 0)
            prev  = float(meta.get("previousClose") or meta.get("chartPreviousClose") or price or 1)
            chg   = round((price - prev) / prev * 100, 2) if prev else 0.0
            out[sym] = {"price": round(price, 4), "chg_pct": chg,
                        "name": meta.get("shortName", sym),
                        "currency": meta.get("currency", "USD")}
        except Exception:
            continue
    return out


@st.cache_data(ttl=600, show_spinner=False)
def fetch_live_pizza_index() -> dict:
    """Update Pizza Index components with live commodity prices from Yahoo Finance."""
    base = PIZZA_INDEX.copy()
    try:
        # Fetch live prices for pizza ingredients
        syms = {"ZW=F":"Wheat (CBOT)","NG=F":"Natural Gas","CL=F":"WTI Crude"}
        quotes = _yahoo_batch(tuple(syms.keys()))

        new_comps = []
        for c in base["components"]:
            nc = dict(c)
            # Update wheat futures
            if "Wheat" in c["name"] and "ZW=F" in quotes:
                q = quotes["ZW=F"]
                nc["val"] = round(q["price"] / 100, 2)  # cents/bu → $/bu
                pct_chg = q["chg_pct"]
                nc["change"] = round(pct_chg, 1)
                # Stress proportional to price (baseline ~5.50/bu)
                stress = min(int(nc["val"] / 8.0 * 100), 95)
                nc["stress"] = max(20, stress)
                nc["note"] = f"Live: ${nc['val']}/bu ({'+' if pct_chg>=0 else ''}{pct_chg:.1f}% 24h) · Ukraine/Russia disruption"
            # Update energy
            elif "Energy" in c["name"] and "NG=F" in quotes:
                q = quotes["NG=F"]
                nc["val"] = round(q["price"], 2)
                pct_chg = q["chg_pct"]
                nc["change"] = round(pct_chg, 1)
                stress = min(int(nc["val"] / 6.0 * 100), 90)
                nc["stress"] = max(15, stress)
                nc["note"] = f"Live: ${nc['val']}/MMBtu ({'+' if pct_chg>=0 else ''}{pct_chg:.1f}% 24h)"
            new_comps.append(nc)

        # Recalculate overall score
        all_stress = [c.get("stress", 50) for c in new_comps]
        new_score = round(sum(all_stress) / len(all_stress))
        col = "#ff3d5a" if new_score >= 75 else "#ff8c42" if new_score >= 55 else "#ffb400" if new_score >= 35 else "#00e676"
        lbl = "CRITICAL STRESS" if new_score >= 75 else "ELEVATED STRESS" if new_score >= 55 else "MODERATE" if new_score >= 35 else "LOW STRESS"

        result = base.copy()
        result["components"] = new_comps
        result["score"] = new_score
        result["color"] = col
        result["label"] = lbl
        result["is_live"] = True
        return result
    except Exception:
        return {**base, "is_live": False}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_indices() -> list:
    SYMS = {
        "^GSPC": ("S&P 500","USA"), "^NDX": ("Nasdaq 100","USA"), "^DJI": ("Dow Jones","USA"),
        "^FTSE": ("FTSE 100","UK"), "^GDAXI": ("DAX","Germany"), "^FCHI": ("CAC 40","France"),
        "^N225": ("Nikkei 225","Japan"), "^HSI": ("Hang Seng","HK"),
        "000001.SS": ("Shanghai Comp.","China"), "^BSESN": ("BSE Sensex","India"),
        "^BVSP": ("Bovespa","Brazil"), "^VIX": ("VIX Fear Index","USA"),
    }
    q = _yahoo_batch(tuple(SYMS))
    return [{"sym": s, "name": n, "country": c,
             "price": q[s]["price"], "chg_pct": q[s]["chg_pct"]}
            for s, (n, c) in SYMS.items() if s in q and q[s]["price"] > 0]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_commodities() -> list:
    SYMS = {
        "GC=F": ("Gold","$/oz","precious"),    "SI=F": ("Silver","$/oz","precious"),
        "HG=F": ("Copper","$/lb","industrial"), "PL=F": ("Platinum","$/oz","precious"),
        "PA=F": ("Palladium","$/oz","precious"),"CL=F": ("WTI Crude","$/bbl","energy"),
        "BZ=F": ("Brent Crude","$/bbl","energy"),"NG=F": ("Natural Gas","$/MMBtu","energy"),
        "ZW=F": ("Wheat (CBOT)","¢/bu","agri"), "ZC=F": ("Corn","¢/bu","agri"),
        "ZS=F": ("Soybeans","¢/bu","agri"),
    }
    q = _yahoo_batch(tuple(SYMS))
    return [{"sym": s, "name": n, "unit": u, "cat": cat,
             "price": q[s]["price"], "chg_pct": q[s]["chg_pct"]}
            for s, (n, u, cat) in SYMS.items() if s in q and q[s]["price"] > 0]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_forex() -> list:
    PAIRS = {
        "EURUSD=X": ("EUR/USD","Euro",False),          "GBPUSD=X": ("GBP/USD","British Pound",False),
        "USDJPY=X": ("USD/JPY","Japanese Yen",True),   "USDCNY=X": ("USD/CNY","Chinese Yuan",True),
        "USDINR=X": ("USD/INR","Indian Rupee",True),   "USDTRY=X": ("USD/TRY","Turkish Lira",True),
        "USDRUB=X": ("USD/RUB","Russian Ruble",True),  "USDUAH=X": ("USD/UAH","Hryvnia",True),
        "USDSAR=X": ("USD/SAR","Saudi Riyal",True),    "USDBRL=X": ("USD/BRL","Brazilian Real",True),
        "USDCHF=X": ("USD/CHF","Swiss Franc",True),    "USDAED=X": ("USD/AED","UAE Dirham",True),
    }
    q = _yahoo_batch(tuple(PAIRS))
    return [{"sym": s, "pair": p, "currency_name": cn, "usd_base": ub,
             "rate": q[s]["price"], "chg_pct": q[s]["chg_pct"]}
            for s, (p, cn, ub) in PAIRS.items() if s in q and q[s]["price"] > 0]


@st.cache_data(ttl=600, show_spinner=False)
def fetch_live_defense() -> list:
    SYMS = {
        "RTX": ("RTX (Raytheon)","USA","USD"),   "LMT": ("Lockheed Martin","USA","USD"),
        "NOC": ("Northrop Grumman","USA","USD"),  "GD":  ("General Dynamics","USA","USD"),
        "BA":  ("Boeing","USA","USD"),            "HII": ("Huntington Ingalls","USA","USD"),
        "RHM.DE": ("Rheinmetall","Germany","EUR"),"SAAB-B.ST": ("Saab AB","Sweden","SEK"),
        "BA.L": ("BAE Systems","UK","GBX"),       "AIR.PA": ("Airbus","France","EUR"),
    }
    q = _yahoo_batch(tuple(SYMS))
    return [{"sym": s, "name": n, "country": c, "currency": cur,
             "price": q[s]["price"], "chg_pct": q[s]["chg_pct"]}
            for s, (n, c, cur) in SYMS.items() if s in q and q[s]["price"] > 0]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_crypto() -> list:
    CG = {
        "bitcoin":("BTC","Bitcoin"),    "ethereum":("ETH","Ethereum"),
        "solana":("SOL","Solana"),       "ripple":("XRP","XRP"),
        "binancecoin":("BNB","BNB"),     "toncoin":("TON","Toncoin"),
    }
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
            params={"ids":",".join(CG),"vs_currencies":"usd",
                    "include_24hr_change":"true","include_market_cap":"true"},
            timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        data = r.json()
        return [{"ticker":t,"name":n,"price":round(float(data[cid].get("usd",0)),2),
                 "chg_pct":round(float(data[cid].get("usd_24h_change",0)),2),
                 "mcap":int(data[cid].get("usd_market_cap",0) or 0)}
                for cid,(t,n) in CG.items() if cid in data and data[cid].get("usd",0)>0]
    except Exception:
        return []



# ─────────────────────────────────────────────
# CINEMATIC INTRO  (plays once per session, 10 s)
# ─────────────────────────────────────────────
if not st.session_state.get("intro_shown", False):
    import streamlit.components.v1 as _ic
    import time as _it

    # Step 1: Hide all Streamlit chrome via CSS (no JS needed here)
    st.markdown("""
<style>
[data-testid="stAppViewContainer"]>section:first-child,
[data-testid="stSidebar"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
footer { display:none!important; }
[data-testid="stAppViewContainer"] { background:#02040a!important; padding:0!important; }
[data-testid="block-container"]    { padding:0!important; max-width:100%!important; }
.main .block-container             { padding:0!important; }
/* Make the iframe fill the whole screen */
iframe[title="st.iframe_component"] ,
iframe { border:none!important; }
section[data-testid="stMain"] > div:first-child > div > iframe {
    position:fixed!important; inset:0!important;
    width:100vw!important; height:100vh!important;
    z-index:999999!important;
}
</style>""", unsafe_allow_html=True)

    # Step 2: Full intro in components.html — JS runs fine here
    _ic.html("""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:100%;height:100%;overflow:hidden;background:#02040a;}
#geo-intro{position:fixed;inset:0;background:#02040a;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;font-family:'IBM Plex Mono',monospace;}
#gi-bg,#gi-globe,#gi-fx{position:absolute;inset:0;width:100%;height:100%;}
#gi-globe,#gi-fx{pointer-events:none;}
#gi-scan{position:absolute;inset:0;pointer-events:none;z-index:5;background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.04) 3px,rgba(0,0,0,.04) 6px);}
#gi-vig{position:absolute;inset:0;pointer-events:none;z-index:4;background:radial-gradient(ellipse 90% 90% at 50% 50%,transparent 28%,rgba(2,4,10,.94) 100%);}
#gi-p1{position:absolute;z-index:20;text-align:center;width:100%;opacity:0;animation:fadein .3s ease .1s forwards,fadeout .4s ease 1.7s forwards;}
@keyframes fadein{to{opacity:1}}@keyframes fadeout{to{opacity:0}}
.cbar{height:1px;background:linear-gradient(90deg,transparent,#ff3d5a,transparent);margin:6px auto;width:clamp(180px,35vw,480px);animation:scaleX .8s ease .15s forwards;opacity:0;transform:scaleX(0);}
@keyframes scaleX{to{opacity:1;transform:scaleX(1)}}
.cline{font-size:clamp(8px,1.1vw,12px);letter-spacing:.3em;color:#ff3d5a;text-transform:uppercase;margin:4px 0;}
#gi-p2{position:absolute;z-index:20;text-align:center;width:100%;opacity:0;animation:fadein .7s ease 2s forwards;}
#gi-lw{opacity:0;transform:translateY(10px);animation:logoin 1s cubic-bezier(.16,1,.3,1) 3s forwards;}
@keyframes logoin{to{opacity:1;transform:translateY(0)}}
#gi-logo{font-family:'Bebas Neue','Impact',sans-serif;font-size:clamp(40px,9vw,110px);letter-spacing:.18em;color:#00c8ff;line-height:1;text-shadow:0 0 60px rgba(0,200,255,.8),0 0 120px rgba(0,200,255,.3),0 0 3px rgba(255,255,255,.5);}
#gi-logo em{color:#ffb400;font-style:normal;text-shadow:0 0 60px rgba(255,180,0,.8),0 0 120px rgba(255,180,0,.3);}
#gi-sub{font-size:clamp(8px,1.2vw,14px);letter-spacing:.38em;text-transform:uppercase;color:rgba(0,200,255,.45);margin-top:8px;}
#gi-div{height:1px;margin:14px auto;width:0;background:linear-gradient(90deg,transparent,rgba(0,200,255,.45),rgba(255,180,0,.45),transparent);animation:divexp .7s ease 4.2s forwards;}
@keyframes divexp{to{width:clamp(240px,46vw,620px)}}
/* Live event list fades in below logo */
#gi-events{margin-top:10px;opacity:0;transform:translateY(6px);animation:logoin .8s ease 4.8s forwards;max-width:clamp(280px,44vw,580px);margin-left:auto;margin-right:auto;}
.gi-ev{display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;text-align:left;}
.gi-ev-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;margin-top:4px;animation:evpulse 1.5s ease-in-out infinite;}
@keyframes evpulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.6)}}
.gi-ev-text{font-size:clamp(8px,.9vw,11px);color:rgba(226,236,248,.55);line-height:1.5;letter-spacing:.04em;}
.gi-ev-tag{font-size:clamp(7px,.8vw,9px);font-weight:600;letter-spacing:.18em;text-transform:uppercase;margin-right:6px;}
.gi-hud{position:absolute;z-index:20;opacity:0;animation:fadein .5s ease 5.8s forwards;}
#gi-tl{top:20px;left:20px;}#gi-tr{top:20px;right:20px;text-align:right;}#gi-bl{bottom:56px;left:20px;}
.gi-hbox{position:relative;padding:8px 12px;border:1px solid rgba(0,200,255,.1);border-radius:2px;background:rgba(2,4,10,.75);}
.gi-hbox::before,.gi-hbox::after,.gi-hbox>.gi-bc::before,.gi-hbox>.gi-bc::after{content:'';position:absolute;width:8px;height:8px;border-color:rgba(0,200,255,.4);border-style:solid;}
.gi-hbox::before{top:-1px;left:-1px;border-width:2px 0 0 2px;}.gi-hbox::after{top:-1px;right:-1px;border-width:2px 2px 0 0;}
.gi-hbox>.gi-bc::before{bottom:-1px;left:-1px;border-width:0 0 2px 2px;}.gi-hbox>.gi-bc::after{bottom:-1px;right:-1px;border-width:0 2px 2px 0;}
.hl{font-size:8px;letter-spacing:.2em;text-transform:uppercase;color:rgba(0,200,255,.4);line-height:1.9;}
.hv{font-size:10px;font-weight:500;color:rgba(0,200,255,.75);}
#gi-thr{position:absolute;top:20px;left:50%;transform:translateX(-50%);z-index:20;display:flex;align-items:center;gap:8px;opacity:0;animation:fadein .5s ease 6.2s forwards;}
.tl{font-size:8px;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.3);}
.tb{display:flex;gap:2px;}.tb span{width:clamp(12px,1.8vw,20px);height:7px;border-radius:1px;background:rgba(255,255,255,.07);}
.tb span.on{animation:bp 2s ease-in-out infinite;}@keyframes bp{0%,100%{opacity:1}50%{opacity:.5}}
#gi-tick{position:absolute;bottom:46px;left:0;right:0;height:26px;background:rgba(6,13,24,.9);border-top:1px solid rgba(255,61,90,.2);display:flex;align-items:center;overflow:hidden;opacity:0;animation:fadein .5s ease 6s forwards;}
.tklbl{flex-shrink:0;background:#ff3d5a;color:#fff;font-size:9px;font-weight:500;letter-spacing:.12em;padding:0 12px;height:100%;display:flex;align-items:center;white-space:nowrap;}
.tkscroll{display:inline-block;white-space:nowrap;font-size:10px;color:rgba(226,236,248,.45);letter-spacing:.05em;padding-left:100%;animation:scroll 16s linear infinite;}
@keyframes scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
#gi-prog{position:absolute;bottom:0;left:0;height:2px;background:linear-gradient(90deg,#ff3d5a,#ff8c42,#ffb400,#00c8ff);animation:prog 10s linear forwards;}
@keyframes prog{0%{width:0%}100%{width:100%}}
#gi-skip{position:absolute;bottom:14px;right:18px;z-index:30;font-size:9px;letter-spacing:.15em;text-transform:uppercase;color:rgba(255,255,255,.25);background:transparent;border:1px solid rgba(255,255,255,.1);padding:4px 12px;border-radius:2px;cursor:pointer;transition:all .2s;}
#gi-skip:hover{color:#00c8ff;border-color:rgba(0,200,255,.3);}
</style>
</head>
<body>
<div id="geo-intro">
  <canvas id="gi-bg"></canvas>
  <canvas id="gi-globe"></canvas>
  <canvas id="gi-fx"></canvas>
  <div id="gi-vig"></div><div id="gi-scan"></div>
  <div class="gi-hud" id="gi-tl">
    <div class="gi-hbox"><div class="gi-bc"></div>
      <div class="hl">SYSTEM STATUS</div><div class="hv" style="color:#00e676">OPERATIONAL</div>
      <div class="hl" id="gi-utc">UTC 00:00:00</div>
    </div>
  </div>
  <div class="gi-hud" id="gi-tr">
    <div class="gi-hbox"><div class="gi-bc"></div>
      <div class="hl">FEEDS ACTIVE</div><div class="hv" style="color:#00e676" id="gi-feeds">CONNECTING...</div>
      <div class="hl">GDELT &middot; USGS &middot; NOAA &middot; YAHOO</div>
    </div>
  </div>
  <div class="gi-hud" id="gi-bl">
    <div class="gi-hbox"><div class="gi-bc"></div>
      <div class="hl">ACTIVE THEATRES</div>
      <div class="hv" style="color:#ff3d5a">UKRAINE &middot; GAZA &middot; IRAN</div>
      <div class="hv" style="color:#ff8c42">SUDAN &middot; MYANMAR &middot; YEMEN</div>
    </div>
  </div>
  <div id="gi-thr">
    <div class="tl">GLOBAL THREAT</div>
    <div class="tb" id="gi-tb"></div>
    <div class="tl" style="color:#ff8c42;font-weight:700;letter-spacing:.1em">ELEVATED</div>
  </div>
  <div id="gi-p1">
    <div class="cbar"></div>
    <div class="cline">&#x25BC; INITIALISING GLOBAL INTELLIGENCE FEED &#x25BC;</div>
    <div class="cline" style="color:rgba(255,61,90,.5);font-size:clamp(6px,.9vw,9px);margin-top:3px">AUTHORISED ACCESS ONLY &nbsp;/&nbsp; ALL ACTIVITY MONITORED</div>
    <div class="cbar"></div>
  </div>
  <div id="gi-p2">
    <div id="gi-lw">
      <div id="gi-logo">THE&nbsp;GEO&#8209;<em>LOCATOR</em></div>
      <div id="gi-sub">Global Intelligence Operations Center</div>
    </div>
    <div id="gi-div"></div>
    <div id="gi-events">
      <!-- Populated by JS: live GDELT events or static fallback -->
    </div>
  </div>
  <div id="gi-tick">
    <div class="tklbl">&#9679;&nbsp;LIVE</div>
    <div style="overflow:hidden;flex:1;height:100%;display:flex;align-items:center;padding-left:80px">
      <div class="tkscroll" id="gi-tkscroll">
        &#x25C6;&nbsp;UKRAINE: Russian missile salvo targets Kyiv power grid &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;GAZA: Ground operations continue &mdash; civilian corridor closed &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;IRAN: IRGC ballistic missile posture elevated following strikes &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;RED SEA: Houthi drone intercepted 40nm from Bab el-Mandeb &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;SUDAN: RSF advancing in North Darfur &mdash; UN declares famine &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;MARKETS: Brent crude +2.1% &mdash; Hormuz closure risk premium rising &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;UKRAINE: Russian missile salvo targets Kyiv power grid &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;GAZA: Ground operations continue &mdash; civilian corridor closed &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;IRAN: IRGC ballistic missile posture elevated following strikes &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;RED SEA: Houthi drone intercepted 40nm from Bab el-Mandeb &nbsp;&nbsp;&nbsp;
      </div>
    </div>
  </div>
  <button id="gi-skip" onclick="geoSkip()">SKIP &rsaquo;</button>
  <div id="gi-prog"></div>
</div>

<script>
(function(){
// ── Canvas + resize ───────────────────────────────
var bgC=document.getElementById('gi-bg'),gbC=document.getElementById('gi-globe'),fxC=document.getElementById('gi-fx');
var bgX=bgC.getContext('2d'),gbX=gbC.getContext('2d'),fxX=fxC.getContext('2d');
var W=window.innerWidth,H=window.innerHeight;
function resize(){W=window.innerWidth;H=window.innerHeight;bgC.width=gbC.width=fxC.width=W;bgC.height=gbC.height=fxC.height=H;}
resize();window.addEventListener('resize',resize);

// ── UTC clock ─────────────────────────────────────
function ck(){var n=new Date(),el=document.getElementById('gi-utc');if(el)el.textContent='UTC '+String(n.getUTCHours()).padStart(2,'0')+':'+String(n.getUTCMinutes()).padStart(2,'0')+':'+String(n.getUTCSeconds()).padStart(2,'0');}
ck();setInterval(ck,1000);

// ── Threat blocks ─────────────────────────────────
var tlC=['#00e676','#00e676','#ffb400','#ffb400','#ff8c42','#ff8c42','#ff3d5a','#ff3d5a'];
var tlEl=document.getElementById('gi-tb');
for(var i=0;i<8;i++){var b=document.createElement('span');b.className=i<6?'on':'';b.style.background=i<6?tlC[i]:'rgba(255,255,255,.07)';if(i<6)b.style.animationDelay=(i*.12)+'s';tlEl.appendChild(b);}

// ── Particles ─────────────────────────────────────
var pts=[];
for(var i=0;i<160;i++)pts.push({x:Math.random()*1920,y:Math.random()*1080,vx:(Math.random()-.5)*.4,vy:(Math.random()-.5)*.4,r:Math.random()*1.3+.25,warm:Math.random()>.75,ph:Math.random()*Math.PI*2});

// ── Conflict hotspots: REAL lat/lon ───────────────
// These use actual geographic coordinates so they rotate WITH the globe
var HOTSPOTS=[
  {lat:49.0,  lon:32.0,  col:'#ff3d5a', label:'UKRAINE',  detail:'Active conflict — frontline shifts daily'},
  {lat:31.5,  lon:34.45, col:'#ff3d5a', label:'GAZA',     detail:'Ground operations + airstrikes ongoing'},
  {lat:32.0,  lon:53.0,  col:'#ff8c42', label:'IRAN',     detail:'Post-strike nuclear posture elevated'},
  {lat:15.5,  lon:32.5,  col:'#ff8c42', label:'SUDAN',    detail:'RSF advancing — famine declared'},
  {lat:17.0,  lon:96.0,  col:'#ffb400', label:'MYANMAR',  detail:'Junta vs resistance — 2M displaced'},
  {lat:15.5,  lon:47.5,  col:'#ff8c42', label:'YEMEN',    detail:'Houthi attacks on Red Sea shipping'},
  {lat:33.85, lon:35.85, col:'#ff8c42', label:'LEBANON',  detail:'Cross-border fire continuing'},
  {lat:4.85,  lon:31.6,  col:'#ffb400', label:'S.SUDAN',  detail:'Renewed fighting — aid access cut'},
];

// Live events fetched from GDELT — populated by fetchLiveEvents()
var liveEvents=[];
var staticEvents=[
  {tag:'UKRAINE',  col:'#ff3d5a', text:'Russian missile salvo targets Kyiv power infrastructure'},
  {tag:'GAZA',     col:'#ff3d5a', text:'IDF ground forces advance in northern corridor'},
  {tag:'RED SEA',  col:'#ff8c42', text:'Houthi anti-ship missile intercepted by USS Gravely'},
  {tag:'IRAN',     col:'#ff8c42', text:'IRGC elevates ballistic missile readiness posture'},
  {tag:'SUDAN',    col:'#ffb400', text:'UN declares famine in North Darfur — 750K at risk'},
  {tag:'MYANMAR',  col:'#ffb400', text:'Resistance forces capture key Sagaing bridge'},
];

function renderEvents(events){
  var el=document.getElementById('gi-events');
  if(!el)return;
  el.innerHTML=events.slice(0,5).map(function(e){
    return '<div class="gi-ev">'
      +'<div class="gi-ev-dot" style="background:'+e.col+';animation-delay:'+(Math.random()*.8)+'s"></div>'
      +'<div class="gi-ev-text"><span class="gi-ev-tag" style="color:'+e.col+'">'+e.tag+'</span>'+e.text+'</div>'
      +'</div>';
  }).join('');
}

// Fetch live events from GDELT (public CORS-enabled API)
function fetchLiveEvents(){
  var url='https://api.gdeltproject.org/api/v2/doc/doc?query=war+conflict+military&mode=artlist&maxrecords=10&format=json&timespan=2h';
  fetch(url,{signal:AbortSignal.timeout(4000)})
    .then(function(r){return r.json();})
    .then(function(data){
      if(data&&data.articles&&data.articles.length){
        liveEvents=data.articles.slice(0,5).map(function(a){
          var title=(a.title||'').slice(0,80);
          // Tag by keywords
          var t='GLOBAL',c='#00c8ff';
          var tl=title.toLowerCase();
          if(tl.indexOf('ukraine')>=0||tl.indexOf('russia')>=0||tl.indexOf('kyiv')>=0){t='UKRAINE';c='#ff3d5a';}
          else if(tl.indexOf('gaza')>=0||tl.indexOf('israel')>=0||tl.indexOf('idf')>=0){t='GAZA';c='#ff3d5a';}
          else if(tl.indexOf('iran')>=0||tl.indexOf('irgc')>=0){t='IRAN';c='#ff8c42';}
          else if(tl.indexOf('sudan')>=0||tl.indexOf('darfur')>=0){t='SUDAN';c='#ffb400';}
          else if(tl.indexOf('houthi')>=0||tl.indexOf('yemen')>=0||tl.indexOf('red sea')>=0){t='RED SEA';c='#ff8c42';}
          else if(tl.indexOf('myanmar')>=0||tl.indexOf('burma')>=0){t='MYANMAR';c='#ffb400';}
          return{tag:t,col:c,text:title};
        });
        renderEvents(liveEvents);
        // Update ticker with live headlines
        var tk=document.getElementById('gi-tkscroll');
        if(tk){
          var txt=liveEvents.map(function(e){return '&#x25C6;&nbsp;'+e.tag+': '+e.text+'&nbsp;&nbsp;&nbsp;'}).join('');
          tk.innerHTML=txt+txt; // double for seamless loop
        }
        document.getElementById('gi-feeds').textContent='12 / 12 LIVE';
      } else {
        renderEvents(staticEvents);
      }
    })
    .catch(function(){renderEvents(staticEvents);});
}
// Start fetching immediately
fetchLiveEvents();
// Re-fetch every 30s to stay fresh during the 10s intro
setInterval(fetchLiveEvents,30000);

// ── Globe: orthographic projection with real lat/lon ──
var gRot=0, gTilt=18*Math.PI/180;

function ll2xy(lat,lon,r,cx,cy){
  // lon offset by gRot so hotspots rotate WITH the grid
  var la=lat*Math.PI/180;
  var lo=(lon*Math.PI/180)+gRot;
  var x=r*Math.cos(la)*Math.sin(lo);
  var y=r*(Math.sin(la)*Math.cos(gTilt)-Math.cos(la)*Math.cos(lo)*Math.sin(gTilt));
  var z=Math.cos(la)*Math.cos(lo)*Math.cos(gTilt)+Math.sin(la)*Math.sin(gTilt);
  return{x:cx+x,y:cy-y,z:z};
}

// Build continent outline points (simplified)
// Key coastline points as lat/lon pairs for major landmasses
var CONTINENTS=[
  // Europe western edge
  [[71,28],[70,31],[69,33],[67,14],[66,14],[65,14],[63,8],[61,5],[59,5],[58,8],[57,11],[55,8],[54,10],[54,18],[52,14],[51,4],[50,2],[48,2],[46,2],[43,2],[42,2],[40,2],[38,9],[36,5],[36,5],[36,2],[36,-5],[35,-6],[36,-5],[38,9],[40,2],[42,2],[43,7],[44,15],[42,19],[41,20],[40,26],[38,27],[37,27],[36,36],[36,36]],
  // Africa
  [[37,10],[37,36],[30,32],[22,37],[12,43],[11,42],[4,42],[0,42],[-4,40],[-10,38],[-22,35],[-30,30],[-34,26],[-34,18],[-28,17],[-22,14],[-18,12],[-14,12],[-5,10],[0,9],[4,7],[4,2],[3,9],[5,1],[5,-5],[4,-9],[2,-9],[0,-9],[-2,-9],[-5,-12],[-5,-12],[-10,-14],[-15,-12],[-16,-12],[-18,-13],[-22,-14],[-18,12]],
  // Asia outline (simplified)
  [[70,30],[70,60],[70,90],[70,140],[60,140],[55,135],[50,135],[43,141],[40,130],[35,130],[30,122],[25,120],[20,110],[15,108],[10,105],[5,103],[1,104],[-5,105],[-8,115],[-10,120],[0,110],[10,105],[20,93],[20,93],[25,90],[23,91],[22,92],[21,92],[20,93],[15,100],[10,99],[5,101],[5,103],[10,77],[8,77],[8,80],[9,80],[10,78],[8,77],[12,80],[15,80],[20,86],[22,92],[25,87],[27,89],[26,88],[24,92],[22,92],[20,92],[18,92],[16,94],[15,100],[10,99],[5,105],[0,105],[-5,105],[-8,114],[-8,115],[-5,120],[0,109],[5,102],[10,99],[12,98],[16,97],[20,93],[20,92]],
  // North America
  [[70,-140],[71,-130],[72,-125],[73,-115],[74,-95],[73,-85],[72,-80],[71,-75],[70,-70],[68,-52],[65,-52],[60,-65],[55,-60],[50,-55],[47,-53],[44,-66],[42,-70],[42,-70],[40,-74],[38,-75],[35,-76],[32,-80],[27,-80],[25,-80],[24,-82],[22,-80],[18,-66],[18,-66],[10,-85],[8,-77],[9,-80],[10,-85],[15,-88],[18,-88],[20,-87],[22,-86],[24,-84],[28,-82],[30,-82],[32,-80],[35,-76],[38,-75],[40,-74],[43,-70],[45,-63],[47,-53],[50,-55],[55,-60],[59,-64],[60,-65],[62,-64],[65,-52],[68,-52],[70,-55],[70,-65],[70,-75],[70,-80],[71,-85],[72,-80],[73,-85],[74,-95],[73,-115],[72,-130],[71,-140],[70,-140]],
  // South America
  [[10,-62],[10,-75],[0,-80],[-5,-81],[-10,-77],[-18,-70],[-22,-70],[-25,-70],[-30,-71],[-34,-71],[-38,-72],[-42,-73],[-46,-74],[-50,-75],[- 55,-68],[-55,-65],[-52,-58],[-50,-50],[-45,-42],[-40,-40],[-35,-38],[-30,-38],[-25,-38],[-22,-41],[-20,-40],[-15,-39],[-10,-37],[-8,-35],[-5,-35],[0,-50],[-5,-50],[-2,-44],[0,-42],[2,-52],[5,-53],[8,-60],[10,-62]],
  // Australia
  [[-14,135],[-15,130],[-15,124],[-18,122],[-20,119],[-22,114],[-25,114],[-28,114],[-32,115],[-35,117],[-38,140],[-39,147],[-38,147],[-35,150],[-32,152],[-28,153],[-25,153],[-20,148],[-16,145],[-14,144],[-12,136],[-12,136],[-14,135]],
];

var globeAlpha=1.0, globeFading=false;

function drawGlobe(){
  var cx=W*.5,cy=H*.5,r=Math.min(W,H)*.25;

  // Atmosphere glow
  var ag=gbX.createRadialGradient(cx,cy,r*.7,cx,cy,r*1.12);
  ag.addColorStop(0,'rgba(0,200,255,0)');ag.addColorStop(.75,'rgba(0,200,255,.025)');ag.addColorStop(1,'rgba(0,200,255,.1)');
  gbX.beginPath();gbX.arc(cx,cy,r*1.12,0,Math.PI*2);gbX.fillStyle=ag;gbX.fill();

  // Latitude grid lines
  for(var lat=-75;lat<=75;lat+=15){
    var pp=[];for(var lo=-180;lo<=180;lo+=3)pp.push(ll2xy(lat,lo,r,cx,cy));
    gbX.beginPath();var go=false;
    for(var k=0;k<pp.length;k++){
      if(pp[k].z<0){go=false;continue;}
      if(!go){gbX.moveTo(pp[k].x,pp[k].y);go=true;}else gbX.lineTo(pp[k].x,pp[k].y);
    }
    gbX.strokeStyle=lat===0?'rgba(0,200,255,.22)':'rgba(0,200,255,.06)';
    gbX.lineWidth=lat===0?1.2:.5;gbX.stroke();
  }

  // Longitude grid lines
  for(var lo2=-180;lo2<180;lo2+=20){
    var pp2=[];for(var la2=-90;la2<=90;la2+=3)pp2.push(ll2xy(la2,lo2,r,cx,cy));
    gbX.beginPath();var go2=false;
    for(var k=0;k<pp2.length;k++){
      if(pp2[k].z<0){go2=false;continue;}
      if(!go2){gbX.moveTo(pp2[k].x,pp2[k].y);go2=true;}else gbX.lineTo(pp2[k].x,pp2[k].y);
    }
    gbX.strokeStyle='rgba(0,200,255,.04)';gbX.lineWidth=.4;gbX.stroke();
  }

  // Continent outlines — drawn as connected lat/lon paths
  CONTINENTS.forEach(function(pts){
    gbX.beginPath();var started=false;
    for(var i=0;i<pts.length;i++){
      var p=ll2xy(pts[i][0],pts[i][1],r,cx,cy);
      if(p.z<0.1){started=false;continue;}
      if(!started){gbX.moveTo(p.x,p.y);started=true;}else gbX.lineTo(p.x,p.y);
    }
    gbX.strokeStyle='rgba(0,200,255,.18)';gbX.lineWidth=.8;gbX.stroke();
    // Subtle continent fill
    gbX.fillStyle='rgba(0,200,255,.015)';gbX.fill();
  });

  // Globe rim
  gbX.beginPath();gbX.arc(cx,cy,r,0,Math.PI*2);
  gbX.strokeStyle='rgba(0,200,255,.2)';gbX.lineWidth=1;gbX.stroke();

  // Conflict hotspots — pinned to real lat/lon, rotate with globe
  var now=Date.now();
  HOTSPOTS.forEach(function(h,idx){
    var p=ll2xy(h.lat,h.lon,r,cx,cy);
    if(p.z<0.08)return; // behind globe — don't draw

    var pulse=(Math.sin(now*.003+idx*0.9)+1)*.5;
    var hx=h.col.replace('#','');
    var R=parseInt(hx.slice(0,2),16),G=parseInt(hx.slice(2,4),16),B=parseInt(hx.slice(4,6),16);

    // Outer pulsing ring
    gbX.beginPath();gbX.arc(p.x,p.y,7+pulse*8,0,Math.PI*2);
    gbX.strokeStyle='rgba('+R+','+G+','+B+','+(0.35*(1-pulse*.7))+')';
    gbX.lineWidth=1.2;gbX.stroke();

    // Middle ring
    gbX.beginPath();gbX.arc(p.x,p.y,4,0,Math.PI*2);
    gbX.strokeStyle='rgba('+R+','+G+','+B+',.6)';gbX.lineWidth=1;gbX.stroke();

    // Core dot
    gbX.beginPath();gbX.arc(p.x,p.y,2.5,0,Math.PI*2);
    gbX.fillStyle=h.col;gbX.fill();

    // Glow
    var glo=gbX.createRadialGradient(p.x,p.y,0,p.x,p.y,12);
    glo.addColorStop(0,'rgba('+R+','+G+','+B+','+(0.2+pulse*.15)+')');
    glo.addColorStop(1,'rgba('+R+','+G+','+B+',0)');
    gbX.beginPath();gbX.arc(p.x,p.y,12,0,Math.PI*2);gbX.fillStyle=glo;gbX.fill();

    // Label with connecting tick
    var lx=p.x+(p.x>cx?12:-12),anchor=p.x>cx?'left':'right';
    gbX.font='500 '+Math.round(W*.006+5)+'px "IBM Plex Mono",monospace';
    gbX.textAlign=p.x>cx?'left':'right';gbX.textBaseline='middle';
    gbX.fillStyle='rgba(226,236,248,.7)';
    gbX.fillText(h.label,lx+( p.x>cx?2:-2),p.y);
    // tick line
    gbX.beginPath();gbX.moveTo(p.x+(p.x>cx?3:-3),p.y);gbX.lineTo(lx,p.y);
    gbX.strokeStyle='rgba('+R+','+G+','+B+',.35)';gbX.lineWidth=.7;gbX.stroke();
  });
}

// ── FX: radar + orbital rings + data arcs ─────────
function drawFX(){
  var cx=W*.5,cy=H*.5,r=Math.min(W,H)*.25,now=Date.now();
  var ang=(now/4200)*Math.PI*2;

  // Radar sweep
  fxX.save();fxX.beginPath();fxX.moveTo(cx,cy);fxX.arc(cx,cy,r,ang-.65,ang);fxX.closePath();
  var rg=fxX.createRadialGradient(cx,cy,0,cx,cy,r);
  rg.addColorStop(0,'rgba(0,200,255,0)');rg.addColorStop(.5,'rgba(0,200,255,.04)');rg.addColorStop(1,'rgba(0,200,255,.11)');
  fxX.fillStyle=rg;fxX.fill();fxX.restore();
  fxX.beginPath();fxX.moveTo(cx,cy);fxX.lineTo(cx+Math.cos(ang)*r,cy+Math.sin(ang)*r);
  fxX.strokeStyle='rgba(0,200,255,.35)';fxX.lineWidth=1.2;fxX.stroke();

  // Orbital ring (amber)
  fxX.beginPath();fxX.ellipse(cx,cy,r*1.2,r*1.2*.27,now/8500,0,Math.PI*2);
  fxX.strokeStyle='rgba(255,180,0,.12)';fxX.lineWidth=1;fxX.stroke();

  // Orbital ring 2 (cyan)
  fxX.beginPath();fxX.ellipse(cx,cy,r*1.38,r*1.38*.21,-now/13000,0,Math.PI*2);
  fxX.strokeStyle='rgba(0,200,255,.06)';fxX.lineWidth=.7;fxX.stroke();

  // Satellite dot + trail
  var sa=now/8500,sx=cx+Math.cos(sa)*r*1.2,sy=cy+Math.sin(sa)*r*1.2*.27;
  for(var t=5;t>=0;t--){
    var ta=sa-t*.04,tx=cx+Math.cos(ta)*r*1.2,ty=cy+Math.sin(ta)*r*1.2*.27;
    fxX.beginPath();fxX.arc(tx,ty,t===0?3:3-t*.38,0,Math.PI*2);
    fxX.fillStyle='rgba(255,180,0,'+(t===0?1:0.5-t*.08)+')';fxX.fill();
  }

  // Data arcs from hotspots to globe center — using real projected positions
  var sA=now*.00085;
  HOTSPOTS.forEach(function(h,idx){
    var ph=(sA+idx*1.05)%(Math.PI*2);if(ph>Math.PI)return;
    var pg=ph/Math.PI;
    // Project hotspot to screen
    var p=ll2xy(h.lat,h.lon,Math.min(W,H)*.25,cx,cy);
    if(p.z<0.1)return;
    var mx=(p.x+cx)*.5+20*Math.sin(idx*1.3),my=(p.y+cy)*.5-50;
    fxX.beginPath();fxX.moveTo(p.x,p.y);
    fxX.quadraticCurveTo(mx,my,p.x+(cx-p.x)*pg,p.y+(cy-p.y)*pg);
    var hx=h.col.replace('#','');
    fxX.strokeStyle='rgba('+parseInt(hx.slice(0,2),16)+','+parseInt(hx.slice(2,4),16)+','+parseInt(hx.slice(4,6),16)+','+(Math.sin(pg*Math.PI)*.28)+')';
    fxX.lineWidth=.9;fxX.stroke();
  });
}

// ── BG: dot grid + particles ──────────────────────
function drawBG(){
  bgX.clearRect(0,0,W,H);var now=Date.now();
  for(var gx=0;gx<W;gx+=55)for(var gy=0;gy<H;gy+=55){
    var p=Math.sin(now*.0005+gx*.018+gy*.014)*.5+.5;
    bgX.globalAlpha=.02+p*.04;bgX.fillStyle='#00c8ff';bgX.fillRect(gx,gy,1,1);
  }
  bgX.globalAlpha=1;
  var sx=W/1920,sy=H/1080;
  for(var i=0;i<pts.length;i++){
    var p=pts[i];p.x+=p.vx;p.y+=p.vy;
    if(p.x<0)p.x=1920;if(p.x>1920)p.x=0;if(p.y<0)p.y=1080;if(p.y>1080)p.y=0;
    p.ph+=.025;var pa=.18+Math.sin(p.ph)*.12;
    bgX.beginPath();bgX.arc(p.x*sx,p.y*sy,p.r,0,Math.PI*2);
    bgX.fillStyle=p.warm?'rgba(255,180,0,'+pa+')':'rgba(0,200,255,'+pa+')';bgX.fill();
    for(var j=i+1;j<pts.length;j++){
      var dx=(p.x-pts[j].x)*sx,dy=(p.y-pts[j].y)*sy,d=Math.sqrt(dx*dx+dy*dy);
      if(d<75){bgX.beginPath();bgX.moveTo(p.x*sx,p.y*sy);bgX.lineTo(pts[j].x*sx,pts[j].y*sy);bgX.strokeStyle='rgba(0,200,255,'+(0.05*(1-d/75))+')';bgX.lineWidth=.4;bgX.stroke();}
    }
  }
}

// ── Globe fade at 5s ──────────────────────────────
var globeAlpha=1.0,globeFading=false;

setTimeout(function(){
  globeFading=true;
  var lw=document.getElementById('gi-lw');
  var dv=document.getElementById('gi-div');
  var ev=document.getElementById('gi-events');
  if(lw){lw.style.transition='opacity 0.9s ease';lw.style.opacity='0';}
  if(dv){dv.style.transition='opacity 0.9s ease';dv.style.opacity='0';}
  if(ev){ev.style.transition='opacity 0.9s ease';ev.style.opacity='0';}
},5000);

// ── Main render loop ──────────────────────────────
function render(){
  gRot+=.0018; // globe rotation speed
  drawBG();
  if(globeAlpha>0){
    if(globeFading) globeAlpha=Math.max(0,globeAlpha-0.012);
    gbX.clearRect(0,0,W,H);fxX.clearRect(0,0,W,H);
    if(globeAlpha>0){
      gbX.globalAlpha=globeAlpha;fxX.globalAlpha=globeAlpha;
      drawGlobe();drawFX();
      gbX.globalAlpha=1;fxX.globalAlpha=1;
    }
  } else {
    gbX.clearRect(0,0,W,H);fxX.clearRect(0,0,W,H);
  }
  requestAnimationFrame(render);
}
render();

// ── Skip ──────────────────────────────────────────
window.geoSkip=function(){
  var ov=document.getElementById('geo-intro');
  if(ov){ov.style.transition='opacity .6s ease';ov.style.opacity='0';setTimeout(function(){ov.style.display='none';},650);}
};
})();
</script>
</body></html>""", height=700, scrolling=False)

    _it.sleep(10)
    st.session_state["intro_shown"] = True
    st.rerun()


# HEADER
# ─────────────────────────────────────────────
m5p         = eq_df[eq_df["mag"]>=5.0]
crit_mv     = [m for m in MOVEMENTS if m["sentiment"]=="CRIT"]
kp          = kp_data["kp"]
active_conf = len([c for c in CONFLICTS.values() if c["status"]=="ACTIVE"])
total_cas   = sum(c["casualties_total"] for c in CONFLICTS.values())

st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:4px">
  <div>
    <div class="wordmark">THE GEO-<em>LOCATOR</em></div>
    <div style="font-size:11px;letter-spacing:.14em;color:var(--muted);font-weight:600;margin-top:3px">
      GLOBAL INTELLIGENCE OPERATIONS CENTER
    </div>
  </div>
  <div style="text-align:right">
    <div style="font-family:var(--fd);font-size:18px;letter-spacing:.1em;color:var(--cyan)">{utc_now}</div>
    <div style="font-size:11px;color:var(--muted);margin-top:2px">All times in UTC · Auto-refreshes every 5 min</div>
  </div>
</div>
<div class="status-row">
  <span><span class="pulse p-green"></span>FEEDS LIVE</span>
  <span><span class="pulse p-red"></span>{active_conf} ACTIVE CONFLICTS</span>
  <span><span class="pulse p-cyan"></span>{len(eq_df)} SEISMIC (24H)</span>
  <span><span class="pulse p-{'red' if crit_mv else 'amber'}"></span>{len(crit_mv)} CRITICAL MOVEMENTS</span>
  <span><span class="pulse p-{'red' if kp>=5 else 'amber'}"></span>Kp {kp:.1f}{'  ⚠ STORM WATCH' if kp>=5 else ''}</span>
</div>""", unsafe_allow_html=True)

c1,c2,c3,c4,c5 = st.columns(5)
# Compute deltas vs previous refresh
_d_eq   = len(eq_df)  - st.session_state.get("prev_eq_count", len(eq_df))
_d_conf = active_conf - st.session_state.get("prev_active_conf", active_conf)
_d_cas  = total_cas   - st.session_state.get("prev_total_cas", total_cas)
# Save current values for next refresh
st.session_state["prev_eq_count"]    = len(eq_df)
st.session_state["prev_active_conf"] = active_conf
st.session_state["prev_total_cas"]   = total_cas

with c1: st.metric("Active Conflicts",  active_conf,      delta=f"{_d_conf:+d} since last refresh" if _d_conf != 0 else "LIVE")
with c2: st.metric("Total Casualties",  f"{total_cas:,}", delta=f"{_d_cas:+,} since last refresh" if _d_cas != 0 else "All theatres")
with c3: st.metric("Seismic (24h)",     len(eq_df),       delta=f"{_d_eq:+d} new · M5+: {len(m5p)}")
with c4: st.metric("Civil Movements",   len(MOVEMENTS),   delta=f"Critical: {len(crit_mv)}")
with c5: st.metric("Kp Index",          f"{kp:.1f}",       delta="Storm ≥5.0")
# ── Geomagnetic storm banner ──────────────────────────────────
if kp >= 5:
    _kp_level = "G5 EXTREME" if kp>=9 else "G4 SEVERE" if kp>=8 else "G3 STRONG" if kp>=7 else "G2 MODERATE" if kp>=6 else "G1 MINOR"
    st.markdown(f"""
    <div style="background:rgba(255,61,90,.1);border:1px solid rgba(255,61,90,.4);border-radius:10px;
                padding:10px 18px;margin-bottom:12px;display:flex;align-items:center;gap:16px">
      <div style="font-size:20px">🌌</div>
      <div>
        <div style="font-family:var(--fd);font-size:16px;letter-spacing:.1em;color:#ff3d5a">
          GEOMAGNETIC STORM ALERT — Kp {kp:.1f} ({_kp_level})
        </div>
        <div style="font-family:var(--fm);font-size:11px;color:var(--muted);margin-top:2px">
          Solar wind speed: {solar_data['speed']:.0f} km/s · 10cm flux: {solar_data['flux']:.0f} sfu ·
          Impacts: GPS degradation, HF radio blackout, satellite drag, aurora at mid-latitudes
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# GLOBAL MAP
# ─────────────────────────────────────────────
total_inc     = sum(len(c["incidents"]) for c in CONFLICTS.values())
crit_inc_cnt  = sum(1 for c in CONFLICTS.values() for i in c["incidents"] if i["severity"]=="CRITICAL")
hist_crit     = sum(1 for e in HISTORICAL_EVENTS if e["severity"]=="CRITICAL")

_dot = lambda c: f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{c};margin-right:4px"></span>'

# Live refresh indicator
import time as _time_mod
_now_ts = datetime.now(tz=timezone.utc)
_next_refresh_s = 60 - (_now_ts.second % 60)
st.markdown(f"""<div style="display:flex;align-items:center;gap:14px;margin-bottom:6px;
  font-family:var(--fm);font-size:10px;color:var(--muted)">
  <span><span class="pulse p-green" style="margin-right:4px"></span>
  LIVE DATA — refreshes every 60s &nbsp;|&nbsp; 
  Last updated: <span style="color:var(--cyan)">{_now_ts.strftime('%H:%M:%S')} UTC</span> &nbsp;|&nbsp;
  Next refresh in: <span style="color:var(--cyan)">{_next_refresh_s}s</span>
  </span>
  <span style="margin-left:auto">
    USGS seismic: <span style="color:#00c8ff">{len(eq_df)} events</span> &nbsp;·&nbsp;
    M5+: <span style="color:#ff3d5a">{len(m5p)}</span> &nbsp;·&nbsp;
    EONET: <span style="color:#ff6a28">{len(eonet_df)}</span>
  </span>
</div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class="map-top-bar">
  <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
    <div class="map-title-text">🌐 GLOBAL COMMAND MAP</div>
    <div style="font-family:var(--fm);font-size:10px;color:var(--muted)">
      Click any marker for details · {len(HISTORICAL_EVENTS)} historical events since 2022 · Toggle layers in sidebar
    </div>
  </div>
  <div class="map-legend">
    <span>{_dot("#00c8ff")}Seismic</span>
    <span>{_dot("#ff6a28")}EONET</span>
    <span>{_dot("#ff3d5a")}Conflict</span>
    <span>{_dot("#9d6eff")}Civil</span>
    <span>{_dot("#ff3d5a88")}History</span>
    <span>{_dot("#00ffc8")}Live</span>
    <span style="margin-left:6px;padding-left:6px;border-left:1px solid rgba(0,200,255,.15)">
      <span class="pulse p-red"></span>{crit_inc_cnt} CRITICAL
    </span>
    <span><span class="pulse p-cyan"></span>{len(eq_df)} seismic</span>
    <span><span class="pulse p-orange"></span>{total_inc} incidents</span>
    <span><span class="pulse p-amber"></span>{hist_crit} hist.critical</span>
    <span class="live-badge"><span class="pulse p-red" style="margin-right:3px"></span>LIVE</span>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown('<div style="border:1px solid rgba(0,200,255,.12);border-top:none;border-radius:0 0 14px 14px;overflow:hidden;margin-bottom:8px">', unsafe_allow_html=True)
_map_selection = st.pydeck_chart(
    build_global_map(eq_df, eonet_df, show_seis, show_volc, show_mvmt, show_conf, show_supp, show_heat,
        show_hist=show_hist, show_live=show_live,
        show_intel=show_intel, show_czones=show_czones, show_mbases=show_mbases,
        show_nuclear=show_nuclear, show_gamma=show_gamma, show_space=show_space,
        show_cables=show_cables, show_pipes=show_pipes, show_aidc=show_aidc,
        show_milact=show_milact, show_ships=show_ships, show_trade=show_trade,
        show_gps=show_gps, show_orbital=show_orbital, show_cii=show_cii,
        show_displaced=show_displaced, show_climate=show_climate, show_weather=show_weather,
        show_outages=show_outages, show_cyber=show_cyber, show_econ=show_econ,
        show_minerals=show_minerals, show_waterways=show_waterways,
        show_fires_layer=show_fires_layer, show_protests=show_protests, show_aviation=show_aviation,
        show_ais=show_ais, show_opensky=show_opensky, show_acled=show_acled),
    use_container_width=True,
    on_select="rerun",
    selection_mode="single-object",
    key=f"global_map_{int(_now_ts.timestamp()) // 60}",
)
st.markdown('</div>', unsafe_allow_html=True)

# ── Click-to-Analyse Panel ────────────────────────────────────────────────────
# Parse the selected object from the map click
_clicked_obj = None
try:
    if _map_selection and hasattr(_map_selection, "selection"):
        _sel = _map_selection.selection
        # _sel.objects is a dict: {layer_id: [list of data row dicts]}
        if _sel and hasattr(_sel, "objects"):
            for _layer_id, _items in _sel.objects.items():
                if _items:
                    _clicked_obj = dict(_items[0])
                    break
        elif isinstance(_sel, dict):
            for _layer_id, _items in _sel.get("objects", {}).items():
                if _items:
                    _clicked_obj = dict(_items[0])
                    break
except Exception:
    _clicked_obj = None

# Persist last click in session state so panel stays visible after reruns
if _clicked_obj:
    st.session_state["_last_clicked"] = _clicked_obj
elif "_last_clicked" not in st.session_state:
    st.session_state["_last_clicked"] = None

# Show "click a point" hint if nothing selected yet
if not st.session_state.get("_last_clicked"):
    st.markdown(
        '<div style="text-align:center;padding:10px;font-family:var(--fm);font-size:11px;color:var(--muted);' +
        'background:var(--card);border:1px solid var(--bord2);border-radius:10px;margin-bottom:16px">' +
        '📍 Click any marker on the map to open its Intelligence Profile' +
        '</div>',
        unsafe_allow_html=True
    )
else:
    _co = st.session_state["_last_clicked"]
    _tip     = str(_co.get("tip", ""))
    _name    = str(_co.get("name", _co.get("title", _co.get("place", ""))))
    _country = get_country_from_tip(_tip)
    if not _country:
        for c in COUNTRY_INTEL:
            if c.lower() in _name.lower() or c.lower() in _tip.lower():
                _country = c
                break
    _col1, _col2 = st.columns([9, 1])
    with _col2:
        if st.button("✕ Clear", key="clear_intel"):
            st.session_state["_last_clicked"] = None
            st.rerun()
    _render_intelligence_panel(_tip, _name, _country, _co)

# ── LIVE EVENTS TRACKER (below global map, always visible) ────────────────
# Fetch in background — use cached result if available, otherwise show
# a lightweight placeholder while the GDELT call completes on next rerun
_live_events = fetch_live_global_events(max_records=15) if st.session_state.get("_map_loaded", False) else []
st.session_state["_map_loaded"] = True
_recent_hist  = _HIST_SORTED[:6]

_tracker_cols = st.columns([2, 1], gap="medium")
with _tracker_cols[0]:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)">⚡ LIVE EVENTS TRACKER</div>
      <div class="live-badge"><span class="pulse p-red" style="margin-right:3px"></span>GDELT · 90s refresh</div>
    </div>""", unsafe_allow_html=True)
    if _live_events:
        _live_html_parts = []
        for _ev in _live_events[:8]:
            _src  = _ev["source"].upper()[:24]
            _ttl  = _ev["title"][:90] + ("…" if len(_ev["title"]) > 90 else "")
            _tm   = _ev["time"]
            _url  = _ev.get("url","")
            _link = f'<a href="{_url}" target="_blank" rel="noopener" style="font-family:var(--fm);font-size:9px;color:var(--cyan);text-decoration:none;padding:1px 7px;border:1px solid rgba(0,200,255,.22);border-radius:4px">→</a>' if _url else ""
            _live_html_parts.append(
                f'<div style="display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--bord2)">' +
                f'<div style="width:6px;height:6px;border-radius:50%;background:#00ffc8;flex-shrink:0;box-shadow:0 0 5px #00ffc8;animation:blink 1.5s infinite"></div>' +
                f'<span style="font-family:var(--fm);font-size:9px;color:#ff8c42;min-width:100px;flex-shrink:0">{_src}</span>' +
                f'<span style="font-size:11px;color:var(--text);flex:1;line-height:1.3">{_ttl}</span>' +
                f'<span style="font-family:var(--fm);font-size:9px;color:var(--muted);white-space:nowrap">{_tm}</span>' +
                _link +
                '</div>'
            )
        st.markdown(
            '<div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 14px">' +
            "".join(_live_html_parts) +
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div style="background:var(--card);border:1px solid var(--bord2);border-radius:10px;padding:10px 14px;font-family:var(--fm);font-size:11px;color:var(--muted)">GDELT live feed connecting… recent events will appear here shortly.</div>', unsafe_allow_html=True)

with _tracker_cols[1]:
    st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">📅 RECENT HISTORY (2022+)</div>', unsafe_allow_html=True)
    for _he in _recent_hist:
        _icon = HIST_TYPE_ICONS.get(_he["type"], "●")
        _sc   = {"CRITICAL":"#ff3d5a","HIGH":"#ff8c42","MED":"#ffb400"}.get(_he["severity"],"#4a6b85")
        _ttl2 = _he["title"][:60] + ("…" if len(_he["title"]) > 60 else "")
        st.markdown(
            f'<div style="display:flex;align-items:flex-start;gap:7px;padding:5px 0;border-bottom:1px solid var(--bord2)">' +
            f'<span style="font-size:12px;flex-shrink:0">{_icon}</span>' +
            f'<div style="flex:1;min-width:0">' +
            f'<div style="font-size:11px;font-weight:600;color:var(--text);line-height:1.3">{_ttl2}</div>' +
            f'<div style="font-family:var(--fm);font-size:9px;display:flex;gap:6px;margin-top:2px">' +
            f'<span style="color:{_sc}">{_he["severity"]}</span>' +
            f'<span style="color:var(--muted)">{_he["date"]}</span>' +
            '</div></div></div>',
            unsafe_allow_html=True
        )

# ── TODAY'S BRIEFING (auto-generated summary panel) ─────────
_brief_lines = []
# Top seismic
if not eq_df.empty:
    _top_eq = eq_df.nlargest(1,"mag").iloc[0]
    _brief_lines.append(f"🌍 Largest seismic: M{_top_eq['mag']} {_top_eq['place'][:40]} ({_top_eq['time']})")
# Active conflicts
_crit_conf = [n for n,c in CONFLICTS.items() if c["intensity"]=="CRITICAL"]
if _crit_conf:
    _brief_lines.append(f"⚔ Critical conflicts: {', '.join(_crit_conf)}")
# Kp storm
if kp_data["kp"] >= 5:
    _brief_lines.append(f"🌌 Geomagnetic storm: Kp {kp_data['kp']:.1f} — GPS/HF radio impacts possible")
# Solar wind
if solar_data["speed"] > 600:
    _brief_lines.append(f"☀ High solar wind: {solar_data['speed']:.0f} km/s — elevated space weather activity")
# Latest historical event
_latest_he = _HIST_SORTED[0]
_brief_lines.append(f"📅 Latest tracked event: {_latest_he['date']} — {_latest_he['title'][:60]}")
# Live feed headline
if _live_events:
    _brief_lines.append(f"⚡ Live: {_live_events[0]['source'].upper()} — {_live_events[0]['title'][:70]}")
# FIRMS
if firms_cnt > 0:
    _brief_lines.append(f"🔥 Active wildfires tracked by NASA FIRMS/EONET: {firms_cnt}")

_brief_html = "".join(
    f'<div style="display:flex;align-items:flex-start;gap:8px;padding:4px 0;border-bottom:1px solid var(--bord2)">'
    f'<div style="font-size:12px;line-height:1.45;color:var(--text2)">{line}</div>'
    f'</div>'
    for line in _brief_lines
)
st.markdown(
    f'<div style="background:var(--panel);border:1px solid var(--border);border-radius:10px;'
    f'padding:12px 16px;margin-bottom:14px">'
    f'<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;'
    f'color:var(--muted);margin-bottom:8px">📋 TODAY\'S BRIEFING &mdash; {utc_now}</div>'
    + _brief_html +
    '</div>',
    unsafe_allow_html=True
)

# Ticker — now includes live events
_live_ticker = [f'<span style="color:#00ffc8">⚡ {a["source"].upper()}: {a["title"][:50]}</span>' for a in _live_events[:5]]
tb = (
    [f'<span class="t-red t-hi">⚔ {n}: {c["intensity"]}</span>' for n,c in CONFLICTS.items()] +
    [f'<span class="t-red">M{r.mag} {r.place[:28]}</span>'       for _,r in eq_df.nlargest(5,"mag").iterrows()] +
    [f'<span class="t-amb">✊ {m["title"]} — {m["location"]}</span>' for m in MOVEMENTS[:3]] +
    _live_ticker
)
ts = '<span class="t-sep"> ◈ </span>'.join(tb)
st.markdown(f'<div class="ticker-wrap"><div class="ticker-inner">{ts}<span class="t-sep"> ◈ </span>{ts}</div></div>', unsafe_allow_html=True)
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS  (removed Training Arena + AI Analyst)
# ─────────────────────────────────────────────
tab_conflict, tab_earth, tab_civil, tab_news, tab_intel, tab_sigint, tab_econ, tab_facility = st.tabs([
    "⚔  Conflict Dashboard",
    "🌍  Earth Signals",
    "✊  Civil Movements",
    "📡  Live News",
    "🛰  Intel Dashboard",
    "📻  SIGINT",
    "📊  Economic & Markets",
    "🏭  Facility Map",
])

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_layoffs() -> list:
    """
    Pull live layoff reports from Google News RSS + GDELT Doc API.
    Returns list of dicts: {company, headline, count, sector, date, age, source, url, severity, ts}
    Falls back to static LAYOFFS constant if all sources fail.
    """
    import xml.etree.ElementTree as ET
    from datetime import datetime, timezone

    results = []
    seen_titles = set()

    LAYOFF_KWS = [
        "layoffs", "job cuts", "job losses", "workforce reduction",
        "redundancies", "downsizing", "headcount reduction",
        "cutting jobs", "eliminating positions", "mass layoff",
        "let go", "retrenchment", "restructuring workers",
    ]

    def _age(dt):
        s = int((datetime.now(tz=timezone.utc) - dt).total_seconds())
        if s < 3600:  return str(s // 60) + "m ago"
        if s < 86400: return str(s // 3600) + "h ago"
        return str(s // 86400) + "d ago"

    def _parse_dt(raw):
        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                    "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]:
            try: return datetime.strptime(raw.strip(), fmt).astimezone(timezone.utc)
            except Exception: pass
        return datetime.now(tz=timezone.utc)

    def _severity(text):
        t = text.lower()
        nums = re.findall(r"([0-9][0-9,]*)\s*(?:jobs?|workers?|employees?|roles?|people|staff)", t)
        n = max((int(x.replace(",", "")) for x in nums if x.replace(",","").isdigit()), default=0)
        if n >= 5000 or any(w in t for w in ["massive","sweeping","thousands"]): return "Critical"
        if n >= 1000 or any(w in t for w in ["significant","hundreds"]): return "High"
        if n >= 200: return "Med"
        return "Low"

    def _count(text):
        nums = re.findall(r"([0-9][0-9,]*)\s*(?:jobs?|workers?|employees?|roles?|people|staff)", text.lower())
        if nums: return "~" + max(nums, key=lambda x: int(x.replace(",","0")))
        pcts = re.findall(r"([0-9]+(?:[.][0-9]+)?)\s*%\s*(?:of\s*)?(?:workforce|staff|employees?)", text.lower())
        if pcts: return "~" + pcts[0] + "% workforce"
        return "undisclosed"

    def _sector(text):
        t = text.lower()
        if any(w in t for w in ["tech","software","google","microsoft","amazon","meta","apple","nvidia","ai ","chip","semiconductor"]): return "Tech"
        if any(w in t for w in ["bank","finance","goldman","jpmorgan","citi","hedge","insurance","fintech"]): return "Finance"
        if any(w in t for w in ["pharma","biotech","healthcare","hospital","medical","pfizer","drug"]): return "Health"
        if any(w in t for w in ["auto","ford","gm","tesla","vehicle","toyota","volkswagen","car "]): return "Auto"
        if any(w in t for w in ["retail","walmart","target","shop","store","consumer"]): return "Retail"
        if any(w in t for w in ["media","disney","netflix","streaming","entertainment","cnn","nbc"]): return "Media"
        if any(w in t for w in ["airline","boeing","airbus","travel","hotel","hospitality"]): return "Travel"
        if any(w in t for w in ["energy","oil","gas","mining","shell","bp ","exxon"]): return "Energy"
        if any(w in t for w in ["telecom","at&t","verizon","comms","wireless","t-mobile"]): return "Telecom"
        return "Other"

    def _company(title):
        m2 = re.match(
            r"^([A-Z][A-Za-z0-9&\.\- ]{1,28}?)"
            r"(?:\s+(?:to\s+)?(?:lay\s*off|cut|slash|fire|eliminat|reduc|announc|plan|axe))",
            title
        )
        return m2.group(1).strip() if m2 else title.split()[0][:22]

    # ── Source 1: Google News RSS ─────────────────────────────────────────────
    gn_queries = [
        "company layoffs job cuts 2026",
        "workforce reduction employees fired 2026",
        "tech layoffs jobs eliminated",
    ]
    for q in gn_queries:
        try:
            url = (
                "https://news.google.com/rss/search?q="
                + requests.utils.quote(q)
                + "&hl=en-US&gl=US&ceid=US:en"
            )
            r = requests.get(url, timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (compatible; GeoLocator/1.0)"})
            if r.status_code != 200:
                continue
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:15]:
                title = (item.findtext("title") or "").strip()
                link  = (item.findtext("link") or "").strip()
                pub   = (item.findtext("pubDate") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                full  = (title + " " + desc).lower()
                if not any(kw in full for kw in LAYOFF_KWS):
                    continue
                key = title[:55].lower()
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                dt = _parse_dt(pub)
                results.append({
                    "company":  _company(title),
                    "headline": title[:110],
                    "count":    _count(title + " " + desc),
                    "sector":   _sector(title + " " + desc),
                    "date":     dt.strftime("%Y-%m-%d"),
                    "age":      _age(dt),
                    "source":   "Google News",
                    "url":      link,
                    "severity": _severity(title + " " + desc),
                    "ts":       dt.timestamp(),
                })
        except Exception:
            continue

    # ── Source 2: GDELT Doc API ───────────────────────────────────────────────
    try:
        gdelt_q = "layoffs job cuts workforce reduction employees fired restructuring"
        r = requests.get(
            "https://api.gdeltproject.org/api/v2/doc/doc",
            params={
                "query":      gdelt_q,
                "mode":       "artlist",
                "maxrecords": "20",
                "format":     "json",
                "timespan":   "3d",
                "sort":       "DateDesc",
                "sourcelang": "english",
            },
            timeout=10,
        )
        if r.status_code == 200:
            for a in r.json().get("articles", []):
                title = (a.get("title") or "").strip()
                url   = a.get("url", "")
                full  = title.lower()
                if not any(kw in full for kw in LAYOFF_KWS):
                    continue
                key = title[:55].lower()
                if key in seen_titles:
                    continue
                seen_titles.add(key)
                raw_dt = str(a.get("seendate", ""))
                try:
                    dt = datetime.strptime(raw_dt[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                except Exception:
                    dt = datetime.now(tz=timezone.utc)
                domain = (a.get("domain") or "").split(".")[0].upper()[:20]
                results.append({
                    "company":  _company(title),
                    "headline": title[:110],
                    "count":    _count(title),
                    "sector":   _sector(title),
                    "date":     dt.strftime("%Y-%m-%d"),
                    "age":      _age(dt),
                    "source":   domain,
                    "url":      url,
                    "severity": _severity(title),
                    "ts":       dt.timestamp(),
                })
    except Exception:
        pass

    # ── Deduplicate + sort newest first ──────────────────────────────────────
    seen2, unique = set(), []
    for item in sorted(results, key=lambda x: -x.get("ts", 0)):
        key = item["company"][:15].lower() + item["date"]
        if key not in seen2:
            seen2.add(key)
            unique.append(item)

    if unique:
        return unique[:30]

    # ── Static fallback ───────────────────────────────────────────────────────
    return [
        {**lo, "headline": lo["company"] + " — " + lo["count"] + " jobs cut",
         "age": lo["date"], "url": "", "ts": 0.0}
        for lo in LAYOFFS
    ]


# ══════════════════════════════════════════════════════════════
# TAB 1 — CONFLICT DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab_conflict:
    st.markdown("""
    <div class="helper">
      <b>Select a conflict theatre</b> below to explore its incident map, faction tracker,
      timeline, supply lines, and media reliability.
    </div>""", unsafe_allow_html=True)

    theatre = st.radio("Select theatre:", list(CONFLICTS.keys()), horizontal=True, key="theatre_sel")
    st.session_state.selected_conflict = theatre
    C = CONFLICTS[theatre]

    esc = C["escalation"]
    esc_col = "#ff3d5a" if esc>=80 else "#ff8c42" if esc>=60 else "#ffb400" if esc>=40 else "#00e676"
    esc_lbl = "CRITICAL" if esc>=80 else "HIGH" if esc>=60 else "ELEVATED" if esc>=40 else "LOW"

    o1,o2,o3,o4 = st.columns(4)
    with o1: st.metric("Status",     C["status"],    delta=C["region"])
    with o2: st.metric("Intensity",  C["intensity"], delta=f"Since {C['start']}")
    with o3: st.metric("Casualties", f"{C['casualties_total']:,}", delta="estimated")
    with o4: st.metric("Displaced",  f"{C['displaced']:,}",        delta="persons")

    st.markdown(f"""
    <div class="gcard" style="margin:12px 0">
      <div style="font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:6px">{C['region']}</div>
      <div style="font-size:14px;color:var(--text2);line-height:1.7">{C['description']}</div>
    </div>""", unsafe_allow_html=True)

    # ── LIVE CONFLICT TRACKER ──────────────────────────────────
    # Computes conflict duration and fetches GDELT news scoped to conflict start date
    from datetime import date as _date
    _start_dt   = datetime.strptime(C["start"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    _now_utc    = datetime.now(tz=timezone.utc)
    _delta      = _now_utc - _start_dt
    _days       = _delta.days
    _years      = _days // 365
    _rem_days   = _days % 365
    _months     = _rem_days // 30
    _rem_d2     = _rem_days % 30
    if _years > 0:
        _dur_str = f"{_years}y {_months}m {_rem_d2}d"
    elif _months > 0:
        _dur_str = f"{_months}m {_rem_d2}d"
    else:
        _dur_str = f"{_days}d"

    # Fetch GDELT articles scoped to this conflict (cached 2 min)
    _gdelt_articles = fetch_gdelt_conflict(theatre, max_records=40)
    _new_count  = sum(1 for a in _gdelt_articles if a.get("is_new"))
    _rec_count  = sum(1 for a in _gdelt_articles if a.get("is_recent"))

    conflict_accent = C.get("factions",[{}])[0].get("color","#ff3d5a") if C.get("factions") else "#ff3d5a"
    int_col = "#ff3d5a" if C["intensity"]=="CRITICAL" else "#ff8c42" if C["intensity"]=="HIGH" else "#ffb400"

    # ── Tracker header bar ─────────────────────────────────────
    # Build a JS live clock for conflict duration
    _start_iso   = C["start"] + "T00:00:00Z"
    _clock_id    = f"clk_{theatre.replace(' ','_').replace('–','_')}"
    import streamlit.components.v1 as _components_inner
    _clock_html = f"""<div style="background:var(--panel,#080f1c);border:1px solid {conflict_accent}33;
        border-radius:12px;padding:14px 20px;display:flex;align-items:center;
        justify-content:space-between;gap:16px;flex-wrap:wrap;font-family:'IBM Plex Mono',monospace">
      <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap">
        <div>
          <div style="font-size:9px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#4a6b85;margin-bottom:2px">CONFLICT DURATION</div>
          <div id="{_clock_id}_dur" style="font-family:'Bebas Neue',sans-serif;font-size:26px;letter-spacing:.06em;color:{conflict_accent};line-height:1">{_dur_str}</div>
          <div style="font-size:9px;color:#4a6b85;margin-top:2px">since {C["start"]}</div>
        </div>
        <div style="width:1px;height:40px;background:rgba(0,200,255,.06)"></div>
        <div>
          <div style="font-size:9px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#4a6b85;margin-bottom:2px">TOTAL DAYS</div>
          <div id="{_clock_id}_days" style="font-family:'Bebas Neue',sans-serif;font-size:26px;color:#ffb400;line-height:1">{_days:,}</div>
        </div>
        <div style="width:1px;height:40px;background:rgba(0,200,255,.06)"></div>
        <div>
          <div style="font-size:9px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#4a6b85;margin-bottom:2px">ELAPSED</div>
          <div id="{_clock_id}_hms" style="font-family:'Bebas Neue',sans-serif;font-size:22px;color:#e2ecf8;line-height:1;letter-spacing:.04em">--:--:--</div>
          <div style="font-size:9px;color:#4a6b85;margin-top:2px">hh:mm:ss live</div>
        </div>
        <div style="width:1px;height:40px;background:rgba(0,200,255,.06)"></div>
        <div>
          <div style="font-size:9px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#4a6b85;margin-bottom:2px">INTENSITY</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:22px;color:{int_col};line-height:1">{C["intensity"]}</div>
        </div>
        <div style="width:1px;height:40px;background:rgba(0,200,255,.06)"></div>
        <div>
          <div style="font-size:9px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#4a6b85;margin-bottom:2px">LIVE ARTICLES</div>
          <div style="font-family:'Bebas Neue',sans-serif;font-size:26px;color:#00e676;line-height:1">{len(_gdelt_articles)}</div>
          <div style="font-size:9px;color:#4a6b85;margin-top:2px">{_rec_count} in 6h · {_new_count} in 1h</div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <div style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;background:rgba(255,61,90,.1);
             border:1px solid rgba(255,61,90,.3);border-radius:20px;font-size:9px;color:#ff3d5a">
          <span style="width:5px;height:5px;border-radius:50%;background:#ff3d5a;
                animation:blink 0.8s ease-in-out infinite;display:inline-block"></span>LIVE TRACKER
        </div>
        <div style="font-size:9px;color:#4a6b85">GDELT · 2min cache · since {C["start"]}</div>
      </div>
    </div>
    <style>@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}</style>
    <script>
    (function(){{
      const start = new Date("{_start_iso}").getTime();
      function tick(){{
        const now = Date.now();
        const diff = now - start;
        const totalSec = Math.floor(diff / 1000);
        const h = Math.floor(totalSec / 3600) % 24;
        const m = Math.floor(totalSec / 60) % 60;
        const s = totalSec % 60;
        const el = document.getElementById("{_clock_id}_hms");
        if(el) el.textContent =
          String(Math.floor(diff/3600000)).padStart(2,'0') + ':' +
          String(m).padStart(2,'0') + ':' +
          String(s).padStart(2,'0');
      }}
      tick();
      setInterval(tick, 1000);
    }})();
    </script>"""
    _components_inner.html(_clock_html, height=108)

    # ── Live feed + RSS side by side ────────────────────────────
    tracker_left, tracker_right = st.columns([3, 2], gap="medium")

    with tracker_left:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
          <div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)">
            📡 LIVE FEED — {theatre.upper()}
          </div>
          <div class="live-badge"><span class="pulse p-red" style="margin-right:2px"></span>GDELT DOC 2.0</div>
          <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">Since {C["start"]} · {len(_gdelt_articles)} results</div>
        </div>""", unsafe_allow_html=True)

        if _gdelt_articles:
            feed_container = st.container()
            with feed_container:
                for art in _gdelt_articles:
                    _is_new    = art.get("is_new", False)
                    _is_recent = art.get("is_recent", False)
                    # Pre-compute ALL conditional fragments — no nested quotes in f-string
                    _border    = conflict_accent if _is_new else (conflict_accent + "88" if _is_recent else "rgba(0,200,255,.08)")
                    _left_bdr  = conflict_accent if _is_recent else "rgba(0,200,255,.06)"
                    _src_col   = "#ff8c42" if _is_new else "#4a6b85"
                    _new_badge = '<span style="font-family:var(--fm);font-size:8px;background:rgba(0,230,118,.15);color:#00e676;border:1px solid rgba(0,230,118,.3);border-radius:4px;padding:1px 6px;margin-left:6px">NEW</span>' if _is_new else ""
                    _rec_badge = '<span style="font-family:var(--fm);font-size:8px;background:rgba(255,61,90,.1);color:#ff3d5a;border:1px solid rgba(255,61,90,.25);border-radius:4px;padding:1px 5px">RECENT</span>' if _is_recent else ""
                    _read_link = ('<a href="' + art["url"] + '" target="_blank" rel="noopener" style="font-family:var(--fm);font-size:9px;color:var(--cyan);text-decoration:none;padding:2px 8px;border:1px solid rgba(0,200,255,.22);border-radius:4px">Read →</a>') if art.get("url") else ""
                    _source    = art["source"].upper()[:30]
                    _time      = art.get("time", "")
                    _title     = art.get("title", "")
                    _dt        = art.get("dt_str", "")
                    st.markdown(
                        f'<div style="background:var(--card);border:1px solid {_border};' +
                        f'border-left:3px solid {_left_bdr};border-radius:8px;padding:10px 14px;margin-bottom:6px">' +
                        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">' +
                        f'<div style="display:flex;align-items:center;gap:6px">' +
                        f'<span style="font-family:var(--fm);font-size:9px;font-weight:600;letter-spacing:.06em;color:{_src_col}">{_source}</span>' +
                        _new_badge +
                        '</div>' +
                        f'<div style="display:flex;align-items:center;gap:6px">' +
                        f'<span style="font-family:var(--fm);font-size:9px;color:var(--muted)">{_time}</span>' +
                        _rec_badge +
                        '</div></div>' +
                        f'<div style="font-size:12px;font-weight:600;color:var(--text);line-height:1.45;margin-bottom:5px">{_title}</div>' +
                        f'<div style="display:flex;align-items:center;justify-content:space-between">' +
                        f'<span style="font-family:var(--fm);font-size:9px;color:var(--muted)">{_dt}</span>' +
                        _read_link +
                        '</div></div>',
                        unsafe_allow_html=True
                    )
        else:
            # GDELT returned nothing — try server-side Python RSS (no CORS proxy needed)
            _rss_articles = fetch_rss_conflict(theatre)
            if _rss_articles:
                st.markdown(
                    f'<div style="font-family:var(--fm);font-size:10px;color:var(--muted);'
                    f'display:flex;align-items:center;gap:8px;margin-bottom:8px">'
                    f'<span style="width:6px;height:6px;border-radius:50%;background:#ffb400;display:inline-block"></span>'
                    f'RSS fallback · {len(_rss_articles)} articles</div>',
                    unsafe_allow_html=True
                )
                feed_container2 = st.container()
                with feed_container2:
                    for art in _rss_articles:
                        _is_new2    = art.get("is_new", False)
                        _is_recent2 = art.get("is_recent", False)
                        _border2    = conflict_accent if _is_new2 else (conflict_accent + "88" if _is_recent2 else "rgba(0,200,255,.08)")
                        _left2      = conflict_accent if _is_recent2 else "rgba(0,200,255,.06)"
                        _src_col2   = "#ff8c42" if _is_new2 else "#4a6b85"
                        _src2       = art.get("source","")[:28].upper()
                        _time2      = art.get("time","")
                        _title2     = art.get("title","")
                        _dt2        = art.get("dt_str","")
                        _url2       = art.get("url","")
                        _link2      = (f'<a href="{_url2}" target="_blank" rel="noopener" ' +
                                       f'style="font-family:var(--fm);font-size:9px;color:var(--cyan);' +
                                       f'text-decoration:none;padding:2px 8px;border:1px solid rgba(0,200,255,.22);border-radius:4px">Read →</a>') if _url2 else ""
                        st.markdown(
                            f'<div style="background:var(--card);border:1px solid {_border2};' +
                            f'border-left:3px solid {_left2};border-radius:8px;padding:10px 14px;margin-bottom:6px">' +
                            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">' +
                            f'<span style="font-family:var(--fm);font-size:9px;font-weight:600;color:{_src_col2}">{_src2}</span>' +
                            f'<span style="font-family:var(--fm);font-size:9px;color:var(--muted)">{_time2}</span>' +
                            f'</div><div style="font-size:12px;font-weight:600;color:var(--text);line-height:1.45;margin-bottom:5px">{_title2}</div>' +
                            f'<div style="display:flex;justify-content:space-between">' +
                            f'<span style="font-family:var(--fm);font-size:9px;color:var(--muted)">{_dt2}</span>' +
                            _link2 + '</div></div>',
                            unsafe_allow_html=True
                        )
            else:
                # Both GDELT and RSS failed — show informative static placeholder
                st.markdown(f"""
                <div style="background:var(--card);border:1px solid var(--bord2);border-radius:10px;padding:20px;text-align:center">
                  <div style="font-size:24px;margin-bottom:10px">📡</div>
                  <div style="font-family:var(--fm);font-size:11px;color:var(--muted);margin-bottom:8px">Live feed temporarily unavailable</div>
                  <div style="font-size:12px;color:var(--text2);margin-bottom:14px">
                    The GDELT and RSS feeds could not be reached. This is usually temporary.
                  </div>
                  <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
                    <a href="https://www.reuters.com/world" target="_blank" rel="noopener"
                       style="font-family:var(--fm);font-size:10px;color:var(--cyan);text-decoration:none;
                              padding:5px 14px;border:1px solid rgba(0,200,255,.25);border-radius:6px">Reuters →</a>
                    <a href="https://www.bbc.com/news/world" target="_blank" rel="noopener"
                       style="font-family:var(--fm);font-size:10px;color:var(--cyan);text-decoration:none;
                              padding:5px 14px;border:1px solid rgba(0,200,255,.25);border-radius:6px">BBC World →</a>
                    <a href="https://www.aljazeera.com" target="_blank" rel="noopener"
                       style="font-family:var(--fm);font-size:10px;color:var(--cyan);text-decoration:none;
                              padding:5px 14px;border:1px solid rgba(0,200,255,.25);border-radius:6px">Al Jazeera →</a>
                    <a href="https://isw.pub/UkraineConflictUpdatesISW" target="_blank" rel="noopener"
                       style="font-family:var(--fm);font-size:10px;color:var(--cyan);text-decoration:none;
                              padding:5px 14px;border:1px solid rgba(0,200,255,.25);border-radius:6px">ISW →</a>
                  </div>
                </div>""", unsafe_allow_html=True)

    with tracker_right:
        st.markdown(f"""
        <div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">
          📊 CONFLICT AT A GLANCE
        </div>""", unsafe_allow_html=True)

        # Duration breakdown bar
        total_conflict_days = max(1, _days)
        year_labels = []
        _tmp = _start_dt
        while _tmp < _now_utc:
            year_labels.append(_tmp.year)
            _tmp = _tmp.replace(year=_tmp.year + 1)
        year_labels = sorted(set(year_labels))

        st.markdown(f"""
        <div style="background:var(--card);border:1px solid var(--bord2);border-radius:10px;padding:14px 16px;margin-bottom:10px">
          <div style="font-size:10px;color:var(--muted);margin-bottom:8px;font-weight:600;letter-spacing:.1em;text-transform:uppercase">Duration Breakdown</div>
          <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:10px">
            <div style="text-align:center">
              <div style="font-family:var(--fd);font-size:28px;color:{conflict_accent};line-height:1">{_years if _years>0 else _months}</div>
              <div style="font-size:9px;color:var(--muted)">{'years' if _years>0 else 'months'}</div>
            </div>
            <div style="text-align:center">
              <div style="font-family:var(--fd);font-size:28px;color:var(--amber);line-height:1">{_days:,}</div>
              <div style="font-size:9px;color:var(--muted)">total days</div>
            </div>
            <div style="text-align:center">
              <div style="font-family:var(--fd);font-size:28px;color:var(--cyan);line-height:1">{_days * 24:,}</div>
              <div style="font-size:9px;color:var(--muted)">hours</div>
            </div>
          </div>
          <div style="height:6px;background:var(--dim);border-radius:3px;overflow:hidden;margin-bottom:6px">
            <div style="height:100%;width:100%;background:linear-gradient(90deg,{conflict_accent}44,{conflict_accent});border-radius:3px"></div>
          </div>
          <div style="display:flex;justify-content:space-between;font-family:var(--fm);font-size:9px;color:var(--muted)">
            <span>{C["start"]}</span>
            <span>NOW</span>
          </div>
        </div>""", unsafe_allow_html=True)

        # Key stats
        cas_per_day = round(C["casualties_total"] / max(1, _days))
        disp_per_day = round(C["displaced"] / max(1, _days))
        inc_total = len(C["incidents"])
        crit_inc  = sum(1 for i in C["incidents"] if i["severity"]=="CRITICAL")

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
          <div style="background:var(--card);border:1px solid var(--bord2);border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:9px;color:var(--muted);margin-bottom:3px">CASUALTIES/DAY</div>
            <div style="font-family:var(--fd);font-size:22px;color:var(--red)">{cas_per_day:,}</div>
          </div>
          <div style="background:var(--card);border:1px solid var(--bord2);border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:9px;color:var(--muted);margin-bottom:3px">DISPLACED/DAY</div>
            <div style="font-family:var(--fd);font-size:22px;color:var(--amber)">{disp_per_day:,}</div>
          </div>
          <div style="background:var(--card);border:1px solid var(--bord2);border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:9px;color:var(--muted);margin-bottom:3px">TRACKED INCIDENTS</div>
            <div style="font-family:var(--fd);font-size:22px;color:var(--cyan)">{inc_total}</div>
          </div>
          <div style="background:var(--card);border:1px solid var(--bord2);border-radius:8px;padding:10px 12px;text-align:center">
            <div style="font-size:9px;color:var(--muted);margin-bottom:3px">CRITICAL EVENTS</div>
            <div style="font-family:var(--fd);font-size:22px;color:var(--red)">{crit_inc}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Recent incident pulse
        st.markdown(f"""
        <div style="font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">
          🔴 MOST RECENT INCIDENTS
        </div>""", unsafe_allow_html=True)

        # ── Live ACLED events for this theatre ─────────────────
        _acled_live = fetch_acled_events(limit=30)
        # Filter to roughly match the theatre's geographic region
        _theatre_country_map = {
            "Ukraine–Russia War":    ["Ukraine","Russia","Belarus"],
            "Gaza Conflict":              ["Palestine","Israel","Gaza","Egypt"],
            "Israel–Iran War":       ["Israel","Iran","Lebanon","Syria","Yemen"],
            "Sudan Civil War":            ["Sudan"],
            "Myanmar Civil War":          ["Myanmar"],
            "Pakistan-Afghanistan Conflict": ["Pakistan","Afghanistan"],
            "Haiti Gang War":             ["Haiti"],
        }
        _theatre_countries = _theatre_country_map.get(theatre, [])
        _acled_theatre = [
            ev for ev in _acled_live
            if not _theatre_countries or
               any(c.lower() in ev.get("country","").lower() or
                   c.lower() in ev.get("location","").lower()
                   for c in _theatre_countries)
        ]

        if _acled_theatre:
            st.markdown(
                f'<div style="font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;' +
                'color:var(--muted);margin-bottom:8px;margin-top:12px;display:flex;align-items:center;gap:8px">' +
                '<span style="width:6px;height:6px;border-radius:50%;background:#ff3d5a;display:inline-block;'
                'animation:pulse-red 1.2s ease-in-out infinite"></span>' +
                f'⚔ ACLED LIVE EVENTS ({len(_acled_theatre)} recent)</div>',
                unsafe_allow_html=True
            )
            for _aev in _acled_theatre[:6]:
                _aev_fat = _aev.get("fatalities", 0) or 0
                _aev_col = "#ff3d5a" if _aev_fat > 10 else "#ff8c42" if _aev_fat > 0 else "#ffb400"
                _aev_type = _aev.get("event_type", "Event")
                _aev_loc  = _aev.get("location", "") or _aev.get("country", "")
                _aev_date = _aev.get("date", "")
                _aev_src  = _aev.get("source", "ACLED")
                _aev_note = (_aev.get("notes","") or "")[:120]
                _aev_actor= _aev.get("actor1","")[:30]
                st.markdown(
                    f'<div style="background:var(--card);border:1px solid rgba(255,61,90,.18);'
                    f'border-left:3px solid {_aev_col};border-radius:8px;padding:9px 13px;margin-bottom:5px">' +
                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">' +
                    f'<span style="font-family:var(--fm);font-size:9px;font-weight:600;color:{_aev_col}">' +
                    f'{_aev_type}</span>' +
                    (f'<span style="font-family:var(--fm);font-size:9px;color:#ff3d5a">{_aev_fat} fatalities</span>' if _aev_fat > 0 else '') +
                    f'</div>' +
                    f'<div style="font-size:12px;font-weight:600;color:var(--text);margin-bottom:3px">{_aev_loc} · {_aev_date}</div>' +
                    (f'<div style="font-size:11px;color:var(--muted);line-height:1.5">{_aev_note}</div>' if _aev_note else '') +
                    f'<div style="font-family:var(--fm);font-size:8.5px;color:var(--muted);margin-top:4px">'
                    f'Actor: {_aev_actor} · Source: {_aev_src}</div>' +
                    '</div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div style="font-family:var(--fm);font-size:9px;color:var(--muted);padding:8px 0">' +
                'ACLED: No key configured — add ACLED_KEY + ACLED_EMAIL to st.secrets for live events.</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")
        sorted_incidents = sorted(C["incidents"], key=lambda x: x.get("date",""), reverse=True)
        for inc in sorted_incidents[:4]:
            icon = INCIDENT_ICONS.get(inc["type"],"●")
            sev  = inc["severity"]
            sc   = {"CRITICAL":"#ff3d5a","HIGH":"#ff8c42","MED":"#ffb400","LOW":"#00e676"}.get(sev,"#4a6b85")
            cas_note = f" · {inc['casualties']} cas." if inc["casualties"] > 0 else ""
            st.markdown(f"""
            <div style="display:flex;gap:8px;align-items:flex-start;padding:7px 0;border-bottom:1px solid var(--bord2)">
              <div style="font-size:14px;flex-shrink:0;padding-top:1px">{icon}</div>
              <div style="flex:1;min-width:0">
                <div style="font-size:11px;font-weight:600;color:var(--text);line-height:1.35">{inc["title"][:70] + ("…" if len(inc["title"])>70 else "")}</div>
                <div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-top:2px;display:flex;gap:6px;flex-wrap:wrap">
                  <span style="color:{sc}">{sev}</span>
                  <span>{inc["date"]}{cas_note}</span>
                  <span>{inc["loc"][:28]}</span>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        # Live pulse ticker
        _pulse_items = [art["title"][:80] for art in _gdelt_articles[:10] if art.get("is_recent")]
        if _pulse_items:
            _ticker_str = " ◈ ".join(_pulse_items)
            _ticker_dup = _ticker_str + " ◈ " + _ticker_str
            st.markdown(f"""
            <div style="margin-top:10px;background:rgba(255,61,90,.06);border:1px solid rgba(255,61,90,.2);border-radius:8px;overflow:hidden;padding:6px 0">
              <div style="font-family:var(--fm);font-size:9px;color:var(--red);padding:0 10px;margin-bottom:4px;letter-spacing:.1em">⚡ LIVE UPDATES (last 6h)</div>
              <div style="overflow:hidden;padding:0 4px">
                <div style="display:inline-block;white-space:nowrap;animation:ticker-scroll 60s linear infinite;font-family:var(--fm);font-size:9px;color:var(--muted)">
                  {_ticker_dup}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    map_c, esc_c, cas_c = st.columns([3,1,1], gap="medium")
    with map_c:
        st.markdown(f'<div class="sec-label">📍 Theatre Incident Map — {theatre}</div>', unsafe_allow_html=True)
        st.pydeck_chart(build_theatre_map(theatre, show_supp), use_container_width=True)
    with esc_c:
        st.markdown('<div class="sec-label">Escalation Index</div>', unsafe_allow_html=True)
        st.plotly_chart(escalation_gauge(esc,"ESCALATION /100",esc_col),use_container_width=True,config={"displayModeBar":False})
        st.markdown(f"""
        <div class="m-panel" style="text-align:center;padding:12px">
          <div class="badge {'b-red' if esc>=80 else 'b-orange' if esc>=60 else 'b-amber'}">{esc_lbl} RISK</div>
          <div class="m-sub" style="margin-top:8px">Ceasefire</div>
          <div style="font-size:15px;font-weight:600;color:{'var(--green)' if C['ceasefire'] else 'var(--red)'}">
            {'✓ IN EFFECT' if C['ceasefire'] else '✗ NONE'}
          </div>
        </div>""", unsafe_allow_html=True)
    with cas_c:
        st.markdown('<div class="sec-label">Human Cost</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="m-panel" style="text-align:center;padding:16px 12px;margin-bottom:10px">
          <div class="m-label">Casualties</div>
          <div class="m-val m-red" style="font-size:28px">{C['casualties_total']:,}</div>
        </div>
        <div class="m-panel" style="text-align:center;padding:16px 12px">
          <div class="m-label">Displaced</div>
          <div class="m-val m-amber" style="font-size:28px">{C['displaced']:,}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    inc_c, fac_c = st.columns([3,2], gap="medium")
    with inc_c:
        st.markdown('<div class="sec-label">📋 Incident Feed</div>', unsafe_allow_html=True)
        inc_filter = st.radio("Filter:", ["ALL","airstrike","ground","drone","naval","rocket","cyber","humanitarian","diplomatic"],
                               horizontal=True, label_visibility="collapsed", key="inc_f")
        for inc in C["incidents"]:
            if inc_filter != "ALL" and inc["type"] != inc_filter: continue
            icon = INCIDENT_ICONS.get(inc["type"],"●")
            ic   = INCIDENT_COLORS.get(inc["type"],"rgba(74,107,133,.12)")
            sev  = SEV_BADGE.get(inc["severity"],"b-muted")
            cas_note = f"  ·  {inc['casualties']} casualties" if inc["casualties"]>0 else ""
            st.markdown(f"""
            <div class="incident-row">
              <div class="inc-icon" style="background:{ic}">{icon}</div>
              <div class="inc-body">
                <div class="inc-title">{inc['title']}</div>
                <div class="inc-meta">{inc['loc']} &nbsp;·&nbsp; {inc['date']}{cas_note}</div>
                <div class="inc-badge-row">
                  <div class="badge {sev}">{inc['severity']}</div>
                  <div class="badge b-muted">{inc['type'].upper()}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    with fac_c:
        st.markdown('<div class="sec-label">🎖 Faction Tracker</div>', unsafe_allow_html=True)
        for fac in C["factions"]:
            sb = "b-red" if fac["status"] in ("Offensive","Advancing","Retaliatory") else "b-cyan" if fac["status"] in ("Defending","Defensive support") else "b-amber"
            st.markdown(f"""
            <div class="conflict-card">
              <div class="cc-header">
                <div style="display:flex;align-items:center;gap:8px">
                  <div style="width:10px;height:10px;border-radius:50%;background:{fac['color']};box-shadow:0 0 6px {fac['color']}55"></div>
                  <div class="cc-title">{fac['name']}</div>
                </div>
                <div class="badge {sb}">{fac['status']}</div>
              </div>
              <div class="cc-body">
                <div style="display:flex;gap:16px;margin-bottom:10px;flex-wrap:wrap">
                  <div><div class="m-label" style="font-size:9px">Territory</div>
                    <div style="font-family:var(--fm);font-size:13px;color:{fac['color']}">{fac['territory_pct']}%</div></div>
                  <div><div class="m-label" style="font-size:9px">Strength</div>
                    <div style="font-family:var(--fm);font-size:13px;color:var(--text2)">{fac['strength']}</div></div>
                  <div><div class="m-label" style="font-size:9px">Backed by</div>
                    <div style="font-size:12px;color:var(--muted)">{', '.join(fac['support'][:3])}</div></div>
                </div>
                <div style="height:5px;background:var(--dim);border-radius:3px;overflow:hidden;margin-bottom:8px">
                  <div style="height:100%;width:{fac['territory_pct']}%;background:{fac['color']}66;border-radius:3px"></div>
                </div>
                <div style="font-size:12px;color:var(--muted)">Key assets: {', '.join(fac['weapons'][:3]) if fac['weapons'] else 'N/A'}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    tl_c, side_c = st.columns([2,1], gap="medium")
    with tl_c:
        st.markdown('<div class="sec-label">📅 Conflict Timeline</div>', unsafe_allow_html=True)

        import json as _json
        _tc_colors = {
            "escalation": "#ff3d5a", "milestone": "#00c8ff",
            "diplomatic": "#00e676", "setback":   "#ffb400", "ongoing": "#9d6eff",
        }
        _tc_icons = {
            "escalation": "⬆", "milestone": "⭐",
            "diplomatic": "🤝", "setback":   "⬇", "ongoing": "🔴",
        }
        _tc_labels = {
            "escalation": "ESCALATION", "milestone": "MILESTONE",
            "diplomatic": "DIPLOMATIC", "setback":   "SETBACK", "ongoing": "ONGOING",
        }
        _tl_items = [
            {
                "date":  item["date"],
                "event": item["event"],
                "type":  item["type"],
                "color": _tc_colors.get(item["type"], "#4a6b85"),
                "icon":  _tc_icons.get(item["type"], "●"),
                "label": _tc_labels.get(item["type"], item["type"].upper()),
            }
            for item in reversed(C["timeline"])
        ]
        _tl_js     = _json.dumps(_tl_items)
        _tl_accent = conflict_accent
        _tl_count  = len(_tl_items)

        _tl_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@400;500&family=DM+Sans:wght@400;600&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#02040a;font-family:'DM Sans',system-ui,sans-serif;color:#e2ecf8;
      padding:16px 12px 8px;}}

/* ── Legend ── */
.legend{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:20px;padding:10px 14px;
         background:#060d18;border:1px solid rgba(0,200,255,.07);border-radius:8px;}}
.leg{{display:flex;align-items:center;gap:6px;font-size:10px;color:#4a6b85;}}
.leg-dot{{width:9px;height:9px;border-radius:50%;flex-shrink:0;}}

/* ── Outer track ── */
.track{{position:relative;padding-left:56px;}}
.track-line{{
  position:absolute;left:20px;top:12px;bottom:12px;width:2px;
  background:linear-gradient(180deg,
    {_tl_accent}80 0%,
    rgba(0,200,255,.25) 40%,
    rgba(0,200,255,.08) 100%);
}}

/* ── Each event card ── */
.item{{
  position:relative;
  margin-bottom:12px;
  opacity:0;
  transform:translateX(12px);
  animation:fadeIn .35s ease forwards;
}}
.item:last-child{{margin-bottom:0;}}
@keyframes fadeIn{{to{{opacity:1;transform:translateX(0);}}}}

/* Dot + connector */
.node{{
  position:absolute;left:-46px;top:16px;
  display:flex;align-items:center;gap:0;
}}
.dot{{
  width:24px;height:24px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;flex-shrink:0;
  border:2px solid #02040a;
  box-shadow:0 0 16px rgba(0,0,0,.6),0 0 0 3px rgba(0,0,0,.3);
  transition:transform .2s;
}}
.item:hover .dot{{transform:scale(1.15);}}
.conn{{width:20px;height:2px;flex-shrink:0;opacity:.3;}}

/* Card body */
.card{{
  background:#0b1524;
  border:1px solid rgba(0,200,255,.08);
  border-radius:10px;
  padding:13px 16px;
  transition:border-color .2s,box-shadow .2s,transform .15s;
  cursor:default;
}}
.card:hover{{
  border-color:rgba(0,200,255,.22);
  box-shadow:0 4px 20px rgba(0,0,0,.35);
  transform:translateY(-1px);
}}
.card-header{{display:flex;align-items:center;justify-content:space-between;
               margin-bottom:7px;gap:8px;flex-wrap:wrap;}}
.date{{
  font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:500;
  color:#4a6b85;letter-spacing:.04em;
}}
.badge{{
  display:inline-flex;align-items:center;padding:2px 9px;
  border-radius:5px;font-family:'IBM Plex Mono',monospace;
  font-size:9px;font-weight:600;letter-spacing:.07em;
  border:1px solid;white-space:nowrap;
}}
.event-text{{
  font-size:13px;font-weight:600;color:#e2ecf8;line-height:1.5;
}}

/* Year group separator */
.year-sep{{
  display:flex;align-items:center;gap:10px;
  margin:18px 0 14px;font-family:'Bebas Neue',sans-serif;
  font-size:16px;letter-spacing:.12em;color:#4a6b85;
}}
.year-sep::after{{content:'';flex:1;height:1px;background:rgba(0,200,255,.08);}}
</style>
</head><body>

<div class="legend">
  <div class="leg"><div class="leg-dot" style="background:#ff3d5a"></div>Escalation</div>
  <div class="leg"><div class="leg-dot" style="background:#00c8ff"></div>Milestone</div>
  <div class="leg"><div class="leg-dot" style="background:#00e676"></div>Diplomatic</div>
  <div class="leg"><div class="leg-dot" style="background:#ffb400"></div>Setback</div>
  <div class="leg"><div class="leg-dot" style="background:#9d6eff"></div>Ongoing</div>
</div>

<div class="track">
  <div class="track-line"></div>
  <div id="tl"></div>
</div>

<script>
const items = {_tl_js};
const badgeBg = {{
  escalation:"rgba(255,61,90,.13)", milestone:"rgba(0,200,255,.13)",
  diplomatic:"rgba(0,230,118,.13)", setback:"rgba(255,180,0,.13)",
  ongoing:"rgba(157,110,255,.13)",
}};
const tl = document.getElementById("tl");
let lastYear = null;
let html = "";

items.forEach((item, idx) => {{
  const year = item.date.slice(0,4);
  if(year !== lastYear) {{
    html += `<div class="year-sep">${{year}}</div>`;
    lastYear = year;
  }}

  const bg  = badgeBg[item.type] || "rgba(74,107,133,.13)";
  const col = item.color;
  const delay = idx * 0.04;

  html += `
  <div class="item" style="animation-delay:${{delay}}s">
    <div class="node">
      <div class="dot" style="background:${{col}}20;border-color:${{col}};box-shadow:0 0 12px ${{col}}40,0 0 0 3px #02040a">
        <span>${{item.icon}}</span>
      </div>
      <div class="conn" style="background:${{col}}"></div>
    </div>
    <div class="card" style="border-left:3px solid ${{col}}55">
      <div class="card-header">
        <span class="date">${{item.date}}</span>
        <span class="badge" style="color:${{col}};border-color:${{col}}44;background:${{bg}}">
          ${{item.label}}
        </span>
      </div>
      <div class="event-text">${{item.event}}</div>
    </div>
  </div>`;
}});

tl.innerHTML = html;
</script>
</body></html>"""

        # Height: legend(70) + year headers(~30 each) + cards(~75 each)
        _n_years = len(set(it["date"][:4] for it in _tl_items))
        _tl_height = min(110 + _n_years * 35 + _tl_count * 78, 740)
        import streamlit.components.v1 as _stc
        _stc.html(_tl_html, height=_tl_height, scrolling=True)

    with side_c:
        st.markdown('<div class="sec-label">⟶ Supply & Support Lines</div>', unsafe_allow_html=True)
        for sl in C["supply_lines"]:
            is_mil = any(k in sl["type"] for k in ["Mil","Arms","RSF","Junta"])
            st.markdown(f"""
            <div class="gcard" style="padding:12px 14px;margin-bottom:8px">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
                <div class="badge {'b-red' if is_mil else 'b-green'}">{sl['type']}</div>
                <div style="font-size:13px;font-weight:600;color:var(--text2)">{sl['provider']}</div>
              </div>
              <div style="font-family:var(--fm);font-size:10px;color:var(--muted)">
                ({sl['from_lat']:.1f}°, {sl['from_lon']:.1f}°) → ({sl['to_lat']:.1f}°, {sl['to_lon']:.1f}°)
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-label" style="margin-top:14px">📰 Media Reliability</div>', unsafe_allow_html=True)
        st.plotly_chart(media_bias_chart(C["media_sources"]),use_container_width=True,config={"displayModeBar":False})
        st.markdown("""
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px">
          <span style="font-size:11px;color:#00c8ff">■ Centre</span>
          <span style="font-size:11px;color:#9d6eff">■ Centre-Left</span>
          <span style="font-size:11px;color:#ff8c42">■ Right/Party</span>
          <span style="font-size:11px;color:#ff3d5a">■ State media</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Cross-theatre analytics
    st.markdown('<div class="sec-label">📊 Cross-Theatre Analytics</div>', unsafe_allow_html=True)
    a1, a2 = st.columns([1,1], gap="medium")
    with a1:
        st.markdown("**Casualties & Displacement**")
        st.plotly_chart(casualty_chart(),use_container_width=True,config={"displayModeBar":False})
    with a2:
        st.markdown("**Incident Frequency by Type**")
        _all_incs = [i for c in CONFLICTS.values() for i in c["incidents"]]
        _type_counts = {}
        for _i in _all_incs:
            _t = _i["type"]
            _type_counts[_t] = _type_counts.get(_t, 0) + 1
        _tc_sorted = sorted(_type_counts.items(), key=lambda x: -x[1])
        _icons_list = [INCIDENT_ICONS.get(t,"●") + " " + t for t,_ in _tc_sorted]
        _counts_list = [c for _,c in _tc_sorted]
        _bar_colors  = ["#ff3d5a" if t=="airstrike" else "#ff8c42" if t=="ground"
                        else "#9d6eff" if t=="drone" else "#00c8ff" if t in ("naval","cyber")
                        else "#ffb400" for t,_ in _tc_sorted]
        _freq_fig = go.Figure(go.Bar(
            x=_counts_list, y=_icons_list, orientation="h",
            marker_color=_bar_colors, marker_line_width=0, opacity=0.85,
            text=_counts_list, textposition="outside",
            textfont=dict(size=10, color="#e2ecf8"),
        ))
        _freq_fig.update_layout(
            height=200, margin=dict(l=0,r=40,t=0,b=0), **bg_chart(),
            xaxis=dict(**ax()), yaxis=dict(color="#dde8f5", tickfont_size=11),
        )
        st.plotly_chart(_freq_fig, use_container_width=True, config={"displayModeBar":False})

    a3, a4 = st.columns([1,1], gap="medium")
    with a3:
        st.markdown("**Escalation Trend (All Theatres)**")
        _esc_names  = [n.split("–")[0].split(" ")[0][:10] for n in CONFLICTS]
        _esc_vals   = [c["escalation"] for c in CONFLICTS.values()]
        _esc_colors = ["#ff3d5a" if e>=80 else "#ff8c42" if e>=60 else "#ffb400" if e>=40 else "#00e676" for e in _esc_vals]
        _esc_fig = go.Figure(go.Bar(
            x=_esc_names, y=_esc_vals, marker_color=_esc_colors,
            marker_line_width=0, opacity=0.85,
            text=_esc_vals, textposition="outside",
            textfont=dict(size=10, color="#e2ecf8"),
        ))
        _esc_fig.update_layout(
            height=160, margin=dict(l=0,r=0,t=0,b=0), **bg_chart(),
            xaxis=dict(**ax()), yaxis=dict(**ax(), range=[0,110]),
        )
        st.plotly_chart(_esc_fig, use_container_width=True, config={"displayModeBar":False})

    with a4:
        st.markdown("**Risk Assessment Matrix**")
        risk_dims   = ["Escalation","Humanitarian","Spillover","WMD Risk","Ceasefire","Intervention"]
        risk_scores = {
            "Ukraine–Russia War": [87,75,80,45,15,82],
            "Gaza Conflict":      [92,95,78,20,20,68],
            "Israel–Iran War":    [88,70,90,65,10,88],
            "Sudan Civil War":    [74,90,55,5,25,35],
            "Myanmar Civil War":  [68,72,40,5,30,22],
        }
        rcols = st.columns(len(CONFLICTS))
        for cname, rcol in zip(CONFLICTS.keys(), rcols):
            scores = risk_scores.get(cname,[50]*6)
            with rcol:
                short = cname.split("–")[0].split(" ")[0][:8]
                st.markdown(f'<div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-bottom:8px;text-align:center;font-weight:600">{short}</div>', unsafe_allow_html=True)
                for dim, sc in zip(risk_dims, scores):
                    bg  = "rgba(255,61,90,.22)" if sc>=75 else "rgba(255,140,66,.18)" if sc>=50 else "rgba(255,180,0,.14)" if sc>=30 else "rgba(0,230,118,.1)"
                    col = "#ff3d5a" if sc>=75 else "#ff8c42" if sc>=50 else "#ffb400" if sc>=30 else "#00e676"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 8px;margin-bottom:4px;border-radius:6px;background:{bg}">
                      <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">{dim}</div>
                      <div style="font-family:var(--fd);font-size:15px;color:{col}">{sc}</div>
                    </div>""", unsafe_allow_html=True)


    st.markdown("---")
    # ── Historical Events Timeline (2022+) ───────────────────────
    st.markdown('<div class="sec-label">📅 Global Events Timeline — 2022 to Present</div>', unsafe_allow_html=True)
    _ht_cols = st.columns([1, 1, 1, 1], gap="small")
    with _ht_cols[0]:
        _ht_type = st.selectbox("Event type", ["All"] + sorted(set(e["type"] for e in HISTORICAL_EVENTS)), label_visibility="collapsed", key="ht_type")
    with _ht_cols[1]:
        _ht_sev  = st.selectbox("Severity", ["All","CRITICAL","HIGH","MED"], label_visibility="collapsed", key="ht_sev")
    with _ht_cols[2]:
        _ht_yr   = st.selectbox("Year", ["All","2021","2022","2023","2024","2025","2026"], label_visibility="collapsed", key="ht_yr")
    with _ht_cols[3]:
        _ht_q    = st.text_input("Search", placeholder="filter events…", label_visibility="collapsed", key="ht_q")

    _filtered_hist = [
        e for e in _HIST_SORTED
        if (_ht_type == "All" or e["type"] == _ht_type)
        and (_ht_sev  == "All" or e["severity"] == _ht_sev)
        and (_ht_yr   == "All" or e["date"].startswith(_ht_yr))
        and (_ht_q == "" or _ht_q.lower() in e["title"].lower())
    ]

    st.markdown(f'<div style="font-family:var(--fm);font-size:10px;color:var(--muted);margin-bottom:10px">{len(_filtered_hist)} events matched</div>', unsafe_allow_html=True)

    _ht_left, _ht_right = st.columns(2, gap="medium")
    for _idx, _he in enumerate(_filtered_hist[:40]):
        _icon  = HIST_TYPE_ICONS.get(_he["type"], "●")
        _sc    = {"CRITICAL":"#ff3d5a","HIGH":"#ff8c42","MED":"#ffb400","LOW":"#00c8ff"}.get(_he["severity"],"#4a6b85")
        _bdr   = {"CRITICAL":"b-red","HIGH":"b-orange","MED":"b-amber","LOW":"b-cyan"}.get(_he["severity"],"b-muted")
        _col   = _ht_left if _idx % 2 == 0 else _ht_right
        _title = _he["title"][:80] + ("…" if len(_he["title"]) > 80 else "")
        with _col:
            st.markdown(
                f'<div style="display:flex;gap:10px;padding:8px 12px;background:var(--card);border:1px solid var(--bord2);border-left:3px solid {_sc};border-radius:8px;margin-bottom:6px">' +
                f'<div style="font-size:16px;flex-shrink:0;padding-top:2px">{_icon}</div>' +
                f'<div style="flex:1;min-width:0">' +
                f'<div style="font-size:12px;font-weight:600;color:var(--text);line-height:1.35;margin-bottom:3px">{_title}</div>' +
                f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">' +
                f'<span class="badge {_bdr}" style="font-size:8px">{_he["severity"]}</span>' +
                f'<span style="font-family:var(--fm);font-size:9px;color:var(--muted)">{_he["date"]}</span>' +
                f'<span style="font-family:var(--fm);font-size:8px;color:var(--muted);background:var(--dim);padding:1px 6px;border-radius:4px">{_he["type"].upper()}</span>' +
                '</div></div></div>',
                unsafe_allow_html=True
            )

    if len(_filtered_hist) > 40:
        st.markdown(f'<div style="font-family:var(--fm);font-size:10px;color:var(--muted);text-align:center;padding:8px">… {len(_filtered_hist)-40} more events — refine filters to see more</div>', unsafe_allow_html=True)


    # ══ SITUATION REPORT EXPORT ═══════════════════════════════════
    st.markdown("---")
    st.markdown('<div class="sec-label">📋 Situation Report Export</div>',
                unsafe_allow_html=True)

    _sr_c1, _sr_c2 = st.columns([2, 1])
    with _sr_c1:
        _sitrep_fmt = st.radio(
            "Format:", ["Markdown (.md)", "Plain Text (.txt)", "HTML (.html)"],
            horizontal=True, key="sitrep_fmt"
        )
    with _sr_c2:
        _sitrep_acled = st.checkbox("Include live ACLED events", value=True, key="sitrep_acled")

    # ── Build content ─────────────────────────────────────────────
    _sr_now    = datetime.now(tz=timezone.utc)
    _sr_ts     = _sr_now.strftime("%Y-%m-%d %H:%MZ")
    _sr_facs   = C.get("factions", [])
    _sr_incs   = sorted(C.get("incidents", []), key=lambda x: x.get("date",""), reverse=True)
    _sr_tl     = C.get("timeline", [])
    _sr_media  = C.get("media_sources", [])
    _sr_aclevs = _acled_theatre[:6] if _sitrep_acled else []
    _esc_col   = "#ff3d5a" if C["escalation"]>=80 else "#ff8c42" if C["escalation"]>=60 else "#ffb400"
    _cf_yn     = "YES" if C.get("ceasefire") else "NO"
    _sr_assess = (
        "CRITICAL — active high-intensity combat, no near-term resolution"
        if C["escalation"] >= 80 else
        "HIGH — sustained combat operations, elevated civilian risk"
        if C["escalation"] >= 60 else
        "ELEVATED — ongoing hostilities with intermittent escalation"
        if C["escalation"] >= 40 else
        "MODERATE — low-intensity conflict or ceasefire holding"
    )

    if "Markdown" in _sitrep_fmt:
        _sr_mime, _sr_ext = "text/markdown", "md"
        _sr_fac_block = "\n".join(
            "### " + f["name"] + " (" + f.get("side","") + ")\n"
            + "- **Status:** " + f.get("status","") + "\n"
            + "- **Strength:** " + f.get("strength","") + "\n"
            + "- **Key Systems:** " + ", ".join(f.get("weapons",[])) + "\n"
            + "- **External Support:** " + ", ".join(f.get("support",[])) + "\n"
            for f in _sr_facs
        )
        _sr_inc_block = "\n".join(
            "- **[" + i.get("date","") + "] [" + i.get("severity","") + "]** "
            + i.get("type","").upper() + ": " + i.get("title","")
            + " — *" + i.get("loc","") + "*"
            + (" (Cas: " + str(i.get("casualties",0)) + ")" if i.get("casualties",0) > 0 else "")
            for i in _sr_incs[:8]
        )
        _sr_tl_block = "\n".join(
            "- **[" + ev.get("date","") + "]** " + ev.get("event","")
            for ev in reversed(_sr_tl[-8:])
        )
        _sr_ac_block = ("\n## 5. LIVE ACLED EVENTS\n*Source: ACLED*\n\n" + "\n".join(
            "- **[" + ev.get("date","") + "]** " + ev.get("event_type","")
            + " — " + ev.get("location","") + ", " + ev.get("country","")
            + " | Actor: " + ev.get("actor1","")
            + " | Fatalities: " + str(ev.get("fatalities",0))
            for ev in _sr_aclevs
        )) if _sr_aclevs else ""
        _sr_media_block = "\n".join(
            "- " + ms["name"]
            + " — Bias: " + ms.get("bias","N/A")
            + " — Reliability: " + str(ms.get("reliability","N/A")) + "%"
            for ms in _sr_media
        )
        _sitrep_content = (
            "# SITUATION REPORT — " + theatre.upper() + "\n"
            + "**Classification:** UNCLASSIFIED // FOR RESEARCH USE ONLY\n"
            + "**Prepared:** " + _sr_ts + "\n"
            + "**Source:** GeoLocator Intelligence Dashboard\n\n"
            + "---\n\n"
            + "## 1. EXECUTIVE SUMMARY\n"
            + "**Status:** " + C["status"]
            + " | **Intensity:** " + C["intensity"]
            + " | **Escalation:** " + str(C["escalation"]) + "/100\n"
            + "**Region:** " + C["region"]
            + " | **Duration:** " + _dur_str + " (since " + C["start"] + ")\n"
            + "**Casualties:** " + f"{C['casualties_total']:,}"
            + " | **Displaced:** " + f"{C['displaced']:,}" + "\n"
            + "**Ceasefire:** " + _cf_yn + "\n\n"
            + C.get("description","") + "\n\n"
            + "---\n\n"
            + "## 2. RECENT TIMELINE\n" + _sr_tl_block + "\n\n"
            + "---\n\n"
            + "## 3. ORDER OF BATTLE\n" + _sr_fac_block + "\n"
            + "---\n\n"
            + "## 4. RECENT INCIDENTS\n" + _sr_inc_block + "\n"
            + _sr_ac_block + "\n\n"
            + "---\n\n"
            + "## 6. INTELLIGENCE SOURCES\n" + _sr_media_block + "\n\n"
            + "---\n\n"
            + "## 7. ASSESSMENT\n"
            + "Escalation index " + str(C["escalation"]) + "/100: **" + _sr_assess + "**\n\n"
            + "---\n"
            + "*GeoLocator v2026.03 — " + _sr_ts + " — AI-assisted OSINT*\n"
            + "*Verify all data against primary sources before operational use.*\n"
        )

    elif "Plain Text" in _sitrep_fmt:
        _sr_mime, _sr_ext = "text/plain", "txt"
        _sr_sep  = "=" * 60 + "\n"
        _sr_sep2 = "-" * 40 + "\n"
        _sitrep_content = (
            "SITUATION REPORT — " + theatre.upper() + "\n"
            + _sr_sep
            + "Classification: UNCLASSIFIED // FOR RESEARCH USE ONLY\n"
            + "Prepared:       " + _sr_ts + "\n"
            + "Source:         GeoLocator Intelligence Dashboard\n\n"
            + "1. EXECUTIVE SUMMARY\n" + _sr_sep2
            + "Status:     " + C["status"] + "\n"
            + "Intensity:  " + C["intensity"] + "\n"
            + "Escalation: " + str(C["escalation"]) + "/100\n"
            + "Region:     " + C["region"] + "\n"
            + "Duration:   " + _dur_str + "\n"
            + "Casualties: " + f"{C['casualties_total']:,}" + "\n"
            + "Displaced:  " + f"{C['displaced']:,}" + "\n"
            + "Ceasefire:  " + _cf_yn + "\n\n"
            + C.get("description","") + "\n\n"
            + "2. RECENT INCIDENTS\n" + _sr_sep2
            + "\n".join(
                "[" + i.get("date","") + "] [" + i.get("severity","") + "] "
                + i.get("type","").upper() + ": " + i.get("title","")
                + " (" + i.get("loc","") + ")"
                + (" Cas: " + str(i.get("casualties",0)) if i.get("casualties",0) > 0 else "")
                for i in _sr_incs[:8]
            ) + "\n\n"
            + ("3. ACLED LIVE EVENTS\n" + _sr_sep2
               + "\n".join(
                   "[" + ev.get("date","") + "] "
                   + ev.get("event_type","") + " — "
                   + ev.get("location","") + ", " + ev.get("country","")
                   + " — Fatalities: " + str(ev.get("fatalities",0))
                   + " — " + ev.get("actor1","")
                   for ev in _sr_aclevs
               ) + "\n\n" if _sr_aclevs else "")
            + "4. ASSESSMENT\n" + _sr_sep2
            + _sr_assess + "\n\n"
            + _sr_sep
            + "GeoLocator v2026.03 — " + _sr_ts + "\n"
            + "AI-assisted OSINT — verify against primary sources\n"
        )

    else:  # HTML
        _sr_mime, _sr_ext = "text/html", "html"
        _fac_rows = "".join(
            "<tr><td>" + f["name"] + "</td><td>" + f.get("side","")
            + "</td><td>" + f.get("status","") + "</td><td>" + f.get("strength","")
            + "</td><td>" + ", ".join(f.get("support",[])) + "</td></tr>"
            for f in _sr_facs
        )
        _inc_rows = "".join(
            "<tr><td>" + i.get("date","") + "</td>"
            + "<td style='color:"
            + ("#ff3d5a" if i.get("severity")=="CRITICAL"
               else "#ff8c42" if i.get("severity")=="HIGH" else "#ffb400")
            + "'>" + i.get("severity","") + "</td>"
            + "<td>" + i.get("type","").upper() + "</td>"
            + "<td>" + i.get("title","") + "</td>"
            + "<td>" + i.get("loc","") + "</td>"
            + "<td>" + str(i.get("casualties",0)) + "</td></tr>"
            for i in _sr_incs[:10]
        )
        _ac_rows = "".join(
            "<tr><td>" + ev.get("date","") + "</td><td>" + ev.get("event_type","")
            + "</td><td>" + ev.get("location","") + ", " + ev.get("country","")
            + "</td><td>" + ev.get("actor1","")
            + "</td><td>" + str(ev.get("fatalities",0)) + "</td></tr>"
            for ev in _sr_aclevs
        )
        _acled_table = (
            "<h2>5. Live ACLED Events</h2>"
            + "<table><thead><tr><th>Date</th><th>Type</th><th>Location</th>"
            + "<th>Actor</th><th>Fatalities</th></tr></thead><tbody>"
            + _ac_rows + "</tbody></table>"
        ) if _ac_rows else ""

        _sitrep_content = (
            "<!DOCTYPE html><html lang='en'><head>"
            + "<meta charset='utf-8'>"
            + "<title>SitRep — " + theatre + " — " + _sr_ts + "</title>"
            + "<style>"
            + "body{font-family:Georgia,serif;max-width:900px;margin:40px auto;"
            + "padding:0 24px;color:#1a1a2e;line-height:1.7;}"
            + "h1{font-family:monospace;font-size:20px;border-bottom:3px solid "
            + _esc_col + ";padding-bottom:8px;margin-bottom:6px;}"
            + "h2{font-family:monospace;font-size:13px;color:#555;margin-top:28px;"
            + "letter-spacing:.1em;text-transform:uppercase;border-bottom:1px solid #eee;padding-bottom:4px;}"
            + ".meta{font-family:monospace;font-size:11px;color:#888;margin-bottom:20px;}"
            + ".kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0;}"
            + ".kpi{border:1px solid #ddd;border-radius:4px;padding:14px;text-align:center;"
            + "border-top:3px solid " + _esc_col + ";}"
            + ".kpi-v{font-family:monospace;font-size:26px;font-weight:bold;color:" + _esc_col + ";}"
            + ".kpi-l{font-size:10px;color:#999;text-transform:uppercase;letter-spacing:.1em;margin-top:4px;}"
            + "table{width:100%;border-collapse:collapse;margin:12px 0;font-size:13px;}"
            + "thead tr{background:#1a1a2e;color:#fff;}"
            + "th{padding:8px 10px;text-align:left;font-family:monospace;font-size:11px;letter-spacing:.05em;}"
            + "td{padding:7px 10px;border-bottom:1px solid #eee;vertical-align:top;}"
            + "tr:nth-child(even){background:#f9f9f9;}"
            + ".assess{background:#fef9f0;border-left:4px solid " + _esc_col + ";"
            + "padding:14px 18px;border-radius:2px;margin:12px 0;}"
            + ".footer{font-family:monospace;font-size:10px;color:#aaa;border-top:1px solid #eee;"
            + "margin-top:32px;padding-top:12px;}"
            + "</style></head><body>"
            + "<h1>SITUATION REPORT — " + theatre.upper() + "</h1>"
            + "<div class='meta'>Prepared: " + _sr_ts
            + " &nbsp;|&nbsp; Classification: UNCLASSIFIED — Research Use Only<br>"
            + "Status: <strong>" + C["status"] + " / " + C["intensity"]
            + "</strong> &nbsp;|&nbsp; Duration: " + _dur_str + "</div>"
            + "<div class='kpi-grid'>"
            + "<div class='kpi'><div class='kpi-v'>" + str(C["escalation"])
            + "/100</div><div class='kpi-l'>Escalation Index</div></div>"
            + "<div class='kpi'><div class='kpi-v'>" + f"{C['casualties_total']:,}"
            + "</div><div class='kpi-l'>Est. Casualties</div></div>"
            + "<div class='kpi'><div class='kpi-v'>" + f"{C['displaced']:,}"
            + "</div><div class='kpi-l'>Displaced</div></div>"
            + "<div class='kpi'><div class='kpi-v'>" + _cf_yn
            + "</div><div class='kpi-l'>Ceasefire</div></div>"
            + "</div>"
            + "<p>" + C.get("description","") + "</p>"
            + "<h2>3. Order of Battle</h2>"
            + "<table><thead><tr><th>Faction</th><th>Side</th><th>Status</th>"
            + "<th>Strength</th><th>External Support</th></tr></thead><tbody>"
            + _fac_rows + "</tbody></table>"
            + "<h2>4. Recent Incidents</h2>"
            + "<table><thead><tr><th>Date</th><th>Severity</th><th>Type</th>"
            + "<th>Description</th><th>Location</th><th>Cas.</th></tr></thead><tbody>"
            + _inc_rows + "</tbody></table>"
            + _acled_table
            + "<h2>7. Assessment</h2>"
            + "<div class='assess'>" + _sr_assess + "</div>"
            + "<div class='footer'>GeoLocator Intelligence Dashboard v2026.03 — "
            + _sr_ts + "<br>"
            + "AI-assisted OSINT composite — verify all data against primary sources "
            + "before operational use.</div>"
            + "</body></html>"
        )

    # ── Download + preview ────────────────────────────────────────
    _sr_fname = (
        "sitrep_"
        + theatre.lower().replace(" ","_").replace("\u2013","_").replace("–","_")
        + "_" + _sr_now.strftime("%Y%m%d_%H%M")
        + "." + _sr_ext
    )
    st.download_button(
        label="⬇  Export SitRep — " + theatre + " (" + _sr_ext.upper() + ")",
        data=_sitrep_content.encode("utf-8"),
        file_name=_sr_fname,
        mime=_sr_mime,
        use_container_width=True,
        type="primary",
    )
    with st.expander("👁  Preview SitRep", expanded=False):
        if "HTML" in _sitrep_fmt:
            import streamlit.components.v1 as _sr_cmp
            _sr_cmp.html(_sitrep_content, height=520, scrolling=True)
        else:
            st.code(
                _sitrep_content[:3000] + ("…" if len(_sitrep_content) > 3000 else ""),
                language="markdown" if "Markdown" in _sitrep_fmt else "text"
            )



# ══════════════════════════════════════════════════════════════
# TAB 2 — EARTH SIGNALS
# ══════════════════════════════════════════════════════════════
with tab_earth:
    st.markdown("""
    <div class="helper">
      <b>Earth Signals</b> shows live USGS seismic data, NASA EONET volcanic/wildfire events,
      and NOAA geomagnetic conditions. The global command map above shows all layers combined.
    </div>""", unsafe_allow_html=True)

    mc, rc = st.columns([3,1], gap="medium")
    with mc:
        layers_e = []
        if show_seis and not eq_df.empty:
            ep = eq_df.copy()
            ep["_fc"]  = ep["mag"].apply(lambda m: [255,55,85,220] if m>=5.5 else [255,180,0,200] if m>=4.5 else [0,230,118,175] if m>=3.5 else [0,200,255,150])
            ep["_rad"] = (ep["mag"]**2.3*15000).clip(10000,240000)
            ep["tip"]  = ep.apply(lambda r: f"🌍 SEISMIC  M{r['mag']}\n{r['place']}\nDepth: {r['depth_km']} km  |  {r['time']}", axis=1)
            layers_e.append(pdk.Layer("ScatterplotLayer",data=ep,get_position=["lon","lat"],get_radius="_rad",get_fill_color="_fc",pickable=True,auto_highlight=True))
        if show_volc and not eonet_df.empty:
            eo = eonet_df.copy(); eo["_fc"]=[[255,110,40,200]]*len(eo); eo["_rad"]=70000
            eo["tip"] = eo.apply(lambda r: f"🌋 EONET EVENT\n{r['title']}\nCategory: {r.get('cat','')}", axis=1)
            layers_e.append(pdk.Layer("ScatterplotLayer",data=eo,get_position=["lon","lat"],get_radius="_rad",get_fill_color="_fc",pickable=True,auto_highlight=True))
        if show_heat and not eq_df.empty:
            layers_e.append(pdk.Layer("HeatmapLayer",data=eq_df[["lat","lon","mag"]].rename(columns={"mag":"weight"}),get_position=["lon","lat"],get_weight="weight",radiusPixels=50,opacity=.45,pickable=False))

        st.markdown('<div class="sec-label">🗺 Earth Signals Map</div>', unsafe_allow_html=True)
        st.pydeck_chart(pdk.Deck(layers=layers_e,
            initial_view_state=pdk.ViewState(latitude=20,longitude=10,zoom=1.3),
            map_style=CARTO_DARK,
            tooltip={"text": "{tip}", "style": {"backgroundColor": "#080f1c", "color": "#e2ecf8", "border": "1px solid rgba(0,200,255,.3)", "fontFamily": "IBM Plex Mono, monospace", "fontSize": "12px", "padding": "10px 14px", "borderRadius": "8px", "boxShadow": "0 4px 24px rgba(0,0,0,.6)", "lineHeight": "1.7", "whiteSpace": "pre-line", "maxWidth": "280px"}},
            height=380), use_container_width=True)

        st.markdown('<div class="sec-label" style="margin-top:12px">📈 Geomagnetic Kp — 24 hours</div>', unsafe_allow_html=True)
        st.caption("Kp ≥ 5 = geomagnetic storm. Affects GPS, HF radio, and power grids.")
        st.plotly_chart(kp_chart(kp_data["series"]),use_container_width=True,config={"displayModeBar":False})

        # M5+ depth profile (last 30 days)
        if not sig_eq_df.empty:
            st.markdown('<div class="sec-label" style="margin-top:12px">🔵 M5+ Depth Profile — 30 days</div>', unsafe_allow_html=True)
            _depth_fig = go.Figure()
            _depth_fig.add_trace(go.Scatter(
                x=sig_eq_df["depth_km"], y=sig_eq_df["mag"],
                mode="markers",
                marker=dict(
                    size=sig_eq_df["mag"].apply(lambda m: max(4, int(m*2))),
                    color=sig_eq_df["depth_km"],
                    colorscale=[[0,"#ff3d5a"],[0.3,"#ff8c42"],[0.6,"#ffb400"],[1,"#00c8ff"]],
                    opacity=0.75,
                    showscale=True,
                    colorbar=dict(title="Depth km", titlefont=dict(color="#4a6b85",size=9),
                                  tickfont=dict(color="#4a6b85",size=8), thickness=8, len=0.7)
                ),
                hovertext=sig_eq_df.apply(lambda r: f"M{r['mag']} — {r['place'][:30]}\nDepth: {r['depth_km']} km", axis=1),
                hoverinfo="text",
            ))
            _depth_fig.update_layout(
                height=200, margin=dict(l=0,r=40,t=0,b=0),
                **bg_chart(),
                xaxis=dict(**ax(), title="Depth (km)"),
                yaxis=dict(**ax(), title="Mag"),
            )
            st.plotly_chart(_depth_fig, use_container_width=True, config={"displayModeBar":False})

    with rc:
        st.markdown('<div class="sec-label">📊 Magnitude Distribution</div>', unsafe_allow_html=True)
        if not eq_df.empty:
            st.plotly_chart(mag_hist(eq_df),use_container_width=True,config={"displayModeBar":False})

        st.markdown('<div class="sec-label">⚠ Significant — M4.5+</div>', unsafe_allow_html=True)
        for _, row in eq_df[eq_df["mag"]>=4.5].nlargest(12,"mag").iterrows():
            m = row["mag"]
            bc = "b-red" if m>=5.5 else "b-amber" if m>=4.5 else "b-cyan"
            st.markdown(f"""
            <div class="gcard {'gcard-crit' if m>=5.5 else ''}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
                <div class="sig-title">{row['place'][:36]}</div>
                <div class="badge {bc}">M{m}</div>
              </div>
              <div class="sig-meta">Depth {row['depth_km']} km · {row['time']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-label" style="margin-top:12px">🌋 EONET Events</div>', unsafe_allow_html=True)
        for _, row in eonet_df.iterrows():
            cat = row.get("cat","Event")
            cc  = "b-orange" if "Volcan" in cat else "b-amber"
            st.markdown(f"""
            <div class="gcard">
              <div class="sig-title">{row['title'][:40]}</div>
              <div style="display:flex;gap:6px;margin-top:6px;align-items:center">
                <div class="badge {cc}">{cat}</div>
                <div class="sig-meta" style="margin:0">{row.get('date','')}</div>
              </div>
            </div>""", unsafe_allow_html=True)

        # Solar wind panel
        _sw = solar_data
        _sw_col = "#ff3d5a" if _sw["speed"]>700 else "#ff8c42" if _sw["speed"]>500 else "#00e676"
        _fx_col = "#ff3d5a" if _sw["flux"]>180 else "#ff8c42" if _sw["flux"]>130 else "#00c8ff"
        st.markdown(f"""
        <div class="m-panel" style="margin-top:12px">
          <div class="m-label">☀ Space Weather</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:4px">
            <div>
              <div style="font-size:9px;color:var(--muted);margin-bottom:2px">Solar Wind</div>
              <div style="font-family:var(--fd);font-size:22px;color:{_sw_col}">{_sw["speed"]:.0f}</div>
              <div style="font-size:9px;color:var(--muted)">km/s</div>
            </div>
            <div>
              <div style="font-size:9px;color:var(--muted);margin-bottom:2px">10cm Flux</div>
              <div style="font-family:var(--fd);font-size:22px;color:{_fx_col}">{_sw["flux"]:.0f}</div>
              <div style="font-size:9px;color:var(--muted)">sfu</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 3 — CIVIL MOVEMENTS
# ══════════════════════════════════════════════════════════════
with tab_civil:
    st.markdown("""
    <div class="helper">
      <b>Civil Movements</b> tracks protests, strikes, and civil unrest. Sentiment is rated
      MED / HIGH / CRIT based on size, duration, and government response.
    </div>""", unsafe_allow_html=True)

    mv_map, mv_right = st.columns([3,1], gap="medium")
    with mv_map:
        mdf = pd.DataFrame(MOVEMENTS)
        mdf["_fc"]  = mdf["sentiment"].map({"CRIT":[200,60,255,220],"HIGH":[157,110,255,190],"MED":[120,80,220,160]})
        mdf["_rad"] = mdf["scale"] * 2200
        mdf["tip"]  = mdf.apply(lambda r: f"📢 CIVIL MOVEMENT\n{r['title']}\n{r['location']}\nSize: {r['size']} · {r['type'].upper()} · Sentiment: {r['sentiment']}", axis=1)
        st.markdown('<div class="sec-label">🗺 Civil Movements Map</div>', unsafe_allow_html=True)
        st.pydeck_chart(pdk.Deck(
            layers=[pdk.Layer("ScatterplotLayer",data=mdf,get_position=["lon","lat"],get_radius="_rad",get_fill_color="_fc",pickable=True,auto_highlight=True)],
            initial_view_state=pdk.ViewState(latitude=25,longitude=20,zoom=1.3),
            map_style=CARTO_DARK,
            tooltip={"text": "{tip}", "style": {"backgroundColor": "#080f1c", "color": "#e2ecf8", "border": "1px solid rgba(157,110,255,.35)", "fontFamily": "IBM Plex Mono, monospace", "fontSize": "12px", "padding": "10px 14px", "borderRadius": "8px", "boxShadow": "0 4px 24px rgba(0,0,0,.6)", "lineHeight": "1.7", "whiteSpace": "pre-line", "maxWidth": "280px"}},
            height=350), use_container_width=True)
        st.markdown('<div class="sec-label" style="margin-top:12px">📊 Mobilisation Scale</div>', unsafe_allow_html=True)
        st.plotly_chart(mv_bar(MOVEMENTS),use_container_width=True,config={"displayModeBar":False})

    with mv_right:
        ft = st.radio("Filter:", ["ALL","protest","strike","civil"], horizontal=True, label_visibility="collapsed")
        st.markdown('<div class="sec-label">Active Events</div>', unsafe_allow_html=True)
        for m in MOVEMENTS:
            if ft != "ALL" and m["type"] != ft: continue
            is_crit = m["sentiment"]=="CRIT"
            sc = "b-red" if is_crit else "b-violet" if m["sentiment"]=="HIGH" else "b-amber"
            tc_= "b-violet" if m["type"]=="civil" else "b-orange" if m["type"]=="protest" else "b-amber"
            fc = "#ff3d5a" if is_crit else "#9d6eff" if m["sentiment"]=="HIGH" else "#ffb400"
            st.markdown(f"""
            <div class="gcard {'gcard-crit' if is_crit else ''}">
              <div class="sig-title">{m['title']}</div>
              <div class="sig-meta">{m['location']} · {m['age_h']}h ago</div>
              <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;align-items:center">
                <div class="badge {tc_}">{m['type'].upper()}</div>
                <div class="badge {sc}">{m['sentiment']}</div>
                <span style="font-size:12px;color:var(--text2)">{m['size']}</span>
              </div>
              <div class="scale-wrap">
                <div class="scale-track">
                  <div class="scale-fill" style="width:{m['scale']}%;background:linear-gradient(90deg,{fc}66,{fc})"></div>
                </div>
                <span style="font-family:var(--fm);font-size:10px;color:var(--muted)">{m['scale']}</span>
              </div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 4 — LIVE NEWS
# ══════════════════════════════════════════════════════════════
with tab_news:
    sub_tv, sub_articles, sub_directory = st.tabs([
        "📺  Live TV Streams",
        "📰  Article Feeds",
        "📋  Source Directory",
    ])

    # ── SUB-TAB A: LIVE TV ───────────────────────────────────
    with sub_tv:
        ch_js = json.dumps(HLS_CHANNELS)

        tv_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#02040a;font-family:'DM Sans',system-ui,sans-serif;color:#e2ecf8;}}

/* ── Channel grid ── */
#cg{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;padding:12px;}}
@media(max-width:700px){{#cg{{grid-template-columns:repeat(3,1fr);}}}}
@media(max-width:440px){{#cg{{grid-template-columns:repeat(2,1fr);}}}}
.cb{{background:#0b1524;border:1px solid rgba(0,200,255,.12);border-radius:8px;
     padding:10px 12px;cursor:pointer;transition:all .18s;text-align:left;border-left:3px solid transparent;}}
.cb:hover{{border-color:rgba(0,200,255,.3);background:#0f1e35;}}
.cb.active{{border-left-color:var(--col,#00c8ff);background:rgba(0,200,255,.06);
            box-shadow:0 0 14px rgba(0,200,255,.09);}}
.cb.active .cn{{color:var(--col,#00c8ff);}}
.cn{{font-size:12px;font-weight:700;color:#c8daea;line-height:1.3;margin-bottom:3px;
     display:flex;align-items:center;gap:6px;}}
.dot-ch{{width:7px;height:7px;border-radius:50%;flex-shrink:0;}}
.cd{{font-size:10px;color:#4a6b85;line-height:1.4;}}

/* ── Player ── */
#pw{{margin:0 12px 12px;background:#000;border-radius:10px;overflow:hidden;
     border:1px solid rgba(0,200,255,.15);}}
#pb{{display:flex;align-items:center;justify-content:space-between;padding:8px 14px;
     background:#070e1a;border-bottom:1px solid rgba(0,200,255,.1);flex-wrap:wrap;gap:6px;}}
#np{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#e2ecf8;
     display:flex;align-items:center;gap:8px;}}
.lp{{background:#ff3d5a;color:#fff;font-size:9px;font-weight:700;padding:2px 7px;
     border-radius:20px;letter-spacing:.05em;animation:pulse 1.8s ease-in-out infinite;}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}
#pa{{display:flex;gap:6px;flex-wrap:wrap;}}
.pb2{{background:transparent;border:1px solid rgba(0,200,255,.22);color:#00c8ff;
      font-family:'IBM Plex Mono',monospace;font-size:10px;padding:4px 10px;
      border-radius:5px;cursor:pointer;transition:background .15s;}}
.pb2:hover{{background:rgba(0,200,255,.1);}}
#vw{{width:100%;aspect-ratio:16/9;background:#000;display:block;}}
#sb{{padding:7px 14px;background:#060d18;font-family:'IBM Plex Mono',monospace;font-size:10px;
     color:#4a6b85;border-top:1px solid rgba(0,200,255,.08);min-height:28px;
     display:flex;align-items:center;gap:7px;flex-wrap:wrap;}}
.sdot{{width:5px;height:5px;border-radius:50%;flex-shrink:0;transition:background .3s;}}
.s-ok{{background:#00e676;box-shadow:0 0 5px #00e676;}}
.s-loading{{background:#ffb400;animation:pulse .9s ease-in-out infinite;}}
.s-err{{background:#ff3d5a;}}
#stxt{{flex:1;}}
#sfb{{font-size:9px;color:#4a6b85;}}

/* ── Fallback overlay ── */
#fallback{{display:none;position:absolute;inset:0;background:rgba(2,4,10,.92);
           flex-direction:column;align-items:center;justify-content:center;
           gap:14px;padding:24px;text-align:center;z-index:10;}}
#fallback.show{{display:flex;}}
#fallback h3{{font-size:14px;color:#e2ecf8;font-weight:600;}}
#fallback p{{font-size:12px;color:#4a6b85;line-height:1.6;max-width:360px;}}
#fallback a{{display:inline-block;padding:9px 22px;background:rgba(0,200,255,.1);
             border:1px solid rgba(0,200,255,.35);color:#00c8ff;text-decoration:none;
             border-radius:6px;font-family:'IBM Plex Mono',monospace;font-size:11px;
             transition:background .15s;}}
#fallback a:hover{{background:rgba(0,200,255,.2);}}
#vwrap{{position:relative;}}
</style></head><body>
<div id="cg"></div>
<div id="pw">
  <div id="pb">
    <div id="np">
      <span class="lp" id="livepill">● LIVE</span>
      <span id="pname">Select a channel below</span>
    </div>
    <div id="pa">
      <button class="pb2" id="mbtn" onclick="doMute()">🔊 Unmute</button>
      <button class="pb2" onclick="doWeb()">↗ Official site</button>
      <button class="pb2" onclick="doFS()">⛶ Fullscreen</button>
    </div>
  </div>
  <div id="vwrap">
    <video id="vw" controls autoplay muted playsinline></video>
    <div id="fallback">
      <h3 id="fb-title">Stream unavailable</h3>
      <p id="fb-msg">All HLS sources for this channel failed. Watch the live stream directly on the broadcaster's website.</p>
      <a id="fb-link" href="#" target="_blank" rel="noopener">Watch live on official site →</a>
    </div>
  </div>
  <div id="sb">
    <div class="sdot s-loading" id="sdot"></div>
    <span id="stxt">Ready — select a channel above</span>
    <span id="sfb"></span>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/hls.js@1.5.13/dist/hls.min.js"></script>
<script>
const CH = {ch_js};
let curIdx = null, muted = true, hls = null, curWeb = '';

/* ── Render channel grid ── */
function renderGrid() {{
  document.getElementById('cg').innerHTML = CH.map((c, i) => `
    <div class="cb" id="b${{i}}" style="--col:${{c.color}}" onclick="pick(${{i}})">
      <div class="cn">
        <span class="dot-ch" style="background:${{c.color}}"></span>${{c.name}}
      </div>
      <div class="cd">${{c.desc.slice(0,55)}}</div>
    </div>`).join('');
}}

/* ── Status bar helpers ── */
function setSt(txt, cls, fb) {{
  document.getElementById('stxt').textContent = txt;
  document.getElementById('sdot').className = 'sdot ' + cls;
  document.getElementById('sfb').textContent = fb || '';
}}

function showFallback(ch) {{
  document.getElementById('fb-title').textContent = ch.name + ' — stream unavailable';
  document.getElementById('fb-link').href = ch.web;
  document.getElementById('fb-link').textContent = 'Watch ' + ch.name + ' live →';
  document.getElementById('fallback').classList.add('show');
  document.getElementById('livepill').style.background = '#4a6b85';
  setSt('All sources failed — click "Official site" or use the link above', 's-err');
}}

function hideFallback() {{
  document.getElementById('fallback').classList.remove('show');
  document.getElementById('livepill').style.background = '';
}}

/* ── Core: try each HLS URL in sequence ── */
function tryHLS(ch, urls, attempt) {{
  if (attempt >= urls.length) {{
    showFallback(ch);
    return;
  }}
  const url = urls[attempt];
  const v = document.getElementById('vw');
  setSt(
    'Trying source ' + (attempt + 1) + '/' + urls.length + ' for ' + ch.name + '…',
    's-loading',
    url.split('/').slice(2, 3).join('/')   // show hostname only
  );

  if (hls) {{ hls.destroy(); hls = null; }}

  if (Hls.isSupported()) {{
    hls = new Hls({{
      enableWorker: true,
      lowLatencyMode: true,
      backBufferLength: 30,
      manifestLoadingTimeOut: 8000,
      manifestLoadingMaxRetry: 1,
      levelLoadingTimeOut: 8000,
      fragLoadingTimeOut: 12000,
    }});
    hls.loadSource(url);
    hls.attachMedia(v);

    hls.on(Hls.Events.MANIFEST_PARSED, () => {{
      hideFallback();
      v.muted = muted;
      v.play().catch(() => {{ v.muted = true; muted = true; updateMuteBtn(); v.play(); }});
      setSt('● Live · ' + ch.name + (muted ? ' · click 🔊 Unmute for audio' : ' · audio on'), 's-ok', '');
    }});

    hls.on(Hls.Events.ERROR, (evt, data) => {{
      if (data.fatal) {{
        if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {{
          // Fatal network error on this source → try next
          hls.destroy(); hls = null;
          tryHLS(ch, urls, attempt + 1);
        }} else if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {{
          setSt('Media error, attempting recovery…', 's-loading');
          hls.recoverMediaError();
        }} else {{
          hls.destroy(); hls = null;
          tryHLS(ch, urls, attempt + 1);
        }}
      }}
    }});

  }} else if (v.canPlayType('application/vnd.apple.mpegurl')) {{
    // Safari native HLS
    v.src = url;
    v.muted = muted;
    hideFallback();
    v.play().catch(() => {{ v.muted = true; v.play(); }});
    setSt('● Live · ' + ch.name + ' (native HLS)', 's-ok', '');
  }} else {{
    showFallback(ch);
  }}
}}

/* ── Pick a channel ── */
function pick(i) {{
  curIdx = i;
  document.querySelectorAll('.cb').forEach((b, j) => b.classList.toggle('active', j === i));
  const ch = CH[i];
  curWeb = ch.web;
  document.getElementById('pname').textContent = ch.name;
  hideFallback();
  // Normalize: ch.hls is always an array now
  const urls = Array.isArray(ch.hls) ? ch.hls : [ch.hls];
  tryHLS(ch, urls, 0);
}}

/* ── Controls ── */
function updateMuteBtn() {{
  document.getElementById('mbtn').textContent = muted ? '🔊 Unmute' : '🔇 Mute';
}}
function doMute() {{
  const v = document.getElementById('vw');
  muted = !muted; v.muted = muted; updateMuteBtn();
}}
function doWeb() {{ if (curWeb) window.open(curWeb, '_blank'); }}
function doFS() {{
  const w = document.getElementById('pw');
  if (!document.fullscreenElement) w.requestFullscreen?.();
  else document.exitFullscreen?.();
}}

renderGrid();
</script></body></html>"""

        components.html(tv_html, height=920, scrolling=False)
        st.caption("Each channel has up to 4 HLS fallback sources tried automatically. If all fail, use **↗ Official site** to watch on the broadcaster's website. Start muted — click 🔊 Unmute for audio.")

    # ── SUB-TAB B: ARTICLE FEEDS ─────────────────────────────
    with sub_articles:
        cat_sel = st.radio(
            "Category:", CAT_TABS_NEWS,
            format_func=lambda x: CAT_NAMES_ART.get(x, x),
            horizontal=True, label_visibility="collapsed",
        )
        vis_src = [s for s in NEWS_SOURCES if cat_sel=="ALL" or s["cat"]==cat_sel]

        st.markdown('<div class="sec-label">📡 Live Article Feed</div>', unsafe_allow_html=True)
        st.caption("Fetched live in your browser via CORS proxy fallbacks.")

        # Server-side RSS fetch — no CORS issues, works on Streamlit Cloud
        _news_arts = fetch_news_rss(cat_sel.lower() if cat_sel != "ALL" else "global")
        from html import escape as _nhe
        _art_cat_col = NEWS_CAT_COLOR.get(cat_sel.lower(), "#00c8ff") if cat_sel != "ALL" else "#00c8ff"
        if _news_arts:
            st.markdown(
                '<div style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#00e676;'
                'margin-bottom:12px;display:flex;align-items:center;gap:8px">'
                '<span style="width:6px;height:6px;border-radius:50%;background:#00e676;'
                'display:inline-block;animation:pulse 1.2s ease-in-out infinite"></span>'
                f' {len(_news_arts)} articles — live</div>',
                unsafe_allow_html=True
            )
            _art_cols = st.columns(2)
            for _ai, _art in enumerate(_news_arts[:24]):
                with _art_cols[_ai % 2]:
                    _ac = NEWS_CAT_COLOR.get(
                        next((s["cat"] for s in NEWS_SOURCES
                              if s["name"].upper() == _art.get("source","").upper()), "global"),
                        _art_cat_col)
                    _art_url = _art.get("url","")
                    _rbtn = (f'<a href="{_nhe(_art_url)}" target="_blank" rel="noopener" '
                             'style="font-family:IBM Plex Mono,monospace;font-size:10px;'
                             'color:#00c8ff;text-decoration:none;padding:3px 10px;'
                             'border:1px solid rgba(0,200,255,.28);border-radius:5px">Read →</a>'
                             ) if _art_url else ""
                    st.markdown(
                        f'<div style="background:#0b1524;border:1px solid rgba(0,200,255,.12);'
                        f'border-left:3px solid {_ac};border-radius:10px;padding:14px 16px;margin-bottom:10px">'
                        f'<div style="font-family:IBM Plex Mono,monospace;font-size:9px;font-weight:600;'
                        f'letter-spacing:.07em;text-transform:uppercase;color:{_ac};margin-bottom:6px">'
                        f'{_nhe(_art.get("source",""))}</div>'
                        f'<div style="font-size:13px;font-weight:600;color:#e2ecf8;line-height:1.45;margin-bottom:8px">'
                        f'{_nhe((_art.get("title") or "")[:120])}</div>'
                        f'<div style="display:flex;align-items:center;justify-content:space-between">'
                        f'<span style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#4a6b85">'
                        f'{_nhe(_art.get("time",""))}</span>{_rbtn}</div></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="font-family:IBM Plex Mono,monospace;font-size:11px;color:#ff8c42;'
                'padding:16px;border:1px solid rgba(255,140,66,.25);border-radius:8px;'
                'background:rgba(255,140,66,.05)">RSS feeds temporarily unavailable. '
                'Try again shortly or visit sources directly.</div>',
                unsafe_allow_html=True)
            for _fs in vis_src[:6]:
                st.markdown(
                    f'<a href="https://{_fs["site"]}" target="_blank" rel="noopener" '
                    f'style="font-family:IBM Plex Mono,monospace;font-size:10px;color:#00c8ff;'
                    f'text-decoration:none;margin-right:12px">{_fs["name"]} →</a>',
                    unsafe_allow_html=True)

    # ── SUB-TAB C: SOURCE DIRECTORY ──────────────────────────
    with sub_directory:
        st.markdown('<div class="sec-label">📺 Live TV Channels (HLS Streams)</div>', unsafe_allow_html=True)
        yt_dir_cols = st.columns(5)
        for i, ch in enumerate(HLS_CHANNELS):
            col = ch["color"]
            fb_count = len(ch["hls"]) if isinstance(ch["hls"], list) else 1
            with yt_dir_cols[i % 5]:
                st.markdown(f"""
                <div class="src-directory-card" style="border-left:3px solid {col}">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
                    <div style="font-family:var(--fm);font-size:11px;font-weight:600;color:{col}">{ch['name']}</div>
                    <div class="badge b-muted" style="font-size:8px">{fb_count} src</div>
                  </div>
                  <div style="font-size:12px;color:var(--muted);margin-bottom:8px">{ch['desc']}</div>
                  <a href="{ch['web']}" target="_blank" class="news-link" style="font-size:10px">Watch live →</a>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="sec-label">📰 RSS Article Sources</div>', unsafe_allow_html=True)
        src_dir_cols = st.columns(4)
        for i, s in enumerate(NEWS_SOURCES):
            col = NEWS_CAT_COLOR.get(s["cat"],"#4a6b85")
            with src_dir_cols[i % 4]:
                st.markdown(f"""
                <div class="src-directory-card" style="border-left:3px solid {col}">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
                    <div style="font-family:var(--fm);font-size:11px;font-weight:600;color:{col}">{s['name']}</div>
                    <div class="badge" style="color:{col};border-color:{col}44;background:{col}15;font-size:8px">{s['cat'].upper()}</div>
                  </div>
                  <div style="font-size:12px;color:var(--muted);margin-bottom:8px">{s.get('desc','')}</div>
                  <a href="https://{s.get('site',s['name'])}" target="_blank"
                     class="news-link" style="font-size:10px">Visit {s.get('site',s['name'])} →</a>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# INTEL & ECONOMIC DATA  (static + live-fetched)
# ══════════════════════════════════════════════════════════════

# ── Country Instability Index (ICRG-style scores, 0–100) ─────
# Country Instability Index — 50 countries, 4-component model (U=Unrest, C=Conflict, S=Security, I=Information)
# Scores 0-100. Components are already on 0-100 scale. Baseline March 2026.
COUNTRY_INSTABILITY = [
    # Active war zones
    {"country":"Sudan",        "score":91,"trend":"↑","U":92,"C":88,"S":82,"I":76,"region":"Africa"},
    {"country":"Gaza",         "score":98,"trend":"↑","U":99,"C":99,"S":95,"I":80,"region":"Middle East"},
    {"country":"Myanmar",      "score":85,"trend":"→","U":82,"C":88,"S":78,"I":74,"region":"Asia"},
    {"country":"Yemen",        "score":83,"trend":"→","U":80,"C":88,"S":70,"I":72,"region":"Middle East"},
    {"country":"Haiti",        "score":84,"trend":"↑","U":88,"C":80,"S":74,"I":72,"region":"Americas"},
    {"country":"Somalia",      "score":79,"trend":"→","U":76,"C":82,"S":72,"I":66,"region":"Africa"},
    {"country":"DR Congo",     "score":78,"trend":"↑","U":74,"C":84,"S":68,"I":64,"region":"Africa"},
    {"country":"Libya",        "score":76,"trend":"→","U":70,"C":78,"S":70,"I":68,"region":"Africa"},
    {"country":"Ethiopia",     "score":72,"trend":"↑","U":68,"C":76,"S":66,"I":60,"region":"Africa"},
    {"country":"Mali",         "score":71,"trend":"↑","U":72,"C":72,"S":60,"I":60,"region":"Africa"},
    {"country":"Afghanistan",  "score":70,"trend":"→","U":68,"C":72,"S":60,"I":62,"region":"Asia"},
    {"country":"Syria",        "score":74,"trend":"↓","U":64,"C":72,"S":76,"I":70,"region":"Middle East"},
    # Active conflict participants
    {"country":"Ukraine",      "score":88,"trend":"→","U":70,"C":98,"S":84,"I":72,"region":"Europe"},
    {"country":"Russia",       "score":76,"trend":"↑","U":62,"C":90,"S":72,"I":88,"region":"Europe/Asia"},
    {"country":"Israel",       "score":78,"trend":"↑","U":66,"C":94,"S":76,"I":68,"region":"Middle East"},
    {"country":"Iran",         "score":80,"trend":"↑","U":72,"C":82,"S":78,"I":90,"region":"Middle East"},
    {"country":"Lebanon",      "score":72,"trend":"↑","U":68,"C":76,"S":66,"I":62,"region":"Middle East"},
    {"country":"Iraq",         "score":63,"trend":"↓","U":58,"C":64,"S":56,"I":54,"region":"Middle East"},
    # High-tension states
    {"country":"North Korea",  "score":74,"trend":"→","U":40,"C":64,"S":82,"I":98,"region":"Asia"},
    {"country":"Venezuela",    "score":62,"trend":"→","U":66,"C":54,"S":58,"I":68,"region":"Americas"},
    {"country":"Pakistan",     "score":64,"trend":"↑","U":62,"C":68,"S":58,"I":54,"region":"Asia"},
    {"country":"China",        "score":55,"trend":"→","U":52,"C":38,"S":58,"I":80,"region":"Asia"},
    {"country":"Turkey",       "score":54,"trend":"→","U":54,"C":56,"S":48,"I":60,"region":"Middle East/Europe"},
    {"country":"Saudi Arabia", "score":48,"trend":"→","U":42,"C":50,"S":44,"I":64,"region":"Middle East"},
    {"country":"Egypt",        "score":52,"trend":"→","U":54,"C":44,"S":48,"I":68,"region":"Africa"},
    {"country":"Nigeria",      "score":66,"trend":"↑","U":64,"C":72,"S":60,"I":52,"region":"Africa"},
    {"country":"Kenya",        "score":48,"trend":"→","U":48,"C":42,"S":44,"I":42,"region":"Africa"},
    {"country":"Indonesia",    "score":38,"trend":"→","U":38,"C":28,"S":36,"I":44,"region":"Asia"},
    {"country":"Philippines",  "score":44,"trend":"→","U":46,"C":44,"S":40,"I":42,"region":"Asia"},
    {"country":"India",        "score":46,"trend":"→","U":48,"C":42,"S":42,"I":54,"region":"Asia"},
    {"country":"Bangladesh",   "score":55,"trend":"↑","U":58,"C":44,"S":52,"I":60,"region":"Asia"},
    {"country":"Thailand",     "score":44,"trend":"→","U":44,"C":36,"S":42,"I":50,"region":"Asia"},
    # Elevated instability
    {"country":"Brazil",       "score":46,"trend":"↑","U":50,"C":46,"S":46,"I":40,"region":"Americas"},
    {"country":"Mexico",       "score":56,"trend":"→","U":52,"C":62,"S":54,"I":44,"region":"Americas"},
    {"country":"Colombia",     "score":50,"trend":"↓","U":46,"C":56,"S":48,"I":42,"region":"Americas"},
    {"country":"Ecuador",      "score":54,"trend":"↑","U":52,"C":58,"S":52,"I":44,"region":"Americas"},
    {"country":"Peru",         "score":48,"trend":"→","U":50,"C":42,"S":44,"I":44,"region":"Americas"},
    # Relatively stable but monitored
    {"country":"USA",          "score":38,"trend":"↑","U":46,"C":18,"S":36,"I":42,"region":"Americas"},
    {"country":"UK",           "score":32,"trend":"→","U":34,"C":14,"S":30,"I":36,"region":"Europe"},
    {"country":"France",       "score":34,"trend":"↑","U":42,"C":14,"S":28,"I":36,"region":"Europe"},
    {"country":"Germany",      "score":28,"trend":"→","U":30,"C":10,"S":26,"I":30,"region":"Europe"},
    {"country":"Japan",        "score":24,"trend":"→","U":20,"C":12,"S":28,"I":24,"region":"Asia"},
    {"country":"South Korea",  "score":36,"trend":"↑","U":36,"C":28,"S":34,"I":40,"region":"Asia"},
    {"country":"Australia",    "score":18,"trend":"→","U":18,"C":6, "S":20,"I":20,"region":"Pacific"},
    {"country":"Canada",       "score":22,"trend":"↑","U":24,"C":8, "S":20,"I":24,"region":"Americas"},
    {"country":"Singapore",    "score":16,"trend":"→","U":14,"C":8, "S":18,"I":22,"region":"Asia"},
    {"country":"New Zealand",  "score":14,"trend":"→","U":14,"C":4, "S":16,"I":16,"region":"Pacific"},
]
# Build a fast lookup dict
_CI_LOOKUP = {c["country"].lower(): c for c in COUNTRY_INSTABILITY}

# ── Strategic Risk ────────────────────────────────────────────
STRATEGIC_RISK = {
    "score": 58, "label": "ELEVATED", "trend": "Stable",
    "color": "#ff8c42",
    "components": [
        {"name":"Military Conflict","val":78,"col":"#ff3d5a"},
        {"name":"Cyber Threats","val":65,"col":"#9d6eff"},
        {"name":"Economic Disruption","val":61,"col":"#ffb400"},
        {"name":"Political Instability","val":54,"col":"#ff8c42"},
        {"name":"Climate / Disaster","val":42,"col":"#00e676"},
        {"name":"Pandemic Risk","val":28,"col":"#00c8ff"},
    ]
}

# ── Infrastructure Cascade ────────────────────────────────────
INFRA_CASCADE = {
    "cables":  {"count":86,  "at_risk":12, "items":[
        {"name":"SEA-ME-WE 4","region":"Indian Ocean","risk":72,"status":"Degraded"},
        {"name":"FLAG Atlantic-1","region":"Atlantic","risk":45,"status":"Active"},
        {"name":"Africa Coast to Europe","region":"W Africa","risk":81,"status":"Cut"},
        {"name":"PEACE Cable","region":"ME/Africa","risk":68,"status":"Degraded"},
        {"name":"AAE-1","region":"Asia-Europe","risk":55,"status":"Active"},
    ]},
    "pipelines":{"count":88, "at_risk":9, "items":[
        {"name":"Nord Stream (inactive)","region":"Baltic","risk":95,"status":"Sabotaged"},
        {"name":"Trans-Arabian Pipeline","region":"Middle East","risk":78,"status":"Suspended"},
        {"name":"Druzhba Pipeline","region":"Europe","risk":65,"status":"Reduced"},
        {"name":"TANAP","region":"Turkey","risk":32,"status":"Active"},
    ]},
    "ports":    {"count":62, "at_risk":8, "items":[
        {"name":"Port of Hodeidah","region":"Yemen","risk":88,"status":"Blockaded"},
        {"name":"Port Sudan","region":"Sudan","risk":74,"status":"Contested"},
        {"name":"Strait of Hormuz ports","region":"Iran/UAE","risk":71,"status":"At Risk"},
    ]},
    "chokepoints":{"count":13,"at_risk":4,"items":[
        {"name":"Strait of Hormuz","risk":82,"status":"At Risk","traffic_pct":20},
        {"name":"Suez Canal","risk":55,"status":"Reduced","traffic_pct":12},
        {"name":"Bab el-Mandeb","risk":79,"status":"Threatened","traffic_pct":9},
        {"name":"Strait of Malacca","risk":28,"status":"Active","traffic_pct":25},
    ]},
    "power_grids":{"count":191,"at_risk":22,"items":[
        {"name":"Ukraine National Grid","region":"Ukraine","risk":88,"status":"Under Attack"},
        {"name":"Sudan Power Corp","region":"Sudan","risk":75,"status":"Disrupted"},
    ]},
}

# ── Force Posture ─────────────────────────────────────────────
FORCE_POSTURE = [
    {"activity":"Combined air-naval activity","actors":"UK/Unknown","signals":860,"risk":49,"col":"#ff3d5a"},
    {"activity":"Combined air-naval activity","actors":"NATO/USA","signals":63,"risk":39,"col":"#ff8c42"},
    {"activity":"Combined air-naval activity","actors":"NATO/Japan","signals":19,"risk":37,"col":"#ffb400"},
    {"activity":"Missile test/launch","actors":"Iran","signals":12,"risk":82,"col":"#ff3d5a"},
    {"activity":"Troop mobilisation","actors":"Russia","signals":44,"risk":65,"col":"#ff8c42"},
    {"activity":"Air defence activation","actors":"Israel","signals":31,"risk":58,"col":"#ffb400"},
    {"activity":"Naval patrol","actors":"China/SCS","signals":28,"risk":45,"col":"#ff8c42"},
    {"activity":"Cyber operation","actors":"Unknown/State","signals":77,"risk":72,"col":"#9d6eff"},
]

# ── Supply Chain Chokepoints ──────────────────────────────────
CHOKEPOINTS = [
    {
        "name":"Strait of Hormuz","risk":80,"status":"red","flow":"eastbound/westbound",
        "warnings":0,"ais_disruptions":0,"wow_change":-94.4,
        "context":"Active conflict — Iran-Israel war; Iranian naval blockade risk and mines reported in Persian Gulf; Traffic down 95% vs 30-day baseline — vessels may be transiting dark (AIS off)",
        "exports":["Gulf Oil Exports","Qatar LNG","Iran Exports"],
        "lat":26.56,"lon":56.26,
    },
    {
        "name":"Kerch Strait","risk":70,"status":"red","flow":"northbound/southbound",
        "warnings":0,"ais_disruptions":0,"wow_change":37.5,
        "context":"Active conflict zone; Russia controls Kerch Bridge; Ukraine grain exports via Azov severely restricted",
        "exports":["Ukraine Grain","Russian Coal","Azov Steel"],
        "lat":45.35,"lon":36.62,
    },
    {
        "name":"Bab el-Mandeb","risk":75,"status":"red","flow":"northbound/southbound",
        "warnings":3,"ais_disruptions":12,"wow_change":-41.0,
        "context":"Houthi attacks on commercial shipping continue; Red Sea rerouting adding 2–3 weeks to Asia-Europe routes",
        "exports":["Suez Canal traffic","EU-Asia trade","Oil tankers"],
        "lat":12.58,"lon":43.38,
    },
    {
        "name":"Suez Canal","risk":52,"status":"amber","flow":"northbound/southbound",
        "warnings":1,"ais_disruptions":3,"wow_change":-18.0,
        "context":"Reduced traffic due to Red Sea security situation; Some rerouting via Cape of Good Hope continues",
        "exports":["EU-Asia Container","Mediterranean Oil","LNG"],
        "lat":30.42,"lon":32.35,
    },
    {
        "name":"Strait of Malacca","risk":22,"status":"green","flow":"eastbound/westbound",
        "warnings":0,"ais_disruptions":0,"wow_change":2.1,
        "context":"Normal operations. China-Taiwan tensions monitored but no current disruption to commercial shipping.",
        "exports":["SE Asia Trade","China Imports","Japan/Korea Oil"],
        "lat":3.0,"lon":101.0,
    },
    {
        "name":"Taiwan Strait","risk":55,"status":"amber","flow":"northbound/southbound",
        "warnings":0,"ais_disruptions":2,"wow_change":-8.4,
        "context":"PLA military exercises increasing. Some vessels rerouting. Semiconductor supply chain vulnerability elevated.",
        "exports":["Taiwan Semiconductors","China Exports","Japan Trade"],
        "lat":24.5,"lon":119.5,
    },
]


# ── Trade Policy ──────────────────────────────────────────────
TRADE_RESTRICTIONS = [
    {"country":"India","type":"MFN Applied Tariff","coverage":"All products","avg_rate":16.2,"impact":"High","year":2024},
    {"country":"South Korea","type":"MFN Applied Tariff","coverage":"All products","avg_rate":13.4,"impact":"High","year":2024},
    {"country":"Brazil","type":"MFN Applied Tariff","coverage":"All products","avg_rate":12.0,"impact":"High","year":2024},
    {"country":"China","type":"MFN + Retaliatory","coverage":"US goods + semiconductors","avg_rate":21.5,"impact":"Critical","year":2025},
    {"country":"USA","type":"Section 301 / IRA","coverage":"Chinese EVs, steel, tech","avg_rate":25.0,"impact":"Critical","year":2025},
    {"country":"EU","type":"Carbon Border Tax","coverage":"Steel, cement, chemicals","avg_rate":8.4,"impact":"Med","year":2026},
    {"country":"Russia","type":"Sanctions + Counter","coverage":"SWIFT blocked, tech embargo","avg_rate":0,"impact":"Critical","year":2022},
]
TARIFFS = [
    {"route":"US → China","rate":145,"change":"+125pp","impact":"Critical","sector":"Electronics/EVs"},
    {"route":"China → US","rate":125,"change":"+84pp","impact":"Critical","sector":"All goods"},
    {"route":"US → EU","rate":10,"change":"+10pp","impact":"Med","sector":"Steel/Autos"},
    {"route":"EU → US","rate":3,"change":"+1pp","impact":"Low","sector":"Varied"},
    {"route":"US → Mexico","rate":25,"change":"+25pp","impact":"High","sector":"Manufactured goods"},
]

# ── Economic Indicators (FRED-style) ─────────────────────────
ECON_INDICATORS = [
    {"name":"Fed Total Assets","val":"6,646$B","change":"+17450$B","ticker":"WALCL","date":"2026-03-11","up":True},
    {"name":"Fed Funds Rate","val":"3.64%","change":"−0%","ticker":"FEDFUNDS","date":"2026-02-01","up":False},
    {"name":"10Y-2Y Spread","val":"0.55%","change":"+0.04%","ticker":"T10Y2Y","date":"2026-03-13","up":True},
    {"name":"Unemployment","val":"4.4%","change":"+0.1%","ticker":"UNRATE","date":"2026-02-01","up":False},
    {"name":"CPI YoY","val":"3.2%","change":"+0.3%","ticker":"CPIAUCSL","date":"2026-02-01","up":False},
    {"name":"GDP Growth","val":"2.3%","change":"−0.4%","ticker":"A191RL1Q225SBEA","date":"2025-Q4","up":False},
]
OIL_DATA = [
    {"name":"Brent Crude","val":91.42,"change":+2.14,"unit":"$/bbl"},
    {"name":"WTI Crude","val":88.71,"change":+1.98,"unit":"$/bbl"},
    {"name":"Natural Gas (HH)","val":2.84,"change":-0.12,"unit":"$/MMBtu"},
    {"name":"Uranium","val":106.50,"change":+0.50,"unit":"$/lb"},
]
CRYPTO_DATA = [
    {"name":"Bitcoin","ticker":"BTC","val":70729.19,"change":-0.64},
    {"name":"Ethereum","ticker":"ETH","val":2078.04,"change":-1.23},
    {"name":"BNB","ticker":"BNB","val":654.02,"change":-0.42},
]
SECTOR_HEATMAP = [
    {"s":"XLK","v":-0.75},{"s":"XLF","v":+0.12},{"s":"XLE","v":+0.33},{"s":"XLV","v":-0.25},
    {"s":"XLY","v":-0.59},{"s":"XLI","v":-0.36},{"s":"XLP","v":+0.58},{"s":"XLU","v":+0.99},
    {"s":"XLB","v":-0.99},{"s":"XLRE","v":+0.26},{"s":"XLC","v":-0.71},{"s":"SMH","v":-0.21},
]

# ── Fires / Active Hotspots ───────────────────────────────────
FIRES_DATA = [
    {"region":"Ukraine","fires":2162,"high":59,"frp":17100},
    {"region":"Iran","fires":485,"high":20,"frp":4000},
    {"region":"Sudan","fires":1240,"high":41,"frp":8800},
    {"region":"Brazil","fires":3820,"high":88,"frp":24600},
    {"region":"Indonesia","fires":910,"high":18,"frp":5200},
    {"region":"Australia","fires":340,"high":12,"frp":2100},
    {"region":"California","fires":180,"high":7,"frp":980},
]

# ── BTC ETF ───────────────────────────────────────────────────
BTC_ETF = {"net_flow":-466.5,"est_flow":113.8,"total_vol":0,"etfs":["IBIT","FBTC","ARKB","BITB","HODL"]}

# ── Layoffs Tracker ───────────────────────────────────────────
LAYOFFS = [
    {"company":"Meta","sector":"Tech","count":"~3,500","source":"layoffs.fyi","severity":"High","date":"2026-03"},
    {"company":"Microsoft","sector":"Tech","count":"~2,000","source":"WSJ","severity":"Med","date":"2026-02"},
    {"company":"Goldman Sachs","sector":"Finance","count":"~1,200","source":"Bloomberg","severity":"Med","date":"2026-02"},
    {"company":"Boeing","sector":"Aerospace","count":"~4,000","source":"Reuters","severity":"High","date":"2026-01"},
    {"company":"Citigroup","sector":"Finance","count":"~5,000","source":"FT","severity":"High","date":"2026-01"},
    {"company":"Intel","sector":"Tech","count":"~15,000","source":"CNBC","severity":"Critical","date":"2025-12"},
]

# ── Pizza Index (PizzaINT) ─────────────────────────────────────
# The "Pizza Index" is a geopolitical/economic composite: tracks how affordable
# a standard pizza is as a proxy for cost-of-living stress, energy prices,
# wheat/flour supply-chain disruption, and disposable income pressure.
# Named after The Economist's Big Mac Index methodology.
PIZZA_INDEX = {
    "score": 62,
    "label": "ELEVATED STRESS",
    "color": "#ff8c42",
    "description": "The Pizza Index measures cost-of-living pressure via the real-world cost of a standard margherita pizza. Scores above 60 indicate supply-chain, energy, or wage pressures are materially impacting consumer food costs.",
    "components": [
        {"name":"Wheat Futures (CBOT)","val":5.82,"unit":"$/bu","change":+8.4,"stress":72,"note":"Ukraine/Russia supply disruption"},
        {"name":"Cheese (Block CWT)","val":1.74,"unit":"$/lb","change":+3.1,"stress":45,"note":"Dairy input costs steady"},
        {"name":"Tomato Paste","val":0.94,"unit":"$/kg","change":+12.6,"stress":68,"note":"Italian crop yields down 18%"},
        {"name":"Energy (NG HH)","val":2.84,"unit":"$/MMBtu","change":-4.2,"stress":38,"note":"Oven energy costs falling"},
        {"name":"Mozzarella (EU)","val":2.41,"unit":"€/kg","change":+6.8,"stress":61,"note":"Feed grain prices elevated"},
        {"name":"Avg Pizza Price (NYC)","val":5.50,"unit":"$/slice","change":+22.2,"stress":88,"note":"Up from $4.50 in 2022"},
        {"name":"Avg Pizza Price (London)","val":4.20,"unit":"£/slice","change":+18.6,"stress":82,"note":"Driven by energy + labour"},
        {"name":"Avg Pizza Price (Mumbai)","val":180,"unit":"₹/slice","change":+11.3,"stress":55,"note":"Stable relative to local wages"},
    ],
    "city_prices":[
        {"city":"New York","price":5.50,"currency":"USD","baseline":3.00,"stress":88},
        {"city":"London","price":4.20,"currency":"GBP","baseline":2.50,"stress":82},
        {"city":"Rome","price":1.80,"currency":"EUR","baseline":1.20,"stress":55},
        {"city":"Tokyo","price":420,"currency":"JPY","baseline":300,"stress":45},
        {"city":"Dubai","price":18,"currency":"AED","baseline":12,"stress":62},
        {"city":"Mumbai","price":180,"currency":"INR","baseline":100,"stress":55},
        {"city":"Kyiv","price":95,"currency":"UAH","baseline":40,"stress":95},
        {"city":"Khartoum","price":2800,"currency":"SDG","baseline":500,"stress":98},
    ]
}

# ── Sanctions Tracker ─────────────────────────────────────────
SANCTIONS_DATA = [
    {"entity":"Russia",      "type":"Comprehensive","year":2022,"scope":"G7+EU+allies","impact":"Critical",
     "detail":"SWIFT exclusion, asset freeze, energy embargo, 3,000+ item export controls"},
    {"entity":"Iran",        "type":"Comprehensive","year":2018,"scope":"USA+EU","impact":"Critical",
     "detail":"Oil export ban, SWIFT cutoff, nuclear programme restrictions, JCPOA collapsed"},
    {"entity":"North Korea", "type":"Comprehensive","year":2006,"scope":"UN+USA+EU","impact":"Critical",
     "detail":"Arms embargo, financial restrictions, luxury goods ban, coal & seafood exports banned"},
    {"entity":"Venezuela",   "type":"Sectoral",     "year":2017,"scope":"USA+EU","impact":"High",
     "detail":"Oil sector, gold trade, financial system — Maduro regime targeted"},
    {"entity":"Myanmar",     "type":"Targeted",     "year":2021,"scope":"USA+EU+UK","impact":"High",
     "detail":"Military junta post-coup targeted, gems & timber sectors, SWIFT limited"},
    {"entity":"Belarus",     "type":"Sectoral",     "year":2021,"scope":"USA+EU+UK","impact":"High",
     "detail":"Potash, financial sector, aviation — Lukashenko regime officials"},
    {"entity":"Cuba",        "type":"Comprehensive","year":1962,"scope":"USA","impact":"High",
     "detail":"Oldest active US embargo — trade, financial, travel restrictions since 1962"},
    {"entity":"Syria",       "type":"Comprehensive","year":2012,"scope":"USA+EU","impact":"High",
     "detail":"Government, military, central bank — energy sector embargo"},
    {"entity":"Sudan",       "type":"Targeted",     "year":2017,"scope":"USA","impact":"Med",
     "detail":"Arms embargo, RSF+SAF commanders, human rights violators targeted"},
    {"entity":"Nicaragua",   "type":"Targeted",     "year":2018,"scope":"USA+EU","impact":"Med",
     "detail":"Ortega officials, election fraud, judicial system corruption"},
]

# ── Currency Crisis / Devaluation Monitor ─────────────────────
CURRENCY_CRISIS = [
    {"country":"Argentina", "currency":"ARS","usd_rate":1015, "yoy_chg":210,"status":"Crisis",  "col":"#f87171","note":"Milei shock therapy — hyperinflation legacy"},
    {"country":"Turkey",    "currency":"TRY","usd_rate":38.2, "yoy_chg":62, "status":"Crisis",  "col":"#f87171","note":"Erdogan monetary unorthodoxy — structural lira decline"},
    {"country":"Venezuela", "currency":"VES","usd_rate":40.1, "yoy_chg":180,"status":"Crisis",  "col":"#f87171","note":"Petro collapse + US sanctions — economy in freefall"},
    {"country":"Sudan",     "currency":"SDG","usd_rate":595,  "yoy_chg":140,"status":"Crisis",  "col":"#f87171","note":"Civil war + RSF looting — monetary system collapsed"},
    {"country":"Egypt",     "currency":"EGP","usd_rate":50.5, "yoy_chg":68, "status":"Stress",  "col":"#fb923c","note":"IMF bailout 2024 — FX crisis stabilising slowly"},
    {"country":"Nigeria",   "currency":"NGN","usd_rate":1610, "yoy_chg":55, "status":"Stress",  "col":"#fb923c","note":"Tinubu FX reform — parallel rate gap narrowing"},
    {"country":"Ethiopia",  "currency":"ETB","usd_rate":124,  "yoy_chg":30, "status":"Stress",  "col":"#fb923c","note":"Tigray aftermath + drought — forex reserves depleted"},
    {"country":"Ghana",     "currency":"GHS","usd_rate":15.4, "yoy_chg":28, "status":"Stress",  "col":"#fb923c","note":"IMF programme 2024 — debt restructure stabilising"},
    {"country":"Pakistan",  "currency":"PKR","usd_rate":278,  "yoy_chg":22, "status":"Pressure","col":"#fbbf24","note":"IMF bailout — political instability weighing on FX"},
    {"country":"Ukraine",   "currency":"UAH","usd_rate":41.8, "yoy_chg":18, "status":"Pressure","col":"#fbbf24","note":"Managed float — NBU intervention + Western aid propping"},
]

# ── Geopolitical Risk Premiums ─────────────────────────────────
GEO_RISK_PREMIUMS = [
    {"name":"Red Sea / Houthi Attacks",  "asset":"Oil/Shipping","impact":"+$12-18/bbl  ·  +110% freight","driver":"Houthi missile+drone ops","status":"Active"},
    {"name":"Hormuz Closure Scenario",   "asset":"Oil",         "impact":"+$40-80/bbl spike risk",        "driver":"Iran-Israel escalation","status":"Elevated"},
    {"name":"Black Sea Grain Corridor",  "asset":"Wheat/Corn",  "impact":"Wheat +18%  ·  Corn +8%",       "driver":"Ukraine war + Russia blockade","status":"Active"},
    {"name":"Russia Gas Cutoff (EU)",    "asset":"Nat Gas",     "impact":"EU TTF +35% vs baseline",       "driver":"War sanctions + NS2 sabotage","status":"Active"},
    {"name":"Taiwan Strait Flashpoint",  "asset":"Semis/Tech",  "impact":"Semi stocks -25% scenario",     "driver":"PLA exercise pressure + TSMC","status":"Elevated"},
    {"name":"Suez Canal Rerouting",      "asset":"Shipping",    "impact":"Asia-Europe freight +110%",     "driver":"Red Sea crisis → Cape detour","status":"Active"},
    {"name":"Middle East Escalation",    "asset":"Oil/Gold",    "impact":"Oil +8-15%  ·  Gold +5-10%",    "driver":"Iran nuclear strikes aftermath","status":"Elevated"},
    {"name":"DPRK Provocation Risk",     "asset":"Nikkei/KOSPI","impact":"NK test → Nikkei -2-4%",        "driver":"Hwasong-17/18 ICBM posture","status":"Watch"},
    {"name":"Russia Nuclear Signalling", "asset":"All markets", "impact":"VIX spike +8-15 pts",           "driver":"Tactical doctrine threshold lowered","status":"Watch"},
    {"name":"US-China Trade War",        "asset":"Tech/Mfg",   "impact":"Semi tariffs +25-50%",           "driver":"Export controls + CHIPS Act","status":"Elevated"},
]

# ══════════════════════════════════════════════════════════════
# SIGINT DASHBOARD DATA
# ══════════════════════════════════════════════════════════════

# ── COMINT: Known signals / communications intelligence ────────
COMINT_SIGNALS = [
    {"id":"C001","actor":"Russia GRU","signal_type":"HF Burst","freq":"9-18 MHz","mode":"FSK","location":"Kaliningrad","target":"NATO Baltic","intercept":"Active","confidence":88,"last_active":"2026-03-19","detail":"High-frequency burst transmissions consistent with GRU Unit 26165 C2 tasking. Observed during Baltic NATO exercise periods."},
    {"id":"C002","actor":"IRGC","signal_type":"UHF Encrypted","freq":"420-450 MHz","mode":"AES-256","location":"Tehran / Isfahan","target":"IRGC Ground Forces","intercept":"Active","confidence":91,"last_active":"2026-03-19","detail":"Encrypted UHF comms between IRGC Quds Force and proxy networks. Traffic spike correlated with IDF strike responses."},
    {"id":"C003","actor":"DPRK RGB","signal_type":"Satellite Uplink","freq":"Ku-band","mode":"BPSK","location":"Pyongyang","target":"Overseas agents","intercept":"Active","confidence":75,"last_active":"2026-03-18","detail":"Korean-language encrypted satellite comms attributed to Reconnaissance General Bureau overseas operations."},
    {"id":"C004","actor":"China MSS","signal_type":"OTH Radar","freq":"5-30 MHz","mode":"FMCW","location":"Xinjiang / Hainan","target":"Pacific Fleet tracking","intercept":"Active","confidence":85,"last_active":"2026-03-19","detail":"Over-the-horizon Skywave radar emissions covering Western Pacific AO. Consistent with PLAN CSG tracking."},
    {"id":"C005","actor":"Russia SVR","signal_type":"Shortwave","freq":"7-14 MHz","mode":"AM numbers","location":"Moscow","target":"EU embedded assets","intercept":"Intermittent","confidence":70,"last_active":"2026-03-17","detail":"Numbers station transmissions in Czech / German language. Attributed to SVR Line S (illegals support)."},
    {"id":"C006","actor":"Houthi (IRGC-linked)","signal_type":"VHF Tactical","freq":"136-174 MHz","mode":"FM P25","location":"Hodeidah / Saada","target":"Anti-ship ops","intercept":"Active","confidence":80,"last_active":"2026-03-19","detail":"VHF tactical comms coordinating drone/missile targeting. IRGC advisory signals co-located."},
]

# ── ELINT: Electronic intelligence ────────────────────────────
ELINT_SIGNALS = [
    {"id":"E001","type":"Radar Emission","system":"Nebo-M VHF","actor":"Russia","lat":54.7,"lon":20.5,"status":"Active","freq":"150-180 MHz","range_km":1800,"capability":"Stealth detection","detail":"Nebo-M VHF radar active at Kaliningrad. Effective against F-35/B-2. Coverage extends to Baltic + Poland."},
    {"id":"E002","type":"SAM Guidance","system":"S-400 Fire Control","actor":"Russia","lat":47.97,"lon":33.58,"status":"Active","freq":"8-10 GHz","range_km":400,"capability":"A2/AD Ukraine","detail":"S-400 engagement radar active near Crimea. Creating A2/AD bubble over southern Ukraine. Multiple Patriot engagements."},
    {"id":"E003","type":"ABM Radar","system":"Don-2N (Pill Box)","actor":"Russia","lat":55.83,"lon":37.64,"status":"Active","freq":"X-band","range_km":3700,"capability":"ICBM tracking","detail":"Moscow ABM radar active. Tracks US/NATO ICBM trajectories. Part of A-135 Moscow ABM system."},
    {"id":"E004","type":"Naval Radar","system":"Type 346 AESA","actor":"China","lat":24.0,"lon":122.0,"status":"Active","freq":"S/X-band dual","range_km":500,"capability":"Carrier tracking","detail":"Type 346 AESA on CNS Fujian active during Taiwan Strait exercises. Tracking US CSG movements."},
    {"id":"E005","type":"EW Suite","system":"Krasukha-4","actor":"Russia","lat":50.5,"lon":30.5,"status":"Active","freq":"Broadband","range_km":300,"capability":"Drone/UAV jamming","detail":"Krasukha-4 EW complex active in Ukraine. Successfully jamming Starlink-dependent drones."},
    {"id":"E006","type":"OTH Radar","system":"Sunflower OTHR","actor":"Russia","lat":66.0,"lon":30.0,"status":"Active","freq":"3-30 MHz","range_km":3000,"capability":"Stealth detection","detail":"Sunflower OTH radar in northern Russia. Monitoring NATO Arctic operations and stealth aircraft."},
    {"id":"E007","type":"SIGINT Station","system":"NSA FORNSAT","actor":"USA","lat":25.0,"lon":-77.3,"status":"Active","freq":"Multi-band","range_km":500,"capability":"Comms intercept","detail":"NSA FORNSAT collection covering Middle East / Gulf region. ECHELON derivative. Bahamas facility."},
    {"id":"E008","type":"Jammer","system":"Murmansk-BN","actor":"Russia","lat":69.0,"lon":33.0,"status":"Active","freq":"3-30 MHz","range_km":5000,"capability":"HF comms disruption","detail":"Murmansk-BN strategic HF jammer. Coverage of N.Atlantic and Arctic. Disrupts NATO HF comms."},
]

# ── MASINT: Measurement and Signature Intelligence ─────────────
MASINT_EVENTS = [
    {"id":"M001","type":"Seismic","event":"Suspected underground detonation","location":"Punggye-ri, DPRK","lat":41.27,"lon":129.08,"magnitude":None,"depth_km":1.2,"confidence":55,"date":"2026-02-28","detail":"Seismic event Mb 2.1 at Punggye-ri. Shallow depth consistent with underground blast. Monitoring continues."},
    {"id":"M002","type":"Nuclear Radiation","event":"Elevated gamma signature","location":"Natanz, Iran","lat":33.72,"lon":51.73,"magnitude":None,"depth_km":0,"confidence":88,"date":"2026-03-07","detail":"Airborne gamma radiation detected by CTBTO IMS stations following IDF strike. Consistent with Cs-137 / Am-241 release from centrifuge destruction."},
    {"id":"M003","type":"Acoustic","event":"Underwater explosion signature","location":"Baltic Sea","lat":57.0,"lon":18.0,"magnitude":None,"depth_km":0.08,"confidence":78,"date":"2026-02-14","detail":"SOSUS hydrophone array detected underwater blast event. Possible sabotage of subsea infrastructure. Under investigation."},
    {"id":"M004","type":"Chemical","event":"Chlorine marker detected","location":"Idlib, Syria","lat":35.93,"lon":36.63,"magnitude":None,"depth_km":0,"confidence":62,"date":"2026-01-30","detail":"Trace chlorine signatures detected by OPCW remote sensors. Assad regime suspected. UN investigation requested."},
    {"id":"M005","type":"Thermal","event":"Large thermal signature","location":"Yongbyon, DPRK","lat":39.81,"lon":125.75,"magnitude":None,"depth_km":0,"confidence":82,"date":"2026-03-10","detail":"LANDSAT thermal anomaly at Yongbyon reprocessing plant. Consistent with active plutonium separation. Assessed: active production cycle."},
    {"id":"M006","type":"Seismic","event":"Underground construction","location":"Sanya, Hainan, China","lat":18.25,"lon":109.52,"magnitude":None,"depth_km":0.3,"confidence":74,"date":"2026-03-01","detail":"Persistent seismic signature consistent with major tunnel excavation. Likely expansion of PLAN submarine base."},
]

# ── OSINT Feeds & Collection Platforms ────────────────────────
OSINT_PLATFORMS = [
    {"name":"Sentinel Hub","type":"SAR/Optical Imagery","provider":"ESA/Commercial","coverage":"Global daily","resolution":"1-10m","status":"Active","use_case":"Conflict damage assessment, military movements"},
    {"name":"Planet Labs","type":"Optical IMINT","provider":"Commercial","coverage":"Global 3x/day","resolution":"3m","status":"Active","use_case":"Change detection, base construction monitoring"},
    {"name":"Maxar WorldView","type":"High-res IMINT","provider":"Commercial","coverage":"Tasked","resolution":"30cm","status":"Active","use_case":"Equipment ID, personnel counting"},
    {"name":"MarineTraffic AIS","type":"Vessel tracking","provider":"Commercial","coverage":"Global","resolution":"N/A","status":"Active","use_case":"Naval movements, dark ship detection"},
    {"name":"FlightRadar24","type":"ADS-B tracking","provider":"Commercial","coverage":"Global","resolution":"N/A","status":"Active","use_case":"Military aircraft movements, escort ops"},
    {"name":"GDELT Project","type":"Event data/NLP","provider":"Google/Open","coverage":"Global","resolution":"15-min updates","status":"Active","use_case":"Conflict escalation signals, media analysis"},
    {"name":"FIRMS NASA","type":"Fire/Thermal","provider":"NASA","coverage":"Global","resolution":"375m","status":"Active","use_case":"Conflict hotspots, industrial activity"},
    {"name":"Bellingcat OSINT","type":"Geolocation","provider":"Independent","coverage":"Conflict zones","resolution":"Street-level","status":"Active","use_case":"War crime documentation, equipment tracking"},
    {"name":"DigitalGlobe Archive","type":"Historical IMINT","provider":"Maxar","coverage":"Global","resolution":"50cm","status":"Active","use_case":"Before/after analysis, baseline comparison"},
    {"name":"Radio Free Europe","type":"HUMINT/Media","provider":"US Gov (USAGM)","coverage":"Russia/E.Europe","resolution":"N/A","status":"Active","use_case":"Regime instability signals, public opinion"},
]

# ── Signals of Interest: Active collection priorities ──────────
COLLECTION_PRIORITIES = [
    {"priority":1,"target":"Iran nuclear reconstruction","type":"IMINT/MASINT","status":"Active","collection":["Sentinel Hub","Maxar WV","CTBTO IMS"],"intel_gap":"Post-strike reconstruction timeline","last_update":"2026-03-19"},
    {"priority":2,"target":"DPRK ICBM preparations","type":"IMINT/SIGINT","status":"Active","collection":["Planet Labs","NSA SIGINT","SOSUS"],"intel_gap":"Hwasong-18 launch readiness","last_update":"2026-03-18"},
    {"priority":3,"target":"Russian VKS strike patterns","type":"SIGINT/COMINT","status":"Active","collection":["ELINT aircraft","NSA SCS","GCHQ"],"intel_gap":"Kalibr magazine resupply","last_update":"2026-03-19"},
    {"priority":4,"target":"PLA Taiwan Strait exercises","type":"IMINT/ELINT","status":"Active","collection":["U-2S","RC-135V/W","KH-13"],"intel_gap":"Exercise-to-operation threshold","last_update":"2026-03-17"},
    {"priority":5,"target":"Houthi missile stockpiles","type":"IMINT/HUMINT","status":"Active","collection":["MQ-9 ISR","Maxar","CIA HUMINT"],"intel_gap":"Iranian resupply routes via Oman","last_update":"2026-03-16"},
    {"priority":6,"target":"China South China Sea construction","type":"IMINT","status":"Routine","collection":["Planet Labs","Sentinel-1 SAR"],"intel_gap":"Mischief Reef tunnel depth","last_update":"2026-03-15"},
    {"priority":7,"target":"Wagner/Africa Corps deployment","type":"SIGINT/IMINT","status":"Active","collection":["NSA SIGINT","ELINT aircraft"],"intel_gap":"Mali/Niger operational command structure","last_update":"2026-03-14"},
    {"priority":8,"target":"Pakistan-Afghanistan border","type":"IMINT/SIGINT","status":"Active","collection":["RQ-4 Global Hawk","NSA SCS"],"intel_gap":"TTP tunnel networks in Paktika","last_update":"2026-03-19"},
]

# ── Threat Actor Matrix ────────────────────────────────────────
THREAT_ACTORS = [
    {"actor":"GRU (Russia)","unit":"Unit 26165 / 74455","domain":["CYBER","ELINT","HUMINT"],"threat_level":95,"operations":["Sandworm Ukraine grid","FANCY BEAR NATO","GPS spoofing Baltic"],"attribution":98,"status":"Highly Active"},
    {"actor":"MSS (China)","unit":"APT41 / Volt Typhoon","domain":["CYBER","SIGINT","IMINT"],"threat_level":90,"operations":["US logistics pre-positioning","SE Asia defence","5G supply chain"],"attribution":85,"status":"Highly Active"},
    {"actor":"IRGC (Iran)","unit":"IRGC Cyber / APT33","domain":["CYBER","COMINT","MASINT"],"threat_level":82,"operations":["CII wiper attacks","Satellite comms","Proxy C2"],"attribution":88,"status":"Elevated"},
    {"actor":"RGB (DPRK)","unit":"Lazarus / APT38","domain":["CYBER","SIGINT"],"threat_level":78,"operations":["Crypto theft","SWIFT attacks","Ransomware funding"],"attribution":80,"status":"Active"},
    {"actor":"SVR (Russia)","unit":"Cozy Bear / APT29","domain":["CYBER","HUMINT","COMINT"],"threat_level":88,"operations":["SolarWinds legacy","EU gov networks","NATO intel access"],"attribution":90,"status":"Highly Active"},
    {"actor":"PLA SSF (China)","unit":"Strategic Support Force","domain":["ELINT","CYBER","SPACE"],"threat_level":88,"operations":["GPS jamming SCS","Kill chain space","Taiwan rehearsals"],"attribution":72,"status":"Elevated"},
    {"actor":"Hezbollah SIGINT","unit":"Unit 1800","domain":["HUMINT","COMINT"],"threat_level":65,"operations":["Israel border surveillance","Lebanon telecom intercept","Iran relay"],"attribution":82,"status":"Active"},
    {"actor":"Pakistan ISI","unit":"ISI S Wing","domain":["HUMINT","SIGINT"],"threat_level":58,"operations":["Afghanistan TTP coordination","India border intel","Nuclear security"],"attribution":68,"status":"Routine"},
]

INTEL_FEED_SOURCES = [
    {"source":"Foreign Policy","cat":"ALERT","tag":"MILITARY","title":"Six U.S. Troops Killed in Aircraft Crash in Iraq","time":"20h ago","url":"https://foreignpolicy.com"},
    {"source":"Atlantic Council","cat":"ALERT","tag":"CONFLICT","title":"UN: Putin's deportation of Ukrainian children is a crime against humanity","time":"8h ago","url":"https://atlanticcouncil.org"},
    {"source":"ISW","cat":"REPORT","tag":"UKRAINE","title":"Russian forces continue offensive operations near Avdiivka sector","time":"4h ago","url":"https://understandingwar.org"},
    {"source":"CSIS","cat":"ALERT","tag":"IRAN","title":"IRGC drone production facility destroyed in latest Israeli strike","time":"6h ago","url":"https://csis.org"},
    {"source":"Reuters","cat":"REPORT","tag":"NUCLEAR","title":"IAEA loses monitoring access to Fordow enrichment site after strike","time":"12h ago","url":"https://reuters.com"},
    {"source":"Defense One","cat":"ALERT","tag":"MILITARY","title":"Pentagon orders second carrier strike group to Eastern Mediterranean","time":"3h ago","url":"https://defenseone.com"},
    {"source":"Bellingcat","cat":"REPORT","tag":"OSINT","title":"Geolocated footage confirms new Russian S-400 deployment near Zaporizhzhia","time":"7h ago","url":"https://bellingcat.com"},
    {"source":"Hacker News","cat":"ALERT","tag":"CYBER","title":"NMAP in the Movies — State-sponsored toolchain analysis","time":"1h ago","url":"https://news.ycombinator.com"},
]

CYBER_FEED = [
    {"source":"GlobalSecurity.org","title":"BRP Diego Silang — PH Navy contingent now in Australia for joint exercise","time":"4h ago","sector":"Military"},
    {"source":"IndiaGazette","title":"Iran Army chief says attack on IRIS Dena will not go unanswered","time":"7h ago","sector":"Military"},
    {"source":"NewKerala","title":"Iran Army Chief: Attack on IRIS Dena Warship Will Not Go Unanswered","time":"9h ago","sector":"Military"},
    {"source":"Dawn.com","title":"Sri Lanka repatriates remains of 84 Iranian sailors — World","time":"13h ago","sector":"Diplomatic"},
    {"source":"WCBM","title":"New cyber-physical attack vector targets ICS/SCADA water systems","time":"21h ago","sector":"Cyber"},
    {"source":"Recorded Future","title":"APT41 campaign targeting defence contractors across SE Asia","time":"2h ago","sector":"Cyber"},
]

MARKET_RADAR = {"label":"CASH","posture":"2/7 bullish","flow":"PASSIVE GAP","liquidity":"NORMAL","color":"#ffb400"}



# ══════════════════════════════════════════════════════════════
# TAB 5 — INTEL DASHBOARD
# ══════════════════════════════════════════════════════════════

with tab_intel:
    import json as _ij
    import streamlit.components.v1 as _ic
    from html import escape as _he
    from concurrent.futures import ThreadPoolExecutor as _TPE_i
    # Parallel fetch — includes live nuke/WMD enrichment
    with _TPE_i(max_workers=6) as _ex_i:
        _fi_outage = _ex_i.submit(fetch_outage_feed)
        _fi_risk   = _ex_i.submit(fetch_live_strategic_risk)
        _fi_conf   = _ex_i.submit(fetch_news_rss, "conflict")
        _fi_cyber  = _ex_i.submit(fetch_news_rss, "geopolitics")
        _fi_nuke   = _ex_i.submit(fetch_live_nuke_alerts)
        _fi_wmd    = _ex_i.submit(fetch_live_wmd_posture)
    _outage_arts_pre   = _fi_outage.result()
    _live_risk_pre     = _fi_risk.result()
    _live_conf_pre     = _fi_conf.result()
    _live_cyber_pre    = _fi_cyber.result()
    _live_nuke_data    = _fi_nuke.result()  or NUKE_ALERTS
    _live_wmd_data     = _fi_wmd.result()   or WMD_POSTURE

    _outage_arts = _outage_arts_pre

    # ── helpers ──────────────────────────────────────────────────
    def _bar(pct, col):
        p = min(int(pct), 100)
        return f'<div style="height:3px;background:rgba(255,255,255,.05);border-radius:2px;overflow:hidden;margin:5px 0"><div style="height:100%;width:{p}%;background:{col};border-radius:2px"></div></div>'

    def _rc(r):
        return "#ff3d5a" if r >= 75 else "#ff8c42" if r >= 55 else "#ffb400" if r >= 38 else "#00c8ff"

    def _bdg(text, col):
        t = _he(str(text))
        return f'<span style="display:inline-flex;padding:1px 7px;border-radius:4px;font-size:8px;border:1px solid {col}44;background:{col}18;color:{col}">{t}</span>'

    # ── KPI strip ────────────────────────────────────────────────
    high_risk  = sum(1 for c in COUNTRY_INSTABILITY if c["score"] >= 70)
    high_fp    = sum(1 for f in [
        {"risk":49},{"risk":82},{"risk":65},{"risk":58},{"risk":45},{"risk":72},{"risk":61}
    ] if f["risk"] >= 60)
    nuke_crit  = sum(1 for n in _live_nuke_data if n["level"] == "CRITICAL")
    global_risk = 58

    kpi_html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px">'
    for num, lbl, sub, col in [
        (high_risk,  "High-Risk Nations",  "Instability \u2265 70",  "#ff3d5a"),
        (global_risk,"Global Risk Score",  "ELEVATED",               "#ff8c42"),
        (high_fp,    "Elevated Postures",  "Force risk \u2265 60",   "#ff8c42"),
        (nuke_crit,  "Nuclear CRITICAL",   "Sites at critical",      "#9d6eff"),
    ]:
        kpi_html += f'''<div style="background:#070d18;border:1px solid rgba(0,200,255,.09);border-radius:13px;padding:18px 20px;position:relative;overflow:hidden">
<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{col},{col}00)"></div>
<div style="font-size:8.5px;color:#2e4a63;text-transform:uppercase;letter-spacing:.2em;margin-bottom:10px">{_he(lbl)}</div>
<div style="font-size:50px;font-weight:700;color:{col};line-height:.9;margin-bottom:8px">{num}</div>
<div style="font-size:9.5px;color:#2e4a63">{_he(sub)}</div></div>'''
    kpi_html += '</div>'

    # ── Country instability panel ─────────────────────────────────
    def _instability_panel():
        regions = ["All"] + sorted(set(c["region"] for c in COUNTRY_INSTABILITY))
        pills = "".join(
            f'<button class="ipill" data-pane="ci{i}" onclick="var pp=this.closest(\'.panel\');pp.querySelectorAll(\'.ipill\').forEach(b=>{{b.style.color=\'#3d5a73\';b.style.borderColor=\'rgba(61,90,115,.3)\';b.style.background=\'#0c1a28\';}});this.style.color=\'#00c8ff\';this.style.borderColor=\'rgba(0,200,255,.3)\';this.style.background=\'rgba(0,200,255,.08)\';pp.querySelectorAll(\'.ipane\').forEach(p=>p.style.display=\'none\');pp.querySelector(\'#ci{i}\').style.display=\'block\'" '
            f'style="padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:{"rgba(0,200,255,.08)" if i==0 else "#0c1a28"};border:1px solid {"rgba(0,200,255,.3)" if i==0 else "rgba(61,90,115,.3)"};color:{"#00c8ff" if i==0 else "#3d5a73"};margin:0 4px 4px 0">{_he(r)}</button>'
            for i, r in enumerate(regions)
        )
        panes = ""
        for i, reg in enumerate(regions):
            items = COUNTRY_INSTABILITY if reg == "All" else [c for c in COUNTRY_INSTABILITY if c["region"] == reg]
            items = sorted(items, key=lambda x: -x["score"])
            rows = ""
            for c in items:
                col = _rc(c["score"])
                tc = "#ff8c42" if c["trend"] == "↑" else "#00e676" if c["trend"] == "↓" else "#3d5a73"
                rows += f'''<div class="row-item" style="border-left-color:{col}">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
<span style="font-size:13px;font-weight:600;color:#dce8f5">{_he(c["country"])}</span>
<div style="display:flex;align-items:center;gap:8px">
<span style="font-size:9px;color:#3d5a73">U{c["U"]} C{c["C"]} S{c["S"]} I{c["I"]}</span>
<span style="font-size:9px;color:{tc}">{_he(c["trend"])}</span>
<span style="font-size:24px;font-weight:700;color:{col}">{c["score"]}</span>
</div></div>{_bar(c["score"], col)}</div>'''
            panes += f'<div id="ci{i}" class="ipane" style="display:{"block" if i==0 else "none"}">{rows}</div>'
        return f'<div class="panel"><div class="stitle">Country Instability Index</div><div style="margin-bottom:12px">{pills}</div><div class="scroll">{panes}</div></div>'

    # ── Strategic risk panel — LIVE ──────────────────────────────
    _live_risk = _live_risk_pre

    def _strategic_panel():
        import math
        sr     = _live_risk
        score  = sr["score"]
        col    = sr["color"]
        lbl    = sr["label"]
        trend  = sr.get("trend", "→")
        is_live = sr.get("is_live", False)
        comps  = sr.get("components", [])
        circ   = 2 * math.pi * 36
        dash   = circ * (1 - score / 100)
        live_badge = ('<span style="font-family:Courier New,monospace;font-size:8px;padding:1px 7px;' +
                      'border-radius:10px;background:rgba(0,200,255,.08);border:1px solid rgba(0,200,255,.2);' +
                      'color:#00c8ff;margin-left:8px">⚡ LIVE</span>') if is_live else ""
        comp_rows = "".join(
            f'''<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
<div style="min-width:140px;font-size:11px;color:#7fb3cc">{_he(c["name"])}</div>
<div style="flex:1;height:4px;background:rgba(255,255,255,.06);border-radius:2px;overflow:hidden">
<div style="height:100%;width:{c["val"]}%;background:{c["col"]}"></div></div>
<span style="font-size:10px;color:{c["col"]};min-width:24px;text-align:right">{c["val"]}</span></div>'''
            for c in comps)
        return f'''<div class="panel"><div class="stitle">Strategic Risk Overview{live_badge}</div>
<div style="display:flex;align-items:center;gap:18px;margin-bottom:16px">
<div style="position:relative;width:80px;height:80px;flex-shrink:0">
<svg style="width:80px;height:80px;transform:rotate(-90deg)" viewBox="0 0 80 80">
<circle cx="40" cy="40" r="36" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="6"/>
<circle cx="40" cy="40" r="36" fill="none" stroke="{col}" stroke-width="6" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{dash:.1f}" stroke-linecap="round"/>
</svg>
<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;font-size:26px;font-weight:700;color:{col}">{score}</div>
</div>
<div><div style="font-size:11px;color:{col};font-weight:600;margin-bottom:4px">{_he(lbl)}</div>
<div style="font-size:11px;color:#3d5a73">Trend: {_he(trend)}</div></div></div>
{comp_rows}</div>'''

    # ── Intel feed panel — LIVE ───────────────────────────────────
    _live_conflict_feed = _live_conf_pre
    _live_cyber_feed    = _live_cyber_pre

    def _feed_panel():
        intel_feed = _live_conflict_feed if _live_conflict_feed else [
            {"source":"ISW","cat":"REPORT","tag":"UKRAINE","title":"Russian forces continue offensive near Avdiivka sector","time":"stale","url":"https://understandingwar.org"},
            {"source":"Defense One","cat":"ALERT","tag":"MILITARY","title":"Pentagon orders carrier strike group to E. Mediterranean","time":"stale","url":"https://defenseone.com"},
            {"source":"Reuters","cat":"REPORT","tag":"CONFLICT","title":"Check Reuters for latest conflict updates","time":"stale","url":"https://reuters.com"},
        ]
        # Tag live articles appropriately
        for _it in intel_feed:
            if "cat" not in _it:   _it["cat"] = "REPORT"
            if "tag" not in _it:   _it["tag"] = "INTEL"
        cyber_feed = _live_cyber_feed if _live_cyber_feed else [
            {"source":"Recorded Future","title":"APT41 campaign targeting defence contractors","time":"stale","sector":"Cyber"},
            {"source":"WCBM","title":"Cyber-physical attack vector targets ICS/SCADA","time":"stale","sector":"Cyber"},
        ]
        for _it in cyber_feed:
            if "sector" not in _it: _it["sector"] = "Geopolitics"
        cat_col = {"ALERT":"#ff3d5a","REPORT":"#ffb400","BRIEF":"#00c8ff"}
        tag_col = {"MILITARY":"#ff8c42","CONFLICT":"#ff3d5a","UKRAINE":"#00c8ff","IRAN":"#ffb400","NUCLEAR":"#9d6eff","OSINT":"#00e676","Cyber":"#9d6eff","Military":"#ff8c42"}
        def _rows(items):
            out = ""
            for item in items:
                cc = cat_col.get(item.get("cat",""), "#3d5a73")
                tc = tag_col.get(item.get("tag", item.get("sector","")), "#3d5a73")
                out += f'''<div class="row-item" style="border-left-color:{cc}">
<div style="display:flex;gap:5px;align-items:center;margin-bottom:5px">
<span style="font-size:9px;color:#3d5a73;font-weight:600">{_he(item.get("source","").upper())}</span>
{_bdg(item.get("cat",""), cc) if item.get("cat") else ""}
{_bdg(item.get("tag",item.get("sector","")), tc)}
</div>
<div style="font-size:12px;font-weight:600;color:#dce8f5;margin-bottom:4px">{_he(item.get("title",""))}</div>
<div style="font-size:9px;color:#3d5a73">{_he(item.get("time",""))}</div></div>'''
            return out
        pill_style_on = "padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:rgba(0,200,255,.1);border:1px solid rgba(0,200,255,.3);color:#00c8ff;margin-right:4px"
        pill_style_off = "padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:#0c1a28;border:1px solid rgba(61,90,115,.3);color:#3d5a73;margin-right:4px"
        return f'''<div class="panel"><div class="stitle"><span style="width:6px;height:6px;border-radius:50%;background:#ff3d5a;display:inline-block;animation:bl 1.2s ease-in-out infinite;margin-right:4px"></span>Intelligence Feed</div>
<div style="margin-bottom:12px">
<button onclick="this.parentNode.querySelectorAll(\'button\').forEach(b=>b.setAttribute(\'style\',\'{pill_style_off}\'));this.setAttribute(\'style\',\'{pill_style_on}\');document.getElementById(\'if0\').style.display=\'block\';document.getElementById(\'if1\').style.display=\'none\'" style="{pill_style_on}">Military / Conflict</button>
<button onclick="this.parentNode.querySelectorAll(\'button\').forEach(b=>b.setAttribute(\'style\',\'{pill_style_off}\'));this.setAttribute(\'style\',\'{pill_style_on}\');document.getElementById(\'if0\').style.display=\'none\';document.getElementById(\'if1\').style.display=\'block\'" style="{pill_style_off}">Cyber / OSINT</button>
</div>
<div class="scroll">
<div id="if0">{_rows(intel_feed)}</div>
<div id="if1" style="display:none">{_rows(cyber_feed)}</div>
</div></div>'''

    # ── Force posture panel ────────────────────────────────────────
    def _posture_panel():
        fps = [
            {"activity":"Combined air-naval activity","actors":"UK/Unknown","signals":860,"risk":49},
            {"activity":"Missile test/launch","actors":"Iran","signals":12,"risk":82},
            {"activity":"Troop mobilisation","actors":"Russia","signals":44,"risk":65},
            {"activity":"Air defence activation","actors":"Israel","signals":31,"risk":58},
            {"activity":"Naval patrol","actors":"China/SCS","signals":28,"risk":45},
            {"activity":"Cyber operation","actors":"Unknown/State","signals":77,"risk":72},
            {"activity":"ICBM/MLRS posture alert","actors":"DPRK","signals":18,"risk":61},
        ]
        rows = ""
        for fp in fps:
            col = _rc(fp["risk"])
            rows += f'''<div class="row-item" style="border-left-color:{col};display:flex;align-items:center;gap:10px">
<div style="flex:1">
<div style="font-size:12px;font-weight:600;color:#dce8f5;margin-bottom:2px">{_he(fp["activity"])}</div>
<div style="font-size:9px;color:#3d5a73;margin-bottom:4px">{_he(fp["actors"])} &middot; {fp["signals"]:,} signals</div>
{_bar(fp["risk"], col)}</div>
<div style="font-size:28px;font-weight:700;color:{col};flex-shrink:0">{fp["risk"]}</div></div>'''
        return f'<div class="panel"><div class="stitle">Force Posture Monitor</div><div class="scroll">{rows}</div></div>'

    # ── Infrastructure panel ───────────────────────────────────────
    def _infra_panel():
        infra = {
            "cables": {"count":86,"at_risk":12,"items":[
                {"name":"SEA-ME-WE 4","region":"Indian Ocean","risk":72,"status":"Degraded"},
                {"name":"Africa Coast to Europe","region":"W Africa","risk":81,"status":"Cut"},
                {"name":"PEACE Cable","region":"ME/Africa","risk":65,"status":"Degraded"},
                {"name":"AAE-1","region":"Asia-Europe","risk":55,"status":"Active"},
            ]},
            "pipelines": {"count":88,"at_risk":9,"items":[
                {"name":"Nord Stream (sabotaged)","region":"Baltic","risk":95,"status":"Sabotaged"},
                {"name":"Trans-Arabian Pipeline","region":"Middle East","risk":78,"status":"Suspended"},
                {"name":"Druzhba Pipeline","region":"Europe","risk":62,"status":"Reduced"},
            ]},
            "ports": {"count":62,"at_risk":8,"items":[
                {"name":"Port of Hodeidah","region":"Yemen","risk":88,"status":"Blockaded"},
                {"name":"Port Sudan","region":"Sudan","risk":74,"status":"Contested"},
            ]},
            "chokepoints": {"count":13,"at_risk":4,"items":[
                {"name":"Strait of Hormuz","risk":82,"status":"At Risk","traffic_pct":20},
                {"name":"Bab el-Mandeb","risk":79,"status":"Threatened","traffic_pct":9},
                {"name":"Suez Canal","risk":52,"status":"Reduced","traffic_pct":12},
                {"name":"Strait of Malacca","risk":28,"status":"Active","traffic_pct":25},
            ]},
            "power_grids": {"count":191,"at_risk":22,"items":[
                {"name":"Ukraine National Grid","region":"Ukraine","risk":88,"status":"Under Attack"},
                {"name":"Sudan Power Corp","region":"Sudan","risk":75,"status":"Disrupted"},
            ]},
        }
        status_col = {"Cut":"#ff3d5a","Sabotaged":"#ff3d5a","Blockaded":"#ff3d5a","Under Attack":"#ff3d5a",
                      "Destroyed":"#ff3d5a","Contested":"#ffb400","Degraded":"#ffb400","Suspended":"#ffb400",
                      "Reduced":"#ffb400","At Risk":"#ffb400","Threatened":"#ffb400","Disrupted":"#ffb400","Active":"#00e676"}
        keys   = ["cables","pipelines","ports","chokepoints","power_grids"]
        labels = ["Cables","Pipelines","Ports","Chokepoints","Power Grids"]
        pill_style_on  = "padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:rgba(0,200,255,.1);border:1px solid rgba(0,200,255,.3);color:#00c8ff;margin-right:4px"
        pill_style_off = "padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:#0c1a28;border:1px solid rgba(61,90,133,.3);color:#3d5a73;margin-right:4px"
        pills = "".join(
            f'<button onclick="this.parentNode.querySelectorAll(\'button\').forEach(b=>b.setAttribute(\'style\',\'{pill_style_off}\'));this.setAttribute(\'style\',\'{pill_style_on}\');[\'cables\',\'pipelines\',\'ports\',\'chokepoints\',\'power_grids\'].forEach(k=>document.getElementById(\'ic_\'+k).style.display=\'none\');document.getElementById(\'ic_{k}\').style.display=\'block\'" style="{pill_style_on if i==0 else pill_style_off}">{_he(lbl)}</button>'
            for i,(k,lbl) in enumerate(zip(keys,labels))
        )
        panes = ""
        for i,(k,lbl) in enumerate(zip(keys,labels)):
            d = infra[k]
            items = d["items"]
            rp = round(d["at_risk"]/d["count"]*100) if d["count"] else 0
            stat_cards = "".join(
                f'<div style="background:rgba(255,255,255,.02);border-radius:6px;padding:8px;text-align:center">'
                f'<div style="font-size:8px;color:#3d5a73;text-transform:uppercase;margin-bottom:4px">{lbl2}</div>'
                f'<div style="font-size:24px;font-weight:700;color:{col2}">{val2}</div></div>'
                for lbl2,val2,col2 in [("Total",d["count"],"#00c8ff"),("At Risk",d["at_risk"],"#ff3d5a"),("Risk%",f"{rp}%","#ffb400")]
            )
            item_rows = ""
            for item in items:
                r = item["risk"]
                col = _rc(r)
                sc  = status_col.get(item.get("status",""), "#3d5a73")
                extra = f'{item["traffic_pct"]}% global trade' if item.get("traffic_pct") else item.get("region","")
                item_rows += f'''<div class="row-item" style="border-left-color:{col}">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
<span style="font-size:12px;font-weight:600;color:#dce8f5">{_he(item["name"])}</span>
<div style="display:flex;align-items:center;gap:6px">
{_bdg(item.get("status",""), sc)}
<span style="font-size:18px;font-weight:700;color:{col}">{r}</span>
</div></div>{_bar(r, col)}
<div style="font-size:9px;color:#3d5a73;margin-top:2px">{_he(extra)}</div></div>'''
            panes += f'<div id="ic_{k}" style="display:{"block" if i==0 else "none"}"><div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px">{stat_cards}</div><div class="scroll">{item_rows}</div></div>'
        return f'<div class="panel"><div class="stitle">Infrastructure Cascade</div><div style="margin-bottom:12px">{pills}</div>{panes}</div>'

    # ── Nuclear / WMD panel ────────────────────────────────────────
    def _nuclear_panel():
        pill_style_on  = "padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:rgba(0,200,255,.1);border:1px solid rgba(0,200,255,.3);color:#00c8ff;margin-right:4px"
        pill_style_off = "padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:#0c1a28;border:1px solid rgba(61,90,115,.3);color:#3d5a73;margin-right:4px"
        nuke_rows = ""
        for n in _live_nuke_data:
            lc = "#ff3d5a" if n["level"]=="CRITICAL" else "#ff8c42" if n["level"]=="HIGH" else "#ffb400"
            live_badge = _bdg("LIVE", "#00e676") if n.get("live_hits", 0) > 0 else ""
            live_extra = f'<div style="font-size:9px;color:#2a8a5a;margin-top:3px">▸ {_he(n["live_headline"][:90])}</div>' if n.get("live_headline") else ""
            nuke_rows += f'''<div class="row-item" style="border-left-color:{n.get("col",lc)};background:#06101e">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
<span style="font-size:12px;font-weight:600;color:#dce8f5">{_he(n["site"])}</span>
<div style="display:flex;gap:4px;align-items:center">{live_badge}{_bdg(n["status"], lc)}</div></div>
<div style="font-size:11px;color:#7fb3cc;line-height:1.5">{_he(n["detail"])}</div>{live_extra}</div>'''
        wmd_rows = ""
        for w in _live_wmd_data:
            col = _rc(w["risk"])
            live_badge = _bdg("LIVE", "#00e676") if w.get("live_hits", 0) > 0 else ""
            live_extra = f'<div style="font-size:9px;color:#2a8a5a;margin-top:3px">▸ {_he(w["live_headline"][:90])}</div>' if w.get("live_headline") else ""
            wmd_rows += f'''<div class="row-item" style="border-left-color:{col}">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
<div><span style="font-size:12px;font-weight:600;color:#dce8f5">{_he(w["actor"])}</span>
<span style="font-size:9px;color:#3d5a73;margin-left:8px">{_he(w["type"])}</span></div>
<div style="display:flex;gap:4px;align-items:center">{live_badge}<span style="font-size:24px;font-weight:700;color:{col}">{w["risk"]}</span></div></div>
{_bar(w["risk"], col)}
<div style="font-size:10px;color:#3d5a73;margin-top:2px">{_he(w["assets"][:70])}</div>{live_extra}</div>'''
        return f'''<div class="panel"><div class="stitle">Nuclear &amp; WMD Status</div>
<div style="margin-bottom:12px">
<button onclick="this.parentNode.querySelectorAll(\'button\').forEach(b=>b.setAttribute(\'style\',\'{pill_style_off}\'));this.setAttribute(\'style\',\'{pill_style_on}\');document.getElementById(\'nw0\').style.display=\'block\';document.getElementById(\'nw1\').style.display=\'none\'" style="{pill_style_on}">Nuclear Sites</button>
<button onclick="this.parentNode.querySelectorAll(\'button\').forEach(b=>b.setAttribute(\'style\',\'{pill_style_off}\'));this.setAttribute(\'style\',\'{pill_style_on}\');document.getElementById(\'nw0\').style.display=\'none\';document.getElementById(\'nw1\').style.display=\'block\'" style="{pill_style_off}">WMD Posture</button>
</div>
<div class="scroll">
<div id="nw0">{nuke_rows}</div>
<div id="nw1" style="display:none">{wmd_rows}</div>
</div></div>'''

    # ── Chokepoints panel ──────────────────────────────────────────
    def _chokepoints_panel():
        cps = [
            {"name":"Strait of Hormuz","risk":80,"status":"red","flow":"eastbound/westbound","warnings":0,"ais":0,"wow":-94.4,"context":"Active conflict - Iran-Israel war. Iranian naval blockade risk elevated. 20% of global oil transits here.","exports":["Gulf Oil Exports","Qatar LNG","Iran Exports"]},
            {"name":"Bab el-Mandeb","risk":75,"status":"red","flow":"northbound/southbound","warnings":3,"ais":12,"wow":-41.0,"context":"Houthi attacks continuing. Red Sea rerouting adding 2-3 weeks to Asia-Europe routes.","exports":["Suez traffic","EU-Asia trade","Oil tankers"]},
            {"name":"Suez Canal","risk":52,"status":"amber","flow":"northbound/southbound","warnings":1,"ais":3,"wow":-18.0,"context":"Reduced traffic due to Red Sea security. Some rerouting via Cape of Good Hope continues.","exports":["EU-Asia Container","Mediterranean Oil","LNG"]},
            {"name":"Taiwan Strait","risk":55,"status":"amber","flow":"northbound/southbound","warnings":0,"ais":2,"wow":-8.4,"context":"PLA military exercises increasing. Semiconductor supply chain vulnerability elevated.","exports":["Taiwan Semiconductors","China Exports","Japan Trade"]},
            {"name":"Strait of Malacca","risk":22,"status":"green","flow":"eastbound/westbound","warnings":0,"ais":0,"wow":2.1,"context":"Normal operations. 25% of global trade and 300+ vessels per day.","exports":["SE Asia Trade","China Imports","Japan/Korea Oil"]},
        ]
        rows = ""
        for cp in cps:
            col = "#ff3d5a" if cp["status"]=="red" else "#ffb400" if cp["status"]=="amber" else "#00e676"
            wc  = "#ff3d5a" if cp["wow"] < 0 else "#00e676"
            wow_str = f'+{cp["wow"]}' if cp["wow"] > 0 else str(cp["wow"])
            exps = " ".join(_bdg(e, "#3d5a73") for e in cp["exports"])
            rows += f'''<div class="row-item" style="border-left-color:{col}">
<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px">
<div>
<div style="font-size:13px;font-weight:700;color:#dce8f5;margin-bottom:2px">{_he(cp["name"])}</div>
<div style="font-size:9px;color:#3d5a73">{cp["warnings"]} warnings &middot; {cp["ais"]} AIS &middot; {_he(cp["flow"])}</div>
</div>
<div style="text-align:right;flex-shrink:0;margin-left:12px">
<div style="font-size:28px;font-weight:700;color:{col}">{cp["risk"]}</div>
<div style="font-size:9px;color:{wc}">WoW {wow_str}%</div>
</div></div>
{_bar(cp["risk"], col)}
<div style="font-size:11px;color:#7fb3cc;line-height:1.55;margin:6px 0">{_he(cp["context"][:140])}</div>
<div>{exps}</div></div>'''
        return f'<div class="panel"><div class="stitle">Supply Chain Chokepoints</div><div class="scroll">{rows}</div></div>'

    # ── Outages panel ──────────────────────────────────────────────
    def _outages_panel():
        pill_style_on  = "padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:rgba(0,200,255,.1);border:1px solid rgba(0,200,255,.3);color:#00c8ff;margin-right:4px"
        pill_style_off = "padding:4px 12px;border-radius:20px;font-size:10px;cursor:pointer;background:#0c1a28;border:1px solid rgba(61,90,115,.3);color:#3d5a73;margin-right:4px"
        known = [
            {"name":"Gaza - Total Blackout","severity":"Total","cause":"Infrastructure destruction"},
            {"name":"Sudan - Partial","severity":"Partial","cause":"Conflict/Power"},
            {"name":"Myanmar - Targeted Shutdown","severity":"Targeted","cause":"Junta censorship"},
            {"name":"Iran - Throttled","severity":"Throttled","cause":"Government restriction"},
            {"name":"Russia - Selective Block","severity":"Selective","cause":"Censorship"},
            {"name":"Ukraine - Disrupted","severity":"Disrupted","cause":"Missile strikes"},
        ]
        if _outage_arts:
            live_rows = ""
            for o in _outage_arts[:8]:
                live_rows += f'''<div class="row-item" style="border-left-color:#ff8c42">
<div style="display:flex;justify-content:space-between;margin-bottom:3px">
<span style="font-size:9px;color:#ff8c42;font-weight:600">{_he((o.get("source","")).upper()[:28])}</span>
<span style="font-size:9px;color:#3d5a73">{_he(o.get("time",""))}</span></div>
<div style="font-size:12px;color:#dce8f5;margin-bottom:3px">{_he(o.get("title","")[:85])}</div>
{"" if not o.get("url") else f'<a href="{_he(o["url"])}" target="_blank" style="font-size:9px;color:#00c8ff;text-decoration:none">Read &#8594;</a>'}</div>'''
        else:
            live_rows = '<div style="font-size:10px;color:#3d5a73;padding:10px 0">No live outage alerts in the last 6 hours.</div>'
        known_rows = ""
        for io in known:
            ic = "#ff3d5a" if io["severity"]=="Total" else "#ff8c42" if io["severity"] in ("Partial","Disrupted") else "#ffb400"
            known_rows += f'''<div class="row-item" style="border-left-color:{ic}">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
<span style="font-size:12px;font-weight:600;color:#dce8f5">{_he(io["name"])}</span>
{_bdg(io["severity"], ic)}</div>
<div style="font-size:9px;color:#3d5a73">{_he(io["cause"])}</div></div>'''
        return f'''<div class="panel"><div class="stitle"><span style="width:6px;height:6px;border-radius:50%;background:#ff8c42;display:inline-block;animation:bl 1.2s ease-in-out infinite;margin-right:4px"></span>Internet Outages &amp; Censorship</div>
<div style="margin-bottom:12px">
<button onclick="this.parentNode.querySelectorAll(\'button\').forEach(b=>b.setAttribute(\'style\',\'{pill_style_off}\'));this.setAttribute(\'style\',\'{pill_style_on}\');document.getElementById(\'io0\').style.display=\'block\';document.getElementById(\'io1\').style.display=\'none\'" style="{pill_style_on}">Live Feed</button>
<button onclick="this.parentNode.querySelectorAll(\'button\').forEach(b=>b.setAttribute(\'style\',\'{pill_style_off}\'));this.setAttribute(\'style\',\'{pill_style_on}\');document.getElementById(\'io0\').style.display=\'none\';document.getElementById(\'io1\').style.display=\'block\'" style="{pill_style_off}">Known Outages</button>
</div>
<div class="scroll">
<div id="io0">{live_rows}</div>
<div id="io1" style="display:none">{known_rows}</div>
</div></div>'''

    # ── Assemble all panels ────────────────────────────────────────
    def _grid(*panels):
        inner = "".join(panels)
        n = len(panels)
        cols = f"repeat({n},1fr)"
        return f'<div style="display:grid;grid-template-columns:{cols};gap:14px;margin-bottom:20px">{inner}</div>'

    _p_instab  = _instability_panel()
    _p_strat   = _strategic_panel()
    _p_feed    = _feed_panel()
    _p_posture = _posture_panel()
    _p_infra   = _infra_panel()
    _p_nuclear = _nuclear_panel()
    _p_choke   = _chokepoints_panel()
    _p_outages = _outages_panel()

    _intel_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html{{scroll-behavior:smooth;}}
body{{
  background:#030609;
  background-image:radial-gradient(ellipse 70% 30% at 50% -2%,rgba(0,180,255,.04) 0%,transparent 65%);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
  color:#d4e5f5;padding:22px 20px 60px;line-height:1.45;
}}
.fm{{font-family:"Courier New",Courier,monospace;}}
.fd{{font-family:Arial,sans-serif;font-weight:700;letter-spacing:.02em;}}
.panel{{
  background:#070d18;
  border:1px solid rgba(0,200,255,.09);
  border-radius:14px;padding:20px 22px;
  position:relative;overflow:hidden;
}}
.panel::before{{
  content:"";position:absolute;top:0;left:18px;right:18px;height:1px;
  background:linear-gradient(90deg,transparent,rgba(0,200,255,.1),transparent);
}}
.stitle{{
  font-size:8.5px;font-weight:700;letter-spacing:.22em;
  text-transform:uppercase;color:#2e4a63;
  display:flex;align-items:center;gap:10px;margin-bottom:16px;
}}
.stitle::after{{content:"";flex:1;height:1px;background:rgba(46,74,99,.25);}}
.row-item{{
  border-left:2px solid;border-radius:8px;padding:11px 13px;
  margin-bottom:8px;background:#06101e;
  border-top:1px solid rgba(255,255,255,.025);
  border-right:1px solid rgba(255,255,255,.025);
  border-bottom:1px solid rgba(255,255,255,.025);
  transition:background .13s;
}}
.row-item:last-child{{margin-bottom:0;}}
.row-item:hover{{background:#091525;}}
.scroll{{max-height:370px;overflow-y:auto;padding-right:2px;}}
::-webkit-scrollbar{{width:3px;}}
::-webkit-scrollbar-thumb{{background:rgba(0,200,255,.18);border-radius:2px;}}
::-webkit-scrollbar-track{{background:transparent;}}
@keyframes bl{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.2;transform:scale(.6)}}}}
@media(max-width:900px){{.g4{{grid-template-columns:1fr 1fr!important;}}}}
@media(max-width:700px){{.g4,.g25,.g2{{grid-template-columns:1fr!important;}}}}
</style>
</head>
<body>
{kpi_html}
<div class="g4" style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px">
{_p_instab}{_p_strat}{_p_feed}{_p_posture}
</div>
<div class="g25" style="display:grid;grid-template-columns:2fr 3fr;gap:14px;margin-bottom:20px">
{_p_infra}{_p_nuclear}
</div>
<div class="g2" style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
{_p_choke}{_p_outages}
</div>
</body></html>"""

    _ic.html(_intel_html, height=5400, scrolling=True)


# ══════════════════════════════════════════════════════════════
# TAB 7 — SIGINT DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab_sigint:
    import json as _sj
    import streamlit.components.v1 as _sc
    from datetime import datetime as _sdt, timezone as _stz

    # ── SIGINT-specific auto-refresh (60 seconds) ─────────────
    try:
        from streamlit_autorefresh import st_autorefresh as _sar
        _sar(interval=90_000, key="sigint_refresh")  # 90s — intel feed refresh
    except ImportError:
        pass

    # ── Live data collection — parallel ────────────────────────
    from concurrent.futures import ThreadPoolExecutor as _TPE_s
    with _TPE_s(max_workers=18) as _ex_s:
        _fs_news    = _ex_s.submit(fetch_news_rss, "geopolitics")
        _fs_conf    = _ex_s.submit(fetch_news_rss, "conflict")
        _fs_evts    = _ex_s.submit(fetch_live_global_events, 25)
        _fs_out     = _ex_s.submit(fetch_outage_feed)
        _fs_risk    = _ex_s.submit(fetch_live_strategic_risk)
        _fs_kp      = _ex_s.submit(fetch_kp)
        _fs_usgs    = _ex_s.submit(fetch_usgs)
        _fs_cyber   = _ex_s.submit(fetch_gdelt_conflict, "cyber attack espionage hacking")
        # Live SIGINT enrichment — replaces hardcoded baselines
        _fs_comint  = _ex_s.submit(fetch_live_comint)
        _fs_elint   = _ex_s.submit(fetch_live_elint)
        _fs_masint  = _ex_s.submit(fetch_live_masint)
        _fs_actors  = _ex_s.submit(fetch_live_threat_actors)
        # Live overlay enrichment — replaces remaining hardcoded map arrays
        _fs_gps_jam = _ex_s.submit(fetch_live_gps_jamming)
        _fs_cythrt  = _ex_s.submit(fetch_live_cyber_threats)
        _fs_cii     = _ex_s.submit(fetch_live_cii)
        _fs_inet    = _ex_s.submit(fetch_live_internet_outages)
        _fs_milact  = _ex_s.submit(fetch_live_military_activity)
    _sigint_news      = _fs_news.result()
    _sigint_conf      = _fs_conf.result()
    _sigint_events    = _fs_evts.result()
    _sigint_outage    = _fs_out.result()
    _sigint_risk      = _fs_risk.result()
    _sigint_kp        = _fs_kp.result()
    _sigint_usgs      = _fs_usgs.result()
    _sigint_cyber_raw = _fs_cyber.result()
    # Live-enriched SIGINT datasets (fall back to static baseline on failure)
    _live_comint  = _fs_comint.result()  or COMINT_SIGNALS
    _live_elint   = _fs_elint.result()   or ELINT_SIGNALS
    _live_masint  = _fs_masint.result()  or MASINT_EVENTS
    _live_actors  = _fs_actors.result()  or THREAT_ACTORS
    # Live-enriched overlay datasets
    _live_gps_jam = _fs_gps_jam.result() or GPS_JAMMING_ZONES
    _live_cythrt  = _fs_cythrt.result()  or CYBER_THREATS_GEO
    _live_cii     = _fs_cii.result()     or CII_INSTABILITY
    _live_inet    = _fs_inet.result()    or INTERNET_OUTAGES
    _live_milact  = _fs_milact.result()  or MILITARY_ACTIVITY

    # Seismic events M3.5+ last 24h for MASINT overlay
    _sig_quakes = []
    try:
        if _sigint_usgs is not None and not _sigint_usgs.empty:
            _q24 = _sigint_usgs[_sigint_usgs["mag"] >= 3.5].nlargest(12, "mag")
            _sig_quakes = [
                {"place": str(r["place"]), "mag": float(r["mag"]),
                 "depth_km": float(r["depth_km"]), "time": str(r["time"]),
                 "lat": float(r["lat"]), "lon": float(r["lon"])}
                for _, r in _q24.iterrows()
            ]
    except Exception:
        pass

    # KP index summary — fully defensive against any return shape
    _kp_current = 0
    _kp_status  = "Quiet"
    try:
        _kp_raw = _sigint_kp if isinstance(_sigint_kp, dict) else {}
        _kp_series_raw = _kp_raw.get("series") or []
        _kp_vals = []
        for _p in _kp_series_raw[-6:]:
            try:
                if isinstance(_p, dict):
                    _kp_vals.append(float(_p.get("kp", 0) or _p.get("kp_index", 0) or 0))
                else:
                    _kp_vals.append(float(_p))
            except (TypeError, ValueError):
                pass
        if _kp_vals:
            _kp_current = round(max(_kp_vals), 1)
        _kp_status = ("EXTREME STORM" if _kp_current >= 8 else
                      "SEVERE STORM"  if _kp_current >= 7 else
                      "STRONG STORM"  if _kp_current >= 6 else
                      "MODERATE STORM"if _kp_current >= 5 else
                      "MINOR STORM"   if _kp_current >= 4 else
                      "Unsettled"     if _kp_current >= 3 else "Quiet")
    except Exception:
        pass  # keep defaults

    # Active internet outages from live feed
    _outage_live = _sigint_outage[:10] if _sigint_outage else []

    # Build enriched GDELT cyber events
    _cyber_live = []
    for _ev in (_sigint_cyber_raw or [])[:8]:
        _cyber_live.append({
            "title":  _ev.get("title", ""),
            "source": _ev.get("source", ""),
            "time":   _ev.get("time", ""),
            "url":    _ev.get("url", ""),
        })

    # Live GDELT global events for threat tracking
    _live_events_sigint = []
    for _gev in (_sigint_events or [])[:15]:
        _live_events_sigint.append({
            "title":  _gev.get("title", ""),
            "source": _gev.get("source", ""),
            "time":   _gev.get("time", ""),
            "url":    _gev.get("url", ""),
            "cat":    _gev.get("cat", ""),
        })

    _sig_ts = _sdt.now(tz=_stz.utc).strftime("%H:%M:%S UTC")

    _sigint_payload = _sj.dumps({
        # Live-enriched SIGINT data (GDELT + USGS backed; falls back to baseline)
        "comint":          _live_comint,
        "elint":           _live_elint,
        "masint":          _live_masint,
        "osint_platforms": OSINT_PLATFORMS,
        "collection":      COLLECTION_PRIORITIES,
        "actors":          _live_actors,
        "orbital":         ORBITAL_SURVEILLANCE,
        "gps_jamming":     _live_gps_jam,
        "cyber_threats":   _live_cythrt,
        "cii":             _live_cii,
        "mil_activity":    _live_milact,
        "internet_static": _live_inet,
        # Live data
        "live_feed":       (_sigint_news  or [])[:15],
        "live_conflict":   (_sigint_conf  or [])[:10],
        "live_events":     _live_events_sigint,
        "live_cyber":      _cyber_live,
        "live_outages":    _outage_live,
        "live_quakes":     _sig_quakes,
        "live_risk":       _sigint_risk,
        "kp_current":      _kp_current,
        "kp_status":       _kp_status,
        "kp_series":       (_sigint_kp.get("series") or [])[-24:],
        "ts":              _sig_ts,
        "refresh_interval": 180,
    })


    # Computed vars for f-string injection
    _sig_risk_score = _sigint_risk.get("score", "—") if isinstance(_sigint_risk, dict) else "—"
    _sig_risk_label = _sigint_risk.get("label", "") if isinstance(_sigint_risk, dict) else ""
    _jam_count = sum(1 for z in _live_gps_jam if z.get("severity") == "High")
    _crit_actors = sum(1 for a in _live_actors if a.get("threat_level", 0) >= 85)
    _cii_crit = sum(1 for c in _live_cii if c.get("risk", 0) >= 90)
    _live_count = len(_sigint_news or []) + len(_sigint_conf or [])

    _sigint_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
:root{{
  --bg:#03060d;--bg1:#060d18;--bg2:#0a1525;--bg3:#0f1e35;
  --edge:rgba(0,180,255,.07);--edge2:rgba(0,180,255,.14);
  --amber:#f0a500;--cyan:#00d4ff;--red:#ff2d55;--green:#00e5a0;--violet:#a855f7;
  --text:#c2d8ee;--text2:#7aa0be;--text3:#2e4d66;
}}
html,body{{height:100%;}}
body{{background:var(--bg);font-family:'Barlow',system-ui,sans-serif;color:var(--text);overflow-x:hidden;
  background-image:radial-gradient(ellipse 70% 30% at 50% 0%,rgba(0,180,255,.055) 0%,transparent 65%),
    radial-gradient(ellipse 40% 60% at 98% 50%,rgba(240,165,0,.03) 0%,transparent 55%),
    radial-gradient(ellipse 30% 50% at 2% 80%,rgba(168,85,247,.025) 0%,transparent 55%);}}
body::after{{content:'';pointer-events:none;position:fixed;inset:0;z-index:9999;
  background:repeating-linear-gradient(0deg,transparent 0,transparent 3px,rgba(0,0,0,.02) 3px,rgba(0,0,0,.02) 4px);}}
/* Topbar */
.topbar{{position:sticky;top:0;z-index:200;display:grid;grid-template-columns:auto 1fr auto;align-items:stretch;
  background:rgba(3,6,13,.94);border-bottom:1px solid var(--edge2);
  backdrop-filter:blur(16px);box-shadow:0 1px 28px rgba(0,0,0,.5);}}
.tb-logo{{display:flex;flex-direction:column;justify-content:center;padding:10px 20px;border-right:1px solid var(--edge2);}}
.tb-name{{font-family:'Orbitron',monospace;font-weight:900;font-size:14px;letter-spacing:.18em;color:var(--cyan);}}
.tb-sub{{font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:.25em;color:var(--text3);margin-top:3px;}}
.tb-metrics{{display:flex;align-items:stretch;overflow-x:auto;}}
.tb-m{{display:flex;flex-direction:column;justify-content:center;padding:8px 18px;border-right:1px solid var(--edge);min-width:0;flex-shrink:0;}}
.tb-ml{{font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:.2em;text-transform:uppercase;color:var(--text3);margin-bottom:3px;}}
.tb-mv{{font-family:'Orbitron',monospace;font-weight:700;font-size:14px;}}
.tb-right{{display:flex;align-items:center;gap:10px;padding:0 16px;border-left:1px solid var(--edge2);}}
.tb-ts{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);}}
.tb-pill{{display:flex;align-items:center;gap:5px;padding:5px 11px;border-radius:2px;
  border:1px solid rgba(0,229,160,.28);background:rgba(0,229,160,.06);
  font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.1em;color:var(--green);}}
.tb-cd{{font-family:'JetBrains Mono',monospace;font-size:7.5px;color:var(--text3);}}
/* Ticker */
.ticker{{overflow:hidden;white-space:nowrap;background:rgba(240,165,0,.03);border-bottom:1px solid rgba(240,165,0,.1);padding:6px 0;}}
.t-inner{{display:inline-block;animation:scr 100s linear infinite;}}
@keyframes scr{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}
.ti{{display:inline-flex;align-items:center;gap:8px;margin-right:56px;font-family:'JetBrains Mono',monospace;font-size:9px;color:rgba(194,216,238,.38);}}
.ti-s{{color:var(--amber);font-weight:500;}}
/* KPIs */
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--edge2);border-bottom:1px solid var(--edge2);}}
.kpi{{background:var(--bg1);padding:18px 20px;position:relative;overflow:hidden;}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--kc,var(--cyan)) 40%,transparent);}}
.kpi-l{{font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:var(--text3);margin-bottom:10px;}}
.kpi-v{{font-family:'Orbitron',monospace;font-weight:900;font-size:44px;color:var(--kc,var(--cyan));line-height:.9;margin-bottom:6px;}}
.kpi-s{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);}}
/* Layout */
.body{{padding:14px 16px 40px;}}
.r2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;}}
.r3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;}}
@media(max-width:1100px){{.r3{{grid-template-columns:1fr 1fr;}}}}
@media(max-width:680px){{.r2,.r3{{grid-template-columns:1fr;}}}}
/* Cards */
.card{{background:var(--bg1);border:1px solid var(--edge2);border-radius:3px;position:relative;overflow:hidden;display:flex;flex-direction:column;animation:rise .3s ease both;}}
@keyframes rise{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
.card:nth-child(2){{animation-delay:.06s;}}.card:nth-child(3){{animation-delay:.12s;}}
.card::before{{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(0,180,255,.22),transparent);pointer-events:none;}}
.ch{{display:flex;align-items:center;gap:9px;padding:10px 14px;border-bottom:1px solid var(--edge);background:rgba(0,0,0,.28);flex-shrink:0;}}
.ch-ico{{width:22px;height:22px;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:11px;flex-shrink:0;}}
.ch-title{{font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--text2);flex:1;}}
.ch-ct{{font-family:'JetBrains Mono',monospace;font-size:8px;padding:2px 7px;border-radius:2px;background:rgba(0,0,0,.5);border:1px solid var(--edge2);color:var(--text3);}}
.live-chip{{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:2px;background:rgba(0,229,160,.06);border:1px solid rgba(0,229,160,.22);font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:.1em;color:var(--green);}}
.classif{{position:absolute;bottom:8px;right:10px;pointer-events:none;font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:.15em;color:var(--text3);opacity:.35;text-transform:uppercase;}}
/* Scroll */
.scroll{{overflow-y:auto;flex:1;padding:10px 12px;max-height:330px;scrollbar-width:thin;scrollbar-color:var(--bg3) transparent;display:flex;flex-direction:column;gap:5px;}}
.scroll::-webkit-scrollbar{{width:2px;}}.scroll::-webkit-scrollbar-thumb{{background:var(--bg3);}}
/* Items */
.item{{background:var(--bg2);border-radius:2px;border-left:2px solid;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);padding:9px 11px;transition:background .12s;}}
.item:hover{{background:var(--bg3);}}
.i-top{{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:5px;}}
.i-name{{font-family:'Barlow',sans-serif;font-size:13px;font-weight:600;color:#e0eefa;line-height:1.2;}}
.i-meta{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);margin-top:2px;}}
.i-detail{{font-size:12px;color:var(--text2);line-height:1.55;margin-top:4px;}}
/* Actor items */
.actor{{background:var(--bg2);border-left:3px solid;border-radius:2px;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);padding:12px 13px;transition:background .12s;display:flex;gap:13px;align-items:flex-start;}}
.actor:hover{{background:var(--bg3);}}
.a-score{{font-family:'Orbitron',monospace;font-weight:900;font-size:34px;min-width:50px;text-align:center;flex-shrink:0;line-height:1;}}
.a-slbl{{font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:.12em;color:var(--text3);text-align:center;margin-top:3px;}}
.a-body{{flex:1;min-width:0;}}
.a-name{{font-family:'Barlow',sans-serif;font-size:14px;font-weight:600;color:#e0eefa;margin-bottom:1px;}}
.a-unit{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);margin-bottom:6px;}}
.a-ops{{display:flex;flex-wrap:wrap;gap:3px;margin-top:5px;}}
.a-op{{font-family:'JetBrains Mono',monospace;font-size:7.5px;padding:2px 7px;border-radius:2px;background:rgba(0,180,255,.06);border:1px solid rgba(0,180,255,.12);color:var(--text2);}}
/* Priority items */
.prio{{background:var(--bg2);border-left:3px solid;border-radius:2px;padding:10px 12px;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);transition:background .12s;}}
.prio:hover{{background:var(--bg3);}}
.p-row{{display:flex;align-items:flex-start;gap:11px;}}
.p-num{{font-family:'Orbitron',monospace;font-weight:900;font-size:28px;min-width:30px;text-align:center;flex-shrink:0;line-height:1;padding-top:2px;}}
.p-target{{font-size:13px;font-weight:600;color:#e0eefa;margin-bottom:2px;}}
.p-type{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);margin-bottom:4px;}}
.p-gap{{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--amber);opacity:.85;margin-top:5px;}}
.p-gap::before{{content:'⚠ GAP: ';}}
.p-plats{{display:flex;flex-wrap:wrap;gap:3px;margin-top:5px;}}
.p-plat{{font-family:'JetBrains Mono',monospace;font-size:7.5px;padding:2px 7px;border-radius:2px;background:rgba(0,180,255,.06);border:1px solid rgba(0,180,255,.12);color:var(--text2);}}
/* Feed items */
.fi{{background:var(--bg2);border-left:2px solid var(--cyan);border-radius:2px;padding:9px 11px;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);transition:background .12s;}}
.fi:hover{{background:var(--bg3);}}
.fi-src{{font-family:'JetBrains Mono',monospace;font-size:8px;font-weight:500;color:var(--cyan);}}
.fi-title{{font-size:12px;color:var(--text);line-height:1.5;margin:3px 0;}}
.fi-time{{font-family:'JetBrains Mono',monospace;font-size:7.5px;color:var(--text3);}}
.fi-link{{font-family:'JetBrains Mono',monospace;font-size:7.5px;color:rgba(0,212,255,.55);text-decoration:none;}}
.fi-link:hover{{color:var(--cyan);}}
/* Bars */
.mbar{{height:2px;background:var(--edge);border-radius:1px;overflow:hidden;margin:5px 0;}}
.mbar-f{{height:100%;border-radius:1px;}}
/* Badges */
.badge{{display:inline-flex;align-items:center;padding:2px 7px;border-radius:2px;font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:.06em;text-transform:uppercase;border:1px solid;white-space:nowrap;}}
.bc{{color:var(--red);border-color:rgba(255,45,85,.3);background:rgba(255,45,85,.07);}}
.bh{{color:var(--amber);border-color:rgba(240,165,0,.3);background:rgba(240,165,0,.07);}}
.bl{{color:var(--green);border-color:rgba(0,229,160,.25);background:rgba(0,229,160,.05);}}
.ba{{color:var(--cyan);border-color:rgba(0,212,255,.25);background:rgba(0,212,255,.05);}}
.bv{{color:var(--violet);border-color:rgba(168,85,247,.25);background:rgba(168,85,247,.06);}}
.dom{{font-family:'JetBrains Mono',monospace;font-size:7px;padding:2px 6px;border-radius:2px;background:rgba(0,212,255,.07);border:1px solid rgba(0,212,255,.15);color:var(--cyan);letter-spacing:.06em;}}
/* KP chart */
.kp-bars{{display:flex;align-items:flex-end;gap:2px;height:40px;padding:0 2px;}}
.kp-seg{{flex:1;border-radius:1px 1px 0 0;min-width:0;}}
/* CII */
.cii-item{{background:var(--bg2);border-left:2px solid;border-radius:2px;padding:9px 11px;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);}}
/* Section label */
.slbl{{font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.22em;text-transform:uppercase;color:var(--text3);padding:14px 16px 8px;display:flex;align-items:center;gap:10px;}}
.slbl::after{{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--edge2),transparent);}}
/* Animations */
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.15;transform:scale(.5)}}}}
.dot{{width:6px;height:6px;border-radius:50%;display:inline-block;animation:pulse 1.4s ease-in-out infinite;flex-shrink:0;}}
</style></head>
<body>
<div class="topbar">
  <div class="tb-logo">
    <div class="tb-name">SIGINT</div>
    <div class="tb-sub">Signals Intelligence Dashboard</div>
  </div>
  <div class="tb-metrics">
    <div class="tb-m"><div class="tb-ml">Global Risk</div><div class="tb-mv" id="hbar-risk" style="color:var(--amber)">{_sig_risk_score} {_sig_risk_label}</div></div>
    <div class="tb-m"><div class="tb-ml">KP Index</div><div class="tb-mv" style="color:var(--cyan)">{_kp_current}</div></div>
    <div class="tb-m"><div class="tb-ml">GPS Jamming</div><div class="tb-mv" style="color:var(--red)">{_jam_count}</div></div>
    <div class="tb-m"><div class="tb-ml">Threat Actors</div><div class="tb-mv" style="color:var(--amber)">{_crit_actors}</div></div>
    <div class="tb-m"><div class="tb-ml">CII Critical</div><div class="tb-mv" style="color:var(--red)">{_cii_crit}</div></div>
    <div class="tb-m"><div class="tb-ml">Live Signals</div><div class="tb-mv" style="color:var(--green)">{_live_count}</div></div>
  </div>
  <div class="tb-right">
    <span class="tb-ts" id="live-ts">{_sig_ts}</span>
    <span class="tb-pill"><span class="dot" style="background:var(--green)"></span><span id="poll-status">LIVE</span></span>
    <span class="tb-cd">↻&thinsp;<span id="cd">60</span>s</span>
  </div>
</div>
<div class="ticker"><div class="t-inner" id="ticker-inner">Loading intelligence feed…</div></div>
<div class="kpis" id="kpi-strip"></div>
<div class="body" id="R"></div>
<script>
const D={_sigint_payload};
const esc=s=>String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const tlvl=v=>v>=85?'var(--red)':v>=70?'var(--amber)':v>=50?'#f0d050':'var(--green)';
const mbar=(p,c)=>'<div class="mbar"><div class="mbar-f" style="width:'+Math.min(p,100)+'%;background:'+c+'"></div></div>';

function buildKPIs(){{
  var jam=(D.gps_jamming||[]).filter(z=>z.severity==='High').length;
  var act=(D.actors||[]).filter(a=>a.threat_level>=85).length;
  var elnt=(D.elint||[]).filter(e=>e.status==='Active').length;
  var cii=(D.cii||[]).filter(c=>c.risk>=90).length;
  var data=[
    {{v:jam,l:'Active GPS Jamming',s:'High-severity zones',c:'var(--red)'}},
    {{v:act,l:'Critical Threat Actors',s:'Threat level ≥85',c:'var(--amber)'}},
    {{v:elnt,l:'Active ELINT Systems',s:'Emissions tracked',c:'var(--cyan)'}},
    {{v:cii,l:'CII Critical Risk',s:'Infrastructure risk ≥90',c:'var(--red)'}},
  ];
  document.getElementById('kpi-strip').innerHTML=data.map(k=>
    '<div class="kpi" style="--kc:'+k.c+'"><div class="kpi-l">'+esc(k.l)+'</div>'+
    '<div class="kpi-v">'+k.v+'</div><div class="kpi-s">'+esc(k.s)+'</div></div>'
  ).join('');
}}

function buildTicker(){{
  var all=(D.live_events||[]).concat(D.live_conflict||[]).concat(D.live_feed||[]).slice(0,24);
  if(!all.length)return;
  var h=all.map(a=>'<span class="ti"><span class="ti-s">▶ '+esc((a.source||'').toUpperCase().slice(0,18))+'</span>'+esc((a.title||'').slice(0,88))+'</span>').join('');
  document.getElementById('ticker-inner').innerHTML=h+h;
}}

function updateHeader(){{
  var ts=document.getElementById('live-ts');
  if(ts)ts.textContent=new Date().toUTCString().replace(/.*([0-9][0-9]:[0-9][0-9]:[0-9][0-9]).*/,'$1')+' UTC';
}}

function panelActors(){{
  var sorted=(D.actors||[]).slice().sort((a,b)=>b.threat_level-a.threat_level);
  var rows=sorted.map(a=>{{
    var col=tlvl(a.threat_level);
    var doms=(a.domain||[]).map(d=>'<span class="dom">'+esc(d)+'</span>').join('');
    var ops=(a.operations||[]).map(o=>'<span class="a-op">'+esc(o)+'</span>').join('');
    return '<div class="actor" style="border-color:'+col+'">'+
      '<div><div class="a-score" style="color:'+col+'">'+a.threat_level+'</div><div class="a-slbl">THREAT</div></div>'+
      '<div class="a-body"><div class="a-name">'+esc(a.actor)+'</div><div class="a-unit">'+esc(a.unit||'')+'</div>'+
      mbar(a.threat_level,col)+
      '<div style="display:flex;gap:5px;align-items:center;flex-wrap:wrap;margin-bottom:4px">'+doms+
      '<span style="margin-left:auto;font-family:JetBrains Mono,monospace;font-size:7.5px;color:var(--text3)">ATTR '+(a.attribution||0)+'%</span></div>'+
      '<div class="a-ops">'+ops+'</div></div></div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(255,45,85,.1);color:var(--red)">⚠</div>'+
    '<div class="ch-title">Threat Actor Matrix</div><div class="ch-ct">'+sorted.length+' actors</div></div>'+
    '<div class="scroll">'+rows+'</div><div class="classif">SIGINT // EYES ONLY</div></div>';
}}

function panelCollection(){{
  var priCol=p=>p<=2?'var(--red)':p<=4?'var(--amber)':p<=6?'#f0d050':'var(--green)';
  var rows=(D.collection||[]).map(p=>{{
    var col=priCol(p.priority);
    var st=p.status==='Active'?'<span class="badge bc">Active</span>':'<span class="badge bl">Routine</span>';
    var plats=(p.collection||[]).map(c=>'<span class="p-plat">'+esc(c)+'</span>').join('');
    return '<div class="prio" style="border-color:'+col+'">'+
      '<div class="p-row"><div><div class="p-num" style="color:'+col+'">P'+p.priority+'</div></div>'+
      '<div class="a-body"><div style="display:flex;align-items:center;gap:7px;margin-bottom:3px">'+
      '<span class="p-target">'+esc(p.target)+'</span>'+st+'</div>'+
      '<div class="p-type">'+esc(p.type||'')+' · '+esc(p.last_update||'')+'</div>'+
      '<div class="p-plats">'+plats+'</div>'+
      '<div class="p-gap">'+esc(p.intel_gap||'')+'</div>'+
      '</div></div></div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(240,165,0,.1);color:var(--amber)">🎯</div>'+
    '<div class="ch-title">Collection Requirements</div><div class="ch-ct">P1–'+(D.collection||[]).length+'</div></div>'+
    '<div class="scroll">'+rows+'</div><div class="classif">COLLECTION PLAN</div></div>';
}}

function panelCOMINT(){{
  var rows=(D.comint||[]).map(s=>{{
    var col=s.intercept==='Active'?'var(--amber)':'var(--violet)';
    var bc=s.intercept==='Active'?'bh':'bv';
    return '<div class="item" style="border-color:'+col+'">'+
      '<div class="i-top"><div><div class="i-name">'+esc(s.actor)+'</div>'+
      '<div class="i-meta">'+esc(s.id||'')+' · '+esc(s.signal_type||'')+' · '+esc(s.freq||'')+'</div></div>'+
      '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex-shrink:0">'+
      '<span class="badge '+bc+'">'+esc(s.intercept||'')+'</span>'+
      '<span style="font-family:JetBrains Mono,monospace;font-size:7.5px;color:var(--text3)">CONF '+(s.confidence||0)+'%</span></div></div>'+
      mbar(s.confidence||0,col)+
      '<div class="i-detail">'+esc(s.detail||'')+'</div>'+
      '<div style="font-family:JetBrains Mono,monospace;font-size:8px;color:var(--text3);margin-top:5px">⊳ TARGET: '+esc(s.target||'')+'</div></div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(240,165,0,.1);color:var(--amber)">📡</div>'+
    '<div class="ch-title">COMINT — Communications Intel</div><div class="ch-ct">'+((D.comint||[]).length)+' signals</div></div>'+
    '<div class="scroll">'+rows+'</div><div class="classif">TOP SECRET // COMINT</div></div>';
}}

function panelELINT(){{
  var ac=a=>a.includes('Russia')?'var(--red)':a.includes('China')?'var(--amber)':a.includes('USA')?'var(--cyan)':'var(--green)';
  var rows=(D.elint||[]).map(e=>{{
    var col=ac(e.actor||'');
    return '<div class="item" style="border-color:'+col+'">'+
      '<div class="i-top"><div><div class="i-name">'+esc(e.system||'')+'</div>'+
      '<div class="i-meta">'+esc(e.type||'')+' · '+esc(e.freq||'')+' · Range: '+(e.range_km||'?')+'km</div></div>'+
      '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:3px;flex-shrink:0">'+
      '<span class="badge" style="color:'+col+';border-color:'+col+'40;background:'+col+'12">'+esc(e.actor||'')+'</span>'+
      '<span style="font-family:JetBrains Mono,monospace;font-size:7.5px;color:var(--text3);text-align:right">'+esc(e.capability||'')+'</span></div></div>'+
      '<div class="i-detail">'+esc(e.detail||'')+'</div></div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(0,212,255,.08);color:var(--cyan)">⚡</div>'+
    '<div class="ch-title">ELINT — Electronic Intelligence</div><div class="ch-ct">'+((D.elint||[]).length)+' tracked</div></div>'+
    '<div class="scroll">'+rows+'</div><div class="classif">TOP SECRET // ELINT</div></div>';
}}

function panelMASINT(){{
  var tc={{Seismic:'#f0d050','Nuclear Radiation':'var(--red)',Acoustic:'var(--cyan)',Chemical:'var(--amber)',Thermal:'var(--amber)'}};
  var rows=(D.masint||[]).map(m=>{{
    var col=tc[m.type]||'var(--green)';
    return '<div class="item" style="border-color:'+col+'">'+
      '<div class="i-top"><div><div class="i-name">'+esc(m.event||'')+'</div>'+
      '<div class="i-meta">'+esc(m.id||'')+' · '+esc(m.location||'')+' · '+esc(m.date||'')+'</div></div>'+
      '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:3px;flex-shrink:0">'+
      '<span class="badge" style="color:'+col+';border-color:'+col+'40;background:'+col+'12">'+esc(m.type||'')+'</span>'+
      '<span style="font-family:JetBrains Mono,monospace;font-size:7.5px;color:var(--text3)">CONF '+(m.confidence||0)+'%</span></div></div>'+
      mbar(m.confidence||0,col)+
      '<div class="i-detail">'+esc(m.detail||'')+'</div></div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(240,208,80,.08);color:#f0d050">🔭</div>'+
    '<div class="ch-title">MASINT — Measurement & Signature</div><div class="ch-ct">'+((D.masint||[]).length)+' events</div></div>'+
    '<div class="scroll">'+rows+'</div><div class="classif">TOP SECRET // MASINT</div></div>';
}}

function panelJamming(){{
  var rows=(D.gps_jamming||[]).map(z=>{{
    var col=z.severity==='High'?'var(--red)':'#f0d050';
    var bc=z.severity==='High'?'bc':'bh';
    return '<div class="item" style="border-color:'+col+'">'+
      '<div class="i-top"><div><div class="i-name">'+esc(z.name||'')+'</div>'+
      '<div class="i-meta">Source: '+esc(z.source||'')+' · Radius: '+(z.radius_km||'?')+'km</div></div>'+
      '<span class="badge '+bc+'">'+esc(z.severity||'')+'</span></div>'+mbar(z.severity==='High'?90:55,col)+'</div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(255,45,85,.08);color:var(--red)">📵</div>'+
    '<div class="ch-title">GPS/GNSS Jamming Zones</div><div class="ch-ct">'+((D.gps_jamming||[]).length)+' zones</div></div>'+
    '<div class="scroll">'+rows+'</div></div>';
}}

function panelOrbital(){{
  var oc=o=>o.includes('USA')?'var(--cyan)':o.includes('Russia')?'var(--red)':o.includes('China')?'var(--amber)':o.includes('Israel')?'#f0d050':'var(--green)';
  var rows=(D.orbital||[]).map(o=>{{
    var col=oc(o.operator||'');
    return '<div class="item" style="border-color:'+col+'">'+
      '<div class="i-top"><div><div class="i-name">'+esc(o.name||'')+'</div>'+
      '<div class="i-meta">'+esc(o.type||'')+'</div></div>'+
      '<span class="badge" style="color:'+col+';border-color:'+col+'40;background:'+col+'12">'+esc(o.operator||'')+'</span></div></div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(0,212,255,.08);color:var(--cyan)">🛰</div>'+
    '<div class="ch-title">Orbital ISR — Surveillance Sat</div><div class="ch-ct">'+((D.orbital||[]).length)+' systems</div></div>'+
    '<div class="scroll">'+rows+'</div></div>';
}}

function panelLiveCyber(){{
  var ac=a=>a.includes('Russia')?'var(--red)':a.includes('China')?'var(--amber)':a.includes('Iran')?'#f0d050':a.includes('DPRK')?'var(--violet)':'var(--green)';
  var base=(D.cyber_threats||[]).map(c=>{{
    var col=ac(c.actor||'');
    return '<div class="item" style="border-color:'+col+'">'+
      '<div class="i-top"><div><div class="i-name">'+esc(c.name||'')+'</div>'+
      '<div class="i-meta">Targets: '+esc(c.targets||'')+'</div></div>'+
      '<span class="badge" style="color:'+col+';border-color:'+col+'40;background:'+col+'12">'+esc(c.actor||'')+'</span></div></div>';
  }}).join('');
  var live=(D.live_cyber||[]).slice(0,5).map(a=>
    '<div class="fi" style="border-left-color:var(--violet)">'+
    '<div class="fi-src">'+esc((a.source||'').toUpperCase())+'</div>'+
    '<div class="fi-title">'+esc((a.title||'').slice(0,100))+'</div>'+
    '<div class="fi-time">'+esc(a.time||'')+'</div></div>'
  ).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(168,85,247,.1);color:var(--violet)">💀</div>'+
    '<div class="ch-title">CYBINT — Cyber Threats</div>'+
    '<div class="live-chip"><span class="dot" style="background:var(--green)"></span>GDELT</div></div>'+
    '<div class="scroll" id="live-cyber-inner">'+base+(live?'<div style="height:1px;background:var(--edge2);margin:4px 0"></div>'+live:'')+'</div>'+
    '<div class="classif">TOP SECRET // CYBER</div></div>';
}}

function panelSeismic(){{
  var q=D.live_quakes||[];
  var rows=q.length?q.map(q=>{{
    var col=q.mag>=6?'var(--red)':q.mag>=5?'var(--amber)':q.mag>=4?'#f0d050':'var(--green)';
    return '<div class="item" style="border-color:'+col+'">'+
      '<div class="i-top"><div><div class="i-name">'+esc(q.place||q.loc||'')+'</div>'+
      '<div class="i-meta">Depth: '+(q.depth_km||'?')+'km · '+esc(q.time||'')+'</div></div>'+
      '<span style="font-family:Orbitron,monospace;font-weight:700;font-size:18px;color:'+col+'">M'+q.mag+'</span></div></div>';
  }}).join(''):'<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:var(--text3);padding:12px 0">Polling USGS…</div>';
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(240,208,80,.08);color:#f0d050">🌍</div>'+
    '<div class="ch-title">MASINT — Live Seismic</div>'+
    '<div class="live-chip"><span class="dot" style="background:var(--green)"></span>USGS</div></div>'+
    '<div id="live-seismic-inner" class="scroll">'+rows+'</div></div>';
}}

function panelKP(){{
  var kp=D.kp_current||0;var col=kp>=5?'var(--red)':kp>=3?'var(--amber)':'var(--green)';
  var bars=(D.kp_series||[]).slice(-24).map(p=>{{
    var v=Math.min(p.kp||p||0,9);var h=Math.max(Math.round((v/9)*100),3);
    var c=v>=5?'var(--red)':v>=3?'var(--amber)':'var(--green)';
    return '<div class="kp-seg" style="height:'+h+'%;background:'+c+';opacity:.8"></div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(0,229,160,.08);color:var(--green)">☀</div>'+
    '<div class="ch-title">Space Weather / KP Index</div>'+
    '<div class="live-chip"><span class="dot" style="background:var(--green)"></span>NOAA</div></div>'+
    '<div id="live-kp-inner" style="padding:14px 16px">'+
    '<div style="display:flex;align-items:center;gap:18px;margin-bottom:12px">'+
    '<div><div style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:var(--text3);margin-bottom:4px">KP INDEX</div>'+
    '<div style="font-family:Orbitron,monospace;font-weight:900;font-size:48px;color:'+col+';line-height:1">'+kp+'</div></div>'+
    '<div><div style="font-family:JetBrains Mono,monospace;font-size:11px;color:'+col+';margin-bottom:4px">'+esc(D.kp_status||'Quiet')+'</div>'+
    '<div style="font-family:JetBrains Mono,monospace;font-size:8px;color:var(--text3)">≥5 Storm · ≥7 Severe · ≥9 Extreme</div></div></div>'+
    '<div class="kp-bars">'+bars+'</div>'+
    '<div style="font-family:JetBrains Mono,monospace;font-size:7px;color:var(--text3);margin-top:3px;text-align:right">← 24h Kp history</div>'+
    '</div></div>';
}}

function panelOutages(){{
  var items=(D.live_outages||D.internet_static||[]).slice(0,10);
  var rows=items.length?items.map(o=>
    '<div class="item" style="border-color:var(--red)">'+
    '<div class="i-name">'+esc(o.region||o.title||'')+'</div>'+
    '<div class="i-meta">'+(o.provider||o.source||'')+' · '+(o.time||o.ts||'')+'</div></div>'
  ).join(''):'<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:var(--text3);padding:12px 0">No major outages detected.</div>';
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(255,45,85,.08);color:var(--red)">🔌</div>'+
    '<div class="ch-title">Internet Outages</div>'+
    '<div class="live-chip"><span class="dot" style="background:var(--green)"></span>Live</div></div>'+
    '<div class="scroll">'+rows+'</div></div>';
}}

function panelLiveFeed(){{
  var all=(D.live_events||[]).concat(D.live_conflict||[]).concat(D.live_feed||[]).slice(0,25);
  var cc={{CONFLICT:'var(--red)',MILITARY:'var(--amber)',NUCLEAR:'var(--red)',OSINT:'var(--cyan)',CYBER:'var(--violet)'}};
  var rows=all.length?all.map(a=>{{
    var col=cc[a.cat||'']||'var(--cyan)';
    return '<div class="fi" style="border-left-color:'+col+'">'+
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">'+
      '<span class="fi-src" style="color:'+col+'">'+esc((a.source||'').slice(0,22).toUpperCase())+'</span>'+
      '<span class="fi-time">'+esc(a.time||'')+'</span></div>'+
      '<div class="fi-title">'+esc((a.title||'').slice(0,110))+'</div>'+
      (a.url?'<a class="fi-link" href="'+esc(a.url)+'" target="_blank" rel="noopener">READ →</a>':'')+
      '</div>';
  }}).join(''):'<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:var(--text3);padding:12px 0">Fetching live signals…</div>';
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(0,212,255,.08);color:var(--cyan)">📰</div>'+
    '<div class="ch-title">Live OSINT / SIGINT Feed</div>'+
    '<div class="live-chip"><span class="dot" style="background:var(--green)"></span>'+all.length+' signals</div></div>'+
    '<div class="scroll" id="live-feed-inner">'+rows+'</div></div>';
}}

function panelOSINT(){{
  var rows=(D.osint_platforms||[]).map(p=>
    '<div class="item" style="border-color:var(--green)">'+
    '<div class="i-top"><div><div class="i-name">'+esc(p.name||'')+'</div>'+
    '<div class="i-meta">'+esc(p.type||'')+' · '+esc(p.provider||'')+' · Res: '+esc(p.resolution||'')+'</div></div>'+
    '<span class="badge bl">'+esc(p.status||'')+'</span></div>'+
    '<div class="i-detail">'+esc(p.use_case||'')+'</div></div>'
  ).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(0,229,160,.08);color:var(--green)">👁</div>'+
    '<div class="ch-title">OSINT Collection Platforms</div>'+
    '<div class="ch-ct">'+((D.osint_platforms||[]).length)+' sources</div></div>'+
    '<div class="scroll">'+rows+'</div></div>';
}}

function panelCII(){{
  var sorted=(D.cii||[]).slice().sort((a,b)=>b.risk-a.risk);
  var rows=sorted.map(c=>{{
    var col=c.risk>=90?'var(--red)':c.risk>=75?'var(--amber)':'#f0d050';
    return '<div class="cii-item" style="border-color:'+col+'">'+
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">'+
      '<div><div class="i-name">'+esc(c.name||'')+'</div>'+
      '<div class="i-meta">'+esc(c.country||'')+' · '+esc(c.sector||'')+'</div></div>'+
      '<span style="font-family:Orbitron,monospace;font-weight:900;font-size:20px;color:'+col+'">'+c.risk+'</span></div>'+
      mbar(c.risk,col)+'</div>';
  }}).join('');
  return '<div class="card"><div class="ch"><div class="ch-ico" style="background:rgba(255,45,85,.08);color:var(--red)">🏗</div>'+
    '<div class="ch-title">GEOINT — Critical Infrastructure</div>'+
    '<div class="ch-ct">'+sorted.length+' tracked</div></div>'+
    '<div class="scroll">'+rows+'</div><div class="classif">GEOINT // INFRA</div></div>';
}}

/* ── RENDER ── */
function doRender(){{
  buildKPIs();buildTicker();
  document.getElementById('R').innerHTML=
    '<div class="slbl">Priority Intelligence</div>'+
    '<div class="r2">'+panelActors()+panelCollection()+'</div>'+
    '<div class="slbl">Signals Collection</div>'+
    '<div class="r3">'+panelCOMINT()+panelELINT()+panelMASINT()+'</div>'+
    '<div class="slbl">Environment & Cyber Domain</div>'+
    '<div class="r3">'+panelJamming()+panelOrbital()+panelLiveCyber()+'</div>'+
    '<div class="slbl">Live MASINT & Alerts</div>'+
    '<div class="r3">'+panelSeismic()+panelKP()+panelOutages()+'</div>'+
    '<div class="slbl">Open Source & Infrastructure</div>'+
    '<div class="r2">'+panelLiveFeed()+panelOSINT()+'</div>'+
    panelCII();
  updateHeader();
}}
doRender();

var _el=0,_rs=D.refresh_interval||180;
setInterval(()=>{{_el++;var l=Math.max(0,_rs-_el);var e=document.getElementById('cd');if(e)e.textContent=l;if(l===0)_el=0;}},1000);

var _ls={{feed:D.live_feed||[],cyber:D.live_cyber||[],quakes:D.live_quakes||[],kp:D.kp_current||0,kpStatus:D.kp_status||'Quiet',kpSeries:D.kp_series||[]}};

function relTime(iso){{try{{var d=new Date(iso),s=(Date.now()-d)/1000;if(s<60)return Math.round(s)+'s ago';if(s<3600)return Math.round(s/60)+'m ago';return Math.round(s/3600)+'h ago';}}catch{{return iso||'';}}}}

async function fetchGDELT(q){{try{{var r=await fetch('https://api.gdeltproject.org/api/v2/doc/doc?query='+encodeURIComponent(q+' sourcelang:english')+'&mode=artlist&maxrecords=12&format=json&sort=DateDesc',{{signal:AbortSignal.timeout(10000)}});if(!r.ok)return[];var j=await r.json();return(j.articles||[]).map(a=>{{return{{title:a.title||'',source:(a.domain||'').split('.')[0].toUpperCase(),url:a.url||'',time:relTime(a.seendate),cat:''}};}}); }}catch{{return[];}}}}
async function fetchUSGS(){{try{{var r=await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson',{{signal:AbortSignal.timeout(8000)}});if(!r.ok){{r=await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson',{{signal:AbortSignal.timeout(8000)}});if(!r.ok)return[];}}var j=await r.json();return(j.features||[]).slice(0,10).map(f=>{{return{{place:f.properties.place||'',mag:f.properties.mag||0,depth_km:(f.geometry.coordinates[2]||0).toFixed(1),time:relTime(new Date(f.properties.time).toISOString())}};}}); }}catch{{return[];}}}}
async function fetchKP(){{try{{var r=await fetch('https://services.swpc.noaa.gov/json/planetary_k_index_1m.json',{{signal:AbortSignal.timeout(8000)}});if(!r.ok)return null;var arr=await r.json();var series=arr.slice(-24).map(x=>{{return{{kp:parseFloat(x.Kp||x.kp_index||0)}}}});var recent=series.slice(-6).map(x=>x.kp);var mx=Math.max(...recent,0);var st=mx>=8?'EXTREME STORM':mx>=7?'SEVERE STORM':mx>=6?'STRONG STORM':mx>=5?'MODERATE STORM':mx>=4?'MINOR STORM':mx>=3?'Unsettled':'Quiet';return{{current:Math.round(mx*10)/10,status:st,series}};}}catch{{return null;}}}}

function patchFeed(){{var el=document.getElementById('live-feed-inner');if(!el)return;var cc={{CONFLICT:'var(--red)',MILITARY:'var(--amber)',NUCLEAR:'var(--red)',OSINT:'var(--cyan)',CYBER:'var(--violet)'}};el.innerHTML=_ls.feed.slice(0,25).map(a=>{{var col=cc[a.cat||'']||'var(--cyan)';return'<div class="fi" style="border-left-color:'+col+'"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px"><span class="fi-src" style="color:'+col+'">'+esc((a.source||'').slice(0,22).toUpperCase())+'</span><span class="fi-time">'+esc(a.time||'')+'</span></div><div class="fi-title">'+esc((a.title||'').slice(0,110))+'</div>'+(a.url?'<a class="fi-link" href="'+esc(a.url)+'" target="_blank" rel="noopener">READ →</a>':'')+' </div>';}}).join('');}}
function patchCyber(){{var el=document.getElementById('live-cyber-inner');if(!el)return;var live=_ls.cyber.slice(0,5).map(a=>'<div class="fi" style="border-left-color:var(--violet)"><div class="fi-src">'+esc((a.source||'').toUpperCase())+'</div><div class="fi-title">'+esc((a.title||'').slice(0,100))+'</div><div class="fi-time">'+esc(a.time||'')+'</div></div>').join('');if(live)el.insertAdjacentHTML('beforeend',live);}}
function patchSeismic(){{var el=document.getElementById('live-seismic-inner');if(!el||!_ls.quakes.length)return;el.innerHTML=_ls.quakes.slice(0,8).map(q=>{{var col=q.mag>=6?'var(--red)':q.mag>=5?'var(--amber)':q.mag>=4?'#f0d050':'var(--green)';return'<div class="item" style="border-color:'+col+'"><div class="i-top"><div><div class="i-name">'+esc(q.place||q.loc||'')+'</div><div class="i-meta">Depth: '+(q.depth_km||'?')+'km · '+esc(q.time||'')+'</div></div><span style="font-family:Orbitron,monospace;font-weight:700;font-size:18px;color:'+col+'">M'+q.mag+'</span></div></div>';}}).join('');}}
function patchKP(){{var el=document.getElementById('live-kp-inner');if(!el)return;var kp=_ls.kp;var col=kp>=5?'var(--red)':kp>=3?'var(--amber)':'var(--green)';var bars=_ls.kpSeries.slice(-24).map(p=>{{var v=Math.min(p.kp||p||0,9);var h=Math.max(Math.round((v/9)*100),3);var c=v>=5?'var(--red)':v>=3?'var(--amber)':'var(--green)';return'<div class="kp-seg" style="height:'+h+'%;background:'+c+';opacity:.8"></div>';}}).join('');el.innerHTML='<div style="display:flex;align-items:center;gap:18px;margin-bottom:12px"><div><div style="font-family:JetBrains Mono,monospace;font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:var(--text3);margin-bottom:4px">KP INDEX</div><div style="font-family:Orbitron,monospace;font-weight:900;font-size:48px;color:'+col+';line-height:1">'+kp+'</div></div><div><div style="font-family:JetBrains Mono,monospace;font-size:11px;color:'+col+';margin-bottom:4px">'+esc(_ls.kpStatus)+'</div><div style="font-family:JetBrains Mono,monospace;font-size:8px;color:var(--text3)">≥5 Storm · ≥7 Severe · ≥9 Extreme</div></div></div><div class="kp-bars">'+bars+'</div><div style="font-family:JetBrains Mono,monospace;font-size:7px;color:var(--text3);margin-top:3px;text-align:right">← 24h Kp history</div>';}}
function patchTicker(){{var el=document.getElementById('ticker-inner');if(!el)return;var all=_ls.feed.concat(_ls.cyber).slice(0,20);if(!all.length)return;var h=all.map(a=>'<span class="ti"><span class="ti-s">▶ '+esc((a.source||'').toUpperCase().slice(0,18))+'</span>'+esc((a.title||'').slice(0,88))+'</span>').join('');el.innerHTML=h+h;}}

var _polling=false;
async function pollAll(){{if(_polling)return;_polling=true;var ps=document.getElementById('poll-status');if(ps)ps.textContent='UPDATING…';
  try{{var[feed,cyber,geo,quakes,kpData]=await Promise.all([fetchGDELT('war military strike conflict bombing 2026'),fetchGDELT('cyber attack espionage hacking malware APT'),fetchGDELT('geopolitics sanctions nuclear ballistic missile diplomacy'),fetchUSGS(),fetchKP()]);
    if(feed&&feed.length)_ls.feed=(geo||[]).concat(feed).slice(0,25);
    if(cyber&&cyber.length)_ls.cyber=cyber;
    if(quakes&&quakes.length)_ls.quakes=quakes;
    if(kpData){{_ls.kp=kpData.current;_ls.kpStatus=kpData.status;_ls.kpSeries=kpData.series;}}
  }}catch(e){{console.warn('poll',e);}}
  _polling=false;patchFeed();patchCyber();patchSeismic();patchKP();patchTicker();updateHeader();
  if(ps)ps.textContent='LIVE';
}}
setTimeout(pollAll,4000);setInterval(pollAll,180000);
</script></body></html>"""
    _sc.html(_sigint_html, height=5600, scrolling=True)


with tab_econ:
    import json as _ej
    import streamlit.components.v1 as _ec

    # ── Fetch live market data — all 6 sources in parallel ──────
    from concurrent.futures import ThreadPoolExecutor as _TPE_e
    with _TPE_e(max_workers=9) as _ex_e:
        _fe_idx     = _ex_e.submit(fetch_live_indices)
        _fe_com     = _ex_e.submit(fetch_live_commodities)
        _fe_fx      = _ex_e.submit(fetch_live_forex)
        _fe_def     = _ex_e.submit(fetch_live_defense)
        _fe_cry     = _ex_e.submit(fetch_live_crypto)
        _fe_pizza   = _ex_e.submit(fetch_live_pizza_index)
        _fe_layoffs = _ex_e.submit(fetch_live_layoffs)
        _fe_ship    = _ex_e.submit(fetch_live_shipping_rates)
        _fe_mins    = _ex_e.submit(fetch_live_critical_minerals)
    _live_indices     = _fe_idx.result()
    _live_commodities = _fe_com.result()
    _live_forex       = _fe_fx.result()
    _live_defense     = _fe_def.result()
    _live_crypto      = _fe_cry.result()
    _econ_pizza_pre   = _fe_pizza.result()
    _live_layoffs     = _fe_layoffs.result()
    _live_shipping    = _fe_ship.result()  or SHIPPING_RATES
    _live_minerals    = _fe_mins.result()  or CRIT_MIN_DATA

    # Live-update oil prices if Yahoo succeeded
    _oil_out = []
    _oil_map = {c["name"]: c for c in _live_commodities} if _live_commodities else {}
    for _o in OIL_DATA:
        _lv = _oil_map.get(_o["name"])
        if _lv:
            _oil_out.append({**_o, "val": _lv["price"], "change": round(_lv["chg_pct"], 2)})
        else:
            _oil_out.append(_o)

    # Live-update crypto if CoinGecko succeeded
    _crypto_out = _live_crypto if _live_crypto else CRYPTO_DATA

    # ── Live sector ETF heatmap via Yahoo Finance ─────────────
    _sector_symbols = (
        "XLK", "XLF", "XLE", "XLV", "XLY", "XLI",
        "XLP", "XLU", "XLB", "XLRE", "XLC", "SMH",
    )
    _sector_quotes = _yahoo_batch(_sector_symbols)
    _sectors_live = []
    for _sym in _sector_symbols:
        _q = _sector_quotes.get(_sym)
        if _q:
            _sectors_live.append({"s": _sym, "v": round(_q["chg_pct"], 2)})
    # Fallback to static if Yahoo unavailable
    _sectors_out = _sectors_live if len(_sectors_live) >= 6 else SECTOR_HEATMAP

    # ── Dynamic market posture from VIX + breadth ─────────────
    _vix_data  = next((_x for _x in _live_indices if _x.get("sym") == "^VIX"), None)
    _sp_data   = next((_x for _x in _live_indices if _x.get("sym") == "^GSPC"), None)
    _vix_val   = _vix_data["price"] if _vix_data else 0
    _sp_chg    = _sp_data["chg_pct"] if _sp_data else 0
    _bull_count = sum(1 for _s in _sectors_out if _s["v"] > 0)
    _bear_count = len(_sectors_out) - _bull_count
    if _vix_val >= 30:
        _mkt_label   = "RISK OFF"
        _mkt_posture = f"{_bull_count}/{len(_sectors_out)} bullish"
        _mkt_flow    = "DEFENSIVE MODE"
        _mkt_col     = "#ff3d5a"
    elif _vix_val >= 20 or _sp_chg < -1.0:
        _mkt_label   = "CAUTION"
        _mkt_posture = f"{_bull_count}/{len(_sectors_out)} bullish"
        _mkt_flow    = "RISK REDUCTION"
        _mkt_col     = "#ff8c42"
    elif _sp_chg > 1.5 and _bull_count > 8:
        _mkt_label   = "RISK ON"
        _mkt_posture = f"{_bull_count}/{len(_sectors_out)} bullish"
        _mkt_flow    = "MOMENTUM CHASE"
        _mkt_col     = "#00e676"
    else:
        _mkt_label   = MARKET_RADAR["label"]
        _mkt_posture = f"{_bull_count}/{len(_sectors_out)} bullish"
        _mkt_flow    = MARKET_RADAR["flow"]
        _mkt_col     = "#ffb400"
    _market_live = {
        "label":     _mkt_label,
        "posture":   _mkt_posture,
        "flow":      _mkt_flow,
        "liquidity": MARKET_RADAR.get("liquidity", "NORMAL"),
        "color":     _mkt_col,
    }

    from datetime import datetime as _dtnow, timezone as _tzutc
    _data_ts   = _dtnow.now(tz=_tzutc.utc).strftime("%H:%M UTC")
    _is_live   = bool(_live_indices or _live_commodities)
    _is_live_js = "true" if _is_live else "false"

    _econ_payload = _ej.dumps({
        # Live (Yahoo Finance + CoinGecko)
        "indices":      _live_indices,
        "commodities":  _live_commodities,
        "forex":        _live_forex,
        "defense":      _live_defense,
        "crypto_live":  _crypto_out,
        "ts":           _data_ts,
        # Static / semi-static
        "indicators":   ECON_INDICATORS,
        "oil":          _oil_out,
        "bonds": [
            {"name":"US 10Y","yield":4.42,"change":+0.03,"rating":"AAA","col":"#38bdf8"},
            {"name":"US 2Y", "yield":4.71,"change":-0.01,"rating":"AAA","col":"#38bdf8"},
            {"name":"UK 10Y","yield":4.18,"change":+0.05,"rating":"AA", "col":"#34d399"},
            {"name":"DE 10Y","yield":2.41,"change":+0.02,"rating":"AAA","col":"#34d399"},
            {"name":"JP 10Y","yield":1.52,"change":+0.08,"rating":"A+", "col":"#fbbf24"},
            {"name":"IT 10Y","yield":3.74,"change":+0.04,"rating":"BBB","col":"#fb923c"},
            {"name":"IN 10Y","yield":6.83,"change":-0.02,"rating":"BBB-","col":"#fb923c"},
            {"name":"CN 10Y","yield":2.28,"change":-0.01,"rating":"A+", "col":"#fbbf24"},
            {"name":"TR 10Y","yield":28.4, "change":+0.60,"rating":"B+", "col":"#f87171"},
            {"name":"NG 10Y","yield":19.6, "change":+0.30,"rating":"B-", "col":"#f87171"},
        ],
        "restrictions": TRADE_RESTRICTIONS,
        "tariffs":      TARIFFS,
        "chokepoints":  CHOKEPOINTS,
        "shipping":     _live_shipping,
        "minerals":     _live_minerals,
        "crypto":       CRYPTO_DATA,
        "sectors":      _sectors_out,
        "layoffs":      _live_layoffs,
        "fires":        FIRES_DATA,
        "market":       _market_live,
        "btc_etf":      BTC_ETF,
        "pizza":        _econ_pizza_pre,
        "sanctions":    SANCTIONS_DATA,
        "currency_crisis": CURRENCY_CRISIS,
        "geo_risk":     GEO_RISK_PREMIUMS,
    })

    _econ_html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --void: #04060d;
  --surface: #080d18;
  --raised: #0d1626;
  --lift: #112033;
  --edge: rgba(148,163,184,.08);
  --edge2: rgba(148,163,184,.04);
  --glow: rgba(56,189,248,.06);
  --sky: #38bdf8;
  --mint: #34d399;
  --gold: #fbbf24;
  --coral: #fb923c;
  --rose: #f87171;
  --violet: #a78bfa;
  --ink: #f0f6ff;
  --ink2: #94a3b8;
  --ink3: #475569;
  --fd: 'Syne', sans-serif;
  --fb: 'Inter', system-ui, sans-serif;
  --fm: 'JetBrains Mono', monospace;
}}
*, *::before, *::after {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{
  background: var(--void);
  background-image:
    radial-gradient(ellipse 80% 40% at 50% -10%, rgba(56,189,248,.07) 0%, transparent 70%),
    radial-gradient(ellipse 40% 30% at 90% 60%, rgba(167,139,250,.05) 0%, transparent 60%);
  font-family: var(--fb);
  color: var(--ink);
  padding: 20px 16px 40px;
  min-height: 100vh;
}}

/* ── TYPOGRAPHY ── */
.disp {{ font-family: var(--fd); letter-spacing: -.01em; line-height: 1; }}
.mono {{ font-family: var(--fm); }}
.overline {{ font-family: var(--fm); font-size: 9px; font-weight: 500; letter-spacing: .18em;
             text-transform: uppercase; color: var(--ink3); }}
.section-title {{
  font-family: var(--fm); font-size: 9px; font-weight: 500;
  letter-spacing: .2em; text-transform: uppercase; color: var(--ink3);
  display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
}}
.section-title::after {{ content:''; flex:1; height:1px; background:var(--edge2); }}

/* ── LAYOUT ── */
.main-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr 1.2fr;
  gap: 16px;
  margin-bottom: 24px;
}}
.duo-grid  {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:24px; }}
.trio-grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:24px; }}
@media(max-width:960px) {{ .main-grid {{ grid-template-columns:1fr 1fr; }} }}
@media(max-width:580px) {{ .main-grid, .duo-grid, .trio-grid {{ grid-template-columns:1fr; }} }}

/* ── SURFACE CARDS ── */
.card {{
  background: var(--surface);
  border: 1px solid var(--edge);
  border-radius: 14px;
  padding: 20px 22px;
  position: relative;
  overflow: hidden;
}}
.card::before {{
  content: '';
  position: absolute; top:0; left:0; right:0; height:1px;
  background: linear-gradient(90deg, transparent 0%, rgba(148,163,184,.15) 40%, transparent 100%);
}}
.card-row {{
  background: var(--raised);
  border: 1px solid var(--edge2);
  border-left: 3px solid;
  border-radius: 9px;
  padding: 11px 14px;
  margin-bottom: 8px;
  transition: background .15s, border-color .15s;
  cursor: default;
}}
.card-row:last-child {{ margin-bottom: 0; }}
.card-row:hover {{ background: var(--lift); }}

/* ── KPI CARDS ── */
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(4,1fr);
  gap: 14px;
  margin-bottom: 28px;
}}
@media(max-width:700px) {{ .kpi-grid {{ grid-template-columns:1fr 1fr; }} }}
.kpi {{
  background: var(--surface);
  border: 1px solid var(--edge);
  border-radius: 14px;
  padding: 22px 24px 18px;
  position: relative;
  overflow: hidden;
}}
.kpi-glow {{
  position: absolute; top:0; left:0; right:0; height:60px;
  background: radial-gradient(ellipse at 50% 0%, var(--accent-glow, rgba(56,189,248,.12)), transparent 70%);
  pointer-events: none;
}}
.kpi-top-bar {{
  position: absolute; top:0; left:0; right:0; height:2px;
  background: var(--accent-bar, linear-gradient(90deg,transparent,var(--sky),transparent));
}}
.kpi-num {{ font-family:var(--fd); font-size:46px; line-height:.95; letter-spacing:-.01em; margin-bottom:8px; }}
.kpi-label {{ font-family:var(--fm); font-size:9px; font-weight:500; letter-spacing:.2em;
              text-transform:uppercase; color:var(--ink3); margin-bottom:4px; }}
.kpi-sub {{ font-family:var(--fm); font-size:10px; color:var(--ink3); }}

/* ── PILL TABS ── */
.pill-tabs {{ display:flex; gap:5px; margin-bottom:16px; flex-wrap:wrap; }}
.pill {{
  padding: 5px 14px; border-radius: 20px;
  font-size: 11px; font-weight: 600; cursor: pointer;
  background: var(--raised); border: 1px solid var(--edge2);
  color: var(--ink3); transition: all .15s;
  font-family: var(--fb);
}}
.pill:hover {{ border-color: var(--edge); color: var(--ink2); }}
.pill.on {{ background:rgba(56,189,248,.1); border-color:rgba(56,189,248,.3); color:var(--sky); }}
.pane {{ display:none; }} .pane.on {{ display:block; }}

/* ── BADGE ── */
.badge {{
  display:inline-flex; align-items:center; padding:2px 9px; border-radius:5px;
  font-family:var(--fm); font-size:9px; font-weight:600; letter-spacing:.04em;
  border:1px solid; white-space:nowrap;
}}
.crit  {{ color:var(--rose);   border-color:rgba(248,113,113,.3); background:rgba(248,113,113,.08); }}
.high  {{ color:var(--coral);  border-color:rgba(251,146,60,.3);  background:rgba(251,146,60,.08);  }}
.med   {{ color:var(--gold);   border-color:rgba(251,191,36,.3);  background:rgba(251,191,36,.08);  }}
.low   {{ color:var(--mint);   border-color:rgba(52,211,153,.3);  background:rgba(52,211,153,.08);  }}
.neu   {{ color:var(--ink3);   border-color:rgba(71,85,105,.4);   background:rgba(71,85,105,.06);   }}
.sky-b {{ color:var(--sky);    border-color:rgba(56,189,248,.3);  background:rgba(56,189,248,.08);  }}
.vio-b {{ color:var(--violet); border-color:rgba(167,139,250,.3); background:rgba(167,139,250,.08); }}

/* ── LIVE PULSE ── */
.live-chip {{
  display:inline-flex; align-items:center; gap:5px; padding:3px 10px;
  background:rgba(248,113,113,.08); border:1px solid rgba(248,113,113,.25);
  border-radius:20px; font-family:var(--fm); font-size:8px; color:var(--rose);
  letter-spacing:.1em; text-transform:uppercase;
}}
.live-dot {{
  width:5px; height:5px; border-radius:50%; background:var(--rose);
  animation:pulse 1.4s ease-in-out infinite;
}}
@keyframes pulse {{ 0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:.3;transform:scale(.7)}} }}

/* ── BAR ── */
.bar-track {{ height:4px; background:rgba(148,163,184,.08); border-radius:2px; overflow:hidden; margin:6px 0; }}
.bar-track.thick {{ height:7px; border-radius:4px; margin:8px 0; }}
.bar-fill  {{ height:100%; border-radius:inherit; transition:width .4s ease; }}

/* ── DIVIDER ── */
.divider {{ border:none; border-top:1px solid var(--edge2); margin:28px 0; }}

/* ── SECTOR GRID ── */
.sector-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:6px; }}
.sector-cell {{
  border-radius:8px; padding:9px 6px; text-align:center;
  transition:transform .15s, filter .15s;
}}
.sector-cell:hover {{ transform:translateY(-2px); filter:brightness(1.1); }}

/* ── SCROLLABLE ── */
.scroll {{ max-height:380px; overflow-y:auto; padding-right:4px; }}
.scroll::-webkit-scrollbar {{ width:3px; }}
.scroll::-webkit-scrollbar-thumb {{ background:rgba(148,163,184,.15); border-radius:2px; }}

/* ── PIZZA ── */
.pz-score {{
  font-family: var(--fd);
  font-size: 96px; line-height:.85;
  letter-spacing: -.02em;
}}
.pz-bar {{
  height: 10px; border-radius:5px; overflow:hidden;
  background: linear-gradient(90deg,#34d399 0%,#fbbf24 42%,#fb923c 64%,#f87171 100%);
  margin: 12px 0 4px; position:relative;
}}
.pz-needle {{
  position:absolute; top:-4px; width:3px; height:18px;
  background:#fff; border-radius:2px;
  box-shadow:0 0 8px rgba(255,255,255,.6);
  transform:translateX(-50%);
}}

/* ── FIRE TABLE ── */
.fire-tbl {{ width:100%; border-collapse:collapse; }}
.fire-tbl th {{
  font-family:var(--fm); font-size:9px; font-weight:500; letter-spacing:.12em;
  text-transform:uppercase; color:var(--ink3); text-align:left;
  padding:0 0 10px; border-bottom:1px solid var(--edge2);
}}
.fire-tbl th:not(:first-child) {{ text-align:right; }}
.fire-tbl td {{ padding:9px 0; border-bottom:1px solid var(--edge2); vertical-align:middle; }}
.fire-tbl tr:last-child td {{ border-bottom:none; }}
.fire-tbl td:not(:first-child) {{ text-align:right; font-family:var(--fm); font-size:11px; }}

/* ── ENTRY ANIMATIONS ── */
@keyframes fadeUp {{
  from {{ opacity:0; transform:translateY(10px); }}
  to   {{ opacity:1; transform:translateY(0); }}
}}
.card {{ animation: fadeUp .35s ease both; }}
.kpi:nth-child(1) {{ animation-delay:.04s; }}
.kpi:nth-child(2) {{ animation-delay:.08s; }}
.kpi:nth-child(3) {{ animation-delay:.12s; }}
.kpi:nth-child(4) {{ animation-delay:.16s; }}

  .mn{{font-family:var(--fm);}}
  .fw6{{font-weight:600;}}
  .muted{{color:var(--ink3);}}
  .ink2{{color:var(--ink2);}}
  .s8{{font-size:8px;}}.s9{{font-size:9px;}}.s10{{font-size:10px;}}.s11{{font-size:11px;}}.s12{{font-size:12px;}}.s13{{font-size:13px;}}
  .overline{{font-family:var(--fm);letter-spacing:.12em;text-transform:uppercase;}}
  .panel{{background:var(--surface);border:1px solid var(--edge);border-radius:14px;padding:16px 18px;}}
  .panel-hdr{{display:flex;align-items:center;gap:8px;font-family:var(--fm);font-size:9px;font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:var(--ink3);margin-bottom:12px;}}
</style>
</head>
<body>
<div id="root"></div>
<script>
const D = {_econ_payload};

// ── Helpers ──────────────────────────────────────────────────
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const chg = (v,decimals=2) => {{
  const up=v>=0, c=up?'var(--mint)':'var(--rose)', sym=up?'▲':'▼';
  return `<span style="font-family:var(--fm);font-size:10px;color:${{c}}">${{sym}}${{Math.abs(v).toFixed(decimals)}}</span>`;
}};
const bar = (pct,col,thick=false) =>
  `<div class="bar-track${{thick?' thick':''}}"><div class="bar-fill" style="width:${{pct}}%;background:${{col}}"></div></div>`;
const badge = (txt,cls) => `<span class="badge ${{cls}}">${{esc(txt)}}</span>`;
const sevCls = s => s==='Critical'?'crit':s==='High'?'high':s==='Med'?'med':'low';
const rCol = r => r>=75?'var(--rose)':r>=50?'var(--coral)':r>=35?'var(--gold)':'var(--mint)';

// ── KPI Strip ─────────────────────────────────────────────────
function kpiStrip() {{
  // Prefer live data; fall back to static oil/crypto
  const brentLive = D.commodities.find(c=>c.name.includes('Brent')||c.sym==='BZ=F');
  const wtiLive   = D.commodities.find(c=>c.name.includes('WTI')||c.sym==='CL=F');
  const brentStatic = D.oil.find(o=>o.name.includes('Brent'))||{{}};
  const brentVal  = brentLive ? brentLive.price : brentStatic.val;
  const brentChg  = brentLive ? brentLive.chg_pct : (brentStatic.change||0);
  const wtiVal    = wtiLive ? wtiLive.price : ((D.oil.find(o=>o.name.includes('WTI'))||{{}}).val||0);

  const fed       = D.indicators.find(i=>i.ticker==='FEDFUNDS')||{{}};
  const unrate    = D.indicators.find(i=>i.ticker==='UNRATE')||{{}};

  const cryptoSrc = (D.crypto_live && D.crypto_live.length) ? D.crypto_live : (D.crypto||[]);
  const btc       = cryptoSrc.find(c=>c.ticker==='BTC')||{{}};
  const eth       = cryptoSrc.find(c=>c.ticker==='ETH')||{{}};
  const btcPrice  = btc.price !== undefined ? btc.price : (btc.val||0);
  const ethPrice  = eth.price !== undefined ? eth.price : (eth.val||0);
  const btcChg    = btc.chg_pct !== undefined ? btc.chg_pct : (btc.change||0);

  const sp        = D.indices.find(i=>i.sym==='^GSPC');
  const spChg     = sp ? sp.chg_pct : 0;
  const spCol     = spChg >= 0 ? 'var(--mint)' : 'var(--rose)';

  const pz        = D.pizza;
  const pzCol     = pz.score>=75?'var(--rose)':pz.score>=55?'var(--coral)':pz.score>=35?'var(--gold)':'var(--mint)';
  const brentCol  = brentChg >= 0 ? 'var(--coral)' : 'var(--mint)';
  const btcCol    = btcChg >= 0 ? 'var(--gold)' : 'var(--rose)';

  const items = [
    {{ num: brentVal ? `$${{brentVal.toFixed(0)}}` : '-',
       lbl: 'Brent Crude',
       sub: `WTI $${{wtiVal ? wtiVal.toFixed(0) : '-'}} · ${{brentChg>=0?'+':''}}${{brentChg.toFixed(1)}}% today`,
       col: brentCol, glow:'rgba(251,146,60,.14)', bar:`linear-gradient(90deg,transparent,${{brentCol}},transparent)` }},
    {{ num: fed.val||'-',
       lbl: 'Fed Funds Rate',
       sub: `Unemployment ${{unrate.val||'-'}}`,
       col:'var(--sky)', glow:'rgba(56,189,248,.12)', bar:'linear-gradient(90deg,transparent,var(--sky),transparent)' }},
    {{ num: btcPrice ? `$${{(btcPrice/1000).toFixed(1)}}K` : '-',
       lbl: 'Bitcoin',
       sub: `ETH $${{ethPrice ? ethPrice.toFixed(0) : '-'}} · ${{btcChg>=0?'+':''}}${{btcChg.toFixed(1)}}% 24h`,
       col: btcCol, glow:'rgba(251,191,36,.12)', bar:`linear-gradient(90deg,transparent,${{btcCol}},transparent)` }},
    {{ num: pz.score,
       lbl: '🍕 Pizza Index',
       sub: pz.label,
       col: pzCol, glow:'rgba(251,146,60,.12)', bar:`linear-gradient(90deg,transparent,${{pzCol}},transparent)` }},
  ];
  return `<div class="kpi-grid">${{items.map(k=>`
    <div class="kpi">
      <div class="kpi-glow" style="--accent-glow:${{k.glow}}"></div>
      <div class="kpi-top-bar" style="--accent-bar:${{k.bar}}"></div>
      <div class="kpi-label">${{k.lbl}}</div>
      <div class="kpi-num" style="color:${{k.col}}">${{esc(k.num)}}</div>
      <div class="kpi-sub">${{esc(k.sub)}}</div>
    </div>`).join('')}}</div>`;
}}


// ── Economic Indicators ───────────────────────────────────────
function econPanel() {{
  const indRows = D.indicators.map(e => {{
    const up=e.up, cc=up?'var(--mint)':'var(--rose)';
    return `<div class="card-row" style="border-left-color:${{cc}}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div>
          <div style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(e.name)}}</div>
          <div class="mono" style="font-size:9px;color:var(--ink3);margin-top:2px">${{e.ticker}} · ${{e.date}}</div>
        </div>
        <div style="text-align:right">
          <div class="disp" style="font-size:24px;color:var(--sky)">${{esc(e.val)}}</div>
          <div>${{chg(parseFloat(e.change)||0)}}</div>
        </div>
      </div>
    </div>`;
  }}).join('');

  const oilRows = D.oil.map(o => {{
    const up=o.change>=0, cc=up?'var(--mint)':'var(--rose)';
    return `<div class="card-row" style="border-left-color:var(--coral)">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(o.name)}}</div>
        <div style="text-align:right">
          <span class="disp" style="font-size:24px;color:var(--gold)">${{o.val.toFixed(2)}}</span>
          <span class="mono" style="font-size:10px;color:var(--ink3);margin-left:5px">${{esc(o.unit)}}</span>
          <div>${{chg(o.change)}}</div>
        </div>
      </div>
    </div>`;
  }}).join('');

  const bondRows = D.bonds.map(b => {{
    const up=b.change>=0;
    return `<div class="card-row" style="border-left-color:${{b.col}}">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(b.name)}}</span>
          ${{badge(b.rating,'neu')}}
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <span class="disp" style="font-size:22px;color:${{b.col}}">${{b.yield.toFixed(2)}}%</span>
          ${{chg(b.change)}}
        </div>
      </div>
    </div>`;
  }}).join('');

  return `<div class="card">
    <div class="section-title">Economic Indicators</div>
    <div class="pill-tabs">
      <div class="pill on" onclick="sw('ei','ind',this)">Macro</div>
      <div class="pill" onclick="sw('ei','oil',this)">Energy</div>
      <div class="pill" onclick="sw('ei','bnd',this)">Bonds</div>
    </div>
    <div class="scroll">
      <div id="ei-ind" class="pane on">${{indRows}}</div>
      <div id="ei-oil" class="pane">${{oilRows}}</div>
      <div id="ei-bnd" class="pane">${{bondRows}}</div>
    </div>
  </div>`;
}}

// ── Trade Policy ──────────────────────────────────────────────
function tradePanel() {{
  const restrRows = D.restrictions.map(t => `
    <div class="card-row" style="border-left-color:rgba(148,163,184,.2)">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px;margin-bottom:6px">
        <div>
          <div style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(t.country)}}</div>
          <div style="font-size:11px;color:var(--ink2);margin-top:3px;line-height:1.45">${{esc(t.coverage)}}</div>
        </div>
        ${{badge(t.impact,sevCls(t.impact))}}
      </div>
      <div class="mono" style="font-size:9px;color:var(--ink3)">Avg tariff ${{t.avg_rate}}% · ${{t.year}} · WTO</div>
    </div>`).join('');

  const tariffRows = D.tariffs.map(t => `
    <div class="card-row" style="border-left-color:rgba(248,113,113,.3)">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px">
        <span style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(t.route)}}</span>
        ${{badge(t.impact,sevCls(t.impact))}}
      </div>
      <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:3px">
        <span class="disp" style="font-size:28px;color:var(--rose)">${{t.rate}}%</span>
        <span class="mono" style="font-size:11px;color:var(--coral)">${{esc(t.change)}}</span>
      </div>
      <div class="mono" style="font-size:9px;color:var(--ink3)">${{esc(t.sector)}}</div>
    </div>`).join('');

  return `<div class="card">
    <div class="section-title">Trade Policy</div>
    <div class="pill-tabs">
      <div class="pill on" onclick="sw('tp','re',this)">Restrictions</div>
      <div class="pill" onclick="sw('tp','ta',this)">Tariffs</div>
    </div>
    <div class="scroll">
      <div id="tp-re" class="pane on">${{restrRows}}</div>
      <div id="tp-ta" class="pane">${{tariffRows}}</div>
    </div>
  </div>`;
}}

// ── Supply Chain ──────────────────────────────────────────────
function supplyPanel() {{
  const chkRows = D.chokepoints.map(cp => {{
    const sc=cp.status==='red'?'var(--rose)':cp.status==='amber'?'var(--gold)':'var(--mint)';
    const wc=cp.wow_change<0?'var(--rose)':'var(--mint)';
    return `<div class="card-row" style="border-left-color:${{sc}};margin-bottom:12px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
        <span style="font-size:13px;font-weight:700;color:var(--ink)">${{esc(cp.name)}}</span>
        <span class="disp" style="font-size:20px;color:${{sc}}">${{cp.risk}}</span>
      </div>
      ${{bar(cp.risk,sc,true)}}
      <div style="display:flex;gap:14px;margin-top:5px;flex-wrap:wrap">
        <span class="mono" style="font-size:9px;color:var(--ink3)">${{cp.warnings}} warning(s)</span>
        <span class="mono" style="font-size:9px;color:var(--ink3)">${{cp.ais_disruptions}} AIS</span>
        <span class="mono" style="font-size:9px;color:${{wc}}">WoW ${{cp.wow_change>0?'+':''}}${{cp.wow_change}}%</span>
      </div>
      <div style="font-size:11px;color:var(--ink2);line-height:1.55;margin-top:6px">${{esc(cp.context.substring(0,150))}}${{cp.context.length>150?'…':''}}</div>
    </div>`;
  }}).join('');

  const shipRows = D.shipping.map(r => {{
    const sc=r.status==='Elevated'?'var(--rose)':r.status==='Rising'?'var(--gold)':r.status==='Reduced'?'var(--coral)':'var(--mint)';
    const up=r.change>=0;
    const rateStr=r.rate>999?r.rate.toLocaleString():typeof r.rate==='number'?r.rate.toFixed(2):r.rate;
    return `<div class="card-row" style="border-left-color:${{sc}}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:10px">
        <div>
          <div style="font-size:12px;font-weight:600;color:var(--ink)">${{esc(r.route)}}</div>
          <div class="mono" style="font-size:9px;color:var(--ink3);margin-top:2px">${{esc(r.type)}} · ${{esc(r.note)}}</div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <span class="disp" style="font-size:20px;color:${{sc}}">${{rateStr}}</span>
          <span class="mono" style="font-size:9px;color:var(--ink3);margin-left:3px">${{esc(r.unit)}}</span>
          <div class="mono" style="font-size:10px;color:${{up?'var(--rose)':'var(--mint)'}}">${{up?'▲':'▼'}}${{Math.abs(r.change).toFixed(1)}}%</div>
        </div>
      </div>
    </div>`;
  }}).join('');

  const minRows = D.minerals.map(m => {{
    const dn=m.change<=0, mc=dn?'var(--mint)':'var(--rose)';
    const sr=m.supply_risk, sc=sr>=80?'var(--rose)':sr>=60?'var(--coral)':sr>=40?'var(--gold)':'var(--mint)';
    return `<div class="card-row" style="border-left-color:${{m.col}}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <span style="font-size:13px;font-weight:700;color:var(--ink)">${{esc(m.mineral)}}</span>
        <div style="display:flex;align-items:baseline;gap:8px">
          <span class="disp" style="font-size:20px;color:${{m.col}}">${{m.price}}</span>
          <span class="mono" style="font-size:9px;color:var(--ink3)">${{esc(m.unit)}}</span>
          <span class="mono" style="font-size:10px;color:${{mc}}">${{dn?'▼':'▲'}}${{Math.abs(m.change).toFixed(1)}}%</span>
        </div>
      </div>
      ${{bar(sr,sc)}}
      <div style="display:flex;justify-content:space-between;margin-top:3px">
        <span class="mono" style="font-size:9px;color:var(--ink3)">Supply risk: <span style="color:${{sc}}">${{sr}}</span></span>
        <span class="mono" style="font-size:9px;color:var(--ink3)">${{esc(m.top_producer)}}</span>
      </div>
    </div>`;
  }}).join('');

  return `<div class="card">
    <div class="section-title">Supply Chain</div>
    <div class="pill-tabs">
      <div class="pill on" onclick="sw('sc','ch',this)">Chokepoints</div>
      <div class="pill" onclick="sw('sc','sh',this)">Shipping</div>
      <div class="pill" onclick="sw('sc','mn',this)">Minerals</div>
    </div>
    <div class="scroll">
      <div id="sc-ch" class="pane on">${{chkRows}}</div>
      <div id="sc-sh" class="pane">${{shipRows}}</div>
      <div id="sc-mn" class="pane">${{minRows}}</div>
    </div>
  </div>`;
}}

// ── Financial ─────────────────────────────────────────────────
function finPanel() {{
  const nfUp = D.btc_etf.net_flow >= 0;
  const nfCol = nfUp ? 'var(--mint)' : 'var(--rose)';
  const mCol  = D.market.label === 'CASH' ? 'var(--gold)' : 'var(--sky)';

  // ── Crypto: prefer live CoinGecko data ───────────────────────
  const cryptoSrc = (D.crypto_live && D.crypto_live.length) ? D.crypto_live : (D.crypto || []);
  const cryptoRows = cryptoSrc.map(c => {{
    const chgV = c.chg_pct !== undefined ? c.chg_pct : (c.change || 0);
    const price = c.price !== undefined ? c.price : (c.val || 0);
    const up = chgV >= 0, cc = up ? 'var(--mint)' : 'var(--rose)';
    const mcap = c.mcap > 1e12 ? `$${{(c.mcap/1e12).toFixed(2)}}T`
               : c.mcap > 1e9  ? `$${{(c.mcap/1e9).toFixed(1)}}B` : '';
    return `<div class="card-row" style="border-left-color:${{cc}};display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(c.name)}}</div>
        <div class="mono" style="font-size:9px;color:var(--ink3)">${{esc(c.ticker)}}${{mcap ? ' · ' + mcap : ''}}</div>
      </div>
      <div style="text-align:right">
        <div class="mono" style="font-size:13px;color:var(--ink)">$${{price.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})}}</div>
        <div class="mono" style="font-size:10px;color:${{cc}}">${{up ? '+' : ''}}${{Math.abs(chgV).toFixed(2)}}%</div>
      </div>
    </div>`;
  }}).join('');

  // ── Sector Heatmap: use live defense/indices if available for context ──
  const heatCells = D.sectors.map(s => {{
    const up = s.v >= 0;
    const intensity = Math.min(Math.abs(s.v) / 8, 1);
    const bg = up ? `rgba(52,211,153,${{.08 + intensity * .18}})` : `rgba(248,113,113,${{.08 + intensity * .18}})`;
    const col = up ? 'var(--mint)' : 'var(--rose)';
    return `<div class="sector-cell" style="background:${{bg}}">
      <div class="mono" style="font-size:8px;color:var(--ink3);margin-bottom:3px">${{esc(s.s)}}</div>
      <div class="mono" style="font-size:12px;font-weight:700;color:${{col}}">${{up ? '+' : ''}}${{s.v}}%</div>
    </div>`;
  }}).join('');

  // ── Live timestamp badge ──────────────────────────────────────
  const liveTs = D.ts ? `<span class="mono" style="font-size:8px;color:var(--ink3);margin-left:8px">${{esc(D.ts)}}</span>` : '';
  const liveBadge = (D.crypto_live && D.crypto_live.length)
    ? `<span class="live-chip" style="margin-left:6px"><span class="live-dot"></span>CoinGecko</span>`
    : `<span class="mono" style="font-size:8px;color:var(--ink3);margin-left:6px">static</span>`;

  return `<div class="card">
    <div class="section-title">Financial${{liveTs}}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">

      <div>
        <div class="overline" style="margin-bottom:10px">Crypto${{liveBadge}}</div>
        ${{cryptoRows || '<div class="mono" style="font-size:10px;color:var(--ink3)">Loading…</div>'}}
      </div>

      <div>
        <div class="overline" style="margin-bottom:10px">Sector Heatmap</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-bottom:16px">${{heatCells}}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <div style="background:var(--raised);border:1px solid var(--edge2);border-radius:10px;padding:14px;text-align:center">
            <div class="overline" style="margin-bottom:8px">Market Posture</div>
            <div class="disp" style="font-size:28px;color:${{mCol}};margin-bottom:5px">${{D.market.label}}</div>
            <div class="mono" style="font-size:9px;color:var(--ink3)">${{D.market.posture}}</div>
            <div class="mono" style="font-size:9px;color:var(--gold);margin-top:3px">${{D.market.flow}}</div>
          </div>
          <div style="background:var(--raised);border:1px solid var(--edge2);border-radius:10px;padding:14px;text-align:center">
            <div class="overline" style="margin-bottom:8px">BTC ETF Flow</div>
            <div class="disp" style="font-size:28px;color:${{nfCol}};margin-bottom:5px">$${{Math.abs(D.btc_etf.net_flow)}}M</div>
            ${{badge(nfUp ? 'INFLOW' : 'OUTFLOW', nfUp ? 'low' : 'crit')}}
            <div class="mono" style="font-size:9px;color:var(--ink3);margin-top:6px">Est. $${{D.btc_etf.est_flow}}M</div>
          </div>
        </div>
      </div>

    </div>
  </div>`;
}}


// ── Row 2: Layoffs + Fires ────────────────────────────────────
function row2() {{
  // ── Sector filter state ──────────────────────────────────────
  const allSectors = [...new Set((D.layoffs||[]).map(l=>l.sector||'Other'))].sort();
  const selSec = window._layoffSector || 'All';

  const filtered = (D.layoffs||[]).filter(l=>
    selSec === 'All' || (l.sector||'Other') === selSec
  );

  const sectorBtns = ['All',...allSectors].map(s=>
    `<button onclick="window._layoffSector='${{s}}';doRender()"
      style="font-family:JetBrains Mono,monospace;font-size:9px;padding:3px 10px;border-radius:3px;
             cursor:pointer;border:1px solid ${{s===selSec?'var(--sky)':'rgba(148,163,184,.15)'}};
             background:${{s===selSec?'rgba(56,189,248,.1)':'transparent'}};
             color:${{s===selSec?'var(--sky)':'var(--ink3)'}};margin:0 3px 4px 0">${{s}}</button>`
  ).join('');

  const layoffRows = filtered.slice(0,20).map(l=>{{
    const sc=l.severity==='Critical'?'var(--rose)':l.severity==='High'?'var(--coral)':l.severity==='Med'?'var(--gold)':'var(--mint)';
    const hasUrl = l.url && l.url.length > 4;
    const readBtn = hasUrl
      ? `<a href="${{esc(l.url)}}" target="_blank" rel="noopener"
           style="font-family:JetBrains Mono,monospace;font-size:9px;color:var(--sky);
                  text-decoration:none;padding:2px 8px;border:1px solid rgba(56,189,248,.25);
                  border-radius:3px;white-space:nowrap">Read ↗</a>`
      : '';
    const ageBadge = l.age
      ? `<span class="mono" style="font-size:8px;color:var(--ink3);margin-left:6px">${{esc(l.age)}}</span>`
      : '';
    return `<div class="card-row" style="border-left-color:${{sc}};padding:10px 12px">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px">
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;flex-wrap:wrap">
            <span style="font-size:13px;font-weight:700;color:var(--ink)">${{esc(l.company)}}</span>
            ${{badge(l.severity.toUpperCase(),sevCls(l.severity))}}
            ${{ageBadge}}
          </div>
          <div style="font-size:11px;color:var(--ink2);line-height:1.45;margin-bottom:4px">${{esc((l.headline||'').slice(0,100))}}</div>
        </div>
        <div style="flex-shrink:0;margin-left:10px;text-align:right">
          <div class="mono" style="font-size:11px;color:var(--gold);font-weight:600">${{esc(l.count)}}</div>
          <div class="mono" style="font-size:9px;color:var(--ink3);margin-top:2px">${{esc(l.sector||'')}}</div>
        </div>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="mono" style="font-size:9px;color:var(--ink3)">${{esc(l.source||'')}} · ${{esc(l.date||'')}}</span>
        ${{readBtn}}
      </div>
    </div>`;
  }}).join('');

  const emptyMsg = filtered.length === 0
    ? `<div style="font-family:JetBrains Mono,monospace;font-size:10px;color:var(--ink3);padding:20px;text-align:center">No layoffs reported for this sector.</div>`
    : '';

  const fireRows = D.fires.map(f=>{{
    const ic=f.high>50?'var(--rose)':f.high>20?'var(--coral)':'var(--gold)';
    return `<tr>
      <td><span style="font-size:12px;font-weight:600;color:var(--ink)">${{esc(f.region)}}</span>
          <span style="display:block;font-size:9px;color:var(--ink3)" class="mono">${{f.biome||''}}</span></td>
      <td class="mono" style="color:var(--sky)">${{f.fires.toLocaleString()}}</td>
      <td class="mono" style="color:${{ic}}">${{f.high}}</td>
      <td class="mono" style="color:var(--ink3)">${{(f.frp/1000).toFixed(1)}}k FRP</td>
    </tr>`;
  }}).join('');

  return `<div class="duo-grid">
    <div class="card" style="grid-column:1/-1">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px">
        <div style="display:flex;align-items:center;gap:10px">
          <div class="section-title" style="margin:0">Corporate Layoffs</div>
          <span class="live-chip"><span class="live-dot"></span>Live · Google News + GDELT</span>
        </div>
        <div style="font-family:JetBrains Mono,monospace;font-size:9px;color:var(--ink3)">
          ${{filtered.length}} reports · refreshes every 5 min
        </div>
      </div>
      <div style="margin-bottom:10px;display:flex;flex-wrap:wrap">${{sectorBtns}}</div>
      <div class="scroll" style="max-height:420px">
        ${{layoffRows}}${{emptyMsg}}
      </div>
    </div>
    <div class="card">
      <div class="section-title">🔥 Active Wildfires</div>
      <table class="fire-tbl">
        <thead><tr><th>Region</th><th>Fires</th><th>High</th><th>FRP</th></tr></thead>
        <tbody>${{fireRows}}</tbody>
      </table>
    </div>
  </div>`;
}}

// ── Pizza Index ───────────────────────────────────────────────
function pizzaSection() {{
  const pz=D.pizza;
  const col=pz.score>=75?'var(--rose)':pz.score>=55?'var(--coral)':pz.score>=35?'var(--gold)':'var(--mint)';
  const needlePct=pz.score;

  const compRows = pz.components.map(c=>{{
    const sc=c.stress; const scol=sc>=80?'var(--rose)':sc>=60?'var(--coral)':sc>=40?'var(--gold)':'var(--mint)';
    const up=c.change>0; const csym=up?'▲':'▼'; const ccol=up?'var(--rose)':'var(--mint)';
    return `<div class="card-row" style="border-left-color:${{scol}}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px">
        <div>
          <div style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(c.name)}}</div>
          <div class="mono" style="font-size:9px;color:var(--ink3);margin-top:2px">${{esc(c.note)}}</div>
        </div>
        <div style="text-align:right;flex-shrink:0;margin-left:14px">
          <span class="mono" style="font-size:12px;color:var(--ink2)">${{c.val}} <span style="font-size:9px;color:var(--ink3)">${{esc(c.unit)}}</span></span>
          <div>
            <span class="mono" style="font-size:10px;color:${{ccol}}">${{csym}}${{Math.abs(c.change).toFixed(1)}}%</span>
            <span class="disp" style="font-size:22px;color:${{scol}};margin-left:8px">${{sc}}</span>
          </div>
        </div>
      </div>
      ${{bar(sc,scol,true)}}
    </div>`;
  }}).join('');

  const cityRows = [...pz.city_prices].sort((a,b)=>b.stress-a.stress).map(c=>{{
    const sc=c.stress; const scol=sc>=80?'var(--rose)':sc>=60?'var(--coral)':sc>=40?'var(--gold)':'var(--mint)';
    const pct=Math.round((c.price-c.baseline)/c.baseline*100);
    return `<div class="card-row" style="border-left-color:${{scol}}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <span style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(c.city)}}</span>
        <div style="display:flex;align-items:center;gap:10px">
          <span class="mono" style="font-size:13px;color:var(--ink)">${{c.price}} ${{esc(c.currency)}}</span>
          <span class="mono" style="font-size:10px;color:var(--coral)">+${{pct}}%</span>
          <span class="disp" style="font-size:22px;color:${{scol}}">${{sc}}</span>
        </div>
      </div>
      ${{bar(sc,scol)}}
      <div class="mono" style="font-size:9px;color:var(--ink3);margin-top:2px">baseline ${{c.baseline}} ${{esc(c.currency)}}</div>
    </div>`;
  }}).join('');

  return `
  <div style="background:var(--surface);border:1px solid var(--edge);border-radius:16px;padding:28px 30px;margin-bottom:24px;position:relative;overflow:hidden">
    <div style="position:absolute;top:0;left:0;right:0;height:80px;
                background:radial-gradient(ellipse at 50% -20%, rgba(251,146,60,.1),transparent 70%);pointer-events:none"></div>
    <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:32px;flex-wrap:wrap">
      <div>
        <div class="overline" style="margin-bottom:12px">🍕 Pizza Index &nbsp;
          <span class="badge neu" style="font-size:8px">PIZZAINT METHODOLOGY</span></div>
        <div class="pz-score" style="color:${{col}}">${{pz.score}}</div>
        <div class="mono" style="font-size:13px;color:${{col}};margin-top:10px;letter-spacing:.06em">${{esc(pz.label)}}</div>
      </div>
      <div style="flex:1;min-width:200px;max-width:500px">
        <div style="font-size:13px;color:var(--ink2);line-height:1.8;margin-bottom:18px">${{esc(pz.description)}}</div>
        <div class="overline" style="margin-bottom:8px">Stress gauge</div>
        <div class="pz-bar">
          <div class="pz-needle" style="left:${{needlePct}}%"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:4px">
          <span class="mono" style="font-size:9px;color:var(--mint)">Low</span>
          <span class="mono" style="font-size:9px;color:var(--gold)">Threshold 60</span>
          <span class="mono" style="font-size:9px;color:var(--rose)">Critical 80+</span>
        </div>
      </div>
    </div>
  </div>
  <div class="duo-grid">
    <div class="card">
      <div class="section-title">📦 Input Components</div>
      <div class="scroll">${{compRows}}</div>
    </div>
    <div class="card">
      <div class="section-title">🌍 City Price Index</div>
      <div class="scroll">${{cityRows}}</div>
      <div style="margin-top:16px;padding:16px 18px;background:rgba(251,146,60,.06);
                  border:1px solid rgba(251,146,60,.18);border-radius:10px">
        <div class="overline" style="color:var(--coral);margin-bottom:8px">Methodology</div>
        <div style="font-size:12px;color:var(--ink2);line-height:1.75">
          Inspired by <em>The Economist</em>&rsquo;s Big Mac Index. Tracks margherita pizza prices
          as a proxy for wheat disruption, energy costs, and purchasing power stress.
          Scores above <strong style="color:var(--gold)">60</strong> indicate material supply-chain pressure.
        </div>
      </div>
    </div>
  </div>`;
}}

// ── Tab switch ────────────────────────────────────────────────
function sw(group, id, el) {{
  const card = el.closest('.card');
  card.querySelectorAll('.pill').forEach(p => p.classList.remove('on'));
  el.classList.add('on');
  card.querySelectorAll('.pane').forEach(p => p.classList.remove('on'));
  card.querySelector('#'+group+'-'+id).classList.add('on');
}}

// ── Live tag helper ──────────────────────────────────────────
function mkLt(){{
  if(!D.ts)return'';
  return '<span style="font-family:var(--fm);font-size:8px;display:inline-flex;align-items:center;gap:4px;padding:2px 7px;background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.2);border-radius:10px;color:var(--mint)"><span style="width:4px;height:4px;border-radius:50%;background:var(--mint);display:inline-block;animation:bl 1.2s ease-in-out infinite"></span>LIVE '+esc(D.ts)+'</span>';
}}

// ── Global Stock Indices ──────────────────────────────────────
function panelIndices(){{
  var arr=D.indices||[];
  if(!arr.length)return'<div class="panel"><div class="panel-hdr">Global Indices '+mkLt()+'</div><div class="mn s10 muted">Fetching live data...</div></div>';
  var vix=arr.filter(function(x){{return x.sym==='^VIX';}})[0],vv=vix?vix.price:0;
  var vc=vv>=30?'var(--rose)':vv>=20?'var(--gold)':'var(--mint)';
  var vixH=vix?('<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:rgba(0,0,0,.3);border:1px solid rgba(148,163,184,.1);border-radius:8px;margin-bottom:10px">'+'<span style="font-family:var(--fm);font-size:9px;font-weight:600;color:'+vc+'">VIX FEAR</span>'+'<span style="font-family:var(--fd);font-size:22px;color:'+vc+'">'+vv.toFixed(1)+' <span style="font-size:9px">'+(vv>=30?'EXTREME':vv>=20?'HIGH':'CALM')+'</span></span></div>'):'';
  var rows=arr.filter(function(x){{return x.sym!=='^VIX';}}).map(function(x){{
    var up=x.chg_pct>=0,c=up?'var(--mint)':'var(--rose)';
    var ps=x.price>999?x.price.toLocaleString('en-US',{{maximumFractionDigits:0}}):x.price.toFixed(2);
    return'<div class="card-row" style="border-left-color:'+c+'"><div style="display:flex;justify-content:space-between;align-items:center">'+'<div><span style="font-size:12px;font-weight:600;color:var(--ink)">'+esc(x.name)+'</span> <span class="mn s9 muted">'+esc(x.country)+'</span></div>'+'<div><span class="mn">'+ps+'</span> <span class="mn s10" style="color:'+c+'">'+(up?'&#9650;':'&#9660;')+Math.abs(x.chg_pct).toFixed(2)+'%</span></div>'+'</div></div>';
  }}).join('');
  return'<div class="panel"><div class="panel-hdr">Global Indices '+mkLt()+'</div>'+vixH+'<div class="scroll">'+rows+'</div></div>';
}}

// ── Forex Rates ───────────────────────────────────────────────
function panelForex(){{
  var arr=D.forex||[];
  if(!arr.length)return'<div class="panel"><div class="panel-hdr">Forex Rates '+mkLt()+'</div><div class="mn s10 muted">Fetching live data...</div></div>';
  var cmap={{}};(D.currency_crisis||[]).forEach(function(c){{cmap[c.currency]=c.status;}});
  var rows=arr.map(function(x){{
    var up=x.chg_pct>=0,c=up?'var(--mint)':'var(--rose)';
    var cur=x.usd_base?x.pair.split('/')[1]:x.pair.split('/')[0];
    var cris=cmap[cur]||'';
    var cb=cris?('<span class="mn s8" style="padding:1px 5px;border-radius:3px;background:rgba(255,61,90,.1);color:var(--rose);border:1px solid rgba(255,61,90,.2);margin-left:4px">'+cris+'</span>'):'';
    return'<div class="card-row" style="border-left-color:'+(cris?'var(--rose)':c)+'">'+'<div style="display:flex;justify-content:space-between;align-items:center">'+'<div><span class="mn" style="font-weight:600;color:var(--ink)">'+esc(x.pair)+'</span>'+cb+'<div class="s9 muted">'+esc(x.currency_name)+'</div></div>'+'<div><span class="mn">'+x.rate.toFixed(4)+'</span> <span class="mn s10" style="color:'+c+'">'+(up?'&#9650;':'&#9660;')+Math.abs(x.chg_pct).toFixed(2)+'%</span></div>'+'</div></div>';
  }}).join('');
  return'<div class="panel"><div class="panel-hdr">Forex Rates '+mkLt()+'</div><div class="scroll">'+rows+'</div></div>';
}}

// ── Commodities ───────────────────────────────────────────────
function panelCommodities(){{
  var arr=D.commodities||[];
  if(!arr.length)return'<div class="panel"><div class="panel-hdr">Commodities '+mkLt()+'</div><div class="mn s10 muted">Fetching live data...</div></div>';
  var catL={{energy:'Energy',precious:'Precious Metals',agri:'Agriculture',industrial:'Industrial',nuclear:'Nuclear'}};
  var h='';
  ['energy','precious','agri','industrial','nuclear'].forEach(function(cat){{
    var items=arr.filter(function(x){{return x.cat===cat;}});
    if(!items.length)return;
    h+='<div class="mn s8 muted overline" style="margin:10px 0 6px">'+catL[cat]+'</div>';
    h+=items.map(function(x){{
      var up=x.chg_pct>=0,c=up?'var(--mint)':'var(--rose)';
      var geo=['WTI Crude','Brent Crude','Natural Gas','Wheat (CBOT)'].indexOf(x.name)>-1;
      return'<div class="card-row" style="border-left-color:'+(geo?'var(--gold)':c)+'">'+'<div style="display:flex;justify-content:space-between;align-items:center">'+'<div><span style="font-size:12px;font-weight:600;color:var(--ink)">'+esc(x.name)+'</span>'+(geo?'<span class="mn s8" style="color:var(--gold);margin-left:4px">GEO</span>':'')+'</div>'+'<div><span class="mn" style="color:var(--gold)">'+x.price.toLocaleString('en-US',{{maximumFractionDigits:2}})+'</span> <span class="mn s9 muted">'+esc(x.unit)+'</span> <span class="mn s10" style="color:'+c+'">'+(up?'&#9650;':'&#9660;')+Math.abs(x.chg_pct).toFixed(2)+'%</span></div>'+'</div></div>';
    }}).join('');
  }});
  return'<div class="panel"><div class="panel-hdr">Commodities '+mkLt()+'</div><div class="scroll">'+h+'</div></div>';
}}

// ── Defense & Aerospace Stocks ────────────────────────────────
function panelDefense(){{
  var arr=D.defense||[];
  if(!arr.length)return'<div class="panel"><div class="panel-hdr">Defense &amp; Aerospace '+mkLt()+'</div><div class="mn s10 muted">Fetching live data...</div></div>';
  var rows=arr.map(function(x){{
    var up=x.chg_pct>=0,c=up?'var(--mint)':'var(--rose)';
    var cs=x.currency==='USD'?'$':x.currency==='EUR'?'\u20ac':(x.currency==='GBX'||x.currency==='GBP')?'\u00a3':'';
    var ps=x.currency==='GBX'?(x.price/100).toFixed(2):x.price.toFixed(2);
    return'<div class="card-row" style="border-left-color:var(--sky)">'+'<div style="display:flex;justify-content:space-between;align-items:center">'+'<div><span style="font-size:12px;font-weight:600;color:var(--ink)">'+esc(x.name)+'</span><div class="mn s9 muted">'+esc(x.country)+' \u00b7 '+esc(x.sym)+'</div></div>'+'<div><span class="mn" style="color:var(--sky)">'+cs+ps+'</span> <span class="mn s10" style="color:'+c+'">'+(up?'&#9650;':'&#9660;')+Math.abs(x.chg_pct).toFixed(2)+'%</span></div>'+'</div></div>';
  }}).join('');
  return'<div class="panel"><div class="panel-hdr">Defense &amp; Aerospace '+mkLt()+'</div>'+'<div class="mn s9" style="color:var(--coral);margin-bottom:10px">Conflict escalation drives these higher</div>'+'<div class="scroll">'+rows+'</div></div>';
}}

// ── Crypto (CoinGecko live) ───────────────────────────────────
function panelCrypto(){{
  var arr=(D.crypto_live&&D.crypto_live.length)?D.crypto_live:(D.crypto||[]);
  var rows=arr.map(function(x){{
    var chgV=x.chg_pct!=null?x.chg_pct:(x.change||0),up=chgV>=0,c=up?'var(--mint)':'var(--rose)';
    var mcap=x.mcap>1e12?('$'+(x.mcap/1e12).toFixed(2)+'T'):x.mcap>1e9?('$'+(x.mcap/1e9).toFixed(1)+'B'):'';
    var price=x.price!=null?x.price:(x.val||0);
    return'<div class="card-row" style="border-left-color:var(--gold)">'+'<div style="display:flex;justify-content:space-between;align-items:center">'+'<div><span style="font-size:12px;font-weight:600;color:var(--ink)">'+esc(x.name)+'</span> <span class="mn s9 muted">'+esc(x.ticker)+'</span>'+(mcap?'<div class="mn s9 muted">MCap '+mcap+'</div>':'')+'</div>'+'<div><span class="mn" style="color:var(--gold)">$'+price.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})+'</span> <span class="mn s10" style="color:'+c+'">'+(up?'&#9650;':'&#9660;')+Math.abs(chgV).toFixed(2)+'%</span></div>'+'</div></div>';
  }}).join('')||'<div class="mn s10 muted">Loading from CoinGecko...</div>';
  return'<div class="panel"><div class="panel-hdr">Cryptocurrency '+mkLt()+'</div><div class="scroll">'+rows+'</div></div>';
}}

// ── Sanctions Tracker ─────────────────────────────────────────
function panelSanctions(){{
  var rows=(D.sanctions||[]).map(function(s){{
    var col=s.impact==='Critical'?'var(--rose)':s.impact==='High'?'var(--coral)':'var(--gold)';
    return'<div class="card-row" style="border-left-color:'+col+'">'+'<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:5px">'+'<div><span style="font-size:13px;font-weight:700;color:var(--ink)">'+esc(s.entity)+'</span> <span class="mn s9 muted">'+esc(s.type)+' \u00b7 Since '+s.year+'</span></div>'+'<span class="mn s9" style="padding:2px 7px;border-radius:4px;background:rgba(0,0,0,.3);color:'+col+'">'+s.impact+'</span></div>'+'<div class="mn s9 muted" style="margin-bottom:4px">'+esc(s.scope)+'</div>'+'<div style="font-size:11px;color:var(--ink2);line-height:1.6">'+esc(s.detail)+'</div></div>';
  }}).join('');
  return'<div class="panel"><div class="panel-hdr">Active Sanctions</div><div class="scroll">'+rows+'</div></div>';
}}

// ── Currency Devaluation Monitor ──────────────────────────────
function panelCurrencyCrisis(){{
  var sorted=[].concat(D.currency_crisis||[]).sort(function(a,b){{return b.yoy_chg-a.yoy_chg;}});
  var rows=sorted.map(function(c){{
    var pct=Math.min(c.yoy_chg/250*100,100),col=c.col||'var(--rose)';
    return'<div class="card-row" style="border-left-color:'+col+'">'+'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">'+'<div><span style="font-size:12px;font-weight:700;color:var(--ink)">'+esc(c.country)+'</span> <span class="mn s9 muted">'+esc(c.currency)+'</span></div>'+'<div><span class="mn s11">1 USD = '+c.usd_rate.toLocaleString()+'</span> <span class="mn s10" style="color:'+col+';margin-left:8px">&#9650;'+c.yoy_chg+'% YoY</span></div></div>'+'<div style="height:4px;background:rgba(148,163,184,.08);border-radius:2px;overflow:hidden;margin-bottom:5px"><div style="height:100%;width:'+pct+'%;background:'+col+';border-radius:2px"></div></div>'+'<div class="s10 muted">'+esc(c.note)+'</div></div>';
  }}).join('');
  return'<div class="panel"><div class="panel-hdr">Currency Devaluation Monitor</div><div class="scroll">'+rows+'</div></div>';
}}

// ── Geopolitical Risk Premiums ────────────────────────────────
function panelGeoRisk(){{
  var rows=(D.geo_risk||[]).map(function(r){{
    var col=r.status==='Active'?'var(--rose)':r.status==='Elevated'?'var(--coral)':'var(--gold)';
    return'<div class="card-row" style="border-left-color:'+col+'">'+'<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px">'+'<div><div style="font-size:12px;font-weight:700;color:var(--ink)">'+esc(r.name)+'</div><div class="mn s9 muted" style="margin-top:2px">'+esc(r.driver)+' \u2014 <span style="color:var(--sky)">'+esc(r.asset)+'</span></div></div>'+'<div style="text-align:right;flex-shrink:0"><div class="mn s11" style="font-weight:700;color:'+col+'">'+esc(r.impact)+'</div><span class="mn s9" style="padding:1px 6px;border-radius:3px;background:rgba(0,0,0,.3);color:'+col+'">'+esc(r.status)+'</span></div>'+'</div></div>';
  }}).join('');
  return'<div class="panel"><div class="panel-hdr">Geopolitical Risk Premiums</div>'+'<div class="s10 muted" style="margin-bottom:10px">Market price impact of active conflicts and tensions</div>'+'<div class="scroll">'+rows+'</div></div>';
}}

// ── Render ────────────────────────────────────────────────────
document.getElementById('root').innerHTML =
  kpiStrip() +
  '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px">' +
    panelIndices() + panelForex() + panelCommodities() + panelDefense() +
  '</div>' +
  '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:18px">' +
    panelCrypto() + panelSanctions() + panelCurrencyCrisis() +
  '</div>' +
  panelGeoRisk() +
  '<div class="main-grid" style="margin-top:18px">' + econPanel() + tradePanel() + supplyPanel() + '</div>' +
  '<div style="margin-bottom:24px">' + finPanel() + '</div>' +
  '<hr class="divider">' +
  row2() +
  '<hr class="divider">' +
  pizzaSection();
</script>
</body></html>"""

    _ec.html(_econ_html, height=5200, scrolling=True)


with tab_facility:
    st.markdown('''<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow+Condensed:wght@400;500;600&display=swap');
    .sh{font-family:"Bebas Neue",sans-serif;font-size:1.05rem;letter-spacing:.12em;color:#d4963a;text-transform:uppercase;padding-bottom:8px;border-bottom:1px solid #1e2d46;margin:1.4rem 0 1rem;line-height:1;}
    .prov{font-family:"Barlow Condensed",sans-serif;font-size:.6rem;color:#4a6a8a;letter-spacing:.1em;margin-top:3px;}
    .err-box{background:rgba(224,80,80,.07);border-left:3px solid #e05050;border-radius:0 8px 8px 0;padding:12px 16px;font-family:"Barlow Condensed",sans-serif;font-size:.72rem;color:#e07878;margin:8px 0 12px;}
    .info-box{background:rgba(212,150,58,.06);border-left:3px solid #d4963a;border-radius:0 8px 8px 0;padding:14px 18px;font-size:.85rem;color:#8aaccc;margin:8px 0 14px;line-height:1.6;}
    </style>''', unsafe_allow_html=True)
    

    # ── Facility dataset (~200 global refineries, storage terminals, LNG) ──
    REFINERIES = pd.DataFrame([
        # ── North America ──────────────────────────────────────────────────
        {"Name":"Port Arthur Refinery","Lat":29.899,"Lon":-93.920,"Country":"USA","Operator":"Motiva","Type":"Refinery","Capacity_kbd":630,"Crude":"Sour/Sweet","Status":"Operational","Region":"North America"},
        {"Name":"Galveston Bay Refinery","Lat":29.737,"Lon":-95.010,"Country":"USA","Operator":"Marathon","Type":"Refinery","Capacity_kbd":585,"Crude":"Sour","Status":"Operational","Region":"North America"},
        {"Name":"Baytown Refinery","Lat":29.745,"Lon":-94.975,"Country":"USA","Operator":"ExxonMobil","Type":"Refinery","Capacity_kbd":560,"Crude":"Sour/Sweet","Status":"Operational","Region":"North America"},
        {"Name":"Baton Rouge Refinery","Lat":30.400,"Lon":-91.190,"Country":"USA","Operator":"ExxonMobil","Type":"Refinery","Capacity_kbd":502,"Crude":"Sweet","Status":"Operational","Region":"North America"},
        {"Name":"Garyville Refinery","Lat":30.075,"Lon":-90.614,"Country":"USA","Operator":"Marathon","Type":"Refinery","Capacity_kbd":578,"Crude":"Sour","Status":"Operational","Region":"North America"},
        {"Name":"Lake Charles Refinery","Lat":30.198,"Lon":-93.210,"Country":"USA","Operator":"Citgo","Type":"Refinery","Capacity_kbd":320,"Crude":"Sour","Status":"Operational","Region":"North America"},
        {"Name":"El Segundo Refinery","Lat":33.919,"Lon":-118.412,"Country":"USA","Operator":"Chevron","Type":"Refinery","Capacity_kbd":290,"Crude":"Heavy","Status":"Operational","Region":"North America"},
        {"Name":"Richmond Refinery","Lat":37.932,"Lon":-122.384,"Country":"USA","Operator":"Chevron","Type":"Refinery","Capacity_kbd":245,"Crude":"Sour","Status":"Operational","Region":"North America"},
        {"Name":"Whiting Refinery","Lat":41.677,"Lon":-87.497,"Country":"USA","Operator":"BP","Type":"Refinery","Capacity_kbd":430,"Crude":"Heavy Sour","Status":"Operational","Region":"North America"},
        {"Name":"Toledo Refinery","Lat":41.664,"Lon":-83.555,"Country":"USA","Operator":"BP/Husky","Type":"Refinery","Capacity_kbd":160,"Crude":"Light Sweet","Status":"Operational","Region":"North America"},
        {"Name":"Borger Refinery","Lat":35.667,"Lon":-101.398,"Country":"USA","Operator":"Phillips 66","Type":"Refinery","Capacity_kbd":146,"Crude":"Sweet","Status":"Operational","Region":"North America"},
        {"Name":"Wood River Refinery","Lat":38.861,"Lon":-90.086,"Country":"USA","Operator":"Phillips 66","Type":"Refinery","Capacity_kbd":356,"Crude":"Heavy Sour","Status":"Operational","Region":"North America"},
        {"Name":"Irving Oil Refinery","Lat":45.272,"Lon":-66.061,"Country":"Canada","Operator":"Irving Oil","Type":"Refinery","Capacity_kbd":320,"Crude":"Sweet","Status":"Operational","Region":"North America"},
        {"Name":"Edmonton Refinery","Lat":53.553,"Lon":-113.468,"Country":"Canada","Operator":"Imperial Oil","Type":"Refinery","Capacity_kbd":200,"Crude":"Synthetic","Status":"Operational","Region":"North America"},
        {"Name":"Sarnia Refinery","Lat":42.974,"Lon":-82.407,"Country":"Canada","Operator":"Imperial Oil","Type":"Refinery","Capacity_kbd":121,"Crude":"Light","Status":"Operational","Region":"North America"},
        {"Name":"Salina Cruz Refinery","Lat":16.173,"Lon":-95.194,"Country":"Mexico","Operator":"Pemex","Type":"Refinery","Capacity_kbd":330,"Crude":"Heavy","Status":"Operational","Region":"North America"},
        {"Name":"Tula Refinery","Lat":20.049,"Lon":-99.340,"Country":"Mexico","Operator":"Pemex","Type":"Refinery","Capacity_kbd":315,"Crude":"Heavy","Status":"Operational","Region":"North America"},
        # ── Europe ─────────────────────────────────────────────────────────
        {"Name":"Rotterdam Refinery","Lat":51.895,"Lon":4.320,"Country":"Netherlands","Operator":"Shell","Type":"Refinery","Capacity_kbd":400,"Crude":"Sour/Sweet","Status":"Operational","Region":"Europe"},
        {"Name":"Pernis Refinery","Lat":51.878,"Lon":4.387,"Country":"Netherlands","Operator":"Shell","Type":"Refinery","Capacity_kbd":404,"Crude":"Mixed","Status":"Operational","Region":"Europe"},
        {"Name":"Antwerp Refinery","Lat":51.270,"Lon":4.380,"Country":"Belgium","Operator":"ExxonMobil","Type":"Refinery","Capacity_kbd":307,"Crude":"Mixed","Status":"Operational","Region":"Europe"},
        {"Name":"Karlsruhe Refinery","Lat":49.010,"Lon":8.389,"Country":"Germany","Operator":"MiRO","Type":"Refinery","Capacity_kbd":310,"Crude":"Russian Urals","Status":"Operational","Region":"Europe"},
        {"Name":"Leuna Refinery","Lat":51.340,"Lon":12.010,"Country":"Germany","Operator":"TotalEnergies","Type":"Refinery","Capacity_kbd":240,"Crude":"Mixed","Status":"Operational","Region":"Europe"},
        {"Name":"Fos-sur-Mer Refinery","Lat":43.437,"Lon":4.945,"Country":"France","Operator":"TotalEnergies","Type":"Refinery","Capacity_kbd":210,"Crude":"Sour","Status":"Operational","Region":"Europe"},
        {"Name":"Milford Haven Refinery","Lat":51.706,"Lon":-5.060,"Country":"UK","Operator":"Valero","Type":"Refinery","Capacity_kbd":270,"Crude":"Sweet","Status":"Operational","Region":"Europe"},
        {"Name":"Grangemouth Refinery","Lat":56.018,"Lon":-3.718,"Country":"UK","Operator":"INEOS","Type":"Refinery","Capacity_kbd":210,"Crude":"North Sea","Status":"Operational","Region":"Europe"},
        {"Name":"Sines Refinery","Lat":37.956,"Lon":-8.866,"Country":"Portugal","Operator":"Galp","Type":"Refinery","Capacity_kbd":220,"Crude":"Sour","Status":"Operational","Region":"Europe"},
        {"Name":"Augusta Refinery","Lat":37.231,"Lon":15.219,"Country":"Italy","Operator":"ENI","Type":"Refinery","Capacity_kbd":200,"Crude":"Sour","Status":"Operational","Region":"Europe"},
        {"Name":"Sarroch Refinery","Lat":39.069,"Lon":9.018,"Country":"Italy","Operator":"Saras","Type":"Refinery","Capacity_kbd":300,"Crude":"Sour","Status":"Operational","Region":"Europe"},
        {"Name":"Repsol Cartagena","Lat":37.603,"Lon":-0.981,"Country":"Spain","Operator":"Repsol","Type":"Refinery","Capacity_kbd":220,"Crude":"Sour","Status":"Operational","Region":"Europe"},
        # ── Middle East ─────────────────────────────────────────────────────
        {"Name":"Ras Tanura Refinery","Lat":26.649,"Lon":50.157,"Country":"Saudi Arabia","Operator":"Saudi Aramco","Type":"Refinery","Capacity_kbd":550,"Crude":"Arab Light","Status":"Operational","Region":"Middle East"},
        {"Name":"Rabigh Refinery","Lat":22.800,"Lon":39.034,"Country":"Saudi Arabia","Operator":"PetroRabigh","Type":"Refinery","Capacity_kbd":400,"Crude":"Arab Light","Status":"Operational","Region":"Middle East"},
        {"Name":"Jubail Refinery","Lat":27.004,"Lon":49.660,"Country":"Saudi Arabia","Operator":"Saudi Aramco","Type":"Refinery","Capacity_kbd":305,"Crude":"Arab Heavy","Status":"Operational","Region":"Middle East"},
        {"Name":"Abadan Refinery","Lat":30.340,"Lon":48.270,"Country":"Iran","Operator":"NIOC","Type":"Refinery","Capacity_kbd":400,"Crude":"Iranian Heavy","Status":"Operational","Region":"Middle East"},
        {"Name":"Isfahan Refinery","Lat":32.650,"Lon":51.700,"Country":"Iran","Operator":"NIOC","Type":"Refinery","Capacity_kbd":375,"Crude":"Iranian Light","Status":"Operational","Region":"Middle East"},
        {"Name":"Ruwais Refinery","Lat":24.113,"Lon":52.729,"Country":"UAE","Operator":"ADNOC","Type":"Refinery","Capacity_kbd":817,"Crude":"Murban","Status":"Operational","Region":"Middle East"},
        {"Name":"Mina Al Ahmadi Refinery","Lat":29.080,"Lon":48.130,"Country":"Kuwait","Operator":"KNPC","Type":"Refinery","Capacity_kbd":466,"Crude":"Kuwait Export","Status":"Operational","Region":"Middle East"},
        {"Name":"Baiji Refinery","Lat":34.940,"Lon":43.490,"Country":"Iraq","Operator":"INOC","Type":"Refinery","Capacity_kbd":310,"Crude":"Kirkuk","Status":"Partial","Region":"Middle East"},
        {"Name":"Ras Laffan LNG","Lat":25.893,"Lon":51.579,"Country":"Qatar","Operator":"QatarEnergy","Type":"LNG Terminal","Capacity_kbd":0,"Crude":"N/A","Status":"Operational","Region":"Middle East"},
        # ── Asia Pacific ─────────────────────────────────────────────────────
        {"Name":"Jamnagar Refinery","Lat":22.467,"Lon":70.067,"Country":"India","Operator":"Reliance","Type":"Refinery","Capacity_kbd":1240,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Mangalore Refinery","Lat":12.897,"Lon":74.843,"Country":"India","Operator":"MRPL","Type":"Refinery","Capacity_kbd":300,"Crude":"Sour","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Koyali Refinery","Lat":22.377,"Lon":73.100,"Country":"India","Operator":"IOCL","Type":"Refinery","Capacity_kbd":275,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Zhenhai Refinery","Lat":29.969,"Lon":121.715,"Country":"China","Operator":"Sinopec","Type":"Refinery","Capacity_kbd":460,"Crude":"Sour","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Daqing Refinery","Lat":46.590,"Lon":124.847,"Country":"China","Operator":"PetroChina","Type":"Refinery","Capacity_kbd":200,"Crude":"Daqing","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Dalian Refinery","Lat":38.912,"Lon":121.614,"Country":"China","Operator":"PetroChina","Type":"Refinery","Capacity_kbd":410,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Ulsan Refinery","Lat":35.538,"Lon":129.338,"Country":"South Korea","Operator":"SK Energy","Type":"Refinery","Capacity_kbd":840,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Yeosu Refinery","Lat":34.762,"Lon":127.745,"Country":"South Korea","Operator":"GS Caltex","Type":"Refinery","Capacity_kbd":780,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Negishi Refinery","Lat":35.380,"Lon":139.660,"Country":"Japan","Operator":"ENEOS","Type":"Refinery","Capacity_kbd":270,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Chiba Refinery","Lat":35.559,"Lon":140.100,"Country":"Japan","Operator":"ENEOS","Type":"Refinery","Capacity_kbd":175,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Port Dickson Refinery","Lat":2.524,"Lon":101.799,"Country":"Malaysia","Operator":"Petronas","Type":"Refinery","Capacity_kbd":100,"Crude":"Tapis","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Cilacap Refinery","Lat":-7.717,"Lon":109.017,"Country":"Indonesia","Operator":"Pertamina","Type":"Refinery","Capacity_kbd":348,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Singapore Jurong Island","Lat":1.266,"Lon":103.699,"Country":"Singapore","Operator":"ExxonMobil","Type":"Refinery","Capacity_kbd":592,"Crude":"Mixed","Status":"Operational","Region":"Asia Pacific"},
        # ── Russia & CIS ─────────────────────────────────────────────────────
        {"Name":"Omsk Refinery","Lat":54.991,"Lon":73.368,"Country":"Russia","Operator":"Gazprom Neft","Type":"Refinery","Capacity_kbd":500,"Crude":"West Siberian","Status":"Operational","Region":"Russia/CIS"},
        {"Name":"Kirishi Refinery","Lat":59.449,"Lon":32.020,"Country":"Russia","Operator":"Surgutneftegas","Type":"Refinery","Capacity_kbd":360,"Crude":"Urals","Status":"Operational","Region":"Russia/CIS"},
        {"Name":"Ryazan Refinery","Lat":54.630,"Lon":39.740,"Country":"Russia","Operator":"Rosneft","Type":"Refinery","Capacity_kbd":350,"Crude":"Urals","Status":"Operational","Region":"Russia/CIS"},
        {"Name":"Ufa Refinery","Lat":54.735,"Lon":55.958,"Country":"Russia","Operator":"Rosneft","Type":"Refinery","Capacity_kbd":310,"Crude":"Urals","Status":"Operational","Region":"Russia/CIS"},
        {"Name":"Yaroslavl Refinery","Lat":57.626,"Lon":39.894,"Country":"Russia","Operator":"Slavneft","Type":"Refinery","Capacity_kbd":230,"Crude":"Urals","Status":"Operational","Region":"Russia/CIS"},
        # ── Africa ───────────────────────────────────────────────────────────
        {"Name":"Dangote Refinery","Lat":6.435,"Lon":3.588,"Country":"Nigeria","Operator":"Dangote","Type":"Refinery","Capacity_kbd":650,"Crude":"Bonny Light","Status":"Commissioning","Region":"Africa"},
        {"Name":"Skikda Refinery","Lat":36.878,"Lon":6.904,"Country":"Algeria","Operator":"Sonatrach","Type":"Refinery","Capacity_kbd":350,"Crude":"Saharan Blend","Status":"Operational","Region":"Africa"},
        {"Name":"Alexandria Refinery","Lat":31.200,"Lon":29.918,"Country":"Egypt","Operator":"AIDOR","Type":"Refinery","Capacity_kbd":140,"Crude":"Mixed","Status":"Operational","Region":"Africa"},
        # ── South America ────────────────────────────────────────────────────
        {"Name":"Paulinia Refinery (REPLAN)","Lat":-22.763,"Lon":-47.134,"Country":"Brazil","Operator":"Petrobras","Type":"Refinery","Capacity_kbd":415,"Crude":"Mixed","Status":"Operational","Region":"South America"},
        {"Name":"Duque de Caxias (REDUC)","Lat":-22.745,"Lon":-43.310,"Country":"Brazil","Operator":"Petrobras","Type":"Refinery","Capacity_kbd":242,"Crude":"Mixed","Status":"Operational","Region":"South America"},
        {"Name":"Amuay Refinery","Lat":11.749,"Lon":-70.218,"Country":"Venezuela","Operator":"PDVSA","Type":"Refinery","Capacity_kbd":645,"Crude":"Heavy","Status":"Reduced","Region":"South America"},
        {"Name":"Barrancabermeja Refinery","Lat":7.065,"Lon":-73.855,"Country":"Colombia","Operator":"Ecopetrol","Type":"Refinery","Capacity_kbd":250,"Crude":"Caño Limón","Status":"Operational","Region":"South America"},
    ])

    STORAGE = pd.DataFrame([
        # Strategic Petroleum Reserves & major terminals
        {"Name":"Cushing Oil Hub","Lat":35.985,"Lon":-96.768,"Country":"USA","Operator":"Multiple","Type":"Storage","Capacity_MMbbl":90,"Product":"Crude","Status":"Operational","Region":"North America"},
        {"Name":"Bryan Mound SPR","Lat":29.019,"Lon":-95.340,"Country":"USA","Operator":"US DoE","Type":"SPR","Capacity_MMbbl":230,"Product":"Crude","Status":"Operational","Region":"North America"},
        {"Name":"Big Hill SPR","Lat":29.892,"Lon":-93.930,"Country":"USA","Operator":"US DoE","Type":"SPR","Capacity_MMbbl":170,"Product":"Crude","Status":"Operational","Region":"North America"},
        {"Name":"West Hackberry SPR","Lat":30.052,"Lon":-93.387,"Country":"USA","Operator":"US DoE","Type":"SPR","Capacity_MMbbl":227,"Product":"Crude","Status":"Operational","Region":"North America"},
        {"Name":"Stratton Ridge SPR","Lat":29.178,"Lon":-95.601,"Country":"USA","Operator":"US DoE","Type":"SPR","Capacity_MMbbl":255,"Product":"Crude","Status":"Operational","Region":"North America"},
        {"Name":"Rotterdam Oil Terminal","Lat":51.924,"Lon":4.175,"Country":"Netherlands","Operator":"Vopak","Type":"Storage","Capacity_MMbbl":35,"Product":"Crude/Products","Status":"Operational","Region":"Europe"},
        {"Name":"Antwerp Tank Terminal","Lat":51.310,"Lon":4.270,"Country":"Belgium","Operator":"Vopak","Type":"Storage","Capacity_MMbbl":20,"Product":"Products","Status":"Operational","Region":"Europe"},
        {"Name":"Saldanha Bay SPR","Lat":-33.012,"Lon":17.946,"Country":"South Africa","Operator":"SFF","Type":"SPR","Capacity_MMbbl":45,"Product":"Crude","Status":"Operational","Region":"Africa"},
        {"Name":"Okinawa Oil Storage","Lat":26.335,"Lon":127.803,"Country":"Japan","Operator":"JOGMEC","Type":"SPR","Capacity_MMbbl":47,"Product":"Crude","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Ulsan Tank Farm","Lat":35.503,"Lon":129.386,"Country":"South Korea","Operator":"KNOC","Type":"Storage","Capacity_MMbbl":55,"Product":"Crude","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Juaymah Terminal","Lat":26.953,"Lon":49.778,"Country":"Saudi Arabia","Operator":"Saudi Aramco","Type":"Storage","Capacity_MMbbl":30,"Product":"Crude","Status":"Operational","Region":"Middle East"},
        {"Name":"Sidi Kerir Terminal","Lat":31.132,"Lon":29.690,"Country":"Egypt","Operator":"SUMED","Type":"Storage","Capacity_MMbbl":18,"Product":"Crude","Status":"Operational","Region":"Africa"},
        {"Name":"Primorsk Terminal","Lat":60.368,"Lon":28.620,"Country":"Russia","Operator":"Transneft","Type":"Storage","Capacity_MMbbl":12,"Product":"Crude","Status":"Operational","Region":"Russia/CIS"},
        {"Name":"Kozmino Terminal","Lat":42.826,"Lon":133.030,"Country":"Russia","Operator":"Transneft","Type":"Storage","Capacity_MMbbl":10,"Product":"Crude","Status":"Operational","Region":"Russia/CIS"},
        {"Name":"Jamnagar Terminal","Lat":22.420,"Lon":69.980,"Country":"India","Operator":"Reliance","Type":"Storage","Capacity_MMbbl":75,"Product":"Crude","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Jurong Rock Caverns","Lat":1.254,"Lon":103.703,"Country":"Singapore","Operator":"JTC","Type":"Storage","Capacity_MMbbl":14,"Product":"Crude/Products","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Shui Dong Terminal","Lat":21.578,"Lon":111.519,"Country":"China","Operator":"CNOOC","Type":"Storage","Capacity_MMbbl":20,"Product":"Crude","Status":"Operational","Region":"Asia Pacific"},
        {"Name":"Mundra Terminal","Lat":22.839,"Lon":69.725,"Country":"India","Operator":"APSEZ","Type":"Storage","Capacity_MMbbl":14,"Product":"Crude","Status":"Operational","Region":"Asia Pacific"},
    ])

    # Major pipeline routes [start_lat, start_lon, end_lat, end_lon, name, product]
    PIPELINES = [
        # North America
        (29.899,-93.920, 35.985,-96.768, "Gulf Coast → Cushing", "Crude"),
        (35.985,-96.768, 41.677,-87.497, "Cushing → Whiting", "Crude"),
        (53.553,-113.468, 41.677,-87.497, "Keystone XL Corridor", "Crude"),
        (29.019,-95.340, 29.899,-93.920, "SPR → Port Arthur", "Crude"),
        # Trans-Arabian / Middle East
        (26.649,50.157, 26.953,49.778, "Ras Tanura → Juaymah", "Crude"),
        (24.113,52.729, 25.893,51.579, "Ruwais → Ras Laffan", "Crude/LNG"),
        (30.340,48.270, 31.132,29.690, "Abadan → Sidi Kerir (SUMED)", "Crude"),
        # Russia export routes
        (54.991,73.368, 60.368,28.620, "Druzhba → Primorsk", "Crude"),
        (57.626,39.894, 51.895,4.320, "Yaroslavl → Rotterdam", "Crude"),
        (54.735,55.958, 42.826,133.030, "ESPO Pipeline", "Crude"),
        # European
        (51.895,4.320, 49.010,8.389, "Rotterdam → Karlsruhe", "Crude"),
        (51.895,4.320, 51.270,4.380, "Rotterdam → Antwerp", "Products"),
        # Asia
        (22.467,70.067, 12.897,74.843, "Jamnagar → Mangalore", "Products"),
        (29.969,121.715, 46.590,124.847, "Zhenhai → Daqing", "Products"),
        (1.266,103.699, 35.380,139.660, "Singapore → Japan", "LNG"),
    ]

    # ── UI Controls ─────────────────────────────────────────────────────────
    st.markdown("<div class='sh'>Global Refinery, Storage & Pipeline Map</div>", unsafe_allow_html=True)

    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        layer_ref  = st.toggle("🏭 Refineries",        value=True)
    with fc2:
        layer_stor = st.toggle("🗄️ Storage / SPR",    value=True)
    with fc3:
        layer_pipe = st.toggle("🔗 Pipelines",         value=True)
    with fc4:
        proj = st.selectbox("Projection", ["natural earth","orthographic","equirectangular","mercator"], key="fac_proj")

    fc5, fc6 = st.columns(2)
    with fc5:
        region_filter = st.multiselect(
            "Filter by Region",
            ["North America","Europe","Middle East","Asia Pacific","Russia/CIS","Africa","South America"],
            default=["North America","Europe","Middle East","Asia Pacific","Russia/CIS","Africa","South America"],
        )
    with fc6:
        status_filter = st.multiselect(
            "Filter by Status",
            ["Operational","Commissioning","Partial","Reduced"],
            default=["Operational","Commissioning","Partial","Reduced"],
        )

    # Apply filters
    ref_filt  = REFINERIES[REFINERIES["Region"].isin(region_filter) & REFINERIES["Status"].isin(status_filter)]
    stor_filt = STORAGE[STORAGE["Region"].isin(region_filter)]

    # ── Build Map ────────────────────────────────────────────────────────────
    fac_fig = _go.Figure()

    # ── Layer 1: Pipelines ───────────────────────────────────────────────────
    if layer_pipe:
        pipe_colors = {"Crude":"#e8a020","Products":"#40c8b0","LNG":"#f06060","Crude/LNG":"#a060e8","Crude/Products":"#60a8e8"}
        for (slat,slon,elat,elon,pname,ptype) in PIPELINES:
            # Draw as great-circle arc via intermediate points
            lats = [slat, (slat+elat)/2 + np.random.uniform(-0.5,0.5), elat, None]
            lons = [slon, (slon+elon)/2 + np.random.uniform(-0.5,0.5), elon, None]
            pc = pipe_colors.get(ptype, "#6080a8")
            fac_fig.add_trace(_go.Scattergeo(
                lat=lats, lon=lons, mode="lines",
                line=dict(width=1.4, color=pc),
                opacity=0.55, name=pname, showlegend=False,
                hovertemplate=f"<b>{pname}</b><br>Product: {ptype}<extra></extra>",
            ))

    # ── Layer 2: Storage terminals ───────────────────────────────────────────
    if layer_stor:
        stor_colors = {"Storage":"#60a8e8","SPR":"#a060e8"}
        for stype, grp in stor_filt.groupby("Type"):
            sc = stor_colors.get(stype, "#60a8e8")
            fac_fig.add_trace(_go.Scattergeo(
                lat=grp["Lat"], lon=grp["Lon"],
                mode="markers",
                marker=dict(
                    size=np.clip(grp["Capacity_MMbbl"].values / 8 + 8, 8, 30),
                    color=sc, symbol="square", opacity=0.85,
                    line=dict(width=1.2, color="rgba(255,255,255,0.3)"),
                ),
                name=f"{stype}",
                customdata=grp[["Operator","Capacity_MMbbl","Product","Status","Country"]].values,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Operator: %{customdata[0]}<br>"
                    "Capacity: %{customdata[1]} MMbbl<br>"
                    "Product: %{customdata[2]}<br>"
                    "Status: %{customdata[3]}<br>"
                    "Country: %{customdata[4]}<extra></extra>"
                ),
                text=grp["Name"],
            ))

    # ── Layer 3: Refineries ──────────────────────────────────────────────────
    if layer_ref:
        status_colors = {
            "Operational":"#40b860","Commissioning":"#e8a020",
            "Partial":"#f06060","Reduced":"#a060e8",
        }
        for status, grp in ref_filt.groupby("Status"):
            sc = status_colors.get(status, "#6080a8")
            fac_fig.add_trace(_go.Scattergeo(
                lat=grp["Lat"], lon=grp["Lon"],
                mode="markers",
                marker=dict(
                    size=np.clip(grp["Capacity_kbd"].values / 30 + 8, 8, 32),
                    color=sc, symbol="circle", opacity=0.9,
                    line=dict(width=1.2, color="rgba(255,255,255,0.25)"),
                ),
                name=f"Refinery — {status}",
                customdata=grp[["Operator","Capacity_kbd","Crude","Status","Country","Region"]].values,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Operator: %{customdata[0]}<br>"
                    "Capacity: %{customdata[1]:,} kb/d<br>"
                    "Crude Type: %{customdata[2]}<br>"
                    "Status: %{customdata[3]}<br>"
                    "Country: %{customdata[4]}<br>"
                    "Region: %{customdata[5]}<extra></extra>"
                ),
                text=grp["Name"],
            ))

    fac_fig.update_layout(
        geo=dict(
            projection_type=proj,
            showland=True,      landcolor="#0d1825",
            showocean=True,     oceancolor="#07090f",
            showcountries=True, countrycolor="#1b2d4f",
            showlakes=True,     lakecolor="#07090f",
            showrivers=False,
            bgcolor="#07090f",
            showcoastlines=True, coastlinecolor="#1b3060",
        ),
        paper_bgcolor="#07090f",
        font=dict(color="#6080a8", family="Space Mono, monospace", size=10),
        legend=dict(
            bgcolor="rgba(7,9,15,0.85)", bordercolor="#1b2d4f", borderwidth=1,
            x=0.01, y=0.99, font=dict(size=10),
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=600,
    )
    st.plotly_chart(fac_fig, use_container_width=True)

    # ── Legend explainer ─────────────────────────────────────────────────────
    st.markdown("""
    <div style='display:flex;gap:20px;flex-wrap:wrap;font-family:var(--mono);font-size:0.6rem;color:#4a6fa5;padding:6px 0 14px;'>
        <span><span style='color:#40b860'>●</span> Refinery — Operational</span>
        <span><span style='color:#e8a020'>●</span> Refinery — Commissioning</span>
        <span><span style='color:#f06060'>●</span> Refinery — Partial</span>
        <span><span style='color:#a060e8'>●</span> Refinery — Reduced</span>
        <span><span style='color:#60a8e8'>■</span> Storage Terminal</span>
        <span><span style='color:#a060e8'>■</span> Strategic Reserve (SPR)</span>
        <span>── Pipeline (color = product type) &nbsp; bubble size = capacity</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Summary stats (always visible, above selector) ──────────────────────
    st.markdown("<div class='sh'>Global Capacity Summary</div>", unsafe_allow_html=True)
    total_ref_cap  = ref_filt["Capacity_kbd"].sum()
    total_stor_cap = stor_filt["Capacity_MMbbl"].sum()
    st.markdown(f"""
    <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:4px 0 24px;'>
        <div style='background:linear-gradient(135deg,var(--panel),var(--panel2));
                    border:1px solid var(--border);border-top:2px solid var(--gold);
                    border-radius:10px;padding:18px 20px;'>
            <div style='font-family:var(--mono);font-size:0.62rem;font-weight:600;color:var(--muted);
                        letter-spacing:0.16em;text-transform:uppercase;margin-bottom:8px;'>Total Refineries</div>
            <div style='font-family:var(--display);font-size:2.2rem;color:var(--text);line-height:1;'>{len(ref_filt)}</div>
            <div style='font-family:var(--mono);font-size:0.6rem;color:var(--text3);margin-top:6px;'>in current filter</div>
        </div>
        <div style='background:linear-gradient(135deg,var(--panel),var(--panel2));
                    border:1px solid var(--border);border-top:2px solid var(--teal);
                    border-radius:10px;padding:18px 20px;'>
            <div style='font-family:var(--mono);font-size:0.62rem;font-weight:600;color:var(--muted);
                        letter-spacing:0.16em;text-transform:uppercase;margin-bottom:8px;'>Refining Capacity</div>
            <div style='font-family:var(--display);font-size:2.2rem;color:var(--text);line-height:1;'>{total_ref_cap/1000:.1f} <span style='font-size:1.1rem;color:var(--text3);'>Mb/d</span></div>
            <div style='font-family:var(--mono);font-size:0.6rem;color:var(--text3);margin-top:6px;'>{total_ref_cap:,} kb/d total</div>
        </div>
        <div style='background:linear-gradient(135deg,var(--panel),var(--panel2));
                    border:1px solid var(--border);border-top:2px solid var(--blue);
                    border-radius:10px;padding:18px 20px;'>
            <div style='font-family:var(--mono);font-size:0.62rem;font-weight:600;color:var(--muted);
                        letter-spacing:0.16em;text-transform:uppercase;margin-bottom:8px;'>Storage Terminals</div>
            <div style='font-family:var(--display);font-size:2.2rem;color:var(--text);line-height:1;'>{len(stor_filt)}</div>
            <div style='font-family:var(--mono);font-size:0.6rem;color:var(--text3);margin-top:6px;'>in current filter</div>
        </div>
        <div style='background:linear-gradient(135deg,var(--panel),var(--panel2));
                    border:1px solid var(--border);border-top:2px solid var(--amber);
                    border-radius:10px;padding:18px 20px;'>
            <div style='font-family:var(--mono);font-size:0.62rem;font-weight:600;color:var(--muted);
                        letter-spacing:0.16em;text-transform:uppercase;margin-bottom:8px;'>Storage Capacity</div>
            <div style='font-family:var(--display);font-size:2.2rem;color:var(--text);line-height:1;'>{total_stor_cap:,.0f} <span style='font-size:1.1rem;color:var(--text3);'>MMbbl</span></div>
            <div style='font-family:var(--mono);font-size:0.6rem;color:var(--text3);margin-top:6px;'>strategic + commercial</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Facility Intelligence Panel ──────────────────────────────────────────
    st.markdown("<div class='sh'>Facility Intelligence Panel</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='info-box'>
    Select a facility below to open a live intelligence panel — NASA FIRMS flaring detection,
    real-time weather, Esri World Imagery satellite tiles, and AIS vessel tracking.
    </div>""", unsafe_allow_html=True)

    # Build combined facility list for selector
    all_facilities = pd.concat([
        ref_filt[["Name","Lat","Lon","Country","Operator","Type","Region","Status"]].assign(
            Detail=ref_filt.apply(lambda r: f"{r['Operator']} · {r['Capacity_kbd']:,} kb/d · {r['Crude']}", axis=1)
        ),
        stor_filt[["Name","Lat","Lon","Country","Operator","Type","Region","Status"]].assign(
            Detail=stor_filt.apply(lambda r: f"{r['Operator']} · {r['Capacity_MMbbl']:,} MMbbl · {r['Product']}", axis=1)
        ),
    ], ignore_index=True)

    fac_options = ["— select a facility —"] + all_facilities["Name"].tolist()
    selected_fac = st.selectbox("Choose facility", fac_options, key="fac_select")

    if selected_fac != "— select a facility —":
        fac_row = all_facilities[all_facilities["Name"] == selected_fac].iloc[0]
        fac_lat, fac_lon = float(fac_row["Lat"]), float(fac_row["Lon"])
        fac_type = fac_row["Type"]

        STATUS_DOT = {"Operational":"🟢","Commissioning":"🟡","Partial":"🟠",
                      "Reduced":"🔴","SPR":"🛡️","Storage":"🗄️"}
        dot = STATUS_DOT.get(fac_row["Status"], "⚪")

        # Pre-fetch weather + FIRMS in parallel so sub-tabs are instant
        from concurrent.futures import ThreadPoolExecutor as _TPE_f
        with _TPE_f(max_workers=2) as _ex_f:
            _ff_wx    = _ex_f.submit(fetch_weather, fac_lat, fac_lon)
            _ff_firms = _ex_f.submit(fetch_nasa_firms, fac_lat, fac_lon, 50)
        _fac_wx_pre    = _ff_wx.result()
        _fac_firms_pre = _ff_firms.result()

        # ── Facility header ──────────────────────────────────────
        st.markdown(f"""
        <div style='background:#0d1825;border:1px solid #1b2d4f;border-radius:10px;
                    padding:18px 22px;margin:10px 0 18px;'>
            <div style='font-family:var(--display);font-weight:800;font-size:1.3rem;
                        color:#e8dfc8;'>{dot} {selected_fac}</div>
            <div style='font-family:var(--mono);font-size:0.62rem;color:#3a5a88;
                        margin:4px 0 10px;'>{fac_row["Country"]} · {fac_row["Region"]} · {fac_type}</div>
            <div style='font-size:0.82rem;color:#8aaccc;'>
                <b style='color:#c8a060;'>Operator</b>&nbsp; {fac_row["Operator"]} &nbsp;·&nbsp;
                <b style='color:#c8a060;'>Details</b>&nbsp; {fac_row["Detail"]} &nbsp;·&nbsp;
                <b style='color:#c8a060;'>Coords</b>&nbsp;
                <span style='font-family:var(--mono);font-size:0.72rem;'>
                {fac_lat:.4f}°, {fac_lon:.4f}°</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ════════════════════════════════════════════
        # PANEL COLUMNS: left = data, right = visuals
        # ════════════════════════════════════════════
        # ── Intelligence Panel — tabbed layout (no column height overlap) ───
        panel_tab1, panel_tab2, panel_tab3, panel_tab4 = st.tabs([
            "🌤 Weather", "🔥 NASA FIRMS", "🛰 Satellite", "🚢 AIS Tracking"
        ])

        with panel_tab1:

            # ── Live Weather ────────────────────────────────────
            st.markdown("<div class='sh'>🌤 Live Weather — Open-Meteo</div>", unsafe_allow_html=True)
            with st.spinner("Fetching weather…"):
                wx = _fac_wx_pre

            if wx.get("ok"):
                st.markdown(f"""
                <div style='background:#0d1220;border:1px solid #1b2d4f;border-radius:8px;
                            padding:16px 18px;margin-bottom:12px;'>
                    <div style='font-size:2rem;font-weight:800;color:#e8dfc8;font-family:var(--display);'>
                        {wx["temp_c"]:.1f}°C
                        <span style='font-size:0.9rem;color:#6080a8;font-weight:400;'>{wx["condition"]}</span>
                    </div>
                    <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px;
                                font-family:var(--mono);font-size:0.65rem;color:#8aaccc;'>
                        <div><span style='color:#c8a060;'>WIND</span><br>
                             {wx["wind_kmh"]:.0f} km/h @ {wx["wind_dir"]:.0f}°</div>
                        <div><span style='color:#c8a060;'>HUMIDITY</span><br>{wx["humidity"]}%</div>
                        <div><span style='color:#c8a060;'>PRESSURE</span><br>{wx["pressure"]:.0f} hPa</div>
                        <div><span style='color:#c8a060;'>VISIBILITY</span><br>
                             {wx["visibility"]/1000:.1f} km</div>
                    </div>
                </div>
                <div style='font-family:var(--mono);font-size:0.55rem;color:#2a4060;'>
                ▸ {wx["source"]} · {wx["fetched_at"]}</div>
                """, unsafe_allow_html=True)

                # 24h forecast sparklines
                fdf_wx = wx["fcast_df"]
                if not fdf_wx.empty:
                    fig_wx = _make_subplots(rows=2, cols=1, shared_xaxes=True,
                                          vertical_spacing=0.08, row_heights=[0.5, 0.5])
                    fig_wx.add_trace(_go.Scatter(
                        x=fdf_wx["time"], y=fdf_wx["wind_kmh"], name="Wind (km/h)",
                        line=dict(color=PALETTE["Brent"], width=1.6),
                        fill="tozeroy", fillcolor=rgba(PALETTE["Brent"], 0.1),
                    ), row=1, col=1)
                    fig_wx.add_trace(_go.Bar(
                        x=fdf_wx["time"], y=fdf_wx["precip_pct"], name="Precip %",
                        marker_color=rgba(PALETTE["NatGas"], 0.6),
                    ), row=2, col=1)
                    apply_theme(fig_wx, "24h Forecast", height=220,
                                margin=dict(l=45, r=10, t=28, b=28))
                    fig_wx.update_xaxes(**THEME["xaxis"])
                    fig_wx.update_yaxes(**THEME["yaxis"])
                    st.plotly_chart(fig_wx, use_container_width=True)
            else:
                err_box(f"Weather: {wx.get('error','')}")


        with panel_tab2:
            # ── NASA FIRMS Thermal Anomalies ─────────────────────
            st.markdown("<div class='sh'>🔥 NASA FIRMS — Thermal Anomaly Detection</div>",
                        unsafe_allow_html=True)
            st.markdown(
                "<div style='font-family:var(--mono);font-size:0.58rem;color:var(--text3);"
                "margin-bottom:8px;'>VIIRS + MODIS NRT · Last 24h · ~50km radius · No key</div>",
                unsafe_allow_html=True,
            )
            with st.spinner("Querying NASA FIRMS…"):
                firms = _fac_firms_pre

            if firms.get("ok"):
                if firms["count"] == 0:
                    st.markdown("""
                    <div style='background:rgba(56,184,106,0.07);border:1px solid rgba(56,184,106,0.2);
                                border-radius:8px;padding:14px 16px;
                                font-family:var(--mono);font-size:0.72rem;color:#38b86a;'>
                        ✓ No thermal anomalies in last 24h within 50 km.<br>
                        <span style='color:var(--text3);font-size:0.62rem;'>Normal baseline.</span>
                    </div>""", unsafe_allow_html=True)
                else:
                    df_f = firms["df"]
                    avg_frp = df_f["frp"].mean()
                    max_frp = df_f["frp"].max()
                    severity = "🔴 HIGH" if max_frp > 500 else ("🟡 MODERATE" if max_frp > 100 else "🟢 LOW")
                    st.markdown(f"""
                    <div style='background:rgba(224,80,80,0.07);border:1px solid rgba(224,80,80,0.25);
                                border-radius:8px;padding:14px 16px;margin-bottom:10px;'>
                        <div style='font-family:var(--body);font-weight:600;font-size:0.95rem;
                                    color:#e05858;'>{firms["count"]} thermal anomalies detected</div>
                        <div style='font-family:var(--mono);font-size:0.62rem;color:#a08060;margin-top:6px;'>
                            Severity: {severity} &nbsp;·&nbsp; Sensor: {firms.get("sensor","")} <br>
                            Avg FRP: {avg_frp:.1f} MW &nbsp;·&nbsp; Peak FRP: {max_frp:.1f} MW
                        </div>
                    </div>""", unsafe_allow_html=True)

                    fig_firms = _go.Figure()
                    fig_firms.add_trace(_go.Scattergeo(
                        lat=[fac_lat], lon=[fac_lon], mode="markers",
                        marker=dict(size=14, color=PALETTE["WTI"], symbol="star"),
                        name="Facility",
                    ))
                    fig_firms.add_trace(_go.Scattergeo(
                        lat=df_f["latitude"], lon=df_f["longitude"], mode="markers",
                        marker=dict(
                            size=np.clip(df_f["frp"].fillna(10) / 20 + 5, 5, 20),
                            color=df_f["frp"].fillna(0),
                            colorscale=[[0,"#ff6b6b"],[0.5,"#ff0000"],[1,"#ffffff"]],
                            opacity=0.85, showscale=True,
                            colorbar=dict(thickness=10,
                                          title=dict(text="FRP MW", font=dict(size=9)),
                                          tickfont=dict(size=8)),
                        ),
                        name="Hotspot",
                        hovertemplate="FRP: %{marker.color:.0f} MW<br>%{lat:.3f}, %{lon:.3f}<extra></extra>",
                    ))
                    deg_r = 0.6
                    fig_firms.update_layout(
                        geo=dict(
                            projection_type="mercator", showland=True, landcolor="#0d1825",
                            showocean=True, oceancolor="#07090f",
                            showcountries=True, countrycolor="#1b2d4f", bgcolor="#07090f",
                            lonaxis=dict(range=[fac_lon-deg_r, fac_lon+deg_r]),
                            lataxis=dict(range=[fac_lat-deg_r, fac_lat+deg_r]),
                        ),
                        paper_bgcolor="#07090f",
                        font=dict(color="#5a7898", family="Barlow Condensed", size=9),
                        margin=dict(l=0,r=0,t=0,b=0), height=260,
                        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
                    )
                    st.plotly_chart(fig_firms, use_container_width=True)
                    st.dataframe(
                        df_f[["acq_date","acq_time","frp","bright_ti4","confidence"]]
                        .rename(columns={"acq_date":"Date","acq_time":"Time",
                                         "frp":"FRP (MW)","bright_ti4":"Brightness (K)",
                                         "confidence":"Confidence"})
                        .sort_values("FRP (MW)", ascending=False).head(10),
                        use_container_width=True, hide_index=True,
                    )
                st.markdown(
                    f"<div class='prov'>▸ {firms['source']} · {firms['fetched_at']}</div>",
                    unsafe_allow_html=True,
                )
            else:
                # CSV blocked — show interactive FIRMS map embed instead
                embed_url = firms.get(
                    "embed_url",
                    f"https://firms.modaps.eosdis.nasa.gov/map/#d:24hrs;@{fac_lon:.4f},{fac_lat:.4f},11z"
                )
                st.markdown(f"""
                <div style='font-family:var(--mono);font-size:0.62rem;color:var(--text3);margin-bottom:6px;'>
                    NRT CSV unavailable on this network · Showing NASA FIRMS interactive map.
                    Fire detections update every 3–12 hours from satellite passes.
                </div>
                <div style='border:1px solid var(--border);border-radius:8px;overflow:hidden;'>
                    <iframe src="{embed_url}" width="100%" height="320"
                        style="border:none;display:block;" loading="lazy"
                        title="NASA FIRMS Active Fire Map">
                    </iframe>
                </div>
                <div class='prov' style='margin-top:4px;'>
                    ▸ NASA FIRMS Active Fire Map · VIIRS + MODIS · No key ·
                    <a href="{embed_url}" target="_blank" style='color:var(--gold);'>Open full screen ↗</a>
                </div>""", unsafe_allow_html=True)



        with panel_tab3:

            # ── Satellite Imagery ────────────────────────────────
            st.markdown("<div class='sh'>🛰 Satellite Imagery</div>", unsafe_allow_html=True)
            st.markdown(
                "<div style='font-family:var(--mono);font-size:0.58rem;color:#3a5a88;"
                "margin-bottom:8px;'>Esri World Imagery (ArcGIS) · Free · No key · "
                "Sub-metre resolution where available</div>",
                unsafe_allow_html=True,
            )

            sat_zoom = st.slider("Zoom level", 10, 17, 14, key="sat_zoom")

            # Fetch 3×3 tile mosaic from Esri World Imagery
            with st.spinner("Loading satellite tiles…"):
                mosaic = fetch_satellite_mosaic(fac_lat, fac_lon, zoom=sat_zoom)

            if mosaic["ok"] and mosaic["tiles"]:
                import io
                try:
                    from PIL import Image
                    # Stitch 3×3 grid into single image
                    tile_size = 256
                    grid = Image.new("RGB", (tile_size * 3, tile_size * 3))
                    for row, col, tile_bytes in mosaic["tiles"]:
                        tile_img = Image.open(io.BytesIO(tile_bytes)).convert("RGB")
                        grid.paste(tile_img, (col * tile_size, row * tile_size))
                    # Annotate centre crosshair
                    from PIL import ImageDraw
                    draw = ImageDraw.Draw(grid)
                    cx, cy = tile_size * 3 // 2, tile_size * 3 // 2
                    draw.ellipse([cx-8, cy-8, cx+8, cy+8], outline="#e8a020", width=2)
                    draw.line([cx-14, cy, cx+14, cy], fill="#e8a020", width=1)
                    draw.line([cx, cy-14, cx, cy+14], fill="#e8a020", width=1)
                    buf = io.BytesIO()
                    grid.save(buf, format="PNG")
                    st.image(buf.getvalue(), use_container_width=True,
                             caption=f"{selected_fac} · {fac_lat:.4f}°, {fac_lon:.4f}° · zoom {sat_zoom}")
                    st.markdown(
                        f"<div class='prov'>▸ {mosaic['source']} · {mosaic['fetched_at']} "
                        f"· 3×3 tile mosaic</div>",
                        unsafe_allow_html=True,
                    )
                except ImportError:
                    # Pillow not available — show centre tile only
                    centre_tile = next(
                        (b for r,c,b in mosaic["tiles"] if r==1 and c==1), None
                    )
                    if centre_tile:
                        st.image(centre_tile, use_container_width=True,
                                 caption=f"{selected_fac} · zoom {sat_zoom}")
                    st.markdown(
                        f"<div class='prov'>▸ {mosaic['source']} · centre tile only "
                        f"(install Pillow for full mosaic)</div>",
                        unsafe_allow_html=True,
                    )
            else:
                err_box(f"Satellite tiles: {mosaic.get('error','fetch failed')}")

            # External viewers
            gmaps_url = google_maps_satellite_url(fac_lat, fac_lon, zoom=sat_zoom)
            st.markdown(f"""
            <div style='display:flex;gap:10px;margin:8px 0 20px;flex-wrap:wrap;'>
                <a href="{gmaps_url.replace('output=embed&','')}"
                   target="_blank"
                   style='font-family:var(--mono);font-size:0.6rem;
                          color:#e8a020;text-decoration:none;
                          background:#0d1825;border:1px solid #1b2d4f;
                          border-radius:4px;padding:5px 12px;'>
                   🗺 Open in Google Maps ↗
                </a>
                <a href="https://livingatlas.arcgis.com/wayback/#active=18150&ext={fac_lon-0.03},{fac_lat-0.02},{fac_lon+0.03},{fac_lat+0.02}"
                   target="_blank"
                   style='font-family:var(--mono);font-size:0.6rem;
                          color:#e8a020;text-decoration:none;
                          background:#0d1825;border:1px solid #1b2d4f;
                          border-radius:4px;padding:5px 12px;'>
                   📅 Esri Wayback (historical imagery) ↗
                </a>
                <a href="https://earthengine.google.com/timelapse#v={fac_lat:.4f},{fac_lon:.4f},12,latLng"
                   target="_blank"
                   style='font-family:var(--mono);font-size:0.6rem;
                          color:#e8a020;text-decoration:none;
                          background:#0d1825;border:1px solid #1b2d4f;
                          border-radius:4px;padding:5px 12px;'>
                   ⏱ Google Earth Timelapse ↗
                </a>
            </div>""", unsafe_allow_html=True)


        with panel_tab4:
            # ── AIS Vessel Tracking ──────────────────────────────
            st.markdown("<div class='sh'>🚢 AIS Live Vessel Tracking — MarineTraffic</div>",
                        unsafe_allow_html=True)
            st.markdown(
                "<div style='font-family:var(--mono);font-size:0.58rem;color:#3a5a88;"
                "margin-bottom:8px;'>Live AIS positions · Tankers, product carriers & LNG vessels "
                "near this terminal · Updates every ~2 min</div>",
                unsafe_allow_html=True,
            )
            ais_zoom = st.slider("AIS map zoom", 7, 14, 10, key="ais_zoom")
            ais_url = marinetraffic_url(fac_lat, fac_lon, zoom=ais_zoom)

            st.markdown(f"""
            <div style='border:1px solid #1b2d4f;border-radius:8px;overflow:hidden;
                        margin-bottom:6px;'>
                <iframe src="{ais_url}"
                    width="100%" height="400"
                    style="border:none;display:block;"
                    loading="lazy"
                    title="AIS vessel tracking — {selected_fac}">
                </iframe>
            </div>
            <div style='font-family:var(--mono);font-size:0.55rem;color:#2a4060;'>
                ▸ MarineTraffic AIS · IMO/MMSI broadcast data ·
                <a href="https://www.marinetraffic.com/en/ais/home/centerx:{fac_lon:.3f}/centery:{fac_lat:.3f}/zoom:{ais_zoom}"
                target="_blank" style='color:#e8a020;'>Open full screen ↗</a>
            </div>""", unsafe_allow_html=True)


        # ── Facility Detail Cards — inside if block, after columns ────────────
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.expander("📋 Full Facility Database — Refineries & Storage"):
            card_tab1, card_tab2 = st.tabs(["🏭 Refineries", "🗄️ Storage & SPR"])

            with card_tab1:
                card_region = st.selectbox("Region", ["All"] + sorted(REFINERIES["Region"].unique()), key="card_reg")
                card_status = st.selectbox("Status", ["All"] + sorted(REFINERIES["Status"].unique()), key="card_stat")
                card_df = REFINERIES.copy()
                if card_region != "All":
                    card_df = card_df[card_df["Region"] == card_region]
                if card_status != "All":
                    card_df = card_df[card_df["Status"] == card_status]
                card_df = card_df.sort_values("Capacity_kbd", ascending=False)
                STATUS_DOT2 = {"Operational":"🟢","Commissioning":"🟡","Partial":"🟠","Reduced":"🔴"}
                cols_per_row = 3
                for row_start in range(0, len(card_df), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for ci, (_, row) in enumerate(card_df.iloc[row_start:row_start+cols_per_row].iterrows()):
                        dot2 = STATUS_DOT2.get(row["Status"], "⚪")
                        with cols[ci]:
                            st.markdown(f"""
                            <div style='background:#0d1220;border:1px solid #1b2d4f;border-radius:8px;
                                        padding:14px 16px;margin-bottom:10px;min-height:160px;'>
                                <div style='font-family:var(--display);font-size:0.88rem;color:#dde3ee;margin-bottom:6px;'>{dot2} {row["Name"]}</div>
                                <div style='font-family:var(--mono);font-size:0.6rem;color:#3a5a88;margin-bottom:8px;'>{row["Country"]} · {row["Region"]}</div>
                                <div style='font-size:0.78rem;color:#8aaccc;line-height:1.7;'>
                                    <b style='color:#c8a060;'>Operator</b> {row["Operator"]}<br>
                                    <b style='color:#c8a060;'>Capacity</b> {row["Capacity_kbd"]:,} kb/d<br>
                                    <b style='color:#c8a060;'>Crude</b> {row["Crude"]}<br>
                                    <b style='color:#c8a060;'>Status</b> {row["Status"]}
                                </div>
                            </div>""", unsafe_allow_html=True)
                dl_button(card_df, "refineries_global.csv")

            with card_tab2:
                stor_region2 = st.selectbox("Region", ["All"] + sorted(STORAGE["Region"].unique()), key="stor_reg2")
                stor_df2 = STORAGE if stor_region2 == "All" else STORAGE[STORAGE["Region"] == stor_region2]
                stor_df2 = stor_df2.sort_values("Capacity_MMbbl", ascending=False)
                for row_start in range(0, len(stor_df2), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for ci, (_, row) in enumerate(stor_df2.iloc[row_start:row_start+cols_per_row].iterrows()):
                        stype_icon = "🛡️" if row["Type"] == "SPR" else "🗄️"
                        with cols[ci]:
                            st.markdown(f"""
                            <div style='background:#0d1220;border:1px solid #1b2d4f;border-radius:8px;
                                        padding:14px 16px;margin-bottom:10px;min-height:150px;'>
                                <div style='font-family:var(--display);font-size:0.88rem;color:#dde3ee;margin-bottom:6px;'>{stype_icon} {row["Name"]}</div>
                                <div style='font-family:var(--mono);font-size:0.6rem;color:#3a5a88;margin-bottom:8px;'>{row["Country"]} · {row["Type"]}</div>
                                <div style='font-size:0.78rem;color:#8aaccc;line-height:1.7;'>
                                    <b style='color:#c8a060;'>Operator</b> {row["Operator"]}<br>
                                    <b style='color:#c8a060;'>Capacity</b> {row["Capacity_MMbbl"]:,} MMbbl<br>
                                    <b style='color:#c8a060;'>Product</b> {row["Product"]}<br>
                                    <b style='color:#c8a060;'>Status</b> {row["Status"]}
                                </div>
                            </div>""", unsafe_allow_html=True)
                dl_button(stor_df2, "storage_terminals_global.csv")
