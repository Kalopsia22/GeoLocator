"""
THE GEO-LOCATOR v8
==============
Changes from v7:
  - PERF: st.tabs() was executing every tab's ~70 API calls on every rerun
    regardless of which tab was visible. Replaced with a session-state
    selector so only the active tab's code runs per interaction.
  - PERF: sig_eq_df moved from mandatory startup fetch to lazy per-tab fetch.
  - LIVE MAP: cyber-threat and wildfire layers now source live data
    (fetch_live_cyber_threats, EONET wildfire filter) instead of static
    hardcoded points. Map legend now distinguishes LIVE vs REFERENCE layers.
  - DATA: Recent History panel now filters to 2025+ events (was showing
    an unfiltered top-6 slice under a stale "2022+" label) and the
    2025-2026 event pool was broadened beyond war/politics.
  - RELIABILITY: bare `except:` clauses replaced with `except Exception:`;
    key fetchers now log failures instead of failing silently.
  - MODULARITY: static reference datasets (shipping rates, military bases,
    nuclear sites, historical events, etc.) extracted to data_constants.py.
  - ALERTING: optional webhook alerts (Slack/Discord-compatible) on
    critical-threshold changes — no AI/LLM involved, just a plain HTTP
    POST to a URL you configure in st.secrets.

Changes from v5 (carried forward):
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

import logging
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json, requests, re, time
from datetime import datetime, timezone
import plotly.graph_objects as _go
from plotly.subplots import make_subplots as _make_subplots

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s")
_log = logging.getLogger("geo_locator")

# v8 module split (phase 1): static reference datasets now live in
# data_constants.py — see that file's docstring for scope/rationale.
# NOTE: `import *` silently skips names starting with underscore, so the
# two derived-lookup constants (_CI_LOOKUP, _HIST_SORTED) must be imported
# explicitly or every downstream reference to them raises NameError.
from data_constants import *
from data_constants import _CI_LOOKUP, _HIST_SORTED
# v8: fetch functions previously failed silently (bare `except Exception: pass`),
# which made it impossible to tell a genuine outage from cached/stale data.
# `_log.warning(...)` calls are added to the most-frequently-hit live fetchers
# below so failures surface in the server console without affecting the UI.

# ── Pre-defined data constants (defined early to prevent NameError on any line) ──
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


# ── Webhook alerting (v8) ───────────────────────────────────────
# Optional, plain HTTP — no AI/LLM of any kind. If ALERT_WEBHOOK_URL is set
# in st.secrets, a Slack- or Discord-compatible JSON payload ({"text": ...}
# / {"content": ...}) is POSTed whenever a tracked threshold is crossed.
# Debounced via session_state so the same condition doesn't re-fire every
# rerun — it only fires on the transition into the alert state.
@st.cache_data(ttl=3600, show_spinner=False)
def _alert_webhook_url():
    try:
        return st.secrets.get("ALERT_WEBHOOK_URL", None)
    except Exception:
        return None

def send_alert(alert_key: str, message: str) -> bool:
    """
    Fire a webhook alert once per transition into the alert condition.
    `alert_key` should be a stable id for the condition (e.g. "kp_storm",
    "crit_conflict_spike") so the same alert doesn't spam on every rerun.
    Returns True if a webhook was sent, False otherwise (not configured,
    already sent, or the POST failed — failures are logged, not raised).
    """
    url = _alert_webhook_url()
    if not url:
        return False
    _fired = st.session_state.setdefault("_alerts_fired", set())
    if alert_key in _fired:
        return False
    try:
        payload = {"text": message, "content": message}  # covers Slack + Discord shapes
        requests.post(url, json=payload, timeout=6)
        _fired.add(alert_key)
        return True
    except Exception as _e:
        _log.warning("send_alert failed for %s: %s", alert_key, _e)
        return False

def clear_alert(alert_key: str) -> None:
    """Call when a condition returns to normal so the alert can re-fire next time it recurs."""
    st.session_state.get("_alerts_fired", set()).discard(alert_key)


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
    st_autorefresh(interval=60_000,  key="auto60s")    # 60s global refresh
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
    except Exception as _e:
        _log.warning("fetch_usgs failed, falling back to persisted/baseline data: %s", _e)
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
    except Exception as _e:
        _log.warning("fetch_eonet failed, falling back to baseline data: %s", _e)
        return _se()

@st.cache_data(ttl=90, show_spinner=False)
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
    except Exception as _e:
        _log.warning("fetch_kp failed, using baseline series: %s", _e)
        return {"kp": 3.7, "series": [1,2,1.5,2.3,3.1,3.7,2.8,2.1,1.8,2.5,3,3.7]*2}

# ── GDELT conflict-scoped fetcher ────────────────────────────
CONFLICT_QUERIES = {
    "Ukraine–Russia War":  ["Ukraine Russia war shelling missile", "Ukraine war frontline", "Russia Ukraine attack"],
    "Gaza Conflict":       ["Gaza Israel war strikes", "Gaza humanitarian IDF Hamas", "Gaza ceasefire"],
    "Israel–Iran War":     ["Israel Iran war strike nuclear", "Israel Iran missiles IRGC", "Hezbollah Israel attack"],
    "Sudan Civil War":     ["Sudan RSF SAF war Darfur", "Sudan civil war Khartoum", "Sudan famine conflict"],
    "Myanmar Civil War":   ["Myanmar junta resistance PDF war", "Myanmar military coup resistance", "Myanmar Tatmadaw"],
}

@st.cache_data(ttl=120, show_spinner=False)
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
                    except Exception:
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


@st.cache_data(ttl=120, show_spinner=False)
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
                    except Exception:
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
        except Exception:
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
                except Exception:
                    age_s = "recent"
                all_arts.append({
                    "title":  a.get("title","")[:100],
                    "source": a.get("domain",""),
                    "url":    url,
                    "time":   age_s,
                })
        except Exception:
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
    except Exception:
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
    except Exception as _e:
        _log.warning("fetch_firms_count failed: %s", _e)
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
            except Exception:
                age_s = ""
            out.append({"title": a.get("title","")[:90], "source": a.get("domain",""),
                        "url": a.get("url",""), "time": age_s})
        return out
    except Exception:
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
    from datetime import datetime, timezone

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
            except Exception: pass
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
    except Exception:
        return pd.DataFrame()


# ── Country Intelligence lookup for click-to-analyse feature ─────────────────
# Maps country name → coordinates + intel data
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


# build_global_map() was removed in v8.1 — the Global Command Map now uses
# a Cobe WebGL rotating globe (see _render_cobe_globe below) instead of the
# pydeck deck.gl multi-layer map. build_theatre_map (below) is unrelated —
# it powers the small per-conflict map in the Conflict Dashboard tab and is
# untouched.

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
    }
    _results = {}
    with _TPE(max_workers=5) as _ex:
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
# sig_eq_df is NOT fetched here (v8): it's only used inside the Earth Signals
# tab, so fetching it unconditionally on every rerun (even when that tab
# isn't open) wasted a network round-trip. It's fetched lazily below, right
# where the Earth Signals tab body executes — st.cache_data still makes
# repeat visits to that tab instant.
utc_now    = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark" style="margin-bottom:4px">THE GEO-<em>LOCATOR</em></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:var(--muted);letter-spacing:.14em;font-weight:700;margin-bottom:16px">GLOBAL INTELLIGENCE PLATFORM v8</p>', unsafe_allow_html=True)
    if _alert_webhook_url():
        st.caption("🔔 Webhook alerts: **on** (critical conflicts, Kp≥5 storms)")
    else:
        st.caption("🔕 Webhook alerts: off — set `ALERT_WEBHOOK_URL` in st.secrets (Slack/Discord incoming webhook URL) to enable")

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    st.markdown("#### 🗺 Global Map Layers")
    st.caption("Groups: toggle categories on/off.")

    st.markdown("#### 🌐 Globe Layers (37)")
    st.caption("Controls which categories render on the rotating globe below.")

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
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=IBM+Plex+Mono:wght@300;400;500&family=Bebas+Neue&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:100%;height:100%;overflow:hidden;background:#020609;}

/* ── Root ── */
#gi{position:fixed;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;font-family:'IBM Plex Mono',monospace;}

/* ── Canvas layers ── */
#c-bg,#c-globe,#c-fx{position:absolute;inset:0;width:100%;height:100%;}
#c-globe,#c-fx{pointer-events:none;}
#c-scan{position:absolute;inset:0;pointer-events:none;z-index:5;
  background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.03) 3px,rgba(0,0,0,.03) 4px);}
#c-vig{position:absolute;inset:0;pointer-events:none;z-index:4;
  background:radial-gradient(ellipse 88% 88% at 50% 50%,transparent 22%,rgba(2,6,9,.96) 100%);}

/* ── Boot flash ── */
#p1{position:absolute;z-index:20;text-align:center;width:100%;
  opacity:0;animation:fi .3s ease .1s forwards,fo .4s ease 1.7s forwards;}
@keyframes fi{to{opacity:1}} @keyframes fo{to{opacity:0}}
.cbar{height:1px;background:linear-gradient(90deg,transparent,#ff2d55,transparent);
  margin:6px auto;width:clamp(180px,35vw,480px);
  animation:sx .8s ease .15s forwards;opacity:0;transform:scaleX(0);}
@keyframes sx{to{opacity:1;transform:scaleX(1)}}
.cline{font-size:clamp(8px,1.1vw,12px);letter-spacing:.3em;color:#ff2d55;text-transform:uppercase;margin:4px 0;}

/* ── Main layer ── */
#p2{position:absolute;z-index:20;text-align:center;width:100%;
  opacity:0;animation:fi .7s ease 2s forwards;}

/* ── Logo ── */
#lw{opacity:0;transform:translateY(10px);animation:li 1s cubic-bezier(.16,1,.3,1) 3s forwards;}
@keyframes li{to{opacity:1;transform:translateY(0)}}
#logo{font-family:'Orbitron',monospace;font-weight:900;
  font-size:clamp(36px,8vw,100px);letter-spacing:.14em;color:#00d4ff;line-height:1;
  text-shadow:0 0 60px rgba(0,212,255,.8),0 0 120px rgba(0,212,255,.3),0 0 3px rgba(255,255,255,.4);}
#logo em{color:#f0a500;font-style:normal;
  text-shadow:0 0 60px rgba(240,165,0,.8),0 0 120px rgba(240,165,0,.3);}
#sub{font-size:clamp(7px,1.1vw,13px);letter-spacing:.42em;text-transform:uppercase;
  color:rgba(0,212,255,.4);margin-top:9px;}
#ver{font-size:clamp(7px,.9vw,11px);letter-spacing:.28em;color:rgba(0,212,255,.25);margin-top:4px;}

/* ── Divider ── */
#divl{height:1px;margin:14px auto;width:0;
  background:linear-gradient(90deg,transparent,rgba(0,212,255,.4),rgba(240,165,0,.4),transparent);
  animation:dw .7s ease 4.2s forwards;}
@keyframes dw{to{width:clamp(240px,48vw,640px)}}

/* ── Feature chips ── */
#chips{opacity:0;transform:translateY(6px);animation:li .8s ease 4.6s forwards;
  display:flex;flex-wrap:wrap;justify-content:center;gap:6px;margin-top:10px;
  max-width:clamp(320px,60vw,780px);padding:0 12px;}
.chip{font-size:clamp(7px,.85vw,10px);letter-spacing:.18em;text-transform:uppercase;
  padding:3px 10px;border-radius:2px;border:1px solid;white-space:nowrap;}
.ch-c{color:#ff2d55;border-color:rgba(255,45,85,.3);background:rgba(255,45,85,.06);}
.ch-s{color:#a855f7;border-color:rgba(168,85,247,.3);background:rgba(168,85,247,.06);}
.ch-e{color:#f0a500;border-color:rgba(240,165,0,.3);background:rgba(240,165,0,.06);}
.ch-i{color:#00d4ff;border-color:rgba(0,212,255,.3);background:rgba(0,212,255,.06);}
.ch-g{color:#00e5a0;border-color:rgba(0,229,160,.3);background:rgba(0,229,160,.06);}

/* ── HUD corners ── */
.hud{position:absolute;z-index:20;opacity:0;animation:fi .5s ease 5.8s forwards;}
#tl{top:20px;left:20px;} #tr{top:20px;right:20px;text-align:right;}
#bl{bottom:56px;left:20px;} #br{bottom:56px;right:20px;text-align:right;}
.hbox{position:relative;padding:8px 12px;
  border:1px solid rgba(0,212,255,.1);border-radius:2px;background:rgba(2,6,9,.8);}
.hbox::before,.hbox::after,.hbox>.bc::before,.hbox>.bc::after{
  content:'';position:absolute;width:8px;height:8px;border-color:rgba(0,212,255,.35);border-style:solid;}
.hbox::before{top:-1px;left:-1px;border-width:2px 0 0 2px;}
.hbox::after{top:-1px;right:-1px;border-width:2px 2px 0 0;}
.hbox>.bc::before{bottom:-1px;left:-1px;border-width:0 0 2px 2px;}
.hbox>.bc::after{bottom:-1px;right:-1px;border-width:0 2px 2px 0;}
.hl{font-size:8px;letter-spacing:.2em;text-transform:uppercase;color:rgba(0,212,255,.35);line-height:1.9;}
.hv{font-size:10px;font-weight:500;color:rgba(0,212,255,.7);}

/* ── Centre threat bar ── */
#thrbar{position:absolute;top:20px;left:50%;transform:translateX(-50%);
  z-index:20;display:flex;align-items:center;gap:8px;
  opacity:0;animation:fi .5s ease 6.2s forwards;}
.tl{font-size:8px;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.28);}
.tb{display:flex;gap:2px;}
.tb span{width:clamp(12px,1.8vw,20px);height:7px;border-radius:1px;background:rgba(255,255,255,.06);}
.tb span.on{animation:bp 2s ease-in-out infinite;}
@keyframes bp{0%,100%{opacity:1}50%{opacity:.45}}

/* ── AIS / airspace counters ── */
#live-ct{position:absolute;top:48px;left:50%;transform:translateX(-50%);
  z-index:20;display:flex;gap:14px;align-items:center;
  opacity:0;animation:fi .5s ease 6.4s forwards;}
.lct{font-size:8px;letter-spacing:.15em;text-transform:uppercase;
  color:rgba(0,229,160,.6);display:flex;align-items:center;gap:5px;}
.lct-dot{width:5px;height:5px;border-radius:50%;animation:bp 1.4s ease-in-out infinite;}

/* ── Ticker ── */
#tick{position:absolute;bottom:46px;left:0;right:0;height:26px;
  background:rgba(3,6,9,.9);border-top:1px solid rgba(0,212,255,.12);
  display:flex;align-items:center;overflow:hidden;
  opacity:0;animation:fi .5s ease 6s forwards;}
.tlbl{flex-shrink:0;background:#ff2d55;color:#fff;
  font-size:9px;font-weight:500;letter-spacing:.12em;
  padding:0 12px;height:100%;display:flex;align-items:center;white-space:nowrap;}
.tks{display:inline-block;white-space:nowrap;
  font-size:10px;color:rgba(194,212,238,.42);letter-spacing:.05em;
  padding-left:100%;animation:scroll 18s linear infinite;}
@keyframes scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* ── Progress bar ── */
#prog{position:absolute;bottom:0;left:0;height:2px;
  background:linear-gradient(90deg,#ff2d55,#f0a500,#00d4ff,#00e5a0);
  animation:pw 10s linear forwards;}
@keyframes pw{0%{width:0%}100%{width:100%}}

/* ── Skip ── */
#skip{position:absolute;bottom:14px;right:18px;z-index:30;
  font-size:9px;letter-spacing:.15em;text-transform:uppercase;
  color:rgba(255,255,255,.22);background:transparent;
  border:1px solid rgba(255,255,255,.08);padding:4px 12px;
  border-radius:2px;cursor:pointer;transition:all .2s;}
#skip:hover{color:#00d4ff;border-color:rgba(0,212,255,.3);}

/* ── Supabase badge (shows if persistence active) ── */
#sbadge{position:absolute;bottom:56px;right:20px;
  opacity:0;animation:fi .5s ease 6.8s forwards;
  font-size:8px;letter-spacing:.14em;text-transform:uppercase;
  color:rgba(0,229,160,.5);display:flex;align-items:center;gap:5px;}
</style>
</head>
<body>
<div id="gi">
  <canvas id="c-bg"></canvas>
  <canvas id="c-globe"></canvas>
  <canvas id="c-fx"></canvas>
  <div id="c-vig"></div>
  <div id="c-scan"></div>

  <!-- HUD: top-left -->
  <div class="hud" id="tl">
    <div class="hbox"><div class="bc"></div>
      <div class="hl">SYSTEM STATUS</div>
      <div class="hv" style="color:#00e5a0">OPERATIONAL</div>
      <div class="hl" id="utc">UTC 00:00:00</div>
    </div>
  </div>

  <!-- HUD: top-right — updated feed count -->
  <div class="hud" id="tr">
    <div class="hbox"><div class="bc"></div>
      <div class="hl">LIVE FEEDS</div>
      <div class="hv" style="color:#00e5a0">25+ SOURCES ACTIVE</div>
      <div class="hl">GDELT &middot; USGS &middot; ACLED &middot; OPENSKY &middot; AIS</div>
    </div>
  </div>

  <!-- HUD: bottom-left — updated theatres -->
  <div class="hud" id="bl">
    <div class="hbox"><div class="bc"></div>
      <div class="hl">ACTIVE THEATRES</div>
      <div class="hv" style="color:#ff2d55">UKRAINE &middot; GAZA &middot; IRAN</div>
      <div class="hv" style="color:#f0a500">SUDAN &middot; MYANMAR &middot; PAK-AFG</div>
      <div class="hv" style="color:rgba(0,212,255,.6)">HAITI</div>
    </div>
  </div>

  <!-- HUD: bottom-right — persistence status -->
  <div class="hud" id="br">
    <div class="hbox"><div class="bc"></div>
      <div class="hl">PERSISTENCE</div>
      <div class="hv" id="persist-status" style="color:#00e5a0">SUPABASE ACTIVE</div>
      <div class="hl">ACLED &middot; AIS &middot; SEISMIC &middot; GDELT</div>
    </div>
  </div>

  <!-- Centre: threat level -->
  <div id="thrbar">
    <div class="tl">GLOBAL THREAT</div>
    <div class="tb" id="tb"></div>
    <div class="tl" style="color:#f0a500;font-weight:700;letter-spacing:.1em">ELEVATED</div>
  </div>

  <!-- Live counters row -->
  <div id="live-ct">
    <div class="lct"><span class="lct-dot" style="background:#00d4ff"></span>AIS VESSELS LIVE</div>
    <div class="lct"><span class="lct-dot" style="background:#f0a500;animation-delay:.4s"></span>OPENSKY AIRSPACE</div>
    <div class="lct"><span class="lct-dot" style="background:#ff2d55;animation-delay:.8s"></span>SIGINT ACTIVE</div>
  </div>

  <!-- Boot flash -->
  <div id="p1">
    <div class="cbar"></div>
    <div class="cline">&#x25BC; INITIALISING GLOBAL INTELLIGENCE FEED &#x25BC;</div>
    <div class="cline" style="color:rgba(255,45,85,.5);font-size:clamp(6px,.9vw,9px);margin-top:3px">
      AUTHORISED ACCESS ONLY &nbsp;/&nbsp; ALL ACTIVITY LOGGED
    </div>
    <div class="cbar"></div>
  </div>

  <!-- Main -->
  <div id="p2">
    <div id="lw">
      <div id="logo">THE&nbsp;GEO&#8209;<em>LOCATOR</em></div>
      <div id="sub">Global Intelligence Operations Center</div>
      <div id="ver">v8 &nbsp;&middot;&nbsp; 8 TABS &nbsp;&middot;&nbsp; 37 MAP LAYERS &nbsp;&middot;&nbsp; 22 LIVE FEEDS</div>
    </div>
    <div id="divl"></div>
    <!-- Feature chips replacing chess board -->
    <div id="chips">
      <span class="chip ch-c">&#9876; Conflict Dashboard</span>
      <span class="chip ch-s">&#128251; SIGINT</span>
      <span class="chip ch-e">&#128202; Economic &amp; Markets</span>
      <span class="chip ch-i">&#128752; Intel Dashboard</span>
      <span class="chip ch-g">&#127758; Earth Signals</span>
      <span class="chip ch-c">&#9876; ACLED Live Events</span>
      <span class="chip ch-i">&#128674; AIS Vessel Tracking</span>
      <span class="chip ch-s">&#9992; OpenSky Airspace</span>
      <span class="chip ch-e">&#128196; SitRep Export</span>
      <span class="chip ch-g">&#128225; Live News</span>
      <span class="chip ch-i">&#128278; Supabase Persistence</span>
      <span class="chip ch-c">61 Military Bases</span>
      <span class="chip ch-s">37 Nuclear Sites</span>
      <span class="chip ch-e">&#127829; Pizza Index</span>
    </div>
  </div>

  <!-- Ticker: updated headlines -->
  <div id="tick">
    <div class="tlbl">&#9679;&nbsp;LIVE</div>
    <div style="overflow:hidden;flex:1;height:100%;display:flex;align-items:center;padding-left:80px">
      <div class="tks">
        &#x25C6;&nbsp;UKRAINE: Russian missile salvo targets Kyiv energy grid &mdash; 12 casualties &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;IRAN: IDF destroys Fordow enrichment complex &mdash; IAEA access lost &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;GAZA: IDF operations in Rafah continue &mdash; aid corridor blocked &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;PAK-AFG: PAF airstrikes in Paktika &mdash; TTP cross-border attack KPK &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;SUDAN: RSF advancing North Darfur &mdash; famine declared 5 regions &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;RED SEA: Houthi anti-ship drone intercepted 40nm from Bab el-Mandeb &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;AIS: 3 tankers transiting dark through Hormuz &mdash; AIS off &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;SIGINT: GPS jamming active Eastern Baltic &mdash; Russia source &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;MARKETS: Brent +2.1% &mdash; Hormuz closure risk premium elevated &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;OPENSKY: Military callsign REAPER tracked over Mediterranean &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;HAITI: Viv Ansanm controls 85% Port-au-Prince &mdash; MSS mission under-resourced &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;UKRAINE: Russian missile salvo targets Kyiv energy grid &mdash; 12 casualties &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;IRAN: IDF destroys Fordow enrichment complex &mdash; IAEA access lost &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;GAZA: IDF operations in Rafah continue &mdash; aid corridor blocked &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;PAK-AFG: PAF airstrikes in Paktika &mdash; TTP cross-border attack KPK &nbsp;&nbsp;&nbsp;
        &#x25C6;&nbsp;SUDAN: RSF advancing North Darfur &mdash; famine declared 5 regions &nbsp;&nbsp;&nbsp;
      </div>
    </div>
  </div>

  <button id="skip" onclick="geoSkip()">SKIP &rsaquo;</button>
  <div id="prog"></div>
</div>

<script>
(function(){
// ── Resize ────────────────────────────────────────────────────
var bgC=document.getElementById('c-bg'),
    gbC=document.getElementById('c-globe'),
    fxC=document.getElementById('c-fx');
var bgX=bgC.getContext('2d'),
    gbX=gbC.getContext('2d'),
    fxX=fxC.getContext('2d');
var W=window.innerWidth,H=window.innerHeight;
function resize(){
  W=window.innerWidth;H=window.innerHeight;
  bgC.width=gbC.width=fxC.width=W;
  bgC.height=gbC.height=fxC.height=H;
}
resize();window.addEventListener('resize',resize);

// ── UTC clock ─────────────────────────────────────────────────
function ck(){
  var n=new Date(),el=document.getElementById('utc');
  if(el)el.textContent='UTC '
    +String(n.getUTCHours()).padStart(2,'0')+':'
    +String(n.getUTCMinutes()).padStart(2,'0')+':'
    +String(n.getUTCSeconds()).padStart(2,'0');
}
ck();setInterval(ck,1000);

// ── Threat blocks (7/8 lit = ELEVATED) ───────────────────────
var tlC=['#00e5a0','#00e5a0','#f0a500','#f0a500','#f0a500','#ff2d55','#ff2d55'];
var tbEl=document.getElementById('tb');
for(var i=0;i<8;i++){
  var b=document.createElement('span');
  b.className=i<7?'on':'';
  b.style.background=i<7?tlC[Math.min(i,6)]:'rgba(255,255,255,.06)';
  if(i<7)b.style.animationDelay=(i*.11)+'s';
  tbEl.appendChild(b);
}

// ── Hotspots: 7 active theatres ───────────────────────────────
var hss=[
  {nx:.455,ny:.395,col:'#ff2d55',lb:'UKR'},   // Ukraine
  {nx:.548,ny:.458,col:'#ff2d55',lb:'GAZ'},   // Gaza
  {nx:.586,ny:.472,col:'#f0a500',lb:'IRN'},   // Iran
  {nx:.432,ny:.572,col:'#f0a500',lb:'SUD'},   // Sudan
  {nx:.726,ny:.516,col:'#f0a500',lb:'MMR'},   // Myanmar
  {nx:.632,ny:.465,col:'#a855f7',lb:'PAK'},   // Pakistan-Afghanistan
  {nx:.285,ny:.478,col:'#00d4ff',lb:'HTI'},   // Haiti
];

// ── Particles ────────────────────────────────────────────────
var pts=[];
for(var i=0;i<180;i++)pts.push({
  x:Math.random()*1920,y:Math.random()*1080,
  vx:(Math.random()-.5)*.38,vy:(Math.random()-.5)*.38,
  r:Math.random()*1.4+.2,warm:Math.random()>.72,
  ph:Math.random()*Math.PI*2
});

// ── Globe renderer ────────────────────────────────────────────
var gRot=0,gTilt=18*Math.PI/180;
function ll(lat,lon,r,cx,cy){
  var la=lat*Math.PI/180,lo=(lon+gRot*180/Math.PI)*Math.PI/180;
  var x=r*Math.cos(la)*Math.sin(lo);
  var y=r*(Math.sin(la)*Math.cos(gTilt)-Math.cos(la)*Math.cos(lo)*Math.sin(gTilt));
  var z=Math.cos(la)*Math.cos(lo)*Math.cos(gTilt)+Math.sin(la)*Math.sin(gTilt);
  return{x:cx+x,y:cy-y,z:z};
}

function drawGlobe(){
  gbX.clearRect(0,0,W,H);
  var cx=W*.5,cy=H*.5,r=Math.min(W,H)*.26;
  // Atmosphere glow
  var ag=gbX.createRadialGradient(cx,cy,r*.7,cx,cy,r*1.14);
  ag.addColorStop(0,'rgba(0,212,255,0)');
  ag.addColorStop(.7,'rgba(0,212,255,.02)');
  ag.addColorStop(1,'rgba(0,212,255,.09)');
  gbX.beginPath();gbX.arc(cx,cy,r*1.14,0,Math.PI*2);gbX.fillStyle=ag;gbX.fill();
  // Latitude lines
  for(var lat=-75;lat<=75;lat+=15){
    var pp=[];for(var lo=-180;lo<=180;lo+=3)pp.push(ll(lat,lo,r,cx,cy));
    gbX.beginPath();var go=false;
    for(var k=0;k<pp.length;k++){
      if(pp[k].z<0){go=false;continue;}
      if(!go){gbX.moveTo(pp[k].x,pp[k].y);go=true;}
      else gbX.lineTo(pp[k].x,pp[k].y);
    }
    gbX.strokeStyle=lat===0?'rgba(0,212,255,.22)':'rgba(0,212,255,.07)';
    gbX.lineWidth=lat===0?1.2:.5;gbX.stroke();
  }
  // Longitude lines
  for(var lo2=-180;lo2<180;lo2+=20){
    var pp2=[];for(var la2=-90;la2<=90;la2+=3)pp2.push(ll(la2,lo2,r,cx,cy));
    gbX.beginPath();var go2=false;
    for(var k=0;k<pp2.length;k++){
      if(pp2[k].z<0){go2=false;continue;}
      if(!go2){gbX.moveTo(pp2[k].x,pp2[k].y);go2=true;}
      else gbX.lineTo(pp2[k].x,pp2[k].y);
    }
    gbX.strokeStyle='rgba(0,212,255,.04)';gbX.lineWidth=.4;gbX.stroke();
  }
  // Equator highlight
  gbX.beginPath();gbX.arc(cx,cy,r,0,Math.PI*2);
  gbX.strokeStyle='rgba(0,212,255,.18)';gbX.lineWidth=1;gbX.stroke();
  // Hotspot pulses
  var now=Date.now();
  hss.forEach(function(h){
    var gla=(0.5-h.ny)*135,glo=(h.nx-0.5)*310;
    var p=ll(gla,glo,r,cx,cy);if(p.z<.05)return;
    var pulse=(Math.sin(now*.0028+h.nx*8)+1)*.5;
    var hx=h.col.replace('#','');
    var rc=parseInt(hx.slice(0,2),16),
        gc=parseInt(hx.slice(2,4),16),
        bc=parseInt(hx.slice(4,6),16);
    // Outer ring
    gbX.beginPath();gbX.arc(p.x,p.y,7+pulse*8,0,Math.PI*2);
    gbX.strokeStyle='rgba('+rc+','+gc+','+bc+','+(0.28*(1-pulse))+')';
    gbX.lineWidth=1;gbX.stroke();
    // Dot
    gbX.beginPath();gbX.arc(p.x,p.y,2.8,0,Math.PI*2);
    gbX.fillStyle=h.col;gbX.fill();
    // Label
    gbX.font='500 '+Math.round(W*.006+6)+'px "IBM Plex Mono",monospace';
    gbX.fillStyle='rgba(194,212,238,.65)';
    gbX.fillText(h.lb,p.x+7,p.y-4);
  });
}

// ── FX (orbit ring + sweep) ───────────────────────────────────
function drawFX(){
  fxX.clearRect(0,0,W,H);
  var cx=W*.5,cy=H*.5,r=Math.min(W,H)*.26,now=Date.now();
  // Sweep arc
  var ang=(now/4400)*Math.PI*2;
  fxX.save();fxX.beginPath();fxX.moveTo(cx,cy);
  fxX.arc(cx,cy,r,ang-.6,ang);fxX.closePath();
  var rg=fxX.createRadialGradient(cx,cy,0,cx,cy,r);
  rg.addColorStop(0,'rgba(0,212,255,0)');
  rg.addColorStop(.5,'rgba(0,212,255,.03)');
  rg.addColorStop(1,'rgba(0,212,255,.1)');
  fxX.fillStyle=rg;fxX.fill();fxX.restore();
  // Sweep line
  fxX.beginPath();fxX.moveTo(cx,cy);
  fxX.lineTo(cx+Math.cos(ang)*r,cy+Math.sin(ang)*r);
  fxX.strokeStyle='rgba(0,212,255,.3)';fxX.lineWidth=1.2;fxX.stroke();
  // Orbit ellipses — represent AIS and OpenSky orbits
  fxX.beginPath();
  fxX.ellipse(cx,cy,r*1.22,r*1.22*.28,now/8800,0,Math.PI*2);
  fxX.strokeStyle='rgba(240,165,0,.1)';fxX.lineWidth=1;fxX.stroke();
  fxX.beginPath();
  fxX.ellipse(cx,cy,r*1.42,r*1.42*.2,-now/13500,0,Math.PI*2);
  fxX.strokeStyle='rgba(0,212,255,.055)';fxX.lineWidth=.7;fxX.stroke();
  // AIS vessel dot on orbit (amber)
  var sa=now/8800,sx=cx+Math.cos(sa)*r*1.22,sy=cy+Math.sin(sa)*r*1.22*.28;
  fxX.beginPath();fxX.arc(sx,sy,3.5,0,Math.PI*2);fxX.fillStyle='#f0a500';fxX.fill();
  for(var t=1;t<=5;t++){
    var ta=sa-t*.045,tx=cx+Math.cos(ta)*r*1.22,ty=cy+Math.sin(ta)*r*1.22*.28;
    fxX.beginPath();fxX.arc(tx,ty,3.5-t*.5,0,Math.PI*2);
    fxX.fillStyle='rgba(240,165,0,'+(0.5-t*.09)+')';fxX.fill();
  }
  // OpenSky aircraft dot on outer orbit (cyan)
  var sA2=now/13500,sx2=cx+Math.cos(-sA2)*r*1.42,sy2=cy+Math.sin(-sA2)*r*1.42*.2;
  fxX.beginPath();fxX.arc(sx2,sy2,3,0,Math.PI*2);fxX.fillStyle='#00d4ff';fxX.fill();
  // Conflict arc lines to globe centre
  var sA=now*.00085;
  hss.forEach(function(h,idx){
    var ph=(sA+idx*1.05)%(Math.PI*2);if(ph>Math.PI)return;
    var pg=ph/Math.PI,hx2=h.nx*W,hy2=h.ny*H;
    var mx=(hx2+cx)*.5+18*Math.sin(idx*1.3),my=(hy2+cy)*.5-48;
    fxX.beginPath();fxX.moveTo(hx2,hy2);
    fxX.quadraticCurveTo(mx,my,hx2+(cx-hx2)*pg,hy2+(cy-hy2)*pg);
    var hxc=h.col.replace('#','');
    fxX.strokeStyle='rgba('+parseInt(hxc.slice(0,2),16)+','+parseInt(hxc.slice(2,4),16)+','+parseInt(hxc.slice(4,6),16)+','+(Math.sin(pg*Math.PI)*.24)+')';
    fxX.lineWidth=.9;fxX.stroke();
  });
}

// ── Background grid + particles ───────────────────────────────
function drawBG(){
  bgX.clearRect(0,0,W,H);var now=Date.now();
  for(var gx=0;gx<W;gx+=60)for(var gy=0;gy<H;gy+=60){
    var p=Math.sin(now*.0005+gx*.016+gy*.013)*.5+.5;
    bgX.globalAlpha=.018+p*.032;bgX.fillStyle='#00d4ff';
    bgX.fillRect(gx,gy,1,1);
  }
  bgX.globalAlpha=1;
  var sx=W/1920,sy=H/1080;
  for(var i=0;i<pts.length;i++){
    var pt=pts[i];
    pt.x+=pt.vx;pt.y+=pt.vy;
    if(pt.x<0)pt.x=1920;if(pt.x>1920)pt.x=0;
    if(pt.y<0)pt.y=1080;if(pt.y>1080)pt.y=0;
    pt.ph+=.025;var pa=.17+Math.sin(pt.ph)*.11;
    bgX.beginPath();bgX.arc(pt.x*sx,pt.y*sy,pt.r,0,Math.PI*2);
    bgX.fillStyle=pt.warm?'rgba(240,165,0,'+pa+')':'rgba(0,212,255,'+pa+')';
    bgX.fill();
    for(var j=i+1;j<pts.length;j++){
      var dx=(pt.x-pts[j].x)*sx,dy=(pt.y-pts[j].y)*sy,d=Math.sqrt(dx*dx+dy*dy);
      if(d<78){
        bgX.beginPath();bgX.moveTo(pt.x*sx,pt.y*sy);bgX.lineTo(pts[j].x*sx,pts[j].y*sy);
        bgX.strokeStyle='rgba(0,212,255,'+(0.045*(1-d/78))+')';bgX.lineWidth=.4;bgX.stroke();
      }
    }
  }
}

// ── Main loop ─────────────────────────────────────────────────
function render(){gRot+=.0016;drawBG();drawGlobe();drawFX();requestAnimationFrame(render);}
render();

// ── Skip ──────────────────────────────────────────────────────
window.geoSkip=function(){
  var ov=document.getElementById('gi');
  if(ov){ov.style.transition='opacity .6s ease';ov.style.opacity='0';
    setTimeout(function(){ov.style.display='none';},650);}
};
})();
</script>
</body></html>""", height=700, scrolling=False)

    _it.sleep(3)
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
_d_eq   = len(eq_df) - st.session_state.get("prev_eq_count", len(eq_df))
_d_conf = active_conf - st.session_state.get("prev_active_conf", active_conf)
st.session_state["prev_eq_count"]    = len(eq_df)
st.session_state["prev_active_conf"] = active_conf
with c1: st.metric("Active Conflicts", active_conf,      delta=f"{_d_conf:+d} this cycle" if _d_conf else "LIVE")
with c2: st.metric("Total Casualties", f"{total_cas:,}", delta="All theatres")
with c3: st.metric("Seismic (24h)",    len(eq_df),       delta=f"{_d_eq:+d} new · M5+: {len(m5p)}")
with c4: st.metric("Civil Movements",  len(MOVEMENTS),   delta=f"Critical: {len(crit_mv)}")
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
# GLOBAL MAP  — v8.2: replaced the pydeck deck.gl multi-layer map with a
# Cobe WebGL rotating globe. Cobe has no built-in tooltip/click-picking or
# per-layer system, so this trades the old 37-layer interactive map for a
# simpler always-live visual: markers are assembled fresh from whichever
# categories are toggled on, and re-rendered every time the page reruns.
# ─────────────────────────────────────────────
total_inc     = sum(len(c["incidents"]) for c in CONFLICTS.values())
crit_inc_cnt  = sum(1 for c in CONFLICTS.values() for i in c["incidents"] if i["severity"]=="CRITICAL")
hist_crit     = sum(1 for e in HISTORICAL_EVENTS if e["severity"]=="CRITICAL")

