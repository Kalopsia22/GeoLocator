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
    st_autorefresh(interval=300_000, key="auto5min")
except ImportError:
    pass

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{
  --void:#02040a;--deep:#060d18;--panel:#080f1c;--card:#0b1524;
  --glass:rgba(8,15,28,.88);--border:rgba(0,200,255,.12);--bord2:rgba(0,200,255,.06);
  --cyan:#00c8ff;--amber:#ffb400;--red:#ff3d5a;--green:#00e676;
  --violet:#9d6eff;--orange:#ff8c42;--text:#e2ecf8;--text2:#a8c0d8;
  --muted:#4a6b85;--dim:#0f2035;
  --fd:'Bebas Neue','Impact',sans-serif;
  --fm:'IBM Plex Mono','Courier New',monospace;
  --fb:'DM Sans',system-ui,sans-serif;
}
html,body,[class*="css"],.stApp{font-family:var(--fb)!important;background:var(--void)!important;color:var(--text)!important;}
.stApp::before{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.02) 3px,rgba(0,0,0,.02) 6px);pointer-events:none;z-index:9000;}
.stApp::after{content:'';position:fixed;inset:0;background:radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,.45) 100%);pointer-events:none;z-index:9001;}
::-webkit-scrollbar{width:4px;height:4px}::-webkit-scrollbar-track{background:var(--deep)}::-webkit-scrollbar-thumb{background:rgba(0,200,255,.2);border-radius:2px}
section[data-testid="stSidebar"]{background:var(--deep)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] .stMarkdown,section[data-testid="stSidebar"] label,section[data-testid="stSidebar"] p{color:var(--text)!important;}
.stTabs [data-baseweb="tab-list"]{background:var(--deep)!important;border-bottom:1px solid var(--border)!important;gap:0!important;padding:0 8px;}
.stTabs [data-baseweb="tab"]{background:transparent!important;border-bottom:3px solid transparent!important;font-family:var(--fb)!important;font-weight:600!important;font-size:13px!important;letter-spacing:.06em!important;color:var(--muted)!important;padding:14px 20px!important;}
.stTabs [aria-selected="true"]{color:var(--cyan)!important;border-bottom-color:var(--cyan)!important;}
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
.t-sep{color:var(--cyan);margin:0 16px;}
.t-hi{color:var(--text);}
.t-red{color:var(--red);}
.t-amb{color:var(--amber);}
.helper{font-size:12px;color:var(--muted);line-height:1.6;padding:10px 14px;background:var(--dim);border-radius:8px;border-left:3px solid var(--bord2);margin-bottom:14px;}
.helper b{color:var(--text2);font-style:normal;}
.sb-div{height:1px;background:var(--bord2);margin:16px 0;}
.tl-item{position:relative;margin-bottom:16px;padding-left:22px;}
.tl-item::before{content:'';position:absolute;left:0;top:4px;width:9px;height:9px;border-radius:50%;border:2px solid var(--dim);}
.tl-date{font-family:var(--fm);font-size:10px;color:var(--muted);margin-bottom:3px;}
.tl-text{font-size:13px;color:var(--text);line-height:1.5;}
.tl-tag{font-family:var(--fm);font-size:9px;margin-top:2px;}
.live-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;background:rgba(255,61,90,.1);border:1px solid rgba(255,61,90,.3);border-radius:20px;font-family:var(--fm);font-size:9px;color:var(--red);}

/* ═══════════════════════════════════════════
   MOBILE RESPONSIVE — phones & small tablets
   ═══════════════════════════════════════════ */
@media (max-width: 768px) {
  /* Stack header vertically */
  .status-row { gap:10px!important; padding:6px 0 10px!important; font-size:10px!important; }
  .wordmark   { font-size:22px!important; letter-spacing:.1em!important; }

  /* Tighten map header */
  .map-top-bar { flex-direction:column!important; align-items:flex-start!important; gap:6px!important; padding:10px 14px!important; }
  .map-legend  { gap:8px!important; font-size:9px!important; flex-wrap:wrap!important; }
  .map-title-text { font-size:14px!important; }

  /* Compact metric cards */
  div[data-testid="stMetric"] { padding:10px 12px!important; }
  div[data-testid="stMetricValue"] { font-size:18px!important; }
  div[data-testid="stMetricLabel"] { font-size:10px!important; }

  /* Full-width tabs, smaller font */
  .stTabs [data-baseweb="tab"] { padding:10px 10px!important; font-size:11px!important; letter-spacing:.02em!important; }

  /* Cards */
  .gcard { padding:12px 14px!important; }
  .conflict-card .cc-body { padding:10px 12px!important; }
  .incident-row { gap:8px!important; padding:10px 0!important; }
  .inc-title { font-size:12px!important; }
  .m-val { font-size:28px!important; }

  /* Tracker header — stack vertically */
  .tracker-header { flex-direction:column!important; gap:12px!important; }

  /* News cards grid */
  .grid { grid-template-columns:1fr!important; }

  /* Sidebar toggles — more touch-friendly */
  .stToggle label { font-size:13px!important; }

  /* Scrollable news feed on mobile */
  .news-feed-mobile { max-height:60vh!important; overflow-y:auto!important; }

  /* Ticker */
  .ticker-inner { font-size:10px!important; }

  /* Buttons */
  .stButton>button { padding:8px 14px!important; font-size:12px!important; }

  /* Helper text */
  .helper { font-size:11px!important; }

  /* Reduce chart heights for mobile */
  .js-plotly-plot { min-height:140px!important; }
}

@media (max-width: 480px) {
  .wordmark { font-size:18px!important; }
  .stTabs [data-baseweb="tab"] { padding:8px 7px!important; font-size:10px!important; }
  .map-top-bar { padding:8px 10px!important; }
  div[data-testid="stMetricValue"] { font-size:15px!important; }
  .m-val { font-size:22px!important; }
  .gcard { padding:10px 11px!important; margin-bottom:7px!important; }
  .live-badge { font-size:8px!important; padding:2px 7px!important; }
}