def _build_globe_markers():
    """
    Assemble every toggled-on layer into one flat list of colored points for
    the globe. Cobe's native marker system only supports a single global
    markerColor, so per-layer color here is carried as an extra "color" field
    and drawn via a custom 2D projection overlay (see the JS below) rather
    than Cobe's built-in marker renderer.

    Line/path-shaped datasets (cables, pipelines, trade routes, displacement
    flows, strategic waterways, ship lanes, supply arcs) don't have a native
    "line" primitive on the globe either — they're represented as their
    endpoint(s) rather than a true connecting arc. That's a real fidelity
    trade-off versus the old pydeck PathLayer/ArcLayer rendering.
    """
    M = []
    def pt(lat, lon, color, size, title="", layer="", body=""):
        # `title` = short headline shown on the sticky note's header.
        # `layer` = category badge (e.g. "Military Base") shown on the note.
        # `body`  = the fuller detail text — reuses each dataset's own
        #           pre-authored `tip` field where one exists, since those
        #           are already well-formatted single-line summaries.
        M.append({"lat": float(lat), "lon": float(lon), "size": size, "color": color,
                   "title": title, "layer": layer, "body": body})

    # ── Core Layers ──────────────────────────────────────────
    if show_seis and not eq_df.empty:
        for _, r in eq_df.iterrows():
            sz = min(0.022 + float(r.get("mag", 0)) * 0.013, 0.11)
            pt(r["lat"], r["lon"], [0,200,255], sz, f"M{r.get('mag','?')} {r.get('place','')}", "Seismic Event",
               f"Magnitude {r.get('mag','?')} · Depth {r.get('depth_km','?')} km · {r.get('time','')}")
    if show_volc and not eonet_df.empty:
        for _, r in eonet_df.iterrows():
            pt(r["lat"], r["lon"], [255,140,60], 0.032, r.get("title","EONET event"), "Volcanic / EONET",
               f"Category: {r.get('cat','')}")
    if show_conf:
        for c in CONFLICTS.values():
            for i in c.get("incidents", []):
                sz = 0.055 if i.get("severity") == "CRITICAL" else 0.035
                pt(i["lat"], i["lon"], [255,60,80], sz, i.get("title",""), "Conflict Incident",
                   f"Severity: {i.get('severity','')} · {i.get('date','')} · Casualties: {i.get('casualties','?')}")
    if show_mvmt:
        for m in MOVEMENTS:
            if m.get("type") == "protest":
                pt(m["lat"], m["lon"], [180,80,255], 0.03 + m.get("scale",50)/100*0.03, m.get("title",""), "Civil Movement",
                   f"{m.get('country','')} · Size: {m.get('size','')} · Sentiment: {m.get('sentiment','')}")
    if show_supp:
        # Proxy for the old ArcLayer: plot supplier-nation origin points for
        # each critical conflict zone rather than a true connecting arc.
        _suppliers = [("USA",38.9,-77.0),("UK",51.5,-0.1),("Russia",55.75,37.61),("Iran",35.7,51.4)]
        for z in CONFLICT_ZONES:
            if z.get("intensity") == "Critical":
                for name, slat, slon in _suppliers[:2]:
                    pt(slat, slon, [255,215,0], 0.025, f"Supply origin: {name}", "Supply Arc",
                       f"Destination: {z.get('name','')}")
    if show_heat and not eq_df.empty:
        for _, r in eq_df.iterrows():
            pt(r["lat"], r["lon"], [255,90,0], 0.02, "Seismic density", "Seismic Heatmap",
               f"M{r.get('mag','?')} at {r.get('place','')}")
    if show_hist:
        for e in _HIST_SORTED[:40]:
            sz = 0.06 if e.get("severity") == "CRITICAL" else 0.032
            pt(e["lat"], e["lon"], [255,190,60], sz, e.get("title",""), "Historical Event",
               f"{e.get('date','')} · Severity: {e.get('severity','')}")
    if show_live:
        try:
            import random as _rnd
            _rng = _rnd.Random(42)
            _hotspots = [(32.08,34.78),(50.45,30.52),(31.4,34.47),(35.69,51.39),(15.55,32.53),
                         (16.87,96.19),(14.5,43.5),(39.9,116.4),(38.9,-77.0)]
            for i, art in enumerate(fetch_live_global_events(max_records=20)):
                blat, blon = _hotspots[i % len(_hotspots)]
                pt(blat + _rng.uniform(-2,2), blon + _rng.uniform(-2,2), [0,255,200], 0.028,
                   art.get('title',''), "Live Event (GDELT)", f"Source: {art.get('source','?')} · {art.get('time','')}")
        except Exception as _e:
            _log.warning("show_live globe layer failed: %s", _e)

    # ── Intelligence ─────────────────────────────────────────
    if show_intel:
        for h in INTEL_HOTSPOTS:
            pt(h["lat"], h["lon"], [255,225,120], 0.03, h.get("name",""), "Intel Hotspot",
               h.get("tip", f"Type: {h.get('type','')} · Risk: {h.get('risk','')}"))
    if show_czones:
        for z in CONFLICT_ZONES:
            pt(z["lat"], z["lon"], [255,80,80], 0.045, z.get("name",""), "Conflict Zone",
               z.get("tip", f"Status: {z.get('status','')} · Intensity: {z.get('intensity','')}"))
    if show_mbases:
        for b in MILITARY_BASES:
            pt(b["lat"], b["lon"], [120,170,255], 0.028, b.get("name",""), "Military Base",
               b.get("tip", f"{b.get('country','')} · {b.get('type','')}"))
    if show_nuclear:
        for n in NUCLEAR_SITES:
            pt(n["lat"], n["lon"], [255,235,59], 0.04, n.get("name",""), "Nuclear Site",
               n.get("tip", f"{n.get('country','')} · {n.get('type','')} · {n.get('status','')}"))
    if show_gamma:
        for g in GAMMA_IRRADIATORS:
            pt(g["lat"], g["lon"], [255,140,0], 0.025, g.get("name",""), "Gamma Irradiator",
               g.get("tip", f"{g.get('country','')} · {g.get('type','')}"))
    if show_cyber:
        try:
            _cyber_src = fetch_live_cyber_threats() or CYBER_THREATS_GEO
        except Exception:
            _cyber_src = CYBER_THREATS_GEO
        for c in _cyber_src:
            pt(c["lat"], c["lon"], [255,60,180], 0.035, c.get("name",""), "Cyber Threat Actor",
               c.get("tip", f"Actor: {c.get('actor','')} · Targets: {c.get('targets','')}"))
    if show_orbital:
        for o in ORBITAL_SURVEILLANCE:
            pt(o["lat"], o["lon"], [140,140,255], 0.025, o.get("name",""), "Orbital Surveillance",
               o.get("tip", f"Operator: {o.get('operator','')} · {o.get('type','')}"))
    if show_gps:
        for g in GPS_JAMMING_ZONES:
            pt(g["lat"], g["lon"], [255,200,0], 0.04, g.get("name",""), "GPS Jamming Zone",
               g.get("tip", f"Source: {g.get('source','')} · Severity: {g.get('severity','')} · Radius: {g.get('radius_km','?')} km"))
    if show_cii:
        for c in CII_INSTABILITY:
            pt(c["lat"], c["lon"], [255,100,100], 0.03, c.get("name",""), "CII Instability",
               c.get("tip", f"{c.get('country','')} · {c.get('sector','')} · Risk: {c.get('risk','')}"))

    # ── Infrastructure ───────────────────────────────────────
    if show_space:
        for s in SPACEPORTS:
            pt(s["lat"], s["lon"], [0,229,255], 0.03, s.get("name",""), "Spaceport",
               s.get("tip", f"{s.get('country','')} · {s.get('type','')} · Active: {s.get('active','')}"))
    if show_cables:
        for c in UNDERSEA_CABLES:
            body = c.get("tip", f"Status: {c.get('status','')} · Risk: {c.get('risk','')}")
            pt(c["from_lat"], c["from_lon"], [0,150,255], 0.022, c.get("name",""), "Undersea Cable", body)
            pt(c["to_lat"],   c["to_lon"],   [0,150,255], 0.022, c.get("name",""), "Undersea Cable", body)
    if show_pipes:
        for p in PIPELINES:
            body = f"Status: {p.get('status','')} · Risk: {p.get('risk','')}"
            pt(p["from_lat"], p["from_lon"], [255,110,0], 0.022, p.get("name",""), "Pipeline", body)
            pt(p["to_lat"],   p["to_lon"],   [255,110,0], 0.022, p.get("name",""), "Pipeline", body)
    if show_aidc:
        for a in AI_DATA_CENTERS:
            pt(a["lat"], a["lon"], [0,255,150], 0.028, a.get("name",""), "AI Data Center",
               a.get("tip", f"Operator: {a.get('operator','')}"))
    if show_outages:
        for o in INTERNET_OUTAGES:
            pt(o["lat"], o["lon"], [160,160,160], 0.035, o.get("name",""), "Internet Outage",
               o.get("tip", f"Severity: {o.get('severity','')} · Cause: {o.get('cause','')}"))
    if show_econ:
        for e in ECONOMIC_CENTERS:
            pt(e["lat"], e["lon"], [0,230,120], 0.03, e.get("name",""), "Economic Center",
               e.get("tip", f"GDP: ${e.get('gdp_t','?')}T · Role: {e.get('role','')}"))

    # ── Military & Traffic ───────────────────────────────────
    if show_milact:
        for m in MILITARY_ACTIVITY:
            pt(m["lat"], m["lon"], [255,90,0], 0.035, m.get("name",""), "Military Activity",
               m.get("tip", f"{m.get('type','')} · {m.get('country','')}"))
    if show_ships:
        for s in SHIP_TRAFFIC_ZONES:
            pt(s["lat"], s["lon"], [0,180,255], 0.035, s.get("name",""), "Ship Traffic Zone",
               s.get("tip", f"Traffic: {s.get('traffic','')} · {s.get('vessels_day','?')} vessels/day"))
    if show_trade:
        for t in TRADE_ROUTE_ARCS:
            body = t.get("tip", f"{t.get('type','')} · Status: {t.get('status','')}")
            pt(t["from_lat"], t["from_lon"], [255,190,0], 0.022, t.get("name",""), "Trade Route", body)
            pt(t["to_lat"],   t["to_lon"],   [255,190,0], 0.022, t.get("name",""), "Trade Route", body)
    if show_aviation:
        for name, alat, alon, status in [
            ("Tel Aviv Ben Gurion",32.01,34.89,"Operating with intermittent alerts"),
            ("Kyiv Boryspil",50.34,30.90,"Closed — active conflict airspace"),
            ("Tehran Imam Khomeini",35.42,51.15,"Operating with restrictions"),
            ("Beirut–Rafic Hariri",33.82,35.49,"Operating with intermittent alerts"),
            ("Khartoum Intl",15.59,32.55,"Closed — active conflict zone"),
        ]:
            pt(alat, alon, [180,220,255], 0.03, name, "Aviation Status", status)
    if show_waterways:
        for w in STRATEGIC_WATERWAYS:
            pt(w["lat"], w["lon"], [0,210,220], 0.04, w.get("name",""), "Strategic Waterway",
               w.get("tip", f"Status: {w.get('status','')}"))

    # ── Live Intelligence ─────────────────────────────────────
    if show_ais:
        try:
            for v in fetch_ais_vessels():
                pt(v["lat"], v["lon"], [0,220,255], 0.02, v.get("name",""), "AIS Vessel (Live)",
                   f"Type: {v.get('type','')} · Speed: {v.get('speed','?')} kn")
        except Exception as _e:
            _log.warning("show_ais globe layer failed: %s", _e)
    if show_opensky:
        try:
            for f in fetch_opensky_flights():
                pt(f["lat"], f["lon"], [200,255,0], 0.018, f.get("callsign", f.get("name","")), "OpenSky Flight (Live)",
                   f"Altitude: {f.get('altitude','?')} · Speed: {f.get('speed','?')}")
        except Exception as _e:
            _log.warning("show_opensky globe layer failed: %s", _e)
    if show_acled:
        try:
            for a in fetch_acled_events(limit=80):
                pt(a["lat"], a["lon"], [255,60,60], 0.03, a.get("event_type",""), "ACLED Event (Live)",
                   f"Fatalities: {a.get('fatalities','?')} · {a.get('date','')}")
        except Exception as _e:
            _log.warning("show_acled globe layer failed: %s", _e)

    # ── Human & Social ────────────────────────────────────────
    if show_protests:
        for m in MOVEMENTS:
            pt(m["lat"], m["lon"], [200,90,255], 0.03 + m.get("scale",50)/100*0.03, m.get("title",""), "Protest",
               f"{m.get('country','')} · Sentiment: {m.get('sentiment','')} · Size: {m.get('size','')}")
    if show_displaced:
        for d in DISPLACEMENT_FLOWS:
            body = d.get("tip", f"Population: {d.get('pop','?')} · Cause: {d.get('cause','')}")
            pt(d["from_lat"], d["from_lon"], [255,150,180], 0.022, d.get("cause",""), "Displacement Flow", body)
            pt(d["to_lat"],   d["to_lon"],   [255,150,180], 0.022, d.get("cause",""), "Displacement Flow", body)
    if show_minerals:
        for c in CRITICAL_MINERALS:
            pt(c["lat"], c["lon"], [0,255,190], 0.032, c.get("name",""), "Critical Mineral",
               c.get("tip", f"Mineral: {c.get('mineral','')} · Global share: {c.get('share_pct','?')}%"))

    # ── Natural & Climate ─────────────────────────────────────
    if show_fires_layer and not eonet_df.empty and "cat" in eonet_df.columns:
        for _, r in eonet_df[eonet_df["cat"].str.contains("wildfire", case=False, na=False)].iterrows():
            pt(r["lat"], r["lon"], [255,60,20], 0.03, r.get("title",""), "Active Fire", "Live NASA EONET wildfire event")
    if show_climate:
        for c in CLIMATE_ANOMALIES:
            pt(c["lat"], c["lon"], [120,200,255], 0.032, c.get("name",""), "Climate Anomaly",
               c.get("tip", f"Type: {c.get('type','')} · Anomaly: {c.get('anomaly','')}"))
    if show_weather:
        for w in WEATHER_ALERTS:
            pt(w["lat"], w["lon"], [255,220,50], 0.032, w.get("name",""), "Weather Alert",
               w.get("tip", f"Type: {w.get('type','')} · Severity: {w.get('severity','')}"))

    return M

_globe_markers = _build_globe_markers()

_dot = lambda c: f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{c};margin-right:4px"></span>'
st.markdown(f"""
<div class="map-top-bar">
  <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
    <div class="map-title-text">🌐 GLOBAL COMMAND GLOBE</div>
    <div style="font-family:var(--fm);font-size:10px;color:var(--muted)">
      Drag to rotate · hover a marker for a preview · click to pin a sticky note · {len(_globe_markers)} markers from {len(HISTORICAL_EVENTS)} historical events since 2022 · Toggle categories in sidebar
    </div>
  </div>
  <div class="map-legend">
    <span style="margin-left:6px;padding-left:6px;border-left:1px solid rgba(0,200,255,.15)">
      <span class="pulse p-red"></span>{crit_inc_cnt} CRITICAL
    </span>
    <span><span class="pulse p-cyan"></span>{len(eq_df)} seismic</span>
    <span><span class="pulse p-orange"></span>{total_inc} incidents</span>
    <span><span class="pulse p-amber"></span>{hist_crit} hist.critical</span>
    <span class="live-badge"><span class="pulse p-red" style="margin-right:3px"></span>LIVE</span>
  </div>
</div>""", unsafe_allow_html=True)

_globe_markers_json = json.dumps(_globe_markers)
_globe_html = f"""
<div style="position:relative;border:1px solid rgba(0,200,255,.12);border-top:none;border-radius:0 0 14px 14px;
            overflow:hidden;margin-bottom:8px;background:#050a12;">
  <div style="display:flex;justify-content:center;">
    <div style="position:relative;width:100%;max-width:560px;aspect-ratio:1;">
      <canvas id="cobeGlobe"   style="position:absolute;inset:0;width:100%;height:100%;cursor:grab"></canvas>
      <canvas id="cobeOverlay" style="position:absolute;inset:0;width:100%;height:100%"></canvas>
      <div id="cobeTooltip" style="position:absolute;display:none;pointer-events:none;z-index:5;
           background:rgba(5,10,18,.96);border:1px solid rgba(0,200,255,.35);border-radius:6px;
           padding:5px 9px;font-family:monospace;font-size:10.5px;color:#dce8f5;max-width:230px;
           white-space:pre-wrap;box-shadow:0 4px 14px rgba(0,0,0,.5)"></div>
    </div>
  </div>
  <div id="stickyBar" style="display:flex;align-items:center;justify-content:space-between;gap:8px;
       padding:6px 12px;border-top:1px solid rgba(0,200,255,.1);font-family:monospace;font-size:9.5px;color:#5a7a95">
    <span>📌 Click a marker to pin its details below</span>
    <span id="stickyCount" style="display:none;cursor:pointer;color:#00d4ff" onclick="window.__clearStickyNotes && window.__clearStickyNotes()">Clear all ✕</span>
  </div>
  <div id="stickyNotes" style="display:flex;flex-wrap:wrap;gap:10px;padding:4px 12px 14px;
       max-height:260px;overflow-y:auto"></div>
</div>
<script type="module">
  import createGlobe from "https://esm.sh/cobe@0.6.3";

  const canvas   = document.getElementById("cobeGlobe");
  const overlay  = document.getElementById("cobeOverlay");
  const tooltip  = document.getElementById("cobeTooltip");
  const notesEl  = document.getElementById("stickyNotes");
  const countEl  = document.getElementById("stickyCount");
  const octx     = overlay.getContext("2d");
  let phi = 0;
  const theta = 0.24;
  let width = 0;
  let pointerInteracting = null;
  let pointerInteractionMovement = 0;
  let lastProjected = [];   // {{x, y, r, title, layer, body, color, id}} for hit-testing
  let hoverPt = null;
  let downInfo = null;      // {{x, y, t}} — used to tell a click from a drag
  const openNotes = new Set();   // ids of currently-pinned sticky notes (no duplicates)

  // Rotating cycle of sticky-note paper tints so pinned notes don't all
  // look identical, independent of each marker's own layer color (which
  // is still used for the note's left accent bar / category dot).
  const paperTints = ["#fef3c7","#fde2e2","#dbeafe","#dcfce7","#ede9fe","#ffe4e6","#e0f2fe"];
  let tintIdx = 0;

  // Per-layer-colored points — Cobe's native marker renderer only supports
  // ONE global markerColor, so with 37 distinguishable layers we draw every
  // point ourselves on a transparent 2D canvas stacked on top, re-projected
  // through the globe's live rotation on every frame. Each point carries
  // title/layer/body fields (otherwise inaccessible — Cobe has no native
  // hover/click picking) which power both the hover tooltip and, on click,
  // a pinned "sticky note" card.
  const points = {_globe_markers_json}.map((m, i) => ({{...m, id: i}}));

  function onResize() {{
    if (!canvas) return;
    width = canvas.offsetWidth;
    const dpr = window.devicePixelRatio || 1;
    overlay.width  = width * dpr;
    overlay.height = width * dpr;
    octx.setTransform(1, 0, 0, 1, 0, 0);
    octx.scale(dpr, dpr);
  }}
  window.addEventListener("resize", onResize);
  onResize();

  function project(lat, lon, phiNow, thetaNow, radius, cx, cy) {{
    const latRad = (lat * Math.PI) / 180;
    const lonRad = (lon * Math.PI) / 180 + phiNow;
    const x  = Math.cos(latRad) * Math.sin(lonRad);
    const y0 = Math.sin(latRad);
    const z0 = Math.cos(latRad) * Math.cos(lonRad);
    const y  = y0 * Math.cos(thetaNow) - z0 * Math.sin(thetaNow);
    const z  = y0 * Math.sin(thetaNow) + z0 * Math.cos(thetaNow);
    if (z < 0.06) return null;  // back-facing / grazing edge — hidden
    return {{ x: cx + x * radius, y: cy - y * radius, depth: z }};
  }}

  function drawOverlay(phiNow) {{
    const w = width;
    octx.clearRect(0, 0, w, w);
    const cx = w / 2, cy = w / 2;
    // Slightly smaller than the canvas half-width so points sit safely on
    // the visible sphere surface rather than the true edge of the canvas —
    // combined with the hard clip below, points can never render outside
    // the globe even if this estimate isn't pixel-perfect.
    const radius = w * 0.46;

    octx.save();
    octx.beginPath();
    octx.arc(cx, cy, radius, 0, Math.PI * 2);
    octx.clip();   // hard boundary — nothing can paint past the globe's edge

    lastProjected = [];
    for (const m of points) {{
      const p = project(m.lat, m.lon, phiNow, theta, radius, cx, cy);
      if (!p) continue;
      const r = Math.max(1.4, m.size * radius * 0.9) * (0.6 + p.depth * 0.4);
      const pinned = openNotes.has(m.id);
      octx.beginPath();
      octx.arc(p.x, p.y, pinned ? r * 1.35 : r, 0, Math.PI * 2);
      octx.fillStyle = `rgba(${{m.color[0]}},${{m.color[1]}},${{m.color[2]}},${{0.6 + p.depth * 0.4}})`;
      octx.fill();
      if (pinned) {{
        octx.lineWidth = 1.4;
        octx.strokeStyle = "rgba(255,255,255,.85)";
        octx.stroke();
      }}
      lastProjected.push({{ x: p.x, y: p.y, r: Math.max(r, 6), title: m.title, layer: m.layer, body: m.body, color: m.color, id: m.id }});
    }}
    octx.restore();

    // Re-draw the hovered point's tooltip position each frame in case the
    // globe is auto-rotating under a stationary cursor
    if (hoverPt) updateTooltip(hoverPt.clientX, hoverPt.clientY);
  }}

  function nearestMarker(clientX, clientY) {{
    const rect = overlay.getBoundingClientRect();
    const mx = clientX - rect.left, my = clientY - rect.top;
    let nearest = null, bestD = Infinity;
    for (const p of lastProjected) {{
      const d = Math.hypot(p.x - mx, p.y - my);
      if (d <= p.r + 5 && d < bestD) {{ bestD = d; nearest = p; }}
    }}
    return {{ nearest, mx, my }};
  }}

  function updateTooltip(clientX, clientY) {{
    const {{ nearest, mx, my }} = nearestMarker(clientX, clientY);
    if (nearest && nearest.title && !openNotes.has(nearest.id)) {{
      tooltip.style.display = "block";
      tooltip.style.left = Math.min(mx + 12, width - 236) + "px";
      tooltip.style.top  = Math.max(my - 10, 4) + "px";
      tooltip.style.borderColor = `rgba(${{nearest.color[0]}},${{nearest.color[1]}},${{nearest.color[2]}},.6)`;
      tooltip.textContent = "📌 " + nearest.layer + ": " + nearest.title + "  (click to pin)";
    }} else {{
      tooltip.style.display = "none";
    }}
  }}

  function updateStickyCount() {{
    const n = openNotes.size;
    countEl.style.display = n > 0 ? "inline" : "none";
    countEl.textContent = n > 0 ? `Clear all (${{n}}) ✕` : "";
  }}

  function addStickyNote(m) {{
    if (openNotes.has(m.id)) return;   // already pinned — don't duplicate
    openNotes.add(m.id);
    updateStickyCount();

    const tint = paperTints[tintIdx % paperTints.length]; tintIdx++;
    const rot = (Math.random() * 4 - 2).toFixed(1);
    const rgb = `rgb(${{m.color[0]}},${{m.color[1]}},${{m.color[2]}})`;

    const note = document.createElement("div");
    note.dataset.markerId = m.id;
    note.style.cssText = `
      position:relative; width:168px; min-height:96px; background:${{tint}};
      color:#20242c; border-radius:3px; padding:10px 11px 12px;
      box-shadow:0 6px 14px rgba(0,0,0,.35), 0 1px 0 rgba(255,255,255,.4) inset;
      transform:rotate(${{rot}}deg); font-family:'JetBrains Mono',monospace;
      transition:transform .15s;
    `;
    note.onmouseenter = () => note.style.transform = `rotate(0deg) scale(1.03)`;
    note.onmouseleave = () => note.style.transform = `rotate(${{rot}}deg) scale(1)`;

    note.innerHTML = `
      <div style="position:absolute;top:-6px;left:50%;transform:translateX(-50%);
           width:10px;height:10px;border-radius:50%;background:${{rgb}};
           box-shadow:0 2px 3px rgba(0,0,0,.4)"></div>
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:4px;margin-bottom:5px">
        <span style="font-size:8px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:${{rgb}};opacity:.9">${{(m.layer||"").replace(/</g,"&lt;")}}</span>
        <span class="sticky-close" style="cursor:pointer;font-size:11px;line-height:1;opacity:.5;padding:0 2px" title="Remove">✕</span>
      </div>
      <div style="font-size:11.5px;font-weight:700;line-height:1.3;margin-bottom:5px;font-family:'Barlow',sans-serif">${{(m.title||"Untitled").slice(0,90).replace(/</g,"&lt;")}}</div>
      <div style="font-size:9.5px;line-height:1.45;opacity:.85;white-space:pre-wrap">${{(m.body||"").slice(0,180).replace(/</g,"&lt;")}}</div>
    `;
    note.querySelector(".sticky-close").addEventListener("click", (ev) => {{
      ev.stopPropagation();
      removeStickyNote(m.id);
    }});
    notesEl.appendChild(note);
  }}

  function removeStickyNote(id) {{
    openNotes.delete(id);
    updateStickyCount();
    const el = notesEl.querySelector(`[data-marker-id="${{id}}"]`);
    if (el) el.remove();
  }}

  window.__clearStickyNotes = () => {{
    openNotes.clear();
    notesEl.innerHTML = "";
    updateStickyCount();
  }};

  const globe = createGlobe(canvas, {{
    devicePixelRatio: 2,
    width: width * 2,
    height: width * 2,
    phi: 0,
    theta: theta,
    dark: 1.1,
    diffuse: 3,
    mapSamples: 16000,
    mapBrightness: 1.8,
    mapBaseBrightness: 0.05,
    baseColor: [1, 1, 1],
    markerColor: [251 / 255, 100 / 255, 21 / 255],
    glowColor: [1, 1, 1],
    markers: [],   // native markers unused — all points render via the overlay canvas
    opacity: 0.85,
    onRender: (state) => {{
      if (!pointerInteracting) {{
        phi += 0.0032;   // auto-rotate
      }}
      const phiNow = phi + pointerInteractionMovement;
      state.phi = phiNow;
      state.width = width * 2;
      state.height = width * 2;
      drawOverlay(phiNow);
    }},
  }});

  // Drag-to-rotate AND click-to-pin — both attached to the overlay, which
  // sits on top and owns pointer events. A "click" is a pointerdown/up pair
  // with very little movement and under ~350ms — anything more is treated
  // as a drag-to-rotate gesture instead, so rotating the globe never
  // accidentally pins a note.
  overlay.style.cursor = "grab";
  overlay.addEventListener("pointerdown", (e) => {{
    pointerInteracting = e.clientX - pointerInteractionMovement;
    downInfo = {{ x: e.clientX, y: e.clientY, t: Date.now() }};
    overlay.style.cursor = "grabbing";
  }});
  window.addEventListener("pointerup", (e) => {{
    if (downInfo) {{
      const moved = Math.hypot(e.clientX - downInfo.x, e.clientY - downInfo.y);
      const elapsed = Date.now() - downInfo.t;
      if (moved < 4 && elapsed < 350) {{
        const {{ nearest }} = nearestMarker(e.clientX, e.clientY);
        if (nearest) {{
          addStickyNote(nearest);
          tooltip.style.display = "none";
        }}
      }}
    }}
    downInfo = null;
    pointerInteracting = null;
    overlay.style.cursor = "grab";
  }});
  window.addEventListener("pointerout", () => {{
    pointerInteracting = null;
    overlay.style.cursor = "grab";
    hoverPt = null;
    tooltip.style.display = "none";
  }});
  overlay.addEventListener("pointermove", (e) => {{
    if (pointerInteracting !== null) {{
      const delta = e.clientX - pointerInteracting;
      pointerInteractionMovement = delta * 0.005;
      tooltip.style.display = "none";
      hoverPt = null;
    }} else {{
      hoverPt = {{ clientX: e.clientX, clientY: e.clientY }};
      updateTooltip(e.clientX, e.clientY);
    }}
  }});
  overlay.addEventListener("touchmove", (e) => {{
    if (pointerInteracting !== null && e.touches[0]) {{
      const delta = e.touches[0].clientX - pointerInteracting;
      pointerInteractionMovement = delta * 0.005;
    }}
  }});
</script>
"""
components.html(_globe_html, height=760, scrolling=False)