/* Touch-friendly map tooltip — larger on mobile */
@media (max-width: 768px) {
  .deck-tooltip {
    font-size:13px!important;
    padding:12px 16px!important;
    max-width:260px!important;
    line-height:1.7!important;
  }
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {
    "selected_conflict": "Ukraine–Russia War",
    "last_refresh": 0,
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
}

INCIDENT_ICONS = {"airstrike":"💥","ground":"⚔️","drone":"🛸","naval":"⚓","rocket":"🚀","cyber":"💻","diplomatic":"🤝","humanitarian":"🏥"}
INCIDENT_COLORS = {
    "airstrike":"rgba(255,61,90,.18)","ground":"rgba(255,140,66,.15)","drone":"rgba(157,110,255,.15)",
    "naval":"rgba(0,200,255,.15)","rocket":"rgba(255,180,0,.15)","cyber":"rgba(0,200,255,.12)",
    "diplomatic":"rgba(0,230,118,.12)","humanitarian":"rgba(0,200,255,.1)",
}
SEV_BADGE = {"CRITICAL":"b-red","HIGH":"b-orange","MED":"b-amber","LOW":"b-green","INFO":"b-muted"}

MOVEMENTS = [
    {"id":"mv1","type":"protest","title":"Anti-austerity rally","location":"Athens, Greece","country":"GR","size":"40,000+","sentiment":"HIGH","scale":82,"lat":37.98,"lon":23.73,"age_h":2},
    {"id":"mv2","type":"strike","title":"Railway workers strike","location":"Paris, France","country":"FR","size":"National","sentiment":"MED","scale":55,"lat":48.85,"lon":2.35,"age_h":6},
    {"id":"mv3","type":"civil","title":"Democracy march","location":"Seoul, South Korea","country":"KR","size":"120,000+","sentiment":"HIGH","scale":90,"lat":37.57,"lon":126.98,"age_h":1},
    {"id":"mv4","type":"protest","title":"Climate blockades","location":"Berlin, Germany","country":"DE","size":"8,000","sentiment":"MED","scale":40,"lat":52.52,"lon":13.41,"age_h":18},
    {"id":"mv5","type":"strike","title":"Dockworkers walkout","location":"Buenos Aires","country":"AR","size":"Port-wide","sentiment":"MED","scale":48,"lat":-34.61,"lon":-58.38,"age_h":8},
    {"id":"mv6","type":"civil","title":"Farmers protest","location":"New Delhi, India","country":"IN","size":"200,000+","sentiment":"CRIT","scale":95,"lat":28.61,"lon":77.21,"age_h":3},
    {"id":"mv7","type":"protest","title":"Cost-of-living rally","location":"London, UK","country":"GB","size":"25,000","sentiment":"MED","scale":50,"lat":51.51,"lon":-0.12,"age_h":14},
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
        return pd.DataFrame(rows)
    except:
        return _sq()

@st.cache_data(ttl=300, show_spinner=False)
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

@st.cache_data(ttl=180, show_spinner=False)
def fetch_kp():
    try:
        r = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=6)
        r.raise_for_status()
        data = r.json()
        return {"kp": float(data[-1][1]), "series": [float(x[1]) for x in data[-24:] if len(x)>1]}
    except:
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
        "war attack military strike conflict",
        "earthquake flood disaster natural",
        "nuclear missile launch threat",
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
    return all_arts[:max_records]


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
@st.cache_data(ttl=60, show_spinner=False)
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
    """Gather all data signals for a country from the static datasets."""
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
    # Military activity
    for m in MILITARY_ACTIVITY:
        if c_lower in m.get("country","").lower() or c_lower in m.get("name","").lower():
            signals["military_activity"].append(m["name"])
    # Historical events (recent 5)
    for e in sorted(HISTORICAL_EVENTS, key=lambda x: x["date"], reverse=True):
        if c_lower in e.get("title","").lower() or c_lower in e.get("tip","").lower():
            signals["historical_events"].append(e)
            if len(signals["historical_events"]) >= 5:
                break
    # Instability index — uses live GDELT-blended data
    signals["instability"] = get_instability_for_country(country)
    # Nuke alerts
    for na in NUKE_ALERTS:
        if c_lower in na["site"].lower():
            signals["nuke_alerts"].append(na)
    # WMD posture
    for wp in WMD_POSTURE:
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
    {"name":"Diego Garcia (BIOT)","country":"US/UK","lat":-7.3,"lon":72.4,"type":"Naval/Air","tip":"🏛 MILITARY BASE | Diego Garcia | US/UK | Naval-Air | Indian Ocean hub"},
    {"name":"Ramstein AFB","country":"USA","lat":49.44,"lon":7.6,"type":"Air","tip":"🏛 MILITARY BASE | Ramstein AFB | USA | Air Command | NATO Europe HQ"},
    {"name":"Al Udeid AFB","country":"USA","lat":25.11,"lon":51.31,"type":"Air","tip":"🏛 MILITARY BASE | Al Udeid | USA | Air | CENTCOM forward HQ Qatar"},
    {"name":"Kadena AFB","country":"USA","lat":26.36,"lon":127.77,"type":"Air","tip":"🏛 MILITARY BASE | Kadena | USA | Air | Largest USAF base in Asia"},
    {"name":"Camp Lemonnier","country":"USA","lat":11.55,"lon":43.15,"type":"Naval/Air","tip":"🏛 MILITARY BASE | Camp Lemonnier | USA | Djibouti | Horn of Africa hub"},
    {"name":"Guantanamo Bay","country":"USA","lat":19.9,"lon":-75.1,"type":"Naval","tip":"🏛 MILITARY BASE | Guantanamo Bay | USA | Caribbean naval station"},
    {"name":"Okinawa MCAS","country":"USA","lat":26.18,"lon":127.65,"type":"Air","tip":"🏛 MILITARY BASE | MCAS Okinawa | USMC | Japan"},
    {"name":"Portsmouth Naval","country":"UK","lat":50.8,"lon":-1.1,"type":"Naval","tip":"🏛 MILITARY BASE | Portsmouth | UK | Main RN surface fleet base"},
    {"name":"Tartus Naval","country":"Russia","lat":34.9,"lon":35.9,"type":"Naval","tip":"🏛 MILITARY BASE | Tartus | Russia | Only Mediterranean naval base"},
    {"name":"Hmeimim AFB","country":"Russia","lat":35.4,"lon":35.95,"type":"Air","tip":"🏛 MILITARY BASE | Hmeimim | Russia | Syria air operations"},
    {"name":"Djibouti PLA Base","country":"China","lat":11.6,"lon":43.2,"type":"Naval","tip":"🏛 MILITARY BASE | PLA Base Djibouti | China | First overseas base"},
    {"name":"Changi Naval Base","country":"Singapore","lat":1.4,"lon":104.0,"type":"Naval","tip":"🏛 MILITARY BASE | Changi | Singapore/US | Strait of Malacca access"},
    {"name":"Incirlik AFB","country":"NATO/USA","lat":37.0,"lon":35.4,"type":"Air","tip":"🏛 MILITARY BASE | Incirlik | NATO/USA | Turkey | Nuclear hosting"},
    {"name":"Suda Bay","country":"USA/NATO","lat":35.49,"lon":24.14,"type":"Naval","tip":"🏛 MILITARY BASE | Suda Bay | US/NATO | Crete | Med operations"},
    {"name":"Bagram (inactive)","country":"USA/Afghan","lat":34.94,"lon":69.27,"type":"Air","tip":"🏛 MILITARY BASE | Bagram | Abandoned 2021 | Afghanistan"},
    {"name":"Sevastopol Fleet","country":"Russia","lat":44.6,"lon":33.5,"type":"Naval","tip":"🏛 MILITARY BASE | Sevastopol | Russia | Black Sea Fleet HQ"},
]

NUCLEAR_SITES = [
    {"name":"Natanz","country":"Iran","lat":33.72,"lon":51.73,"type":"Enrichment","status":"Struck","tip":"☢ NUCLEAR | Natanz | Iran | Enrichment facility | Struck by IDF 2026"},
    {"name":"Fordow","country":"Iran","lat":34.88,"lon":49.93,"type":"Enrichment","status":"Destroyed","tip":"☢ NUCLEAR | Fordow | Iran | Underground enrichment | Destroyed IDF 2026"},
    {"name":"Bushehr NPP","country":"Iran","lat":28.98,"lon":50.84,"type":"Power Plant","status":"Operational","tip":"☢ NUCLEAR | Bushehr NPP | Iran | 1000MW reactor | IAEA monitored"},
    {"name":"Zaporizhzhia NPP","country":"Ukraine","lat":47.5,"lon":34.6,"type":"Power Plant","status":"Occupied","tip":"☢ NUCLEAR | Zaporizhzhia | Ukraine (occupied) | 6 reactors | Frontline risk"},
    {"name":"Dimona","country":"Israel","lat":31.0,"lon":35.15,"type":"Weapons Research","status":"Active","tip":"☢ NUCLEAR | Dimona | Israel | Undeclared arsenal ~90 warheads"},
    {"name":"Khandaq Site","country":"N.Korea","lat":40.86,"lon":129.68,"type":"Weapons","status":"Active","tip":"☢ NUCLEAR | Yongbyon | DPRK | Plutonium production complex"},
    {"name":"Cheyenne Mountain","country":"USA","lat":38.74,"lon":-104.85,"type":"Command","status":"Active","tip":"☢ NUCLEAR | Cheyenne Mountain | USA | NORAD command bunker"},
    {"name":"Seversk","country":"Russia","lat":56.6,"lon":84.86,"type":"Weapons Production","status":"Active","tip":"☢ NUCLEAR | Seversk | Russia | Plutonium-239 production"},
    {"name":"Khushab","country":"Pakistan","lat":32.05,"lon":71.9,"type":"Weapons","status":"Active","tip":"☢ NUCLEAR | Khushab | Pakistan | Plutonium reactor"},
    {"name":"Tarapur","country":"India","lat":19.83,"lon":72.66,"type":"Power Plant","status":"Active","tip":"☢ NUCLEAR | Tarapur | India | BWR reactors"},
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
    {"name":"Strait of Malacca","lat":3.0,"lon":101.0,"traffic":"Extreme","vessels_day":300,"tip":"🚢 SHIP TRAFFIC | Strait of Malacca | 300+ vessels/day | 25% global trade"},
    {"name":"Strait of Hormuz","lat":26.56,"lon":56.26,"traffic":"Critical/Reduced","vessels_day":21,"tip":"🚢 SHIP TRAFFIC | Hormuz | ~21 tankers/day | 20% global oil | DISRUPTED"},
    {"name":"Suez Canal","lat":30.42,"lon":32.35,"traffic":"Reduced","vessels_day":44,"tip":"🚢 SHIP TRAFFIC | Suez Canal | ~44 ships/day | Down 35% vs baseline"},
    {"name":"Bab el-Mandeb","lat":12.58,"lon":43.38,"traffic":"Critical/Disrupted","vessels_day":32,"tip":"🚢 SHIP TRAFFIC | Bab el-Mandeb | Houthi attacks | 32 vessels/day"},
    {"name":"English Channel","lat":51.0,"lon":1.5,"traffic":"Heavy","vessels_day":500,"tip":"🚢 SHIP TRAFFIC | English Channel | World's busiest sea lane | 500+/day"},
    {"name":"Dover Strait","lat":51.1,"lon":1.4,"traffic":"Extreme","vessels_day":400,"tip":"🚢 SHIP TRAFFIC | Dover Strait | 400+ vessels/day"},
    {"name":"Cape of Good Hope","lat":-34.36,"lon":18.48,"traffic":"Increasing","vessels_day":85,"tip":"🚢 SHIP TRAFFIC | Cape of Good Hope | +65% vs 2023 | Suez rerouting"},
    {"name":"Taiwan Strait","lat":24.5,"lon":119.5,"traffic":"Monitored","vessels_day":180,"tip":"🚢 SHIP TRAFFIC | Taiwan Strait | 180/day | PLA exercise risk"},
    {"name":"Kerch Strait","lat":45.35,"lon":36.62,"traffic":"Blocked","vessels_day":3,"tip":"🚢 SHIP TRAFFIC | Kerch | Near-blocked | War zone"},
    {"name":"Singapore Anchorage","lat":1.25,"lon":103.7,"traffic":"Extreme","vessels_day":1000,"tip":"🚢 SHIP TRAFFIC | Singapore | World's 2nd busiest port | 1000+ vessels"},
]