_ts = datetime.now(tz=timezone.utc).strftime("%H:%M:%S")
st.markdown(
    f'<div style="font-family:var(--fm);font-size:10px;color:var(--muted);text-align:right;margin-top:-6px;margin-bottom:6px">' +
    f'<span class="pulse p-green" style="margin-right:4px"></span>' +
    f'LIVE · rendered {_ts} UTC · ' +
    f'seismic: <span style="color:#00c8ff">{len(eq_df)}</span> · ' +
    f'markers: <span style="color:#fb6415">{len(_globe_markers)}</span>' +
    f'</div>',
    unsafe_allow_html=True
)

# Cobe has no click/hover picking API, so the map-click intelligence panel
# below always shows its default "no selection" state now — kept as-is
# (rather than removed) since it degrades gracefully and still works from
# other entry points (e.g. clicking a country in other tabs).
_map_selection = None

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
_recent_hist  = [e for e in _HIST_SORTED if e["date"] >= "2025-01-01"][:8]
if not _recent_hist:  # safety net if the 2025+ dataset is ever empty
    _recent_hist = _HIST_SORTED[:8]

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
    st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">📅 RECENT HISTORY (2025+)</div>', unsafe_allow_html=True)
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
    send_alert("crit_conflict", f"⚔ CRITICAL conflict(s) active: {', '.join(_crit_conf)}")
else:
    clear_alert("crit_conflict")
# Kp storm
if kp_data["kp"] >= 5:
    _brief_lines.append(f"🌌 Geomagnetic storm: Kp {kp_data['kp']:.1f} — GPS/HF radio impacts possible")
    send_alert("kp_storm", f"🌌 Geomagnetic storm alert: Kp index {kp_data['kp']:.1f} (≥5) — GPS/HF radio impacts possible")
else:
    clear_alert("kp_storm")
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
# TABS  (lazy-loaded — v8 perf fix)
# ─────────────────────────────────────────────
# NOTE (v8): st.tabs() renders ALL tab bodies on every single script rerun,
# regardless of which tab is visually active — Streamlit doesn't defer
# execution of inactive tab content. With 8 tabs each firing multiple live
# API calls, that meant every click anywhere in the app re-ran ~70 fetch
# functions across every tab. Switching to a session-state-backed selector
# means only the ACTIVE tab's code (and its API calls) executes per rerun —
# this is the main fix behind the v8 load-time improvement.
_TAB_LABELS = [
    "⚔  Conflict Dashboard",
    "🌍  Earth Signals",
    "✊  Civil Movements",
    "📡  Live News",
    "🛰  Intel Dashboard",
    "📻  SIGINT",
    "📊  Economic & Markets",
    "🏭  Facility Map",
]
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = _TAB_LABELS[0]

st.markdown("""
<style>
div[data-testid="stRadio"] > label { display:none; }
div[data-testid="stRadio"] > div { flex-wrap:wrap; gap:2px; border-bottom:1px solid var(--border); padding-bottom:0; }
div[data-testid="stRadio"] > div > label {
    background:transparent; border:none; border-bottom:2px solid transparent;
    padding:8px 14px; margin:0; border-radius:0; font-family:var(--fs);
    font-size:13px; color:var(--muted); cursor:pointer;
}
div[data-testid="stRadio"] input:checked + div {
    color:var(--cyan) !important;
}
</style>
""", unsafe_allow_html=True)

_active_tab = st.radio(
    "Dashboard section", _TAB_LABELS,
    key="active_tab", horizontal=True, label_visibility="collapsed",
)

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
if _active_tab == "⚔  Conflict Dashboard":
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
    try:
        _start_dt = datetime.strptime(C["start"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (KeyError, ValueError, TypeError):
        # Malformed/missing start date in CONFLICTS — fall back to "today" so the
        # tracker degrades to a 0-day counter instead of crashing the whole tab.
        _start_dt = datetime.now(tz=timezone.utc)
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
if _active_tab == "🌍  Earth Signals":
    sig_eq_df = fetch_usgs_significant()  # lazy (v8): only fetched when this tab is open
    st.markdown("""
    <div class="helper">
      <b>Earth Signals</b> shows live USGS seismic data, NASA EONET volcanic/wildfire events,
      and NOAA geomagnetic conditions. The global command map above shows all layers combined.
    </div>""", unsafe_allow_html=True)

    mc, rc = st.columns([3,1], gap="medium")
    with mc:
        st.markdown('<div class="sec-label">🗺 Earth Signals Map</div>', unsafe_allow_html=True)
        _esc1, _esc2 = st.columns(2)
        show_volc = _esc1.toggle("🌋 EONET events", value=True,  key="es_volc")
        show_heat = _esc2.toggle("🌡 Seismic heatmap", value=False, key="es_heat")
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
if _active_tab == "✊  Civil Movements":
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
if _active_tab == "📡  Live News":
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

# ── Country Instability Index ────────────────────────────────
# NOTE (v8): this used to be a second, byte-for-byte-identical copy of
# COUNTRY_INSTABILITY / _CI_LOOKUP (a pre-existing duplicate from v7,
# surfaced by the module split). Removed — the single definition now
# lives in data_constants.py and is imported at the top of this file.

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

if _active_tab == "🛰  Intel Dashboard":
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
if _active_tab == "📻  SIGINT":
    import json as _sj
    import streamlit.components.v1 as _sc
    from datetime import datetime as _sdt, timezone as _stz

    # ── SIGINT-specific auto-refresh (60 seconds) ─────────────
    try:
        from streamlit_autorefresh import st_autorefresh as _sar
        _sar(interval=180_000, key="sigint_refresh")  # 3 min — was 60s
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

    _sigint_template = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;900&family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Barlow:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --bg:#03060d;--bg1:#060d18;--bg2:#0a1525;--bg3:#0f1e35;
  --edge:rgba(0,180,255,.07);--edge2:rgba(0,180,255,.14);
  --amber:#f0a500;--cyan:#00d4ff;--red:#ff2d55;--green:#00e5a0;--violet:#a855f7;
  --text:#c2d8ee;--text2:#7aa0be;--text3:#2e4d66;
}
html,body{height:100%;}
body{background:var(--bg);font-family:'Barlow',system-ui,sans-serif;color:var(--text);overflow-x:hidden;
  background-image:radial-gradient(ellipse 70% 30% at 50% 0%,rgba(0,180,255,.055) 0%,transparent 65%),
    radial-gradient(ellipse 40% 60% at 98% 50%,rgba(240,165,0,.03) 0%,transparent 55%),
    radial-gradient(ellipse 30% 50% at 2% 80%,rgba(168,85,247,.025) 0%,transparent 55%);}
body::after{content:'';pointer-events:none;position:fixed;inset:0;z-index:9999;
  background:repeating-linear-gradient(0deg,transparent 0,transparent 3px,rgba(0,0,0,.02) 3px,rgba(0,0,0,.02) 4px);}
.topbar{position:sticky;top:0;z-index:200;display:grid;grid-template-columns:auto 1fr auto;align-items:stretch;
  background:rgba(3,6,13,.94);border-bottom:1px solid var(--edge2);
  backdrop-filter:blur(16px);box-shadow:0 1px 28px rgba(0,0,0,.5);}
.tb-logo{display:flex;flex-direction:column;justify-content:center;padding:10px 20px;border-right:1px solid var(--edge2);}
.tb-name{font-family:'Orbitron',monospace;font-weight:900;font-size:14px;letter-spacing:.18em;color:var(--cyan);}
.tb-sub{font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:.25em;color:var(--text3);margin-top:3px;}
.tb-metrics{display:flex;align-items:stretch;overflow-x:auto;}
.tb-m{display:flex;flex-direction:column;justify-content:center;padding:8px 18px;border-right:1px solid var(--edge);min-width:0;flex-shrink:0;}
.tb-ml{font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:.2em;text-transform:uppercase;color:var(--text3);margin-bottom:3px;}
.tb-mv{font-family:'Orbitron',monospace;font-weight:700;font-size:14px;}
.tb-right{display:flex;align-items:center;gap:10px;padding:0 16px;border-left:1px solid var(--edge2);}
.tb-ts{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);}
.tb-pill{display:flex;align-items:center;gap:5px;padding:5px 11px;border-radius:2px;
  border:1px solid rgba(0,229,160,.28);background:rgba(0,229,160,.06);
  font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.1em;color:var(--green);}
.tb-cd{font-family:'JetBrains Mono',monospace;font-size:7.5px;color:var(--text3);}
.ticker{overflow:hidden;white-space:nowrap;background:rgba(240,165,0,.03);border-bottom:1px solid rgba(240,165,0,.1);padding:6px 0;}
.t-inner{display:inline-block;animation:scr 100s linear infinite;}
@keyframes scr{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.ti{display:inline-flex;align-items:center;gap:8px;margin-right:56px;font-family:'JetBrains Mono',monospace;font-size:9px;color:rgba(194,216,238,.38);}
.ti-s{color:var(--amber);font-weight:500;}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--edge2);border-bottom:1px solid var(--edge2);}
.kpi{background:var(--bg1);padding:18px 20px;position:relative;overflow:hidden;}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--kc,var(--cyan)) 40%,transparent);}
.kpi-l{font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.18em;text-transform:uppercase;color:var(--text3);margin-bottom:10px;}
.kpi-v{font-family:'Orbitron',monospace;font-weight:900;font-size:44px;color:var(--kc,var(--cyan));line-height:.9;margin-bottom:6px;}
.kpi-s{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);}
.body{padding:14px 16px 40px;}
.r2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;}
.r3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px;}
@media(max-width:1100px){.r3{grid-template-columns:1fr 1fr;}}
@media(max-width:680px){.r2,.r3{grid-template-columns:1fr;}}
.card{background:var(--bg1);border:1px solid var(--edge2);border-radius:3px;position:relative;overflow:hidden;display:flex;flex-direction:column;animation:rise .3s ease both;}
@keyframes rise{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(0,180,255,.22),transparent);pointer-events:none;}
.ch{display:flex;align-items:center;gap:9px;padding:10px 14px;border-bottom:1px solid var(--edge);background:rgba(0,0,0,.28);flex-shrink:0;}
.ch-ico{width:22px;height:22px;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:11px;flex-shrink:0;}
.ch-title{font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--text2);flex:1;}
.ch-ct{font-family:'JetBrains Mono',monospace;font-size:8px;padding:2px 7px;border-radius:2px;background:rgba(0,0,0,.5);border:1px solid var(--edge2);color:var(--text3);}
.live-chip{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:2px;background:rgba(0,229,160,.06);border:1px solid rgba(0,229,160,.22);font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:.1em;color:var(--green);}
.classif{position:absolute;bottom:8px;right:10px;pointer-events:none;font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:.15em;color:var(--text3);opacity:.35;text-transform:uppercase;}
.scroll{overflow-y:auto;flex:1;padding:10px 12px;max-height:330px;scrollbar-width:thin;scrollbar-color:var(--bg3) transparent;display:flex;flex-direction:column;gap:5px;}
.scroll::-webkit-scrollbar{width:2px;}.scroll::-webkit-scrollbar-thumb{background:var(--bg3);}
.item{background:var(--bg2);border-radius:2px;border-left:2px solid;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);padding:9px 11px;transition:background .12s;}
.item:hover{background:var(--bg3);}
.i-top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:5px;}
.i-name{font-family:'Barlow',sans-serif;font-size:13px;font-weight:600;color:#e0eefa;line-height:1.2;}
.i-meta{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);margin-top:2px;}
.i-detail{font-size:12px;color:var(--text2);line-height:1.55;margin-top:4px;}
.actor{background:var(--bg2);border-left:3px solid;border-radius:2px;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);padding:12px 13px;transition:background .12s;display:flex;gap:13px;align-items:flex-start;}
.actor:hover{background:var(--bg3);}
.a-score{font-family:'Orbitron',monospace;font-weight:900;font-size:34px;min-width:50px;text-align:center;flex-shrink:0;line-height:1;}
.a-slbl{font-family:'JetBrains Mono',monospace;font-size:7px;letter-spacing:.12em;color:var(--text3);text-align:center;margin-top:3px;}
.a-body{flex:1;min-width:0;}
.a-name{font-family:'Barlow',sans-serif;font-size:14px;font-weight:600;color:#e0eefa;margin-bottom:1px;}
.a-unit{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);margin-bottom:6px;}
.a-ops{display:flex;flex-wrap:wrap;gap:3px;margin-top:5px;}
.a-op{font-family:'JetBrains Mono',monospace;font-size:7.5px;padding:2px 7px;border-radius:2px;background:rgba(0,180,255,.06);border:1px solid rgba(0,180,255,.12);color:var(--text2);}
.prio{background:var(--bg2);border-left:3px solid;border-radius:2px;padding:10px 12px;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);transition:background .12s;}
.prio:hover{background:var(--bg3);}
.p-row{display:flex;align-items:flex-start;gap:11px;}
.p-num{font-family:'Orbitron',monospace;font-weight:900;font-size:28px;min-width:30px;text-align:center;flex-shrink:0;line-height:1;padding-top:2px;}
.p-target{font-size:13px;font-weight:600;color:#e0eefa;margin-bottom:2px;}
.p-type{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--text3);margin-bottom:4px;}
.p-gap{font-family:'JetBrains Mono',monospace;font-size:8px;color:var(--amber);opacity:.85;margin-top:5px;}
.p-gap::before{content:'⚠ GAP: ';}
.p-plats{display:flex;flex-wrap:wrap;gap:3px;margin-top:5px;}
.p-plat{font-family:'JetBrains Mono',monospace;font-size:7.5px;padding:2px 7px;border-radius:2px;background:rgba(0,180,255,.06);border:1px solid rgba(0,180,255,.12);color:var(--text2);}
.fi{background:var(--bg2);border-left:2px solid var(--cyan);border-radius:2px;padding:9px 11px;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);transition:background .12s;}
.fi:hover{background:var(--bg3);}
.fi-src{font-family:'JetBrains Mono',monospace;font-size:8px;font-weight:500;color:var(--cyan);}
.fi-title{font-size:12px;color:var(--text);line-height:1.5;margin:3px 0;}
.fi-time{font-family:'JetBrains Mono',monospace;font-size:7.5px;color:var(--text3);}
.fi-link{font-family:'JetBrains Mono',monospace;font-size:7.5px;color:rgba(0,212,255,.55);text-decoration:none;}
.fi-link:hover{color:var(--cyan);}
.mbar{height:2px;background:var(--edge);border-radius:1px;overflow:hidden;margin:5px 0;}
.mbar-f{height:100%;border-radius:1px;}
.badge{display:inline-flex;align-items:center;padding:2px 7px;border-radius:2px;font-family:'JetBrains Mono',monospace;font-size:7.5px;letter-spacing:.06em;text-transform:uppercase;border:1px solid;white-space:nowrap;}
.bc{color:var(--red);border-color:rgba(255,45,85,.3);background:rgba(255,45,85,.07);}
.bh{color:var(--amber);border-color:rgba(240,165,0,.3);background:rgba(240,165,0,.07);}
.bl{color:var(--green);border-color:rgba(0,229,160,.25);background:rgba(0,229,160,.05);}
.ba{color:var(--cyan);border-color:rgba(0,212,255,.25);background:rgba(0,212,255,.05);}
.bv{color:var(--violet);border-color:rgba(168,85,247,.25);background:rgba(168,85,247,.06);}
.dom{font-family:'JetBrains Mono',monospace;font-size:7px;padding:2px 6px;border-radius:2px;background:rgba(0,212,255,.07);border:1px solid rgba(0,212,255,.15);color:var(--cyan);letter-spacing:.06em;}
.kp-bars{display:flex;align-items:flex-end;gap:2px;height:40px;padding:0 2px;}
.kp-seg{flex:1;border-radius:1px 1px 0 0;min-width:0;}
.cii-item{background:var(--bg2);border-left:2px solid;border-radius:2px;padding:9px 11px;border-top:1px solid var(--edge);border-right:1px solid var(--edge);border-bottom:1px solid var(--edge);}
.slbl{font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.22em;text-transform:uppercase;color:var(--text3);padding:14px 16px 8px;display:flex;align-items:center;gap:10px;}
.slbl::after{content:'';flex:1;height:1px;background:linear-gradient(90deg,var(--edge2),transparent);}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.15;transform:scale(.5)}}
.dot{width:6px;height:6px;border-radius:50%;display:inline-block;animation:pulse 1.4s ease-in-out infinite;flex-shrink:0;}
</style></head>
<body>
<div id="root"></div>