TRADE_ROUTE_ARCS = [
    {"name":"Asia-Europe (pre-Houthi)","from_lat":1.35,"from_lon":103.8,"to_lat":51.5,"to_lon":-0.1,"type":"Container","status":"Rerouted"},
    {"name":"Trans-Pacific","from_lat":31.23,"from_lon":121.47,"to_lat":33.74,"to_lon":-118.2,"type":"Container","status":"Active"},
    {"name":"N.America-Europe","from_lat":40.71,"from_lon":-74.0,"to_lat":51.5,"to_lon":-0.1,"type":"Container","status":"Active"},
    {"name":"ME Oil to Asia","from_lat":26.56,"from_lon":56.26,"to_lat":35.68,"to_lon":139.69,"type":"Oil Tanker","status":"Disrupted"},
    {"name":"West Africa Oil","from_lat":6.45,"from_lon":3.4,"to_lat":40.71,"to_lon":-74.0,"type":"Oil Tanker","status":"Active"},
    {"name":"Australia-China Iron","from_lat":-31.95,"from_lon":115.86,"to_lat":31.23,"to_lon":121.47,"type":"Bulk","status":"Active"},
    {"name":"Cape Reroute","from_lat":1.35,"from_lon":103.8,"to_lat":-34.36,"to_lon":18.48,"type":"Container","status":"Active"},
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
    {"name":"Strait of Hormuz","lat":26.56,"lon":56.26,"tip":"⚓ STRATEGIC WATERWAY | Hormuz | 20% global oil | DISRUPTED"},
    {"name":"Suez Canal","lat":30.42,"lon":32.35,"tip":"⚓ STRATEGIC WATERWAY | Suez | 12% global trade | Reduced traffic"},
    {"name":"Bab el-Mandeb","lat":12.58,"lon":43.38,"tip":"⚓ STRATEGIC WATERWAY | Bab el-Mandeb | Houthi zone | 9% global trade"},
    {"name":"Strait of Malacca","lat":3.0,"lon":101.0,"tip":"⚓ STRATEGIC WATERWAY | Malacca | 25% global trade | Normal"},
    {"name":"Panama Canal","lat":8.97,"lon":-79.53,"tip":"⚓ STRATEGIC WATERWAY | Panama | Drought reducing capacity | 3-5% global trade"},
    {"name":"Danish Straits","lat":57.44,"lon":10.0,"tip":"⚓ STRATEGIC WATERWAY | Danish Straits | Baltic access | NATO monitored"},
    {"name":"Kerch Strait","lat":45.35,"lon":36.62,"tip":"⚓ STRATEGIC WATERWAY | Kerch | Russian control | Near-blocked"},
    {"name":"Lombok Strait","lat":-8.5,"lon":115.87,"tip":"⚓ STRATEGIC WATERWAY | Lombok | Indonesia | Malacca alternate"},
    {"name":"Formosa Strait","lat":24.5,"lon":119.5,"tip":"⚓ STRATEGIC WATERWAY | Formosa | PLA tensions | Semiconductor supply"},
    {"name":"Mozambique Channel","lat":-18.0,"lon":41.0,"tip":"⚓ STRATEGIC WATERWAY | Mozambique Channel | LNG export route"},
]

def build_global_map(eq_df, eonet_df, show_seis, show_volc, show_mvmt, show_conf, show_supply, show_heat,
                      show_hist=False, show_live=False,
                      show_intel=False, show_czones=False, show_mbases=False, show_nuclear=False,
                      show_gamma=False, show_space=False, show_cables=False, show_pipes=False,
                      show_aidc=False, show_milact=False, show_ships=False, show_trade=False,
                      show_gps=False, show_orbital=False, show_cii=False, show_displaced=False,
                      show_climate=False, show_weather=False, show_outages=False, show_cyber=False,
                      show_econ=False, show_minerals=False, show_waterways=False, show_fires_layer=False,
                      show_protests=False, show_aviation=False):
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
        stdf = pd.DataFrame(SHIP_TRAFFIC_ZONES)
        stdf["_color"] = stdf["traffic"].apply(lambda t:
            [255,30,60,200] if "Blocked" in t or "Disrupted" in t
            else [255,140,66,180] if "Reduced" in t or "Critical" in t
            else [0,200,255,160] if "Extreme" in t or "Heavy" in t
            else [0,230,118,140])
        stdf["_radius"] = stdf["vessels_day"].apply(lambda v: min(int(v * 400), 220000))
        if "tip" not in stdf.columns:
            stdf["tip"] = stdf.apply(lambda r: f"🚢 SHIP TRAFFIC\n{r['name']}\n{r['vessels_day']} vessels/day\nStatus: {r['traffic']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=stdf, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

    if show_trade:
        t_colors = {"Container":[0,200,255,130],"Oil Tanker":[255,140,66,150],"Bulk":[157,110,255,130]}
        t_data = []
        for r in TRADE_ROUTE_ARCS:
            col = t_colors.get(r["type"],[74,107,133,100])
            if r["status"] in ("Rerouted","Disrupted"): col = [255,61,90,160]
            t_data.append({**r,"_color":col})
        if t_data:
            tdf2 = pd.DataFrame(t_data)
            if "tip" not in tdf2.columns:
                tdf2["tip"] = tdf2.apply(lambda r: f"⚓ TRADE ROUTE\n{r.get('name','')}\nType: {r.get('type','')} · Status: {r.get('status','')}", axis=1)
            layers.append(pdk.Layer("ArcLayer", data=tdf2,
                                     get_source_position=["from_lon","from_lat"],
                                     get_target_position=["to_lon","to_lat"],
                                     get_source_color="_color", get_target_color="_color",
                                     get_width=2, pickable=True, auto_highlight=True))

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
        wway_df = pd.DataFrame(STRATEGIC_WATERWAYS)
        wway_df["_color"] = [[0,200,255,180]]*len(wway_df)
        wway_df["_radius"] = 120000
        if "tip" not in wway_df.columns:
            wway_df["tip"] = wway_df.get("tip", wway_df.apply(lambda r: f"⚓ STRATEGIC WATERWAY\n{r['name']}", axis=1))
        layers.append(pdk.Layer("ScatterplotLayer", data=wway_df, get_position=["lon","lat"],
                                 get_radius="_radius", get_fill_color="_color", pickable=True, auto_highlight=True))

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
# FETCH LIVE DATA
# ─────────────────────────────────────────────
eq_df      = fetch_usgs()
eonet_df   = fetch_eonet()
kp_data    = fetch_kp()
solar_data = fetch_solar()
firms_cnt  = fetch_firms_count()
sig_eq_df  = fetch_usgs_significant()
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
        show_volc  = st.toggle("🟠 Volcanic / EONET",     value=True,  key="lyr_volc")
        show_conf  = st.toggle("🔴 Conflict Incidents",    value=True,  key="lyr_conf")
        show_mvmt  = st.toggle("🟣 Civil Movements",      value=True,  key="lyr_mvmt")
        show_supp  = st.toggle("⟶ Supply Arc Lines",      value=True,  key="lyr_supp")
        show_heat  = st.toggle("🌡 Heatmap (Seismic)",    value=False, key="lyr_heat")
        show_hist  = st.toggle("📅 Historical Events 2022+", value=True, key="lyr_hist")
        show_live  = st.toggle("⚡ Live Events (GDELT)",  value=True,  key="lyr_live")

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
with c1: st.metric("Active Conflicts",  active_conf,       delta="LIVE")
with c2: st.metric("Total Casualties",  f"{total_cas:,}",  delta="All theatres")
with c3: st.metric("Seismic (24h)",     len(eq_df),        delta=f"M5+: {len(m5p)}")
with c4: st.metric("Civil Movements",   len(MOVEMENTS),    delta=f"Critical: {len(crit_mv)}")
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
        show_fires_layer=show_fires_layer, show_protests=show_protests, show_aviation=show_aviation),
    use_container_width=True,
    on_select="rerun",
    selection_mode="single-object",
    key="global_map_select",
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
_live_events = fetch_live_global_events(max_records=15)
_recent_hist  = sorted(HISTORICAL_EVENTS, key=lambda x: x["date"], reverse=True)[:6]

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
_latest_he = sorted(HISTORICAL_EVENTS, key=lambda x: x["date"], reverse=True)[0]
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
tab_conflict, tab_earth, tab_civil, tab_news, tab_intel, tab_econ = st.tabs([
    "⚔  Conflict Dashboard",
    "🌍  Earth Signals",
    "✊  Civil Movements",
    "📡  Live News",
    "🛰  Intel Dashboard",
    "📊  Economic & Markets",
])

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
        e for e in sorted(HISTORICAL_EVENTS, key=lambda x: x["date"], reverse=True)
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

        feeds_js = json.dumps([
            {"name":s["name"],"rss":s["rss"],
             "color":NEWS_CAT_COLOR.get(s["cat"],"#4a6b85"),"cat":s["cat"]}
            for s in vis_src[:4]
        ])

        art_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#02040a;font-family:'DM Sans',system-ui,sans-serif;color:#e2ecf8;padding:12px;}}