<script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script crossorigin src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

<script type="text/babel" data-presets="react">
const {useState, useEffect, useRef} = React;
const D = __PAYLOAD__;

// ── Helpers ──────────────────────────────────────────────────
function tlvl(v){ return v>=85?'var(--red)':v>=70?'var(--amber)':v>=50?'#f0d050':'var(--green)'; }
function relTime(iso){
  try{ const d=new Date(iso), s=(Date.now()-d)/1000;
    if(s<60) return Math.round(s)+'s ago';
    if(s<3600) return Math.round(s/60)+'m ago';
    return Math.round(s/3600)+'h ago';
  }catch(e){ return iso||''; }
}
async function fetchGDELT(q){
  try{
    const r = await fetch('https://api.gdeltproject.org/api/v2/doc/doc?query='+encodeURIComponent(q+' sourcelang:english')+'&mode=artlist&maxrecords=12&format=json&sort=DateDesc',{signal:AbortSignal.timeout(10000)});
    if(!r.ok) return [];
    const j = await r.json();
    return (j.articles||[]).map(a=>({title:a.title||'',source:(a.domain||'').split('.')[0].toUpperCase(),url:a.url||'',time:relTime(a.seendate),cat:''}));
  }catch(e){ return []; }
}
async function fetchUSGS(){
  try{
    let r = await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson',{signal:AbortSignal.timeout(8000)});
    if(!r.ok){ r = await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson',{signal:AbortSignal.timeout(8000)}); if(!r.ok) return []; }
    const j = await r.json();
    return (j.features||[]).slice(0,10).map(f=>({place:f.properties.place||'',mag:f.properties.mag||0,depth_km:(f.geometry.coordinates[2]||0).toFixed(1),time:relTime(new Date(f.properties.time).toISOString())}));
  }catch(e){ return []; }
}
async function fetchKP(){
  try{
    const r = await fetch('https://services.swpc.noaa.gov/json/planetary_k_index_1m.json',{signal:AbortSignal.timeout(8000)});
    if(!r.ok) return null;
    const arr = await r.json();
    const series = arr.slice(-24).map(x=>({kp:parseFloat(x.Kp||x.kp_index||0)}));
    const recent = series.slice(-6).map(x=>x.kp);
    const mx = Math.max(...recent,0);
    const st = mx>=8?'EXTREME STORM':mx>=7?'SEVERE STORM':mx>=6?'STRONG STORM':mx>=5?'MODERATE STORM':mx>=4?'MINOR STORM':mx>=3?'Unsettled':'Quiet';
    return {current:Math.round(mx*10)/10, status:st, series};
  }catch(e){ return null; }
}

// ── Small building blocks ───────────────────────────────────
function MBar({pct,color}){
  return <div className="mbar"><div className="mbar-f" style={{width:Math.min(pct,100)+'%',background:color}}></div></div>;
}
function Badge({cls,children}){ return <span className={"badge "+cls}>{children}</span>; }
function CardShell({icoBg,icoColor,icon,title,count,liveChip,classif,children}){
  return (
    <div className="card">
      <div className="ch">
        <div className="ch-ico" style={{background:icoBg,color:icoColor}}>{icon}</div>
        <div className="ch-title">{title}</div>
        {liveChip ? <div className="live-chip"><span className="dot" style={{background:'var(--green)'}}></span>{liveChip}</div>
                  : (count!=null && <div className="ch-ct">{count}</div>)}
      </div>
      <div className="scroll">{children}</div>
      {classif && <div className="classif">{classif}</div>}
    </div>
  );
}

// ── Panels (each = one card) ─────────────────────────────────
function ActorsPanel({actors}){
  const sorted = [...(actors||[])].sort((a,b)=>b.threat_level-a.threat_level);
  return (
    <CardShell icoBg="rgba(255,45,85,.1)" icoColor="var(--red)" icon="⚠" title="Threat Actor Matrix" count={sorted.length+' actors'} classif="SIGINT // EYES ONLY">
      {sorted.map((a,i)=>{
        const col = tlvl(a.threat_level);
        return (
          <div className="actor" key={i} style={{borderColor:col}}>
            <div><div className="a-score" style={{color:col}}>{a.threat_level}</div><div className="a-slbl">THREAT</div></div>
            <div className="a-body">
              <div className="a-name">{a.actor}</div>
              <div className="a-unit">{a.unit||''}</div>
              <MBar pct={a.threat_level} color={col} />
              <div style={{display:'flex',gap:5,alignItems:'center',flexWrap:'wrap',marginBottom:4}}>
                {(a.domain||[]).map((d,j)=><span className="dom" key={j}>{d}</span>)}
                <span style={{marginLeft:'auto',fontFamily:'JetBrains Mono,monospace',fontSize:7.5,color:'var(--text3)'}}>ATTR {a.attribution||0}%</span>
              </div>
              <div className="a-ops">{(a.operations||[]).map((o,j)=><span className="a-op" key={j}>{o}</span>)}</div>
            </div>
          </div>
        );
      })}
    </CardShell>
  );
}

function CollectionPanel({collection}){
  const priCol = p => p<=2?'var(--red)':p<=4?'var(--amber)':p<=6?'#f0d050':'var(--green)';
  const items = collection||[];
  return (
    <CardShell icoBg="rgba(240,165,0,.1)" icoColor="var(--amber)" icon="🎯" title="Collection Requirements" count={'P1–'+items.length}>
      {items.map((p,i)=>{
        const col = priCol(p.priority);
        return (
          <div className="prio" key={i} style={{borderColor:col}}>
            <div className="p-row">
              <div><div className="p-num" style={{color:col}}>P{p.priority}</div></div>
              <div className="a-body">
                <div style={{display:'flex',alignItems:'center',gap:7,marginBottom:3}}>
                  <span className="p-target">{p.target}</span>
                  {p.status==='Active' ? <Badge cls="bc">Active</Badge> : <Badge cls="bl">Routine</Badge>}
                </div>
                <div className="p-type">{p.type||''} · {p.last_update||''}</div>
                <div className="p-plats">{(p.collection||[]).map((c,j)=><span className="p-plat" key={j}>{c}</span>)}</div>
                <div className="p-gap">{p.intel_gap||''}</div>
              </div>
            </div>
          </div>
        );
      })}
    </CardShell>
  );
}

function COMINTPanel({comint}){
  const items = comint||[];
  return (
    <CardShell icoBg="rgba(240,165,0,.1)" icoColor="var(--amber)" icon="📡" title="COMINT — Communications Intel" count={items.length+' signals'} classif="TOP SECRET // COMINT">
      {items.map((s,i)=>{
        const col = s.intercept==='Active' ? 'var(--amber)' : 'var(--violet)';
        const bc  = s.intercept==='Active' ? 'bh' : 'bv';
        return (
          <div className="item" key={i} style={{borderColor:col}}>
            <div className="i-top">
              <div>
                <div className="i-name">{s.actor}</div>
                <div className="i-meta">{s.id||''} · {s.signal_type||''} · {s.freq||''}</div>
              </div>
              <div style={{display:'flex',flexDirection:'column',alignItems:'flex-end',gap:4,flexShrink:0}}>
                <Badge cls={bc}>{s.intercept||''}</Badge>
                <span style={{fontFamily:'JetBrains Mono,monospace',fontSize:7.5,color:'var(--text3)'}}>CONF {s.confidence||0}%</span>
              </div>
            </div>
            <MBar pct={s.confidence||0} color={col} />
            <div className="i-detail">{s.detail||''}</div>
            <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:8,color:'var(--text3)',marginTop:5}}>⊳ TARGET: {s.target||''}</div>
          </div>
        );
      })}
    </CardShell>
  );
}

function ELINTPanel({elint}){
  const ac = a => a.includes('Russia')?'var(--red)':a.includes('China')?'var(--amber)':a.includes('USA')?'var(--cyan)':'var(--green)';
  const items = elint||[];
  return (
    <CardShell icoBg="rgba(0,212,255,.08)" icoColor="var(--cyan)" icon="⚡" title="ELINT — Electronic Intelligence" count={items.length+' tracked'} classif="TOP SECRET // ELINT">
      {items.map((e,i)=>{
        const col = ac(e.actor||'');
        return (
          <div className="item" key={i} style={{borderColor:col}}>
            <div className="i-top">
              <div>
                <div className="i-name">{e.system||''}</div>
                <div className="i-meta">{e.type||''} · {e.freq||''} · Range: {e.range_km||'?'}km</div>
              </div>
              <div style={{display:'flex',flexDirection:'column',alignItems:'flex-end',gap:3,flexShrink:0}}>
                <span className="badge" style={{color:col,borderColor:col+'40',background:col+'12'}}>{e.actor||''}</span>
                <span style={{fontFamily:'JetBrains Mono,monospace',fontSize:7.5,color:'var(--text3)',textAlign:'right'}}>{e.capability||''}</span>
              </div>
            </div>
            <div className="i-detail">{e.detail||''}</div>
          </div>
        );
      })}
    </CardShell>
  );
}

function MASINTPanel({masint}){
  const tc = {Seismic:'#f0d050','Nuclear Radiation':'var(--red)',Acoustic:'var(--cyan)',Chemical:'var(--amber)',Thermal:'var(--amber)'};
  const items = masint||[];
  return (
    <CardShell icoBg="rgba(240,208,80,.08)" icoColor="#f0d050" icon="🔭" title="MASINT — Measurement & Signature" count={items.length+' events'} classif="TOP SECRET // MASINT">
      {items.map((m,i)=>{
        const col = tc[m.type] || 'var(--green)';
        return (
          <div className="item" key={i} style={{borderColor:col}}>
            <div className="i-top">
              <div>
                <div className="i-name">{m.event||''}</div>
                <div className="i-meta">{m.id||''} · {m.location||''} · {m.date||''}</div>
              </div>
              <div style={{display:'flex',flexDirection:'column',alignItems:'flex-end',gap:3,flexShrink:0}}>
                <span className="badge" style={{color:col,borderColor:col+'40',background:col+'12'}}>{m.type||''}</span>
                <span style={{fontFamily:'JetBrains Mono,monospace',fontSize:7.5,color:'var(--text3)'}}>CONF {m.confidence||0}%</span>
              </div>
            </div>
            <MBar pct={m.confidence||0} color={col} />
            <div className="i-detail">{m.detail||''}</div>
          </div>
        );
      })}
    </CardShell>
  );
}

function JammingPanel({zones}){
  const items = zones||[];
  return (
    <CardShell icoBg="rgba(255,45,85,.08)" icoColor="var(--red)" icon="📵" title="GPS/GNSS Jamming Zones" count={items.length+' zones'}>
      {items.map((z,i)=>{
        const col = z.severity==='High' ? 'var(--red)' : '#f0d050';
        const bc  = z.severity==='High' ? 'bc' : 'bh';
        return (
          <div className="item" key={i} style={{borderColor:col}}>
            <div className="i-top">
              <div>
                <div className="i-name">{z.name||''}</div>
                <div className="i-meta">Source: {z.source||''} · Radius: {z.radius_km||'?'}km</div>
              </div>
              <Badge cls={bc}>{z.severity||''}</Badge>
            </div>
            <MBar pct={z.severity==='High'?90:55} color={col} />
          </div>
        );
      })}
    </CardShell>
  );
}

function OrbitalPanel({orbital}){
  const oc = o => o.includes('USA')?'var(--cyan)':o.includes('Russia')?'var(--red)':o.includes('China')?'var(--amber)':o.includes('Israel')?'#f0d050':'var(--green)';
  const items = orbital||[];
  return (
    <CardShell icoBg="rgba(0,212,255,.08)" icoColor="var(--cyan)" icon="🛰" title="Orbital ISR — Surveillance Sat" count={items.length+' systems'}>
      {items.map((o,i)=>{
        const col = oc(o.operator||'');
        return (
          <div className="item" key={i} style={{borderColor:col}}>
            <div className="i-top">
              <div><div className="i-name">{o.name||''}</div><div className="i-meta">{o.type||''}</div></div>
              <span className="badge" style={{color:col,borderColor:col+'40',background:col+'12'}}>{o.operator||''}</span>
            </div>
          </div>
        );
      })}
    </CardShell>
  );
}

function CyberPanel({cyberThreats,liveCyber}){
  const ac = a => a.includes('Russia')?'var(--red)':a.includes('China')?'var(--amber)':a.includes('Iran')?'#f0d050':a.includes('DPRK')?'var(--violet)':'var(--green)';
  const base = cyberThreats||[];
  const live = (liveCyber||[]).slice(0,5);
  return (
    <div className="card">
      <div className="ch">
        <div className="ch-ico" style={{background:'rgba(168,85,247,.1)',color:'var(--violet)'}}>💀</div>
        <div className="ch-title">CYBINT — Cyber Threats</div>
        <div className="live-chip"><span className="dot" style={{background:'var(--green)'}}></span>GDELT</div>
      </div>
      <div className="scroll">
        {base.map((c,i)=>{
          const col = ac(c.actor||'');
          return (
            <div className="item" key={'b'+i} style={{borderColor:col}}>
              <div className="i-top">
                <div><div className="i-name">{c.name||''}</div><div className="i-meta">Targets: {c.targets||''}</div></div>
                <span className="badge" style={{color:col,borderColor:col+'40',background:col+'12'}}>{c.actor||''}</span>
              </div>
            </div>
          );
        })}
        {live.length>0 && <div style={{height:1,background:'var(--edge2)',margin:'4px 0'}}></div>}
        {live.map((a,i)=>(
          <div className="fi" key={'l'+i} style={{borderLeftColor:'var(--violet)'}}>
            <div className="fi-src">{(a.source||'').toUpperCase()}</div>
            <div className="fi-title">{(a.title||'').slice(0,100)}</div>
            <div className="fi-time">{a.time||''}</div>
          </div>
        ))}
      </div>
      <div className="classif">TOP SECRET // CYBER</div>
    </div>
  );
}

function SeismicPanel({quakes}){
  const q = quakes||[];
  return (
    <div className="card">
      <div className="ch">
        <div className="ch-ico" style={{background:'rgba(240,208,80,.08)',color:'#f0d050'}}>🌍</div>
        <div className="ch-title">MASINT — Live Seismic</div>
        <div className="live-chip"><span className="dot" style={{background:'var(--green)'}}></span>USGS</div>
      </div>
      <div className="scroll">
        {q.length ? q.map((qq,i)=>{
          const col = qq.mag>=6?'var(--red)':qq.mag>=5?'var(--amber)':qq.mag>=4?'#f0d050':'var(--green)';
          return (
            <div className="item" key={i} style={{borderColor:col}}>
              <div className="i-top">
                <div><div className="i-name">{qq.place||qq.loc||''}</div><div className="i-meta">Depth: {qq.depth_km||'?'}km · {qq.time||''}</div></div>
                <span style={{fontFamily:'Orbitron,monospace',fontWeight:700,fontSize:18,color:col}}>M{qq.mag}</span>
              </div>
            </div>
          );
        }) : <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:10,color:'var(--text3)',padding:'12px 0'}}>Polling USGS…</div>}
      </div>
    </div>
  );
}

function KPPanel({kp,kpStatus,kpSeries}){
  const col = kp>=5?'var(--red)':kp>=3?'var(--amber)':'var(--green)';
  const bars = (kpSeries||[]).slice(-24);
  return (
    <div className="card">
      <div className="ch">
        <div className="ch-ico" style={{background:'rgba(0,229,160,.08)',color:'var(--green)'}}>☀</div>
        <div className="ch-title">Space Weather / KP Index</div>
        <div className="live-chip"><span className="dot" style={{background:'var(--green)'}}></span>NOAA</div>
      </div>
      <div style={{padding:'14px 16px'}}>
        <div style={{display:'flex',alignItems:'center',gap:18,marginBottom:12}}>
          <div>
            <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:8,letterSpacing:'.18em',textTransform:'uppercase',color:'var(--text3)',marginBottom:4}}>KP INDEX</div>
            <div style={{fontFamily:'Orbitron,monospace',fontWeight:900,fontSize:48,color:col,lineHeight:1}}>{kp}</div>
          </div>
          <div>
            <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:11,color:col,marginBottom:4}}>{kpStatus||'Quiet'}</div>
            <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:8,color:'var(--text3)'}}>≥5 Storm · ≥7 Severe · ≥9 Extreme</div>
          </div>
        </div>
        <div className="kp-bars">
          {bars.map((p,i)=>{
            const v = Math.min(p.kp||p||0,9);
            const h = Math.max(Math.round((v/9)*100),3);
            const c = v>=5?'var(--red)':v>=3?'var(--amber)':'var(--green)';
            return <div className="kp-seg" key={i} style={{height:h+'%',background:c,opacity:.8}}></div>;
          })}
        </div>
        <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:7,color:'var(--text3)',marginTop:3,textAlign:'right'}}>← 24h Kp history</div>
      </div>
    </div>
  );
}

function OutagesPanel({outages}){
  const items = (outages||[]).slice(0,10);
  return (
    <CardShell icoBg="rgba(255,45,85,.08)" icoColor="var(--red)" icon="🔌" title="Internet Outages" liveChip="Live">
      {items.length ? items.map((o,i)=>(
        <div className="item" key={i} style={{borderColor:'var(--red)'}}>
          <div className="i-name">{o.region||o.title||''}</div>
          <div className="i-meta">{o.provider||o.source||''} · {o.time||o.ts||''}</div>
        </div>
      )) : <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:10,color:'var(--text3)',padding:'12px 0'}}>No major outages detected.</div>}
    </CardShell>
  );
}

function LiveFeedPanel({feed}){
  const cc = {CONFLICT:'var(--red)',MILITARY:'var(--amber)',NUCLEAR:'var(--red)',OSINT:'var(--cyan)',CYBER:'var(--violet)'};
  const all = (feed||[]).slice(0,25);
  return (
    <CardShell icoBg="rgba(0,212,255,.08)" icoColor="var(--cyan)" icon="📰" title="Live OSINT / SIGINT Feed" liveChip={all.length+' signals'}>
      {all.length ? all.map((a,i)=>{
        const col = cc[a.cat||''] || 'var(--cyan)';
        return (
          <div className="fi" key={i} style={{borderLeftColor:col}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:3}}>
              <span className="fi-src" style={{color:col}}>{(a.source||'').slice(0,22).toUpperCase()}</span>
              <span className="fi-time">{a.time||''}</span>
            </div>
            <div className="fi-title">{(a.title||'').slice(0,110)}</div>
            {a.url && <a className="fi-link" href={a.url} target="_blank" rel="noopener">READ →</a>}
          </div>
        );
      }) : <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:10,color:'var(--text3)',padding:'12px 0'}}>Fetching live signals…</div>}
    </CardShell>
  );
}

function OSINTPanel({platforms}){
  const items = platforms||[];
  return (
    <CardShell icoBg="rgba(0,229,160,.08)" icoColor="var(--green)" icon="👁" title="OSINT Collection Platforms" count={items.length+' sources'}>
      {items.map((p,i)=>(
        <div className="item" key={i} style={{borderColor:'var(--green)'}}>
          <div className="i-top">
            <div><div className="i-name">{p.name||''}</div><div className="i-meta">{p.type||''} · {p.provider||''} · Res: {p.resolution||''}</div></div>
            <Badge cls="bl">{p.status||''}</Badge>
          </div>
          <div className="i-detail">{p.use_case||''}</div>
        </div>
      ))}
    </CardShell>
  );
}

function CIIPanel({cii}){
  const sorted = [...(cii||[])].sort((a,b)=>b.risk-a.risk);
  return (
    <CardShell icoBg="rgba(255,45,85,.08)" icoColor="var(--red)" icon="🏗" title="GEOINT — Critical Infrastructure" count={sorted.length+' tracked'} classif="GEOINT // INFRA">
      {sorted.map((c,i)=>{
        const col = c.risk>=90?'var(--red)':c.risk>=75?'var(--amber)':'#f0d050';
        return (
          <div className="cii-item" key={i} style={{borderColor:col}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:4}}>
              <div><div className="i-name">{c.name||''}</div><div className="i-meta">{c.country||''} · {c.sector||''}</div></div>
              <span style={{fontFamily:'Orbitron,monospace',fontWeight:900,fontSize:20,color:col}}>{c.risk}</span>
            </div>
            <MBar pct={c.risk} color={col} />
          </div>
        );
      })}
    </CardShell>
  );
}

// ── KPI strip + ticker ────────────────────────────────────────
function KPIStrip({gpsJamming,actors,elint,cii}){
  const jam  = (gpsJamming||[]).filter(z=>z.severity==='High').length;
  const act  = (actors||[]).filter(a=>a.threat_level>=85).length;
  const elnt = (elint||[]).filter(e=>e.status==='Active').length;
  const ciic = (cii||[]).filter(c=>c.risk>=90).length;
  const data = [
    {v:jam,l:'Active GPS Jamming',s:'High-severity zones',c:'var(--red)'},
    {v:act,l:'Critical Threat Actors',s:'Threat level ≥85',c:'var(--amber)'},
    {v:elnt,l:'Active ELINT Systems',s:'Emissions tracked',c:'var(--cyan)'},
    {v:ciic,l:'CII Critical Risk',s:'Infrastructure risk ≥90',c:'var(--red)'},
  ];
  return (
    <div className="kpis">
      {data.map((k,i)=>(
        <div className="kpi" key={i} style={{'--kc':k.c}}>
          <div className="kpi-l">{k.l}</div>
          <div className="kpi-v">{k.v}</div>
          <div className="kpi-s">{k.s}</div>
        </div>
      ))}
    </div>
  );
}

function Ticker({feed,cyber}){
  const all = [...(feed||[]), ...(cyber||[])].slice(0,20);
  if(!all.length) return <div className="ticker"><div className="t-inner">Loading intelligence feed…</div></div>;
  const items = all.map((a,i)=>(
    <span className="ti" key={i}><span className="ti-s">▶ {(a.source||'').toUpperCase().slice(0,18)}</span>{(a.title||'').slice(0,88)}</span>
  ));
  return <div className="ticker"><div className="t-inner">{items}{items}</div></div>;
}