#st{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#4a6b85;margin-bottom:14px;display:flex;align-items:center;gap:8px;min-height:18px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:#00c8ff;animation:bl 1.2s ease-in-out infinite;flex-shrink:0;}}
@keyframes bl{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.g{{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
@media(max-width:560px){{.g{{grid-template-columns:1fr;}}}}
.c{{background:#0b1524;border:1px solid rgba(0,200,255,.12);border-radius:10px;padding:14px 16px;position:relative;overflow:hidden;transition:border-color .18s,transform .15s;}}
.c:hover{{border-color:rgba(0,200,255,.3);transform:translateY(-1px);}}
.c::after{{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(180deg,var(--ac,#00c8ff),transparent);}}
.s{{font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;margin-bottom:6px;}}
.h{{font-size:13px;font-weight:600;color:#e2ecf8;line-height:1.45;margin-bottom:8px;}}
.f{{display:flex;align-items:center;justify-content:space-between;}}
.t{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6b85;}}
a.r{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#00c8ff;text-decoration:none;padding:3px 10px;border:1px solid rgba(0,200,255,.28);border-radius:5px;white-space:nowrap;}}
a.r:hover{{background:rgba(0,200,255,.1);}}
.err{{color:#ff8c42;font-family:'IBM Plex Mono',monospace;font-size:11px;padding:12px;border:1px solid rgba(255,140,66,.25);border-radius:8px;background:rgba(255,140,66,.05);line-height:1.6;}}
.sl{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}}
.sl a{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#00c8ff;text-decoration:none;padding:4px 12px;border:1px solid rgba(0,200,255,.25);border-radius:20px;}}
</style></head><body>
<div id="st"><div class="dot"></div><span>Loading feeds…</span></div>
<div id="g" class="g"></div>
<script>
const F={feeds_js};
const P=[
  u=>`https://api.allorigins.win/get?url=${{encodeURIComponent(u)}}`,
  u=>`https://corsproxy.io/?${{encodeURIComponent(u)}}`,
  u=>`https://api.codetabs.com/v1/proxy?quest=${{encodeURIComponent(u)}}`,
];
function ta(s){{try{{const d=new Date(s),x=(Date.now()-d)/1000;
  if(x<60)return Math.round(x)+'s ago';if(x<3600)return Math.round(x/60)+'m ago';
  return Math.round(x/3600)+'h ago';}}catch{{return '';}}}}
function esc(s){{return(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}}
function px(xml){{
  try{{const doc=new DOMParser().parseFromString(xml,'text/xml');
    if(doc.querySelector('parsererror'))return[];
    return[...doc.querySelectorAll('item')].slice(0,7).map(it=>{{
      const g=n=>{{const e=it.querySelector(n);return(e?.textContent||e?.getAttribute('href')||'').split('<![CDATA[').join('').split(']]>').join('').trim();}};
      return{{ti:g('title'),li:g('link'),pu:g('pubDate')}};
    }});}}catch{{return[];}}}}
async function ff(f){{
  for(const p of P){{try{{
    const r=await fetch(p(f.rss),{{signal:AbortSignal.timeout(9000)}});
    if(!r.ok)continue;
    const ct=r.headers.get('content-type')||'';
    let xml='';
    if(ct.includes('json')){{const j=await r.json();xml=j.contents||j.data||'';}}
    else xml=await r.text();
    const items=px(xml);
    if(items.length)return{{f,items}};
  }}catch{{}}}}
  return{{f,items:[]}};
}}
async function main(){{
  const se=document.getElementById('st'),ge=document.getElementById('g');
  const res=await Promise.all(F.map(ff));
  const arts=[];let n=0;
  res.forEach(({{f,items}})=>{{if(items.length){{n++;items.forEach(it=>arts.push({{ti:it.ti,li:it.li,tm:ta(it.pu),sr:f.name,co:f.color}}));}}}});
  if(!arts.length){{
    se.innerHTML='<span style="color:#ff8c42">All proxies blocked</span>';
    ge.innerHTML='<div class="err">RSS feeds could not load.<div class="sl">'+
      F.map(f=>`<a href="https://${{f.rss.split('/').slice(0,3).join('/')}}" target="_blank">${{f.name}}</a>`).join('')+
      '</div></div>';return;}}
  se.innerHTML=`<div class="dot" style="background:#00e676"></div><span>${{n}} feed${{n>1?'s':''}} · ${{arts.length}} articles</span>`;
  ge.innerHTML=arts.slice(0,24).map(a=>`
    <div class="c" style="--ac:${{a.co}}">
      <div class="s" style="color:${{a.co}}">${{esc(a.sr)}}</div>
      <div class="h">${{esc(a.ti).slice(0,120)}}</div>
      <div class="f"><span class="t">${{a.tm}}</span>
        ${{a.li?`<a class="r" href="${{a.li}}" target="_blank" rel="noopener">Read →</a>`:''}}
      </div>
    </div>`).join('');}}
main();
</script></body></html>"""

        components.html(art_html, height=680, scrolling=True)

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

    # ── All data needed by Intel tab (defined inline to avoid forward-reference bugs) ──
    _INTEL_INSTABILITY = COUNTRY_INSTABILITY  # defined at top of file ✓

    _INTEL_STRATEGIC = {
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

    _INTEL_FEED = [
        {"source":"Foreign Policy","cat":"ALERT","tag":"MILITARY","title":"Six U.S. Troops Killed in Aircraft Crash in Iraq","time":"20h ago","url":"https://foreignpolicy.com"},
        {"source":"Atlantic Council","cat":"ALERT","tag":"CONFLICT","title":"UN: Putin's deportation of Ukrainian children is a crime against humanity","time":"8h ago","url":"https://atlanticcouncil.org"},
        {"source":"ISW","cat":"REPORT","tag":"UKRAINE","title":"Russian forces continue offensive operations near Avdiivka sector","time":"4h ago","url":"https://understandingwar.org"},
        {"source":"CSIS","cat":"ALERT","tag":"IRAN","title":"IRGC drone production facility destroyed in latest Israeli strike","time":"6h ago","url":"https://csis.org"},
        {"source":"Reuters","cat":"REPORT","tag":"NUCLEAR","title":"IAEA loses monitoring access to Fordow enrichment site after strike","time":"12h ago","url":"https://reuters.com"},
        {"source":"Defense One","cat":"ALERT","tag":"MILITARY","title":"Pentagon orders second carrier strike group to Eastern Mediterranean","time":"3h ago","url":"https://defenseone.com"},
        {"source":"Bellingcat","cat":"REPORT","tag":"OSINT","title":"Geolocated footage confirms new Russian S-400 deployment near Zaporizhzhia","time":"7h ago","url":"https://bellingcat.com"},
    ]

    _CYBER_FEED = [
        {"source":"GlobalSecurity.org","title":"BRP Diego Silang — PH Navy contingent now in Australia for joint exercise","time":"4h ago","sector":"Military"},
        {"source":"IndiaGazette","title":"Iran Army chief says attack on IRIS Dena will not go unanswered","time":"7h ago","sector":"Military"},
        {"source":"Recorded Future","title":"APT41 campaign targeting defence contractors across SE Asia","time":"2h ago","sector":"Cyber"},
        {"source":"WCBM","title":"New cyber-physical attack vector targets ICS/SCADA water systems","time":"21h ago","sector":"Cyber"},
    ]

    _INFRA = {
        "cables":  {"count":86,  "at_risk":12, "items":[
            {"name":"SEA-ME-WE 4","region":"Indian Ocean","risk":72,"status":"Degraded"},
            {"name":"Africa Coast to Europe","region":"W Africa","risk":81,"status":"Cut"},
            {"name":"PEACE Cable","region":"ME/Africa","risk":68,"status":"Degraded"},
        ]},
        "pipelines":{"count":88, "at_risk":9, "items":[
            {"name":"Nord Stream (inactive)","region":"Baltic","risk":95,"status":"Sabotaged"},
            {"name":"Trans-Arabian Pipeline","region":"Middle East","risk":78,"status":"Suspended"},
            {"name":"Druzhba Pipeline","region":"Europe","risk":65,"status":"Reduced"},
        ]},
        "ports":    {"count":62, "at_risk":8, "items":[
            {"name":"Port of Hodeidah","region":"Yemen","risk":88,"status":"Blockaded"},
            {"name":"Port Sudan","region":"Sudan","risk":74,"status":"Contested"},
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

    _FORCE_POSTURE = [
        {"activity":"Combined air-naval activity","actors":"UK/Unknown","signals":860,"risk":49,"col":"#ff3d5a"},
        {"activity":"Combined air-naval activity","actors":"NATO/USA","signals":63,"risk":39,"col":"#ff8c42"},
        {"activity":"Missile test/launch","actors":"Iran","signals":12,"risk":82,"col":"#ff3d5a"},
        {"activity":"Troop mobilisation","actors":"Russia","signals":44,"risk":65,"col":"#ff8c42"},
        {"activity":"Air defence activation","actors":"Israel","signals":31,"risk":58,"col":"#ffb400"},
        {"activity":"Naval patrol","actors":"China/SCS","signals":28,"risk":45,"col":"#ff8c42"},
        {"activity":"Cyber operation","actors":"Unknown/State","signals":77,"risk":72,"col":"#9d6eff"},
    ]

    _CHOKEPOINTS_INTEL = [
        {
            "name":"Strait of Hormuz","risk":80,"status":"red","flow":"eastbound/westbound",
            "warnings":0,"ais_disruptions":0,"wow_change":-94.4,
            "context":"Active conflict — Iran-Israel war; Iranian naval blockade risk and mines reported in Persian Gulf.",
            "exports":["Gulf Oil Exports","Qatar LNG","Iran Exports"],
            "lat":26.56,"lon":56.26,
        },
        {
            "name":"Bab el-Mandeb","risk":75,"status":"red","flow":"northbound/southbound",
            "warnings":3,"ais_disruptions":12,"wow_change":-41.0,
            "context":"Houthi attacks on commercial shipping continue; Red Sea rerouting adding 2–3 weeks to Asia-Europe routes.",
            "exports":["Suez Canal traffic","EU-Asia trade","Oil tankers"],
            "lat":12.58,"lon":43.38,
        },
        {
            "name":"Suez Canal","risk":52,"status":"amber","flow":"northbound/southbound",
            "warnings":1,"ais_disruptions":3,"wow_change":-18.0,
            "context":"Reduced traffic due to Red Sea security situation; some rerouting via Cape of Good Hope.",
            "exports":["EU-Asia Container","Mediterranean Oil","LNG"],
            "lat":30.42,"lon":32.35,
        },
        {
            "name":"Taiwan Strait","risk":55,"status":"amber","flow":"northbound/southbound",
            "warnings":0,"ais_disruptions":2,"wow_change":-8.4,
            "context":"PLA military exercises increasing. Semiconductor supply chain vulnerability elevated.",
            "exports":["Taiwan Semiconductors","China Exports","Japan Trade"],
            "lat":24.5,"lon":119.5,
        },
        {
            "name":"Strait of Malacca","risk":22,"status":"green","flow":"eastbound/westbound",
            "warnings":0,"ais_disruptions":0,"wow_change":2.1,
            "context":"Normal operations. 25% of global trade flows through this corridor daily.",
            "exports":["SE Asia Trade","China Imports","Japan/Korea Oil"],
            "lat":3.0,"lon":101.0,
        },
    ]

    _OUTAGE_KNOWN = [
        {"name":"Gaza — Total Blackout","severity":"Total","cause":"Infrastructure destruction"},
        {"name":"Sudan — Partial","severity":"Partial","cause":"Conflict/Power"},
        {"name":"Myanmar — Targeted Shutdown","severity":"Targeted","cause":"Junta censorship"},
        {"name":"Iran — Throttled","severity":"Throttled","cause":"Government restriction"},
        {"name":"Russia — Selective Block","severity":"Selective","cause":"Censorship"},
        {"name":"Ukraine — Disrupted","severity":"Disrupted","cause":"Missile strikes"},
    ]

    # Fetch live outage feed
    _outage_arts = fetch_outage_feed()

    # Assemble payload — all variables now guaranteed defined
    _intel_payload = _ij.dumps({
        "instability":   _INTEL_INSTABILITY,
        "strategic":     _INTEL_STRATEGIC,
        "intel_feed":    _INTEL_FEED,
        "cyber_feed":    _CYBER_FEED,
        "infra":         _INFRA,
        "force_posture": _FORCE_POSTURE,
        "nuke_alerts":   NUKE_ALERTS,
        "wmd_posture":   WMD_POSTURE,
        "chokepoints":   _CHOKEPOINTS_INTEL,
        "outage_live":   _outage_arts[:8],
        "outage_known":  _OUTAGE_KNOWN,
    })


# ══════════════════════════════════════════════════════════════
# TAB 6 — ECONOMIC & MARKETS
# ══════════════════════════════════════════════════════════════
with tab_econ:
    import json as _ej
    import streamlit.components.v1 as _ec

    # ── Fetch live market data ──────────────────────────────────
    _live_indices     = fetch_live_indices()
    _live_commodities = fetch_live_commodities()
    _live_forex       = fetch_live_forex()
    _live_defense     = fetch_live_defense()
    _live_crypto      = fetch_live_crypto()

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
        "shipping":     SHIPPING_RATES,
        "minerals":     CRIT_MIN_DATA,
        "crypto":       CRYPTO_DATA,
        "sectors":      SECTOR_HEATMAP,
        "layoffs":      LAYOFFS,
        "fires":        FIRES_DATA,
        "market":       MARKET_RADAR,
        "btc_etf":      BTC_ETF,
        "pizza":        PIZZA_INDEX,
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
  grid-template-columns: 1fr 1fr 1.1fr 1fr;
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
  const brent = D.oil.find(o=>o.name.includes('Brent'))||{{}};
  const wti   = D.oil.find(o=>o.name.includes('WTI'))||{{}};
  const fed   = D.indicators.find(i=>i.ticker==='FEDFUNDS')||{{}};
  const btc   = D.crypto.find(c=>c.ticker==='BTC')||{{}};
  const pz    = D.pizza;
  const pzCol = pz.score>=75?'var(--rose)':pz.score>=55?'var(--coral)':pz.score>=35?'var(--gold)':'var(--mint)';

  const items = [
    {{ num: brent.val?`$${{brent.val.toFixed(0)}}`:'-', lbl:'Brent Crude',
       sub:`WTI $${{wti.val?.toFixed(0)||'-'}} · per barrel`,
       col:'var(--coral)', glow:'rgba(251,146,60,.14)', bar:'linear-gradient(90deg,transparent,var(--coral),transparent)' }},
    {{ num: fed.val||'-', lbl:'Fed Funds Rate',
       sub:`Unemployment ${{(D.indicators.find(i=>i.ticker==='UNRATE')||{{}}).val||'-'}}`,
       col:'var(--sky)', glow:'rgba(56,189,248,.12)', bar:'linear-gradient(90deg,transparent,var(--sky),transparent)' }},
    {{ num: btc.val?`$${{(btc.val/1000).toFixed(1)}}K`:'-', lbl:'Bitcoin',
       sub:`ETH $${{(D.crypto.find(c=>c.ticker==='ETH')||{{}}).val?.toFixed(0)||'-'}} · spot`,
       col:'var(--gold)', glow:'rgba(251,191,36,.12)', bar:'linear-gradient(90deg,transparent,var(--gold),transparent)' }},
    {{ num: pz.score, lbl:'🍕 Pizza Index',
       sub:pz.label,
       col:pzCol, glow:`rgba(251,146,60,.12)`, bar:`linear-gradient(90deg,transparent,${{pzCol}},transparent)` }},
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
  const nfUp=D.btc_etf.net_flow>=0;
  const nfCol=nfUp?'var(--mint)':'var(--rose)';
  const mCol=D.market.label==='CASH'?'var(--gold)':'var(--sky)';

  const cryptoRows = D.crypto.map(c=>{{
    const up=c.change>=0, cc=up?'var(--mint)':'var(--rose)';
    return `<div class="card-row" style="border-left-color:${{up?'rgba(52,211,153,.4)':'rgba(248,113,113,.4)'}};display:flex;justify-content:space-between;align-items:center">
      <div>
        <div style="font-size:13px;font-weight:600;color:var(--ink)">${{c.name}}</div>
        <div class="mono" style="font-size:9px;color:var(--ink3)">${{c.ticker}}</div>
      </div>
      <div style="text-align:right">
        <div class="mono" style="font-size:13px;color:var(--ink)">$${{c.val.toLocaleString('en-US',{{minimumFractionDigits:2,maximumFractionDigits:2}})}}</div>
        <div class="mono" style="font-size:10px;color:${{cc}}">${{up?'+':''}}${{c.change.toFixed(2)}}%</div>
      </div>
    </div>`;
  }}).join('');

  const heatCells = D.sectors.map(s=>{{
    const up=s.v>=0;
    const intensity=Math.min(Math.abs(s.v)/8,1);
    const bg=up?`rgba(52,211,153,${{.08+intensity*.18}})`:`rgba(248,113,113,${{.08+intensity*.18}})`;
    const col=up?'var(--mint)':'var(--rose)';
    return `<div class="sector-cell" style="background:${{bg}}">
      <div class="mono" style="font-size:8px;color:var(--ink3);margin-bottom:3px">${{esc(s.s)}}</div>
      <div class="mono" style="font-size:12px;font-weight:700;color:${{col}}">${{up?'+':''}}${{s.v}}%</div>
    </div>`;
  }}).join('');

  return `<div class="card">
    <div class="section-title">Financial <span class="live-chip" style="margin-left:4px"><span class="live-dot"></span>Live</span></div>

    <div style="margin-bottom:18px">
      <div class="overline" style="margin-bottom:10px">Crypto</div>
      ${{cryptoRows}}
    </div>

    <div style="margin-bottom:18px">
      <div class="overline" style="margin-bottom:10px">Sector Heatmap</div>
      <div class="sector-grid">${{heatCells}}</div>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
      <div style="background:var(--raised);border:1px solid var(--edge2);border-radius:10px;padding:14px;text-align:center">
        <div class="overline" style="margin-bottom:8px">Market Posture</div>
        <div class="disp" style="font-size:26px;color:${{mCol}};margin-bottom:5px">${{D.market.label}}</div>
        <div class="mono" style="font-size:9px;color:var(--ink3)">${{D.market.posture}}</div>
        <div class="mono" style="font-size:9px;color:var(--gold);margin-top:3px">${{D.market.flow}}</div>
      </div>
      <div style="background:var(--raised);border:1px solid var(--edge2);border-radius:10px;padding:14px;text-align:center">
        <div class="overline" style="margin-bottom:8px">BTC ETF Flow</div>
        <div class="disp" style="font-size:26px;color:${{nfCol}};margin-bottom:5px">$${{Math.abs(D.btc_etf.net_flow)}}M</div>
        ${{badge(nfUp?'INFLOW':'OUTFLOW',nfUp?'low':'crit')}}
        <div class="mono" style="font-size:9px;color:var(--ink3);margin-top:6px">Est. $${{D.btc_etf.est_flow}}M</div>
      </div>
    </div>
  </div>`;
}}

// ── Row 2: Layoffs + Fires ────────────────────────────────────
function row2() {{
  const layoffRows = D.layoffs.map(l=>{{
    const sc=l.severity==='Critical'?'var(--rose)':l.severity==='High'?'var(--coral)':'var(--gold)';
    return `<div class="card-row" style="border-left-color:${{sc}}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
        <span style="font-size:13px;font-weight:600;color:var(--ink)">${{esc(l.company)}}</span>
        ${{badge(l.severity.toUpperCase(),sevCls(l.severity))}}
      </div>
      <div style="display:flex;justify-content:space-between">
        <span class="mono" style="font-size:10px;color:var(--gold)">${{esc(l.count)}} jobs</span>
        <span class="mono" style="font-size:9px;color:var(--ink3)">${{esc(l.sector)}} · ${{l.date}}</span>
      </div>
    </div>`;
  }}).join('');

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
    <div class="card">
      <div class="section-title">Layoffs Tracker <span class="live-chip" style="margin-left:4px"><span class="live-dot"></span>Live</span></div>
      <div class="scroll">${{layoffRows}}</div>
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
  '<div class="main-grid" style="margin-top:18px">' + econPanel() + tradePanel() + supplyPanel() + finPanel() + '</div>' +
  '<hr class="divider">' +
  row2() +
  '<hr class="divider">' +
  pizzaSection();
</script>
</body></html>"""

    _ec.html(_econ_html, height=5200, scrolling=True)