// ── Root App ─────────────────────────────────────────────────
function App(){
  const [ls, setLs] = useState({
    feed: [...(D.live_events||[]), ...(D.live_conflict||[]), ...(D.live_feed||[])].slice(0,25),
    cyber: D.live_cyber||[],
    quakes: D.live_quakes||[],
    kp: D.kp_current||0,
    kpStatus: D.kp_status||'Quiet',
    kpSeries: (D.kp_series||[]).slice(-24),
  });
  const [pollStatus, setPollStatus] = useState('LIVE');
  const [countdown, setCountdown] = useState(D.refresh_interval || 180);
  const [nowTs, setNowTs] = useState(D.ts || '');
  const pollingRef = useRef(false);

  // 1s countdown ticker (matches original `cd` element)
  useEffect(() => {
    const id = setInterval(() => {
      setCountdown(c => (c<=0 ? (D.refresh_interval||180) : c-1));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  async function pollAll(){
    if (pollingRef.current) return;
    pollingRef.current = true;
    setPollStatus('UPDATING…');
    try{
      const [feed, cyber, geo, quakes, kpData] = await Promise.all([
        fetchGDELT('war military strike conflict bombing 2026'),
        fetchGDELT('cyber attack espionage hacking malware APT'),
        fetchGDELT('geopolitics sanctions nuclear ballistic missile diplomacy'),
        fetchUSGS(),
        fetchKP(),
      ]);
      setLs(prev => ({
        feed:  (feed && feed.length) ? [...(geo||[]), ...feed].slice(0,25) : prev.feed,
        cyber: (cyber && cyber.length) ? cyber : prev.cyber,
        quakes: (quakes && quakes.length) ? quakes : prev.quakes,
        kp: kpData ? kpData.current : prev.kp,
        kpStatus: kpData ? kpData.status : prev.kpStatus,
        kpSeries: kpData ? kpData.series : prev.kpSeries,
      }));
      setNowTs(new Date().toUTCString().replace(/.*([0-9][0-9]:[0-9][0-9]:[0-9][0-9]).*/, '$1') + ' UTC');
    }catch(e){ console.warn('poll', e); }
    pollingRef.current = false;
    setPollStatus('LIVE');
  }

  useEffect(() => {
    const t1 = setTimeout(pollAll, 4000);
    const t2 = setInterval(pollAll, D.refresh_interval ? D.refresh_interval*1000 : 180000);
    return () => { clearTimeout(t1); clearInterval(t2); };
  }, []);

  const sigRisk = D.live_risk || {};
  const jamCount = (D.gps_jamming||[]).filter(z=>z.severity==='High').length;
  const critActors = (D.actors||[]).filter(a=>a.threat_level>=85).length;
  const ciiCrit = (D.cii||[]).filter(c=>c.risk>=90).length;
  const liveCount = (D.live_feed||[]).length + (D.live_conflict||[]).length;

  return (
    <React.Fragment>
      <div className="topbar">
        <div className="tb-logo">
          <div className="tb-name">SIGINT</div>
          <div className="tb-sub">Signals Intelligence Dashboard</div>
        </div>
        <div className="tb-metrics">
          <div className="tb-m"><div className="tb-ml">Global Risk</div><div className="tb-mv" style={{color:'var(--amber)'}}>{sigRisk.score||'—'} {sigRisk.label||''}</div></div>
          <div className="tb-m"><div className="tb-ml">KP Index</div><div className="tb-mv" style={{color:'var(--cyan)'}}>{D.kp_current}</div></div>
          <div className="tb-m"><div className="tb-ml">GPS Jamming</div><div className="tb-mv" style={{color:'var(--red)'}}>{jamCount}</div></div>
          <div className="tb-m"><div className="tb-ml">Threat Actors</div><div className="tb-mv" style={{color:'var(--amber)'}}>{critActors}</div></div>
          <div className="tb-m"><div className="tb-ml">CII Critical</div><div className="tb-mv" style={{color:'var(--red)'}}>{ciiCrit}</div></div>
          <div className="tb-m"><div className="tb-ml">Live Signals</div><div className="tb-mv" style={{color:'var(--green)'}}>{liveCount}</div></div>
        </div>
        <div className="tb-right">
          <span className="tb-ts">{nowTs}</span>
          <span className="tb-pill"><span className="dot" style={{background:'var(--green)'}}></span>{pollStatus}</span>
          <span className="tb-cd">↻&thinsp;{countdown}s</span>
        </div>
      </div>

      <Ticker feed={ls.feed} cyber={ls.cyber} />
      <KPIStrip gpsJamming={D.gps_jamming} actors={D.actors} elint={D.elint} cii={D.cii} />

      <div className="body">
        <div className="slbl">Priority Intelligence</div>
        <div className="r2"><ActorsPanel actors={D.actors} /><CollectionPanel collection={D.collection} /></div>

        <div className="slbl">Signals Collection</div>
        <div className="r3"><COMINTPanel comint={D.comint} /><ELINTPanel elint={D.elint} /><MASINTPanel masint={D.masint} /></div>

        <div className="slbl">Environment & Cyber Domain</div>
        <div className="r3"><JammingPanel zones={D.gps_jamming} /><OrbitalPanel orbital={D.orbital} /><CyberPanel cyberThreats={D.cyber_threats} liveCyber={ls.cyber} /></div>

        <div className="slbl">Live MASINT & Alerts</div>
        <div className="r3"><SeismicPanel quakes={ls.quakes} /><KPPanel kp={ls.kp} kpStatus={ls.kpStatus} kpSeries={ls.kpSeries} /><OutagesPanel outages={D.internet_static} /></div>

        <div className="slbl">Open Source & Infrastructure</div>
        <div className="r2"><LiveFeedPanel feed={ls.feed} /><OSINTPanel platforms={D.osint_platforms} /></div>

        <CIIPanel cii={D.cii} />
      </div>
    </React.Fragment>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
</script>
</body></html>
"""
    _sigint_html = _sigint_template.replace("__PAYLOAD__", _sigint_payload)
    _sc.html(_sigint_html, height=5600, scrolling=True)


if _active_tab == "📊  Economic & Markets":
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

    _econ_template = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {
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
}
*, *::before, *::after { margin:0; padding:0; box-sizing:border-box; }
html { scroll-behavior:smooth; }
body {
  background: var(--void);
  background-image:
    radial-gradient(ellipse 80% 40% at 50% -10%, rgba(56,189,248,.07) 0%, transparent 70%),
    radial-gradient(ellipse 40% 30% at 90% 60%, rgba(167,139,250,.05) 0%, transparent 60%);
  font-family: var(--fb);
  color: var(--ink);
  padding: 20px 16px 40px;
  min-height: 100vh;
}

/* ── TYPOGRAPHY ── */
.disp { font-family: var(--fd); letter-spacing: -.01em; line-height: 1; }
.mono { font-family: var(--fm); }
.overline { font-family: var(--fm); font-size: 9px; font-weight: 500; letter-spacing: .18em;
             text-transform: uppercase; color: var(--ink3); }
.section-title {
  font-family: var(--fm); font-size: 9px; font-weight: 500;
  letter-spacing: .2em; text-transform: uppercase; color: var(--ink3);
  display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
}
.section-title::after { content:''; flex:1; height:1px; background:var(--edge2); }

/* ── LAYOUT ── */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1.2fr;
  gap: 16px;
  margin-bottom: 24px;
}
.duo-grid  { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:24px; }
.trio-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:24px; }
@media(max-width:960px) { .main-grid { grid-template-columns:1fr 1fr; } }
@media(max-width:580px) { .main-grid, .duo-grid, .trio-grid { grid-template-columns:1fr; } }

/* ── SURFACE CARDS ── */
.card {
  background: var(--surface);
  border: 1px solid var(--edge);
  border-radius: 14px;
  padding: 20px 22px;
  position: relative;
  overflow: hidden;
}
.card::before {
  content: '';
  position: absolute; top:0; left:0; right:0; height:1px;
  background: linear-gradient(90deg, transparent 0%, rgba(148,163,184,.15) 40%, transparent 100%);
}
.card-row {
  background: var(--raised);
  border: 1px solid var(--edge2);
  border-left: 3px solid;
  border-radius: 9px;
  padding: 11px 14px;
  margin-bottom: 8px;
  transition: background .15s, border-color .15s;
  cursor: default;
}
.card-row:last-child { margin-bottom: 0; }
.card-row:hover { background: var(--lift); }

/* ── KPI CARDS ── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4,1fr);
  gap: 14px;
  margin-bottom: 28px;
}
@media(max-width:700px) { .kpi-grid { grid-template-columns:1fr 1fr; } }
.kpi {
  background: var(--surface);
  border: 1px solid var(--edge);
  border-radius: 14px;
  padding: 22px 24px 18px;
  position: relative;
  overflow: hidden;
}
.kpi-glow {
  position: absolute; top:0; left:0; right:0; height:60px;
  background: radial-gradient(ellipse at 50% 0%, var(--accent-glow, rgba(56,189,248,.12)), transparent 70%);
  pointer-events: none;
}
.kpi-top-bar {
  position: absolute; top:0; left:0; right:0; height:2px;
  background: var(--accent-bar, linear-gradient(90deg,transparent,var(--sky),transparent));
}
.kpi-num { font-family:var(--fd); font-size:46px; line-height:.95; letter-spacing:-.01em; margin-bottom:8px; }
.kpi-label { font-family:var(--fm); font-size:9px; font-weight:500; letter-spacing:.2em;
              text-transform:uppercase; color:var(--ink3); margin-bottom:4px; }
.kpi-sub { font-family:var(--fm); font-size:10px; color:var(--ink3); }

/* ── PILL TABS ── */
.pill-tabs { display:flex; gap:5px; margin-bottom:16px; flex-wrap:wrap; }
.pill {
  padding: 5px 14px; border-radius: 20px;
  font-size: 11px; font-weight: 600; cursor: pointer;
  background: var(--raised); border: 1px solid var(--edge2);
  color: var(--ink3); transition: all .15s;
  font-family: var(--fb);
}
.pill:hover { border-color: var(--edge); color: var(--ink2); }
.pill.on { background:rgba(56,189,248,.1); border-color:rgba(56,189,248,.3); color:var(--sky); }
.pane { display:none; } .pane.on { display:block; }

/* ── BADGE ── */
.badge {
  display:inline-flex; align-items:center; padding:2px 9px; border-radius:5px;
  font-family:var(--fm); font-size:9px; font-weight:600; letter-spacing:.04em;
  border:1px solid; white-space:nowrap;
}
.crit  { color:var(--rose);   border-color:rgba(248,113,113,.3); background:rgba(248,113,113,.08); }
.high  { color:var(--coral);  border-color:rgba(251,146,60,.3);  background:rgba(251,146,60,.08);  }
.med   { color:var(--gold);   border-color:rgba(251,191,36,.3);  background:rgba(251,191,36,.08);  }
.low   { color:var(--mint);   border-color:rgba(52,211,153,.3);  background:rgba(52,211,153,.08);  }
.neu   { color:var(--ink3);   border-color:rgba(71,85,105,.4);   background:rgba(71,85,105,.06);   }
.sky-b { color:var(--sky);    border-color:rgba(56,189,248,.3);  background:rgba(56,189,248,.08);  }
.vio-b { color:var(--violet); border-color:rgba(167,139,250,.3); background:rgba(167,139,250,.08); }

/* ── LIVE PULSE ── */
.live-chip {
  display:inline-flex; align-items:center; gap:5px; padding:3px 10px;
  background:rgba(248,113,113,.08); border:1px solid rgba(248,113,113,.25);
  border-radius:20px; font-family:var(--fm); font-size:8px; color:var(--rose);
  letter-spacing:.1em; text-transform:uppercase;
}
.live-dot {
  width:5px; height:5px; border-radius:50%; background:var(--rose);
  animation:pulse 1.4s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(.7)} }

/* ── BAR ── */
.bar-track { height:4px; background:rgba(148,163,184,.08); border-radius:2px; overflow:hidden; margin:6px 0; }
.bar-track.thick { height:7px; border-radius:4px; margin:8px 0; }
.bar-fill  { height:100%; border-radius:inherit; transition:width .4s ease; }

/* ── DIVIDER ── */
.divider { border:none; border-top:1px solid var(--edge2); margin:28px 0; }

/* ── SECTOR GRID ── */
.sector-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:6px; }
.sector-cell {
  border-radius:8px; padding:9px 6px; text-align:center;
  transition:transform .15s, filter .15s;
}
.sector-cell:hover { transform:translateY(-2px); filter:brightness(1.1); }

/* ── SCROLLABLE ── */
.scroll { max-height:380px; overflow-y:auto; padding-right:4px; }
.scroll::-webkit-scrollbar { width:3px; }
.scroll::-webkit-scrollbar-thumb { background:rgba(148,163,184,.15); border-radius:2px; }

/* ── PIZZA ── */
.pz-score {
  font-family: var(--fd);
  font-size: 96px; line-height:.85;
  letter-spacing: -.02em;
}
.pz-bar {
  height: 10px; border-radius:5px; overflow:hidden;
  background: linear-gradient(90deg,#34d399 0%,#fbbf24 42%,#fb923c 64%,#f87171 100%);
  margin: 12px 0 4px; position:relative;
}
.pz-needle {
  position:absolute; top:-4px; width:3px; height:18px;
  background:#fff; border-radius:2px;
  box-shadow:0 0 8px rgba(255,255,255,.6);
  transform:translateX(-50%);
}

/* ── FIRE TABLE ── */
.fire-tbl { width:100%; border-collapse:collapse; }
.fire-tbl th {
  font-family:var(--fm); font-size:9px; font-weight:500; letter-spacing:.12em;
  text-transform:uppercase; color:var(--ink3); text-align:left;
  padding:0 0 10px; border-bottom:1px solid var(--edge2);
}
.fire-tbl th:not(:first-child) { text-align:right; }
.fire-tbl td { padding:9px 0; border-bottom:1px solid var(--edge2); vertical-align:middle; }
.fire-tbl tr:last-child td { border-bottom:none; }
.fire-tbl td:not(:first-child) { text-align:right; font-family:var(--fm); font-size:11px; }

/* ── ENTRY ANIMATIONS ── */
@keyframes fadeUp {
  from { opacity:0; transform:translateY(10px); }
  to   { opacity:1; transform:translateY(0); }
}
.card { animation: fadeUp .35s ease both; }
.kpi:nth-child(1) { animation-delay:.04s; }
.kpi:nth-child(2) { animation-delay:.08s; }
.kpi:nth-child(3) { animation-delay:.12s; }
.kpi:nth-child(4) { animation-delay:.16s; }

  .mn{font-family:var(--fm);}
  .fw6{font-weight:600;}
  .muted{color:var(--ink3);}
  .ink2{color:var(--ink2);}
  .s8{font-size:8px;}.s9{font-size:9px;}.s10{font-size:10px;}.s11{font-size:11px;}.s12{font-size:12px;}.s13{font-size:13px;}
  .overline{font-family:var(--fm);letter-spacing:.12em;text-transform:uppercase;}
  .panel{background:var(--surface);border:1px solid var(--edge);border-radius:14px;padding:16px 18px;}
  .panel-hdr{display:flex;align-items:center;gap:8px;font-family:var(--fm);font-size:9px;font-weight:500;letter-spacing:.18em;text-transform:uppercase;color:var(--ink3);margin-bottom:12px;}
</style>
<body>
<div id="root"></div>

<script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script crossorigin src="https://unpkg.com/@babel/standalone/babel.min.js"></script>

<script type="text/babel" data-presets="react">
const {useState} = React;
const D = __PAYLOAD__;

// ── Helpers ──────────────────────────────────────────────────
const sevCls = s => s==='Critical'?'crit':s==='High'?'high':s==='Med'?'med':'low';
const rCol = r => r>=75?'var(--rose)':r>=50?'var(--coral)':r>=35?'var(--gold)':'var(--mint)';

function Chg({v, decimals=2}){
  const up = v>=0, c = up?'var(--mint)':'var(--rose)', sym = up?'▲':'▼';
  return <span style={{fontFamily:'var(--fm)',fontSize:10,color:c}}>{sym}{Math.abs(v).toFixed(decimals)}</span>;
}
function Bar({pct,col,thick}){
  return <div className={"bar-track"+(thick?" thick":"")}><div className="bar-fill" style={{width:pct+'%',background:col}}></div></div>;
}
function Badge({txt,cls}){ return <span className={"badge "+cls}>{txt}</span>; }
function LiveTag(){
  if(!D.ts) return null;
  return <span style={{fontFamily:'var(--fm)',fontSize:8,display:'inline-flex',alignItems:'center',gap:4,padding:'2px 7px',background:'rgba(52,211,153,.08)',border:'1px solid rgba(52,211,153,.2)',borderRadius:10,color:'var(--mint)'}}>
    <span style={{width:4,height:4,borderRadius:'50%',background:'var(--mint)',display:'inline-block'}}></span>LIVE {D.ts}
  </span>;
}
function Panel({title,children,note}){
  return <div className="panel">
    <div className="panel-hdr">{title} <LiveTag /></div>
    {note && <div className="mn s9" style={{color:'var(--coral)',marginBottom:10}}>{note}</div>}
    <div className="scroll">{children}</div>
  </div>;
}
// Pill-tab card: local state per card, no global window state needed
function PillCard({title,tabs,liveTs}){
  const [active, setActive] = useState(0);
  return (
    <div className="card">
      <div className="section-title">{title}{liveTs}</div>
      <div className="pill-tabs">
        {tabs.map((t,i)=>(
          <div key={i} className={"pill"+(i===active?" on":"")} onClick={()=>setActive(i)}>{t.label}</div>
        ))}
      </div>
      <div className="scroll">{tabs[active].content}</div>
    </div>
  );
}

// ── KPI Strip ────────────────────────────────────────────────
function KPIStrip(){
  const brentLive = D.commodities.find(c=>c.name.includes('Brent')||c.sym==='BZ=F');
  const brentStatic = D.oil.find(o=>o.name.includes('Brent'))||{};
  const brentVal = brentLive ? brentLive.price : brentStatic.val;
  const brentChg = brentLive ? brentLive.chg_pct : (brentStatic.change||0);
  const wtiVal = (D.commodities.find(c=>c.name.includes('WTI')||c.sym==='CL=F')||{}).price
               || ((D.oil.find(o=>o.name.includes('WTI'))||{}).val||0);
  const fed = D.indicators.find(i=>i.ticker==='FEDFUNDS')||{};
  const unrate = D.indicators.find(i=>i.ticker==='UNRATE')||{};
  const cryptoSrc = (D.crypto_live && D.crypto_live.length) ? D.crypto_live : (D.crypto||[]);
  const btc = cryptoSrc.find(c=>c.ticker==='BTC')||{};
  const eth = cryptoSrc.find(c=>c.ticker==='ETH')||{};
  const btcPrice = btc.price !== undefined ? btc.price : (btc.val||0);
  const ethPrice = eth.price !== undefined ? eth.price : (eth.val||0);
  const btcChg = btc.chg_pct !== undefined ? btc.chg_pct : (btc.change||0);
  const pz = D.pizza;
  const pzCol = pz.score>=75?'var(--rose)':pz.score>=55?'var(--coral)':pz.score>=35?'var(--gold)':'var(--mint)';
  const brentCol = brentChg>=0 ? 'var(--coral)' : 'var(--mint)';
  const btcCol = btcChg>=0 ? 'var(--gold)' : 'var(--rose)';

  const items = [
    {num: brentVal ? `$${brentVal.toFixed(0)}` : '-', lbl:'Brent Crude',
     sub:`WTI $${wtiVal ? wtiVal.toFixed(0) : '-'} · ${brentChg>=0?'+':''}${brentChg.toFixed(1)}% today`,
     col: brentCol, glow:'rgba(251,146,60,.14)', bar:`linear-gradient(90deg,transparent,${brentCol},transparent)`},
    {num: fed.val||'-', lbl:'Fed Funds Rate', sub:`Unemployment ${unrate.val||'-'}`,
     col:'var(--sky)', glow:'rgba(56,189,248,.12)', bar:'linear-gradient(90deg,transparent,var(--sky),transparent)'},
    {num: btcPrice ? `$${(btcPrice/1000).toFixed(1)}K` : '-', lbl:'Bitcoin',
     sub:`ETH $${ethPrice ? ethPrice.toFixed(0) : '-'} · ${btcChg>=0?'+':''}${btcChg.toFixed(1)}% 24h`,
     col: btcCol, glow:'rgba(251,191,36,.12)', bar:`linear-gradient(90deg,transparent,${btcCol},transparent)`},
    {num: pz.score, lbl:'🍕 Pizza Index', sub: pz.label,
     col: pzCol, glow:'rgba(251,146,60,.12)', bar:`linear-gradient(90deg,transparent,${pzCol},transparent)`},
  ];
  return <div className="kpi-grid">
    {items.map((k,i)=>(
      <div className="kpi" key={i}>
        <div className="kpi-glow" style={{'--accent-glow':k.glow}}></div>
        <div className="kpi-top-bar" style={{'--accent-bar':k.bar}}></div>
        <div className="kpi-label">{k.lbl}</div>
        <div className="kpi-num" style={{color:k.col}}>{k.num}</div>
        <div className="kpi-sub">{k.sub}</div>
      </div>
    ))}
  </div>;
}

// ── Row 1: Indices / Forex / Commodities / Defense ─────────────
function PanelIndices(){
  const arr = D.indices||[];
  if(!arr.length) return <Panel title="Global Indices"><div className="mn s10 muted">Fetching live data...</div></Panel>;
  const vix = arr.find(x=>x.sym==='^VIX'), vv = vix?vix.price:0;
  const vc = vv>=30?'var(--rose)':vv>=20?'var(--gold)':'var(--mint)';
  return <Panel title="Global Indices">
    {vix && <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'8px 12px',background:'rgba(0,0,0,.3)',border:'1px solid rgba(148,163,184,.1)',borderRadius:8,marginBottom:10}}>
      <span style={{fontFamily:'var(--fm)',fontSize:9,fontWeight:600,color:vc}}>VIX FEAR</span>
      <span style={{fontFamily:'var(--fd)',fontSize:22,color:vc}}>{vv.toFixed(1)} <span style={{fontSize:9}}>{vv>=30?'EXTREME':vv>=20?'HIGH':'CALM'}</span></span>
    </div>}
    {arr.filter(x=>x.sym!=='^VIX').map((x,i)=>{
      const up = x.chg_pct>=0, c = up?'var(--mint)':'var(--rose)';
      const ps = x.price>999 ? x.price.toLocaleString('en-US',{maximumFractionDigits:0}) : x.price.toFixed(2);
      return <div className="card-row" key={i} style={{borderLeftColor:c}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div><span style={{fontSize:12,fontWeight:600,color:'var(--ink)'}}>{x.name}</span> <span className="mn s9 muted">{x.country}</span></div>
          <div><span className="mn">{ps}</span> <span className="mn s10" style={{color:c}}>{up?'▲':'▼'}{Math.abs(x.chg_pct).toFixed(2)}%</span></div>
        </div>
      </div>;
    })}
  </Panel>;
}

function PanelForex(){
  const arr = D.forex||[];
  if(!arr.length) return <Panel title="Forex Rates"><div className="mn s10 muted">Fetching live data...</div></Panel>;
  const cmap = {}; (D.currency_crisis||[]).forEach(c=>{ cmap[c.currency]=c.status; });
  return <Panel title="Forex Rates">
    {arr.map((x,i)=>{
      const up = x.chg_pct>=0, c = up?'var(--mint)':'var(--rose)';
      const cur = x.usd_base ? x.pair.split('/')[1] : x.pair.split('/')[0];
      const cris = cmap[cur]||'';
      return <div className="card-row" key={i} style={{borderLeftColor: cris?'var(--rose)':c}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div>
            <span className="mn" style={{fontWeight:600,color:'var(--ink)'}}>{x.pair}</span>
            {cris && <span className="mn s8" style={{padding:'1px 5px',borderRadius:3,background:'rgba(255,61,90,.1)',color:'var(--rose)',border:'1px solid rgba(255,61,90,.2)',marginLeft:4}}>{cris}</span>}
            <div className="s9 muted">{x.currency_name}</div>
          </div>
          <div><span className="mn">{x.rate.toFixed(4)}</span> <span className="mn s10" style={{color:c}}>{up?'▲':'▼'}{Math.abs(x.chg_pct).toFixed(2)}%</span></div>
        </div>
      </div>;
    })}
  </Panel>;
}

function PanelCommodities(){
  const arr = D.commodities||[];
  if(!arr.length) return <Panel title="Commodities"><div className="mn s10 muted">Fetching live data...</div></Panel>;
  const catL = {energy:'Energy',precious:'Precious Metals',agri:'Agriculture',industrial:'Industrial',nuclear:'Nuclear'};
  const geoNames = ['WTI Crude','Brent Crude','Natural Gas','Wheat (CBOT)'];
  return <Panel title="Commodities">
    {['energy','precious','agri','industrial','nuclear'].map(cat=>{
      const items = arr.filter(x=>x.cat===cat);
      if(!items.length) return null;
      return <React.Fragment key={cat}>
        <div className="mn s8 muted overline" style={{margin:'10px 0 6px'}}>{catL[cat]}</div>
        {items.map((x,i)=>{
          const up = x.chg_pct>=0, c = up?'var(--mint)':'var(--rose)';
          const geo = geoNames.indexOf(x.name)>-1;
          return <div className="card-row" key={i} style={{borderLeftColor: geo?'var(--gold)':c}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
              <div><span style={{fontSize:12,fontWeight:600,color:'var(--ink)'}}>{x.name}</span>{geo && <span className="mn s8" style={{color:'var(--gold)',marginLeft:4}}>GEO</span>}</div>
              <div><span className="mn" style={{color:'var(--gold)'}}>{x.price.toLocaleString('en-US',{maximumFractionDigits:2})}</span> <span className="mn s9 muted">{x.unit}</span> <span className="mn s10" style={{color:c}}>{up?'▲':'▼'}{Math.abs(x.chg_pct).toFixed(2)}%</span></div>
            </div>
          </div>;
        })}
      </React.Fragment>;
    })}
  </Panel>;
}

function PanelDefense(){
  const arr = D.defense||[];
  if(!arr.length) return <Panel title="Defense & Aerospace"><div className="mn s10 muted">Fetching live data...</div></Panel>;
  return <Panel title="Defense & Aerospace" note="Conflict escalation drives these higher">
    {arr.map((x,i)=>{
      const up = x.chg_pct>=0, c = up?'var(--mint)':'var(--rose)';
      const cs = x.currency==='USD'?'$':x.currency==='EUR'?'€':(x.currency==='GBX'||x.currency==='GBP')?'£':'';
      const ps = x.currency==='GBX' ? (x.price/100).toFixed(2) : x.price.toFixed(2);
      return <div className="card-row" key={i} style={{borderLeftColor:'var(--sky)'}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div><span style={{fontSize:12,fontWeight:600,color:'var(--ink)'}}>{x.name}</span><div className="mn s9 muted">{x.country} · {x.sym}</div></div>
          <div><span className="mn" style={{color:'var(--sky)'}}>{cs}{ps}</span> <span className="mn s10" style={{color:c}}>{up?'▲':'▼'}{Math.abs(x.chg_pct).toFixed(2)}%</span></div>
        </div>
      </div>;
    })}
  </Panel>;
}

// ── Row 2: Crypto / Sanctions / Currency Crisis ────────────────
function PanelCrypto(){
  const arr = (D.crypto_live && D.crypto_live.length) ? D.crypto_live : (D.crypto||[]);
  return <Panel title="Cryptocurrency">
    {arr.length ? arr.map((x,i)=>{
      const chgV = x.chg_pct!=null ? x.chg_pct : (x.change||0), up = chgV>=0, c = up?'var(--mint)':'var(--rose)';
      const mcap = x.mcap>1e12 ? '$'+(x.mcap/1e12).toFixed(2)+'T' : x.mcap>1e9 ? '$'+(x.mcap/1e9).toFixed(1)+'B' : '';
      const price = x.price!=null ? x.price : (x.val||0);
      return <div className="card-row" key={i} style={{borderLeftColor:'var(--gold)'}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
          <div><span style={{fontSize:12,fontWeight:600,color:'var(--ink)'}}>{x.name}</span> <span className="mn s9 muted">{x.ticker}</span>{mcap && <div className="mn s9 muted">MCap {mcap}</div>}</div>
          <div><span className="mn" style={{color:'var(--gold)'}}>${price.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}</span> <span className="mn s10" style={{color:c}}>{up?'▲':'▼'}{Math.abs(chgV).toFixed(2)}%</span></div>
        </div>
      </div>;
    }) : <div className="mn s10 muted">Loading from CoinGecko...</div>}
  </Panel>;
}

function PanelSanctions(){
  const arr = D.sanctions||[];
  return <Panel title="Active Sanctions">
    {arr.map((s,i)=>{
      const col = s.impact==='Critical'?'var(--rose)':s.impact==='High'?'var(--coral)':'var(--gold)';
      return <div className="card-row" key={i} style={{borderLeftColor:col}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:5}}>
          <div><span style={{fontSize:13,fontWeight:700,color:'var(--ink)'}}>{s.entity}</span> <span className="mn s9 muted">{s.type} · Since {s.year}</span></div>
          <span className="mn s9" style={{padding:'2px 7px',borderRadius:4,background:'rgba(0,0,0,.3)',color:col}}>{s.impact}</span>
        </div>
        <div className="mn s9 muted" style={{marginBottom:4}}>{s.scope}</div>
        <div style={{fontSize:11,color:'var(--ink2)',lineHeight:1.6}}>{s.detail}</div>
      </div>;
    })}
  </Panel>;
}

function PanelCurrencyCrisis(){
  const sorted = [...(D.currency_crisis||[])].sort((a,b)=>b.yoy_chg-a.yoy_chg);
  return <Panel title="Currency Devaluation Monitor">
    {sorted.map((c,i)=>{
      const pct = Math.min(c.yoy_chg/250*100,100), col = c.col||'var(--rose)';
      return <div className="card-row" key={i} style={{borderLeftColor:col}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:4}}>
          <div><span style={{fontSize:12,fontWeight:700,color:'var(--ink)'}}>{c.country}</span> <span className="mn s9 muted">{c.currency}</span></div>
          <div><span className="mn s11">1 USD = {c.usd_rate.toLocaleString()}</span> <span className="mn s10" style={{color:col,marginLeft:8}}>▲{c.yoy_chg}% YoY</span></div>
        </div>
        <div style={{height:4,background:'rgba(148,163,184,.08)',borderRadius:2,overflow:'hidden',marginBottom:5}}>
          <div style={{height:'100%',width:pct+'%',background:col,borderRadius:2}}></div>
        </div>
        <div className="s10 muted">{c.note}</div>
      </div>;
    })}
  </Panel>;
}

function PanelGeoRisk(){
  const arr = D.geo_risk||[];
  return <Panel title="Geopolitical Risk Premiums">
    <div className="s10 muted" style={{marginBottom:10}}>Market price impact of active conflicts and tensions</div>
    {arr.map((r,i)=>{
      const col = r.status==='Active'?'var(--rose)':r.status==='Elevated'?'var(--coral)':'var(--gold)';
      return <div className="card-row" key={i} style={{borderLeftColor:col}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:12}}>
          <div><div style={{fontSize:12,fontWeight:700,color:'var(--ink)'}}>{r.name}</div><div className="mn s9 muted" style={{marginTop:2}}>{r.driver} — <span style={{color:'var(--sky)'}}>{r.asset}</span></div></div>
          <div style={{textAlign:'right',flexShrink:0}}><div className="mn s11" style={{fontWeight:700,color:col}}>{r.impact}</div><span className="mn s9" style={{padding:'1px 6px',borderRadius:3,background:'rgba(0,0,0,.3)',color:col}}>{r.status}</span></div>
        </div>
      </div>;
    })}
  </Panel>;
}

// ── Economic Indicators (pill tabs: Macro / Energy / Bonds) ────
function EconPanel(){
  const ind = D.indicators.map((e,i)=>{
    const cc = e.up ? 'var(--mint)' : 'var(--rose)';
    return <div className="card-row" key={i} style={{borderLeftColor:cc}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <div><div style={{fontSize:13,fontWeight:600,color:'var(--ink)'}}>{e.name}</div><div className="mono" style={{fontSize:9,color:'var(--ink3)',marginTop:2}}>{e.ticker} · {e.date}</div></div>
        <div style={{textAlign:'right'}}><div className="disp" style={{fontSize:24,color:'var(--sky)'}}>{e.val}</div><div><Chg v={parseFloat(e.change)||0} /></div></div>
      </div>
    </div>;
  });
  const oil = D.oil.map((o,i)=>(
    <div className="card-row" key={i} style={{borderLeftColor:'var(--coral)'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <div style={{fontSize:13,fontWeight:600,color:'var(--ink)'}}>{o.name}</div>
        <div style={{textAlign:'right'}}>
          <span className="disp" style={{fontSize:24,color:'var(--gold)'}}>{o.val.toFixed(2)}</span>
          <span className="mono" style={{fontSize:10,color:'var(--ink3)',marginLeft:5}}>{o.unit}</span>
          <div><Chg v={o.change} /></div>
        </div>
      </div>
    </div>
  ));
  const bonds = D.bonds.map((b,i)=>(
    <div className="card-row" key={i} style={{borderLeftColor:b.col}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
        <div style={{display:'flex',alignItems:'center',gap:8}}><span style={{fontSize:13,fontWeight:600,color:'var(--ink)'}}>{b.name}</span><Badge txt={b.rating} cls="neu" /></div>
        <div style={{display:'flex',alignItems:'center',gap:12}}><span className="disp" style={{fontSize:22,color:b.col}}>{b.yield.toFixed(2)}%</span><Chg v={b.change} /></div>
      </div>
    </div>
  ));
  return <PillCard title="Economic Indicators" tabs={[
    {label:'Macro', content: ind}, {label:'Energy', content: oil}, {label:'Bonds', content: bonds},
  ]} />;
}

// ── Trade Policy (pill tabs) ────────────────────────────────────
function TradePanel(){
  const restr = D.restrictions.map((t,i)=>(
    <div className="card-row" key={i} style={{borderLeftColor:'rgba(148,163,184,.2)'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:10,marginBottom:6}}>
        <div><div style={{fontSize:13,fontWeight:600,color:'var(--ink)'}}>{t.country}</div><div style={{fontSize:11,color:'var(--ink2)',marginTop:3,lineHeight:1.45}}>{t.coverage}</div></div>
        <Badge txt={t.impact} cls={sevCls(t.impact)} />
      </div>
      <div className="mono" style={{fontSize:9,color:'var(--ink3)'}}>Avg tariff {t.avg_rate}% · {t.year} · WTO</div>
    </div>
  ));
  const tariffs = D.tariffs.map((t,i)=>(
    <div className="card-row" key={i} style={{borderLeftColor:'rgba(248,113,113,.3)'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:4}}>
        <span style={{fontSize:13,fontWeight:600,color:'var(--ink)'}}>{t.route}</span><Badge txt={t.impact} cls={sevCls(t.impact)} />
      </div>
      <div style={{display:'flex',alignItems:'baseline',gap:10,marginBottom:3}}>
        <span className="disp" style={{fontSize:28,color:'var(--rose)'}}>{t.rate}%</span>
        <span className="mono" style={{fontSize:11,color:'var(--coral)'}}>{t.change}</span>
      </div>
      <div className="mono" style={{fontSize:9,color:'var(--ink3)'}}>{t.sector}</div>
    </div>
  ));
  return <PillCard title="Trade Policy" tabs={[{label:'Restrictions',content:restr},{label:'Tariffs',content:tariffs}]} />;
}

// ── Supply Chain (pill tabs) ─────────────────────────────────────
function SupplyPanel(){
  const chk = D.chokepoints.map((cp,i)=>{
    const sc = cp.status==='red'?'var(--rose)':cp.status==='amber'?'var(--gold)':'var(--mint)';
    const wc = cp.wow_change<0?'var(--rose)':'var(--mint)';
    const ctx = cp.context||'';
    return <div className="card-row" key={i} style={{borderLeftColor:sc,marginBottom:12}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:5}}>
        <span style={{fontSize:13,fontWeight:700,color:'var(--ink)'}}>{cp.name}</span>
        <span className="disp" style={{fontSize:20,color:sc}}>{cp.risk}</span>
      </div>
      <Bar pct={cp.risk} col={sc} thick />
      <div style={{display:'flex',gap:14,marginTop:5,flexWrap:'wrap'}}>
        <span className="mono" style={{fontSize:9,color:'var(--ink3)'}}>{cp.warnings} warning(s)</span>
        <span className="mono" style={{fontSize:9,color:'var(--ink3)'}}>{cp.ais_disruptions} AIS</span>
        <span className="mono" style={{fontSize:9,color:wc}}>WoW {cp.wow_change>0?'+':''}{cp.wow_change}%</span>
      </div>
      <div style={{fontSize:11,color:'var(--ink2)',lineHeight:1.55,marginTop:6}}>{ctx.substring(0,150)}{ctx.length>150?'…':''}</div>
    </div>;
  });
  const ship = D.shipping.map((r,i)=>{
    const sc = r.status==='Elevated'?'var(--rose)':r.status==='Rising'?'var(--gold)':r.status==='Reduced'?'var(--coral)':'var(--mint)';
    const up = r.change>=0;
    const rateStr = r.rate>999 ? r.rate.toLocaleString() : (typeof r.rate==='number' ? r.rate.toFixed(2) : r.rate);
    return <div className="card-row" key={i} style={{borderLeftColor:sc}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:10}}>
        <div><div style={{fontSize:12,fontWeight:600,color:'var(--ink)'}}>{r.route}</div><div className="mono" style={{fontSize:9,color:'var(--ink3)',marginTop:2}}>{r.type} · {r.note}</div></div>
        <div style={{textAlign:'right',flexShrink:0}}>
          <span className="disp" style={{fontSize:20,color:sc}}>{rateStr}</span>
          <span className="mono" style={{fontSize:9,color:'var(--ink3)',marginLeft:3}}>{r.unit}</span>
          <div className="mono" style={{fontSize:10,color: up?'var(--rose)':'var(--mint)'}}>{up?'▲':'▼'}{Math.abs(r.change).toFixed(1)}%</div>
        </div>
      </div>
    </div>;
  });
  const min = D.minerals.map((m,i)=>{
    const dn = m.change<=0, mc = dn?'var(--mint)':'var(--rose)';
    const sr = m.supply_risk, sc = sr>=80?'var(--rose)':sr>=60?'var(--coral)':sr>=40?'var(--gold)':'var(--mint)';
    return <div className="card-row" key={i} style={{borderLeftColor:m.col}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:4}}>
        <span style={{fontSize:13,fontWeight:700,color:'var(--ink)'}}>{m.mineral}</span>
        <div style={{display:'flex',alignItems:'baseline',gap:8}}>
          <span className="disp" style={{fontSize:20,color:m.col}}>{m.price}</span>
          <span className="mono" style={{fontSize:9,color:'var(--ink3)'}}>{m.unit}</span>
          <span className="mono" style={{fontSize:10,color:mc}}>{dn?'▼':'▲'}{Math.abs(m.change).toFixed(1)}%</span>
        </div>
      </div>
      <Bar pct={sr} col={sc} />
      <div style={{display:'flex',justifyContent:'space-between',marginTop:3}}>
        <span className="mono" style={{fontSize:9,color:'var(--ink3)'}}>Supply risk: <span style={{color:sc}}>{sr}</span></span>
        <span className="mono" style={{fontSize:9,color:'var(--ink3)'}}>{m.top_producer}</span>
      </div>
    </div>;
  });
  return <PillCard title="Supply Chain" tabs={[{label:'Chokepoints',content:chk},{label:'Shipping',content:ship},{label:'Minerals',content:min}]} />;
}

// ── Financial (crypto + sector heatmap + posture) ───────────────
function FinPanel(){
  const nfUp = D.btc_etf.net_flow >= 0, nfCol = nfUp ? 'var(--mint)' : 'var(--rose)';
  const mCol = D.market.label === 'CASH' ? 'var(--gold)' : 'var(--sky)';
  const cryptoSrc = (D.crypto_live && D.crypto_live.length) ? D.crypto_live : (D.crypto || []);
  const isLive = D.crypto_live && D.crypto_live.length;

  return <div className="card">
    <div className="section-title">Financial {D.ts && <span className="mono" style={{fontSize:8,color:'var(--ink3)',marginLeft:8}}>{D.ts}</span>}</div>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:20}}>
      <div>
        <div className="overline" style={{marginBottom:10}}>Crypto
          {isLive
            ? <span className="live-chip" style={{marginLeft:6}}><span className="live-dot"></span>CoinGecko</span>
            : <span className="mono" style={{fontSize:8,color:'var(--ink3)',marginLeft:6}}>static</span>}
        </div>
        {cryptoSrc.length ? cryptoSrc.map((c,i)=>{
          const chgV = c.chg_pct !== undefined ? c.chg_pct : (c.change || 0);
          const price = c.price !== undefined ? c.price : (c.val || 0);
          const up = chgV >= 0, cc = up ? 'var(--mint)' : 'var(--rose)';
          const mcap = c.mcap > 1e12 ? `$${(c.mcap/1e12).toFixed(2)}T` : c.mcap > 1e9 ? `$${(c.mcap/1e9).toFixed(1)}B` : '';
          return <div className="card-row" key={i} style={{borderLeftColor:cc,display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <div><div style={{fontSize:13,fontWeight:600,color:'var(--ink)'}}>{c.name}</div><div className="mono" style={{fontSize:9,color:'var(--ink3)'}}>{c.ticker}{mcap?' · '+mcap:''}</div></div>
            <div style={{textAlign:'right'}}>
              <div className="mono" style={{fontSize:13,color:'var(--ink)'}}>${price.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}</div>
              <div className="mono" style={{fontSize:10,color:cc}}>{up?'+':''}{Math.abs(chgV).toFixed(2)}%</div>
            </div>
          </div>;
        }) : <div className="mono" style={{fontSize:10,color:'var(--ink3)'}}>Loading…</div>}
      </div>
      <div>
        <div className="overline" style={{marginBottom:10}}>Sector Heatmap</div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:6,marginBottom:16}}>
          {D.sectors.map((s,i)=>{
            const up = s.v >= 0, intensity = Math.min(Math.abs(s.v)/8, 1);
            const bg = up ? `rgba(52,211,153,${.08+intensity*.18})` : `rgba(248,113,113,${.08+intensity*.18})`;
            const col = up ? 'var(--mint)' : 'var(--rose)';
            return <div className="sector-cell" key={i} style={{background:bg}}>
              <div className="mono" style={{fontSize:8,color:'var(--ink3)',marginBottom:3}}>{s.s}</div>
              <div className="mono" style={{fontSize:12,fontWeight:700,color:col}}>{up?'+':''}{s.v}%</div>
            </div>;
          })}
        </div>
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:10}}>
          <div style={{background:'var(--raised)',border:'1px solid var(--edge2)',borderRadius:10,padding:14,textAlign:'center'}}>
            <div className="overline" style={{marginBottom:8}}>Market Posture</div>
            <div className="disp" style={{fontSize:28,color:mCol,marginBottom:5}}>{D.market.label}</div>
            <div className="mono" style={{fontSize:9,color:'var(--ink3)'}}>{D.market.posture}</div>
            <div className="mono" style={{fontSize:9,color:'var(--gold)',marginTop:3}}>{D.market.flow}</div>
          </div>
          <div style={{background:'var(--raised)',border:'1px solid var(--edge2)',borderRadius:10,padding:14,textAlign:'center'}}>
            <div className="overline" style={{marginBottom:8}}>BTC ETF Flow</div>
            <div className="disp" style={{fontSize:28,color:nfCol,marginBottom:5}}>${Math.abs(D.btc_etf.net_flow)}M</div>
            <Badge txt={nfUp?'INFLOW':'OUTFLOW'} cls={nfUp?'low':'crit'} />
            <div className="mono" style={{fontSize:9,color:'var(--ink3)',marginTop:6}}>Est. ${D.btc_etf.est_flow}M</div>
          </div>
        </div>
      </div>
    </div>
  </div>;
}

// ── Row 2: Layoffs (with sector filter state) + Fires table ────
function Row2(){
  const [selSec, setSelSec] = useState('All');
  const allSectors = [...new Set((D.layoffs||[]).map(l=>l.sector||'Other'))].sort();
  const filtered = (D.layoffs||[]).filter(l=> selSec==='All' || (l.sector||'Other')===selSec);

  return <div className="duo-grid">
    <div className="card" style={{gridColumn:'1/-1'}}>
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:8,marginBottom:10}}>
        <div style={{display:'flex',alignItems:'center',gap:10}}>
          <div className="section-title" style={{margin:0}}>Corporate Layoffs</div>
          <span className="live-chip"><span className="live-dot"></span>Live · Google News + GDELT</span>
        </div>
        <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:9,color:'var(--ink3)'}}>{filtered.length} reports · refreshes every 5 min</div>
      </div>
      <div style={{marginBottom:10,display:'flex',flexWrap:'wrap'}}>
        {['All',...allSectors].map((s,i)=>(
          <button key={i} onClick={()=>setSelSec(s)}
            style={{fontFamily:'JetBrains Mono,monospace',fontSize:9,padding:'3px 10px',borderRadius:3,cursor:'pointer',
                    border:'1px solid '+(s===selSec?'var(--sky)':'rgba(148,163,184,.15)'),
                    background: s===selSec?'rgba(56,189,248,.1)':'transparent',
                    color: s===selSec?'var(--sky)':'var(--ink3)', margin:'0 3px 4px 0'}}>{s}</button>
        ))}
      </div>
      <div className="scroll" style={{maxHeight:420}}>
        {filtered.slice(0,20).map((l,i)=>{
          const sc = l.severity==='Critical'?'var(--rose)':l.severity==='High'?'var(--coral)':l.severity==='Med'?'var(--gold)':'var(--mint)';
          const hasUrl = l.url && l.url.length > 4;
          return <div className="card-row" key={i} style={{borderLeftColor:sc,padding:'10px 12px'}}>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:5}}>
              <div style={{flex:1,minWidth:0}}>
                <div style={{display:'flex',alignItems:'center',gap:6,marginBottom:3,flexWrap:'wrap'}}>
                  <span style={{fontSize:13,fontWeight:700,color:'var(--ink)'}}>{l.company}</span>
                  <Badge txt={(l.severity||'').toUpperCase()} cls={sevCls(l.severity)} />
                  {l.age && <span className="mono" style={{fontSize:8,color:'var(--ink3)',marginLeft:6}}>{l.age}</span>}
                </div>
                <div style={{fontSize:11,color:'var(--ink2)',lineHeight:1.45,marginBottom:4}}>{(l.headline||'').slice(0,100)}</div>
              </div>
              <div style={{flexShrink:0,marginLeft:10,textAlign:'right'}}>
                <div className="mono" style={{fontSize:11,color:'var(--gold)',fontWeight:600}}>{l.count}</div>
                <div className="mono" style={{fontSize:9,color:'var(--ink3)',marginTop:2}}>{l.sector||''}</div>
              </div>
            </div>
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
              <span className="mono" style={{fontSize:9,color:'var(--ink3)'}}>{l.source||''} · {l.date||''}</span>
              {hasUrl && <a href={l.url} target="_blank" rel="noopener" style={{fontFamily:'JetBrains Mono,monospace',fontSize:9,color:'var(--sky)',textDecoration:'none',padding:'2px 8px',border:'1px solid rgba(56,189,248,.25)',borderRadius:3,whiteSpace:'nowrap'}}>Read ↗</a>}
            </div>
          </div>;
        })}
        {filtered.length===0 && <div style={{fontFamily:'JetBrains Mono,monospace',fontSize:10,color:'var(--ink3)',padding:20,textAlign:'center'}}>No layoffs reported for this sector.</div>}
      </div>
    </div>
    <div className="card">
      <div className="section-title">🔥 Active Wildfires</div>
      <table className="fire-tbl">
        <thead><tr><th>Region</th><th>Fires</th><th>High</th><th>FRP</th></tr></thead>
        <tbody>
          {D.fires.map((f,i)=>{
            const ic = f.high>50?'var(--rose)':f.high>20?'var(--coral)':'var(--gold)';
            return <tr key={i}>
              <td><span style={{fontSize:12,fontWeight:600,color:'var(--ink)'}}>{f.region}</span><span style={{display:'block',fontSize:9,color:'var(--ink3)'}} className="mono">{f.biome||''}</span></td>
              <td className="mono" style={{color:'var(--sky)'}}>{f.fires.toLocaleString()}</td>
              <td className="mono" style={{color:ic}}>{f.high}</td>
              <td className="mono" style={{color:'var(--ink3)'}}>{(f.frp/1000).toFixed(1)}k FRP</td>
            </tr>;
          })}
        </tbody>
      </table>
    </div>
  </div>;
}

// ── Pizza Index ──────────────────────────────────────────────
function PizzaSection(){
  const pz = D.pizza;
  const col = pz.score>=75?'var(--rose)':pz.score>=55?'var(--coral)':pz.score>=35?'var(--gold)':'var(--mint)';
  return <React.Fragment>
    <div style={{background:'var(--surface)',border:'1px solid var(--edge)',borderRadius:16,padding:'28px 30px',marginBottom:24,position:'relative',overflow:'hidden'}}>
      <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',gap:32,flexWrap:'wrap'}}>
        <div>
          <div className="overline" style={{marginBottom:12}}>🍕 Pizza Index &nbsp;<span className="badge neu" style={{fontSize:8}}>PIZZAINT METHODOLOGY</span></div>
          <div className="pz-score" style={{color:col}}>{pz.score}</div>
          <div className="mono" style={{fontSize:13,color:col,marginTop:10,letterSpacing:'.06em'}}>{pz.label}</div>
        </div>
        <div style={{flex:1,minWidth:200,maxWidth:500}}>
          <div style={{fontSize:13,color:'var(--ink2)',lineHeight:1.8,marginBottom:18}}>{pz.description}</div>
          <div className="overline" style={{marginBottom:8}}>Stress gauge</div>
          <div className="pz-bar"><div className="pz-needle" style={{left:pz.score+'%'}}></div></div>
          <div style={{display:'flex',justifyContent:'space-between',marginTop:4}}>
            <span className="mono" style={{fontSize:9,color:'var(--mint)'}}>Low</span>
            <span className="mono" style={{fontSize:9,color:'var(--gold)'}}>Threshold 60</span>
            <span className="mono" style={{fontSize:9,color:'var(--rose)'}}>Critical 80+</span>
          </div>
        </div>
      </div>
    </div>
    <div className="duo-grid">
      <div className="card">
        <div className="section-title">📦 Input Components</div>
        <div className="scroll">
          {pz.components.map((c,i)=>{
            const sc = c.stress, scol = sc>=80?'var(--rose)':sc>=60?'var(--coral)':sc>=40?'var(--gold)':'var(--mint)';
            const up = c.change>0, csym = up?'▲':'▼', ccol = up?'var(--rose)':'var(--mint)';
            return <div className="card-row" key={i} style={{borderLeftColor:scol}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:5}}>
                <div><div style={{fontSize:13,fontWeight:600,color:'var(--ink)'}}>{c.name}</div><div className="mono" style={{fontSize:9,color:'var(--ink3)',marginTop:2}}>{c.note}</div></div>
                <div style={{textAlign:'right',flexShrink:0,marginLeft:14}}>
                  <span className="mono" style={{fontSize:12,color:'var(--ink2)'}}>{c.val} <span style={{fontSize:9,color:'var(--ink3)'}}>{c.unit}</span></span>
                  <div><span className="mono" style={{fontSize:10,color:ccol}}>{csym}{Math.abs(c.change).toFixed(1)}%</span><span className="disp" style={{fontSize:22,color:scol,marginLeft:8}}>{sc}</span></div>
                </div>
              </div>
              <Bar pct={sc} col={scol} thick />
            </div>;
          })}
        </div>
      </div>
      <div className="card">
        <div className="section-title">🌍 City Price Index</div>
        <div className="scroll">
          {[...pz.city_prices].sort((a,b)=>b.stress-a.stress).map((c,i)=>{
            const sc = c.stress, scol = sc>=80?'var(--rose)':sc>=60?'var(--coral)':sc>=40?'var(--gold)':'var(--mint)';
            const pct = Math.round((c.price-c.baseline)/c.baseline*100);
            return <div className="card-row" key={i} style={{borderLeftColor:scol}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:4}}>
                <span style={{fontSize:13,fontWeight:600,color:'var(--ink)'}}>{c.city}</span>
                <div style={{display:'flex',alignItems:'center',gap:10}}>
                  <span className="mono" style={{fontSize:13,color:'var(--ink)'}}>{c.price} {c.currency}</span>
                  <span className="mono" style={{fontSize:10,color:'var(--coral)'}}>+{pct}%</span>
                  <span className="disp" style={{fontSize:22,color:scol}}>{sc}</span>
                </div>
              </div>
              <Bar pct={sc} col={scol} />
              <div className="mono" style={{fontSize:9,color:'var(--ink3)',marginTop:2}}>baseline {c.baseline} {c.currency}</div>
            </div>;
          })}
        </div>
        <div style={{marginTop:16,padding:'16px 18px',background:'rgba(251,146,60,.06)',border:'1px solid rgba(251,146,60,.18)',borderRadius:10}}>
          <div className="overline" style={{color:'var(--coral)',marginBottom:8}}>Methodology</div>
          <div style={{fontSize:12,color:'var(--ink2)',lineHeight:1.75}}>
            Inspired by <em>The Economist</em>'s Big Mac Index. Tracks margherita pizza prices
            as a proxy for wheat disruption, energy costs, and purchasing power stress.
            Scores above <strong style={{color:'var(--gold)'}}>60</strong> indicate material supply-chain pressure.
          </div>
        </div>
      </div>
    </div>
  </React.Fragment>;
}

// ── Root App ────────────────────────────────────────────────
function App(){
  return <React.Fragment>
    <KPIStrip />
    <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:14,marginBottom:18}}>
      <PanelIndices /><PanelForex /><PanelCommodities /><PanelDefense />
    </div>
    <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:14,marginBottom:18}}>
      <PanelCrypto /><PanelSanctions /><PanelCurrencyCrisis />
    </div>
    <PanelGeoRisk />
    <div className="main-grid" style={{marginTop:18}}>
      <EconPanel /><TradePanel /><SupplyPanel />
    </div>
    <div style={{marginBottom:24}}><FinPanel /></div>
    <hr className="divider" />
    <Row2 />
    <hr className="divider" />
    <PizzaSection />
  </React.Fragment>;
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);

</script>
</body></html>"""
    _econ_html = _econ_template.replace("__PAYLOAD__", _econ_payload)

    _ec.html(_econ_html, height=5200, scrolling=True)


if _active_tab == "🏭  Facility Map":
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
