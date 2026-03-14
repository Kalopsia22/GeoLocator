"""
OSINT ARENA v5
==============
Fixes in v5:
  1. MAP FIXED  — switched from mapbox:// (requires token) to carto-darkmatter (free, no key)
  2. NEWS FIXED — GDELT Doc API (free JSON, no key) as primary; RSS as secondary; rich fallback
  3. ISRAEL-IRAN WAR — full conflict dataset added
  4. AUTO-REFRESH — streamlit-autorefresh (30s ticker, 5min data)
  5. WEB-DEPENDENT — live GDELT GKG conflict news, live ACLED-style GDELT event stream

Run:
    pip install streamlit pydeck plotly pandas numpy requests streamlit-autorefresh
    streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json, requests, re, html as html_lib, time
from datetime import datetime, timezone, timedelta
import pydeck as pdk
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="OSINT ARENA",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-refresh (optional) ──────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=300_000, key="auto5min")   # refresh every 5 min
except ImportError:
    pass   # works fine without it

# ─────────────────────────────────────────────
# CSS  (unchanged from v4, condensed)
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
/* COMPONENTS */
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
.xp-track{height:5px;background:var(--dim);border-radius:3px;overflow:hidden;margin-top:6px;}
.xp-fill{height:100%;background:linear-gradient(90deg,var(--violet),var(--cyan));border-radius:3px;}
.m-panel{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 18px;margin-bottom:10px;}
.m-label{font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:6px;}
.m-val{font-family:var(--fd);font-size:36px;letter-spacing:.04em;line-height:1;margin-bottom:4px;}
.m-sub{font-family:var(--fm);font-size:11px;color:var(--muted);}
.m-cyan{color:var(--cyan);text-shadow:0 0 20px rgba(0,200,255,.3);}
.m-amber{color:var(--amber);text-shadow:0 0 20px rgba(255,180,0,.2);}
.m-red{color:var(--red);text-shadow:0 0 20px rgba(255,61,90,.25);}
.m-green{color:var(--green);text-shadow:0 0 20px rgba(0,230,118,.2);}
.m-violet{color:var(--violet);text-shadow:0 0 20px rgba(157,110,255,.2);}
.lb-row{display:flex;align-items:center;gap:12px;padding:10px 14px;border-bottom:1px solid var(--bord2);transition:background .15s;}
.lb-avatar{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;}
.ch-card{background:var(--card);border:1px solid var(--border);border-radius:14px;margin-bottom:16px;overflow:hidden;}
.ch-header{padding:12px 18px;border-bottom:1px solid var(--bord2);display:flex;align-items:center;justify-content:space-between;}
.ch-title{font-family:var(--fd);font-size:16px;letter-spacing:.09em;color:var(--violet);}
.ch-body{padding:16px 18px;}
.ch-q{font-size:14px;color:var(--text);line-height:1.65;margin-bottom:14px;}
.clue{display:flex;gap:8px;font-family:var(--fm);font-size:11px;color:var(--muted);margin-bottom:6px;line-height:1.5;}
.clue span{color:var(--violet);flex-shrink:0;}

/* NEWS CARDS */
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
.news-source-pill{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:20px;font-family:var(--fm);font-size:9px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;border:1px solid;}
.news-headline{font-size:14px;font-weight:600;color:var(--text);line-height:1.45;margin:8px 0 6px;}
.news-snippet{font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px;}
.news-footer{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.news-time{font-family:var(--fm);font-size:10px;color:var(--muted);}
.news-link{display:inline-flex;align-items:center;gap:4px;font-family:var(--fm);font-size:10px;color:var(--cyan);text-decoration:none;padding:4px 10px;border:1px solid rgba(0,200,255,.25);border-radius:5px;transition:background .15s;}
.news-link:hover{background:rgba(0,200,255,.1);}
.src-directory-card{background:var(--card);border:1px solid var(--bord2);border-radius:10px;padding:14px 16px;margin-bottom:10px;transition:border-color .2s;}
.src-directory-card:hover{border-color:var(--border);}

/* GLOBAL MAP HEADER */
.map-top-bar{background:var(--panel);border:1px solid var(--border);border-radius:14px 14px 0 0;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;}
.map-title-text{font-family:var(--fd);font-size:17px;letter-spacing:.14em;color:var(--cyan);text-shadow:0 0 16px rgba(0,200,255,.3);}
.map-legend{display:flex;gap:16px;align-items:center;font-family:var(--fm);font-size:10px;color:var(--muted);flex-wrap:wrap;}
.legend-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}

.ticker-wrap{background:var(--deep);border-top:1px solid var(--border);border-bottom:1px solid var(--bord2);overflow:hidden;padding:8px 0;}
.ticker-inner{display:inline-block;white-space:nowrap;animation:ticker-scroll 90s linear infinite;font-family:var(--fm);font-size:11px;color:var(--muted);}
@keyframes ticker-scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.t-sep{color:var(--cyan);margin:0 16px;}
.t-hi{color:var(--text);}
.t-red{color:var(--red);}
.t-amb{color:var(--amber);}
.ai-terminal{background:#010710;border:1px solid var(--border);border-radius:10px;padding:18px;font-family:var(--fm);font-size:13px;color:var(--text);line-height:1.75;white-space:pre-wrap;min-height:180px;}
.ai-terminal::before{content:'▸ ANALYSIS OUTPUT';display:block;font-size:10px;letter-spacing:.2em;color:var(--muted);margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--bord2);}
.helper{font-size:12px;color:var(--muted);line-height:1.6;padding:10px 14px;background:var(--dim);border-radius:8px;border-left:3px solid var(--bord2);margin-bottom:14px;}
.helper b{color:var(--text2);font-style:normal;}
.sb-div{height:1px;background:var(--bord2);margin:16px 0;}
.tl-item{position:relative;margin-bottom:16px;padding-left:22px;}
.tl-item::before{content:'';position:absolute;left:0;top:4px;width:9px;height:9px;border-radius:50%;border:2px solid var(--dim);}
.tl-date{font-family:var(--fm);font-size:10px;color:var(--muted);margin-bottom:3px;}
.tl-text{font-size:13px;color:var(--text);line-height:1.5;}
.tl-tag{font-family:var(--fm);font-size:9px;margin-top:2px;}
.live-badge{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;background:rgba(255,61,90,.1);border:1px solid rgba(255,61,90,.3);border-radius:20px;font-family:var(--fm);font-size:9px;color:var(--red);}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {
    "score": 2840, "answered": {}, "ai_provider": "groq", "ai_key": "",
    "ai_output": "", "conflict_sitrep": "",
    "selected_conflict": "Ukraine–Russia War",
    "last_refresh": 0,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_tier(s):
    if s >= 10000: return "HANDLER","b-red","#ff3d5a"
    if s >=  5000: return "AGENT","b-violet","#9d6eff"
    if s >=  2000: return "ANALYST","b-cyan","#00c8ff"
    return "RECRUIT","b-green","#00e676"

def bg_chart():
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

def ax(color="#4a6b85", grid="#0f2035", sz=10):
    return dict(color=color, tickfont_size=sz, gridcolor=grid)

# ─────────────────────────────────────────────
# CONFLICT DATA
# ─────────────────────────────────────────────
CONFLICTS = {
# ── Ukraine–Russia ──────────────────────────────────────────
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
  "gdelt_query":"Ukraine Russia war",
},
# ── Gaza Conflict ────────────────────────────────────────────
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
  "gdelt_query":"Gaza Israel Hamas war",
},
# ── Israel–Iran War ─────────────────────────────────────────
"Israel–Iran War": {
  "status":"ACTIVE","intensity":"CRITICAL","start":"2024-04-13","region":"Middle East",
  "escalation":88,"ceasefire":False,"casualties_total":2800,"displaced":280000,
  "description":"Direct military confrontation between Israel and Iran, escalating from decades of proxy conflict. Iran's April 2024 drone/missile barrage marked the first direct Iranian attack on Israeli soil. Israel struck Iranian nuclear and military sites in response. Hezbollah, IRGC proxies, and Houthi forces in Yemen form a multi-front pressure network. Risk of regional expansion remains high.",
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
    {"type":"airstrike","title":"Israel strikes Natanz nuclear site — centrifuges destroyed","loc":"Natanz, Iran","lat":33.72,"lon":51.73,"date":"2026-03-07","severity":"CRITICAL","casualties":28},
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
  "gdelt_query":"Israel Iran war strikes nuclear",
},
# ── Sudan Civil War ──────────────────────────────────────────
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
  "gdelt_query":"Sudan RSF SAF war Darfur",
},
# ── Myanmar Civil War ────────────────────────────────────────
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
  "gdelt_query":"Myanmar junta resistance war",
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

CHALLENGES = [
    {"id":"c1","pts":250,"difficulty":"ANALYST","color":"#00c8ff","title":"SEISMIC TRAIL",
     "question":"A M6.1 earthquake struck northern Japan at 55km depth near the Pacific coast. What is the PRIMARY secondary hazard?",
     "clues":["Depth <70km = shallow — strong surface shaking","Pacific Ring of Fire subduction zone","JMA issued Level 3 coastal alert"],
     "options":["Volcanic co-eruption","Tsunami risk within 300km coastline","Inland liquefaction","Atmospheric pressure wave"],"correct":1,
     "explain":"Shallow subduction-zone quakes near coastlines carry the highest tsunami risk. JMA auto-issues warnings for M6+ shallow Pacific events."},
    {"id":"c2","pts":400,"difficulty":"AGENT","color":"#9d6eff","title":"CIVIL UNREST",
     "question":"New Delhi protest: 200,000+ over 72h, rated CRITICAL. Which indicator MOST reliably signals imminent escalation?",
     "clues":["ACLED: protests >72h have 3× higher escalation probability","Government: no dialogue initiated","Coordinated hashtags across 12 states"],
     "options":["Aerial crowd-density photograph","Mobile data traffic spike inside the protest zone","Absence of counter-protests","Regional weather forecast"],"correct":1,
     "explain":"Mobile network traffic anomalies reveal real-time C2 coordination — key ACLED escalation precursor (78% correlation)."},
    {"id":"c3","pts":350,"difficulty":"ANALYST","color":"#ff3d5a","title":"CONFLICT INTEL",
     "question":"Regarding the Israel-Iran conflict: Iran launched ~300 drones and missiles at Israel in April 2024. Approximately what percentage were intercepted?",
     "clues":["Multi-layered air defence: Iron Dome, David's Sling, Arrow-3","Assisted interception by US, UK, Jordan, France","First direct Iranian attack on Israeli soil"],
     "options":["~50% intercepted","~70% intercepted","~99% intercepted","~30% intercepted"],"correct":2,
     "explain":"Approximately 99% of ~300 projectiles were intercepted by the combined layered defence of Israel, USA, UK, Jordan, and France — one of history's most successful interceptions."},
    {"id":"c4","pts":500,"difficulty":"HANDLER","color":"#ffb400","title":"MULTI-SOURCE FUSION",
     "question":"Correlating Israel-Iran escalation + Strait of Hormuz vessel seizures + oil market data: which cascading systemic risk is MOST likely?",
     "clues":["Strait of Hormuz carries ~20% of global seaborne oil","Iran has repeatedly threatened closure of the Strait","Oil price spikes historically trigger inflation and recession"],
     "options":["Global currency devaluation","Energy supply shock and inflationary cascade","Tech sector collapse","Global tourism collapse"],"correct":1,
     "explain":"Energy supply disruption via Strait of Hormuz closure is the primary cascading risk. ~20% of global oil and 18% of LNG transits this chokepoint — an Iranian blockade would spike oil >$150/bbl within days."},
]

LEADERBOARD = [
    ("vectorx","HANDLER",18450,"#ff3d5a"),("sigint_reaper","AGENT",16220,"#9d6eff"),
    ("phantomhex","AGENT",14875,"#ffb400"),("n0de_k1ller","ANALYST",13100,"#ff8c42"),
    ("ghost_proto","ANALYST",9800,"#3d5a75"),
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

@st.cache_data(ttl=600, show_spinner=False)
def fetch_gdelt_news(query: str, max_records: int = 10) -> list:
    """
    GDELT Doc 2.0 API — free, no key required.
    Returns recent news articles matching the query.
    """
    try:
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": query,
            "mode": "artlist",
            "maxrecords": max_records,
            "format": "json",
            "timespan": "24h",
            "sort": "DateDesc",
        }
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        articles = r.json().get("articles", [])
        results = []
        for a in articles:
            # parse GDELT datetime format: YYYYMMDDHHMMSS
            raw_dt = str(a.get("seendate",""))
            try:
                dt = datetime.strptime(raw_dt[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                age = datetime.now(tz=timezone.utc) - dt
                age_s = f"{int(age.total_seconds()//3600)}h ago" if age.total_seconds()>3600 else f"{int(age.total_seconds()//60)}m ago"
            except:
                age_s = "recent"
            results.append({
                "title":  a.get("title","")[:120],
                "url":    a.get("url",""),
                "source": a.get("domain",""),
                "time":   age_s,
                "lang":   a.get("language",""),
            })
        return results
    except:
        return []

@st.cache_data(ttl=600, show_spinner=False)
def fetch_rss_safe(url: str, source: str, cat: str = "general") -> list:
    """
    Fetch and parse an RSS feed. Returns list of article dicts.
    Falls back to empty list on any error.
    """
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (OSINTArena/5.0)"})
        r.raise_for_status()
        items = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
        arts = []
        for item in items[:6]:
            def g(tag, txt):
                m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', txt, re.DOTALL | re.IGNORECASE)
                if m:
                    v = m.group(1).strip()
                    v = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', v, flags=re.DOTALL)
                    return html_lib.unescape(re.sub(r'<[^>]+>', '', v)).strip()
                return ""
            title = g("title", item); desc = g("description", item)
            link  = g("link",  item); pub  = g("pubDate", item)
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub)
                age = datetime.now(tz=timezone.utc) - dt.astimezone(timezone.utc)
                age_s = (f"{int(age.total_seconds()//3600)}h ago"
                         if age.total_seconds() > 3600
                         else f"{int(age.total_seconds()//60)}m ago")
            except:
                age_s = "recent"
            if title and len(title) > 10:
                arts.append({
                    "source": source, "category": cat,
                    "title": title[:120], "desc": (desc or "")[:220],
                    "link": link, "time": age_s,
                })
        return arts
    except:
        return []

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

# ─────────────────────────────────────────────────────────────
# MAP BUILDER  — FIX: uses carto-darkmatter (no Mapbox token)
# ─────────────────────────────────────────────────────────────
CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

def _sev_colors():
    return {
        "CRITICAL": [255,40,70,230], "HIGH": [255,120,40,200],
        "MED":      [255,170,0,170], "LOW":  [0,220,110,150], "INFO": [0,190,255,120],
    }

def build_global_map(eq_df, eonet_df, show_seis, show_volc, show_mvmt, show_conf, show_supply, show_heat):
    layers = []

    # Seismic
    if show_seis and not eq_df.empty:
        ep = eq_df.copy()
        ep["color"] = ep["mag"].apply(lambda m:
            [255,55,85,220] if m>=5.5 else [255,180,0,200] if m>=4.5 else [0,230,118,175] if m>=3.5 else [0,200,255,150])
        ep["radius"] = (ep["mag"]**2.3 * 15000).clip(10000, 240000)
        ep["tip"]    = ep.apply(lambda r: f"SEISMIC  M{r['mag']} | {r['place']} | {r['depth_km']}km depth", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=ep, get_position=["lon","lat"],
                                 get_radius="radius", get_fill_color="color",
                                 get_line_color=[255,255,255,30], line_width_min_pixels=1,
                                 pickable=True, auto_highlight=True))

    # EONET
    if show_volc and not eonet_df.empty:
        eo = eonet_df.copy()
        eo["color"]  = [[255,110,40,200]]*len(eo)
        eo["radius"] = 70000
        eo["tip"]    = eo.apply(lambda r: f"EONET  {r['title']} | {r['cat']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=eo, get_position=["lon","lat"],
                                 get_radius="radius", get_fill_color="color",
                                 pickable=True, auto_highlight=True))

    # Conflict incidents
    if show_conf:
        rows = []
        for cname, c in CONFLICTS.items():
            for inc in c["incidents"]:
                rows.append({**inc, "conflict": cname})
        if rows:
            cdf = pd.DataFrame(rows)
            sc  = _sev_colors()
            cdf["color"]  = cdf["severity"].map(sc)
            cdf["radius"] = cdf["severity"].map({"CRITICAL":100000,"HIGH":75000,"MED":55000,"LOW":40000,"INFO":30000})
            cdf["tip"]    = cdf.apply(lambda r:
                f"{r['conflict']} | {INCIDENT_ICONS.get(r['type'],'?')} {r['title']} | {r['loc']} | {r['severity']}", axis=1)
            layers.append(pdk.Layer("ScatterplotLayer", data=cdf, get_position=["lon","lat"],
                                     get_radius="radius", get_fill_color="color",
                                     pickable=True, auto_highlight=True))

    # Civil movements
    if show_mvmt:
        mdf = pd.DataFrame(MOVEMENTS)
        mdf["color"]  = mdf["sentiment"].map({"CRIT":[200,60,255,200],"HIGH":[157,110,255,185],"MED":[120,80,220,165]})
        mdf["radius"] = mdf["scale"] * 1800
        mdf["tip"]    = mdf.apply(lambda r:
            f"CIVIL  {r['title']} | {r['location']} | {r['size']} | {r['sentiment']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=mdf, get_position=["lon","lat"],
                                 get_radius="radius", get_fill_color="color",
                                 pickable=True, auto_highlight=True))

    # Supply arcs
    if show_supply:
        arc_rows = []
        for c in CONFLICTS.values():
            arc_rows.extend(c["supply_lines"])
        if arc_rows:
            adf = pd.DataFrame(arc_rows)
            color_map = {
                "Military Aid":[255,61,90,160], "Arms/Funding":[255,61,90,160],
                "RSF Support":[255,140,66,140],  "SAF Support":[0,200,255,140],
                "Junta Support":[255,61,90,140], "Arms Supply":[255,180,0,140],
                "Humanitarian":[0,230,118,150],
            }
            adf["color"] = adf["type"].apply(lambda t: color_map.get(t, [74,107,133,120]))
            layers.append(pdk.Layer("ArcLayer", data=adf,
                                     get_source_position=["from_lon","from_lat"],
                                     get_target_position=["to_lon","to_lat"],
                                     get_source_color="color", get_target_color="color",
                                     get_width=2, pickable=True, auto_highlight=True))

    # Heatmap
    if show_heat and not eq_df.empty:
        layers.append(pdk.Layer("HeatmapLayer",
                                 data=eq_df[["lat","lon","mag"]].rename(columns={"mag":"weight"}),
                                 get_position=["lon","lat"], get_weight="weight",
                                 radiusPixels=50, opacity=0.45))

    # ── KEY FIX: carto-darkmatter requires NO token ──────────
    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=22, longitude=18, zoom=1.4, pitch=0),
        map_style=CARTO_DARK,
        tooltip={
            "text": "{tip}",
            "style": {
                "backgroundColor": "#080f1c", "color": "#e2ecf8",
                "border": "1px solid rgba(0,200,255,.25)",
                "fontFamily": "IBM Plex Mono", "fontSize": "12px",
                "padding": "10px 14px", "borderRadius": "8px",
            }
        },
        height=440,
    )

def build_theatre_map(conflict_key, show_supply):
    C = CONFLICTS[conflict_key]
    inc_df = pd.DataFrame(C["incidents"])
    sc = _sev_colors()
    inc_df["color"]  = inc_df["severity"].map(sc)
    inc_df["radius"] = inc_df["severity"].map({"CRITICAL":60000,"HIGH":45000,"MED":35000,"LOW":25000,"INFO":20000})
    inc_df["tip"]    = inc_df.apply(lambda r:
        f"{INCIDENT_ICONS.get(r['type'],'?')} {r['title']}\n{r['loc']} · {r['date']}\nSeverity: {r['severity']} · Casualties: {r['casualties']}", axis=1)
    layers = [pdk.Layer("ScatterplotLayer", data=inc_df, get_position=["lon","lat"],
                          get_radius="radius", get_fill_color="color",
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
            adf["color"] = adf["type"].apply(lambda t: color_map.get(t,[74,107,133,120]))
            layers.append(pdk.Layer("ArcLayer", data=adf,
                get_source_position=["from_lon","from_lat"],
                get_target_position=["to_lon","to_lat"],
                get_source_color="color", get_target_color="color",
                get_width=2, pickable=True, auto_highlight=True))
    cx = np.mean([i["lon"] for i in C["incidents"]])
    cy = np.mean([i["lat"] for i in C["incidents"]])
    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=cy, longitude=cx, zoom=4, pitch=20),
        map_style=CARTO_DARK,
        tooltip={"text":"{tip}","style":{"backgroundColor":"#080f1c","color":"#e2ecf8","border":"1px solid rgba(255,61,90,.3)","fontFamily":"IBM Plex Mono","fontSize":"12px","padding":"10px","borderRadius":"8px"}},
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
# AI CALLER
# ─────────────────────────────────────────────
def call_ai(prompt, provider, api_key):
    if provider == "groq" and api_key:
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                json={"model":"llama-3.1-8b-instant","max_tokens":400,
                      "messages":[{"role":"system","content":"You are a concise OSINT intelligence analyst. Respond in plain text, no markdown, max 380 words."},
                                   {"role":"user","content":prompt}]},timeout=15)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e: return f"[Groq error: {e}]"
    if provider == "ollama":
        try:
            r = requests.post("http://localhost:11434/api/generate",
                json={"model":"llama3","prompt":prompt,"stream":False},timeout=25)
            return r.json().get("response","No response")
        except Exception as e: return f"[Ollama error: {e}]"
    if provider == "openrouter" and api_key:
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization":f"Bearer {api_key}","HTTP-Referer":"https://osint-arena.app","Content-Type":"application/json"},
                json={"model":"meta-llama/llama-3.1-8b-instruct:free","max_tokens":400,
                      "messages":[{"role":"user","content":prompt}]},timeout=16)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e: return f"[OpenRouter error: {e}]"
    return "⚠  No AI provider configured. Select Groq, Ollama, or OpenRouter in the sidebar."

# ─────────────────────────────────────────────
# FETCH LIVE DATA
# ─────────────────────────────────────────────
eq_df    = fetch_usgs()
eonet_df = fetch_eonet()
kp_data  = fetch_kp()
utc_now  = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark" style="margin-bottom:4px">OSINT<em>ARENA</em></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:10px;color:var(--muted);letter-spacing:.14em;font-weight:700;margin-bottom:16px">GLOBAL INTELLIGENCE PLATFORM v5</p>', unsafe_allow_html=True)

    tn, tc, tcol = get_tier(st.session_state.score)
    nt  = {"RECRUIT":2000,"ANALYST":5000,"AGENT":10000,"HANDLER":10000}[tn]
    xpp = min(100, int(st.session_state.score/nt*100))
    st.markdown(f"""
    <div class="m-panel">
      <div class="m-label">Analyst Profile</div>
      <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:6px">
        <div class="m-val m-violet" style="font-size:28px">{st.session_state.score:,}</div>
        <div class="badge {tc}">{tn}</div>
      </div>
      <div class="xp-track"><div class="xp-fill" style="width:{xpp}%"></div></div>
      <div class="m-sub" style="margin-top:4px">{xpp}% → next tier at {nt:,} XP</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    st.markdown("#### 🤖 AI Provider")
    st.caption("Enables AI analysis and situation reports.")
    prov = st.selectbox("AI Provider", ["groq","ollama","openrouter","none"], label_visibility="collapsed")
    st.session_state.ai_provider = prov
    if prov in ("groq","openrouter"):
        st.session_state.ai_key = st.text_input("API Key", type="password",
            placeholder="Paste your API key…", label_visibility="collapsed")
        if prov == "groq":
            st.caption("Free key at console.groq.com")
        else:
            st.caption("Free key at openrouter.ai")
    elif prov == "ollama":
        st.info("Ollama local: `ollama pull llama3 && ollama serve`")

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    st.markdown("#### 🗺 Global Map Layers")
    st.caption("Toggle layers on the command map.")
    show_seis  = st.toggle("🟦 Seismic Events",     value=True)
    show_volc  = st.toggle("🟠 Volcanic / EONET",   value=True)
    show_conf  = st.toggle("🔴 Conflict Incidents",  value=True)
    show_mvmt  = st.toggle("🟣 Civil Movements",    value=True)
    show_supp  = st.toggle("⟶ Supply Arc Lines",    value=True)
    show_heat  = st.toggle("🌡 Heatmap Mode",        value=False)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    st.markdown("#### 📡 Live Data Status")
    feeds_ok = not eq_df.empty
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
        <span><span class="pulse p-cyan"></span>NOAA Kp-index</span>
        <span style="color:var(--muted);font-size:11px">Kp {kp_data['kp']:.1f}</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse p-cyan"></span>GDELT News API</span>
        <span style="color:var(--muted);font-size:11px">free / no key</span>
      </div>
      <div style="display:flex;align-items:center;justify-content:space-between;font-size:12px">
        <span><span class="pulse p-red"></span>Conflict Theatres</span>
        <span style="color:var(--muted);font-size:11px">{len(CONFLICTS)} tracked</span>
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    if st.button("⟳  Refresh All Feeds", use_container_width=True):
        st.cache_data.clear(); st.rerun()

# ─────────────────────────────────────────────
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
    <div class="wordmark">OSINT<em>ARENA</em></div>
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

# Metrics
c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1: st.metric("Active Conflicts",  active_conf,       delta="LIVE")
with c2: st.metric("Total Casualties",  f"{total_cas:,}",  delta="All theatres")
with c3: st.metric("Seismic (24h)",     len(eq_df),        delta=f"M5+: {len(m5p)}")
with c4: st.metric("Civil Movements",   len(MOVEMENTS),    delta=f"Critical: {len(crit_mv)}")
with c5: st.metric("Kp Index",          f"{kp:.1f}",       delta="Storm ≥5.0")
with c6: st.metric("Analyst XP",        f"{st.session_state.score:,}", delta=tn)
st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# PERSISTENT GLOBAL MAP  (always visible, above all tabs)
# ═══════════════════════════════════════════════════════════════
total_inc     = sum(len(c["incidents"]) for c in CONFLICTS.values())
crit_inc_cnt  = sum(1 for c in CONFLICTS.values() for i in c["incidents"] if i["severity"]=="CRITICAL")

# Map header bar
st.markdown(f"""
<div class="map-top-bar">
  <div style="display:flex;align-items:center;gap:14px">
    <div class="map-title-text">🌐 GLOBAL COMMAND MAP</div>
    <div style="font-family:var(--fm);font-size:11px;color:var(--muted)">
      All active signals · Hover any marker for details · Toggle layers in sidebar
    </div>
  </div>
  <div class="map-legend">
    <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#00c8ff;margin-right:4px"></span>Seismic</span>
    <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#ff6a28;margin-right:4px"></span>EONET</span>
    <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#ff3d5a;margin-right:4px"></span>Conflict</span>
    <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#9d6eff;margin-right:4px"></span>Civil</span>
    <span style="margin-left:8px;padding-left:8px;border-left:1px solid rgba(0,200,255,.15)">
      <span class="pulse p-red"></span>{crit_inc_cnt} CRITICAL
    </span>
    <span><span class="pulse p-cyan"></span>{len(eq_df)} seismic</span>
    <span><span class="pulse p-orange"></span>{total_inc} incidents</span>
    <span class="live-badge"><span class="pulse p-red" style="margin-right:3px"></span>LIVE</span>
  </div>
</div>""", unsafe_allow_html=True)

# Map container with border connecting header
st.markdown('<div style="border:1px solid rgba(0,200,255,.12);border-top:none;border-radius:0 0 14px 14px;overflow:hidden;margin-bottom:20px">', unsafe_allow_html=True)
st.pydeck_chart(
    build_global_map(eq_df, eonet_df, show_seis, show_volc, show_mvmt, show_conf, show_supp, show_heat),
    use_container_width=True,
)
st.markdown('</div>', unsafe_allow_html=True)

# Ticker
tb = (
    [f'<span class="t-red t-hi">⚔ {n}: {c["intensity"]}</span>' for n,c in CONFLICTS.items()] +
    [f'<span class="t-red">M{r.mag} {r.place[:28]}</span>'       for _,r in eq_df.nlargest(5,"mag").iterrows()] +
    [f'<span class="t-amb">✊ {m["title"]} — {m["location"]}</span>' for m in MOVEMENTS[:4]]
)
ts = '<span class="t-sep"> ◈ </span>'.join(tb)
st.markdown(f'<div class="ticker-wrap"><div class="ticker-inner">{ts}<span class="t-sep"> ◈ </span>{ts}</div></div>', unsafe_allow_html=True)
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_conflict, tab_earth, tab_civil, tab_news, tab_arena, tab_ai = st.tabs([
    "⚔  Conflict Dashboard",
    "🌍  Earth Signals",
    "✊  Civil Movements",
    "📡  Live News",
    "🎯  Training Arena",
    "🤖  AI Analyst",
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — CONFLICT DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab_conflict:
    st.markdown("""
    <div class="helper">
      <b>Select a conflict theatre</b> below to explore its incident map, faction tracker, timeline,
      supply lines, and media reliability. Use the <b>AI Sitrep Generator</b> at the bottom for live intelligence reports.
    </div>""", unsafe_allow_html=True)

    theatre = st.radio("Select theatre:", list(CONFLICTS.keys()), horizontal=True, key="theatre_sel")
    st.session_state.selected_conflict = theatre
    C = CONFLICTS[theatre]

    int_cls = {"CRITICAL":"m-red","HIGH":"m-orange","MED":"m-amber"}
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

    # ── Live news for this theatre (browser-side JS via rss2json) ──
    with st.expander(f"📰 Live News — {theatre}", expanded=True):
        # Pick the 2 most relevant RSS sources for this conflict's region
        region_src_map = {
            "Ukraine–Russia War": ["Reuters","BBC World","ISW","Defense One"],
            "Gaza Conflict":      ["Al Jazeera","Reuters","BBC World","ISW"],
            "Israel–Iran War":    ["Reuters","Al Jazeera","ISW","BBC World"],
            "Sudan Civil War":    ["Reuters","Al Jazeera","BBC World","ACLED"],
            "Myanmar Civil War":  ["Reuters","BBC World","The Diplomat","ACLED"],
        }
        preferred = region_src_map.get(theatre, ["Reuters","BBC World","ISW"])
        theatre_feeds = [s for s in NEWS_SOURCES if s["name"] in preferred][:3]
        if not theatre_feeds:
            theatre_feeds = NEWS_SOURCES[:3]

        tf_js = json.dumps([
            {"name": s["name"], "rss": s["rss"],
             "color": NEWS_CAT_COLOR.get(s["cat"],"#4a6b85")}
            for s in theatre_feeds
        ])
        conflict_accent = C.get("factions",[{}])[0].get("color","#ff3d5a") if C.get("factions") else "#ff3d5a"

        theatre_news_html = f"""
<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#02040a;font-family:'DM Sans',system-ui,sans-serif;color:#e2ecf8;padding:8px;}}
#status{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6b85;margin-bottom:10px;
         display:flex;align-items:center;gap:6px;}}
.dot{{width:5px;height:5px;border-radius:50%;background:#00c8ff;
      animation:blink 1.2s ease-in-out infinite;flex-shrink:0;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;}}
@media(max-width:700px){{.grid{{grid-template-columns:1fr 1fr;}}}}
@media(max-width:450px){{.grid{{grid-template-columns:1fr;}}}}
.card{{background:#0b1524;border:1px solid rgba(0,200,255,.1);border-radius:9px;
       padding:12px 14px;border-left:3px solid {conflict_accent};transition:border-color .2s;}}
.card:hover{{border-color:rgba(0,200,255,.28);}}
.src{{font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;
      letter-spacing:.07em;text-transform:uppercase;color:#4a6b85;margin-bottom:5px;}}
.hl{{font-size:12px;font-weight:600;color:#e2ecf8;line-height:1.4;margin-bottom:8px;}}
.foot{{display:flex;align-items:center;justify-content:space-between;}}
.ts{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#4a6b85;}}
a.r{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#00c8ff;text-decoration:none;
     padding:2px 8px;border:1px solid rgba(0,200,255,.25);border-radius:4px;}}
a.r:hover{{background:rgba(0,200,255,.1);}}
.err{{color:#ff8c42;font-size:11px;font-family:'IBM Plex Mono',monospace;line-height:1.6;}}
.srclinks{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}}
.srclinks a{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#00c8ff;
             text-decoration:none;padding:3px 10px;
             border:1px solid rgba(0,200,255,.25);border-radius:12px;}}
</style></head><body>
<div id="status"><div class="dot"></div><span>Loading {theatre} news…</span></div>
<div id="grid" class="grid"></div>
<script>
const FEEDS={tf_js};
const PROXIES=[
  u=>`https://api.allorigins.win/get?url=${{encodeURIComponent(u)}}`,
  u=>`https://corsproxy.io/?${{encodeURIComponent(u)}}`,
  u=>`https://api.codetabs.com/v1/proxy?quest=${{encodeURIComponent(u)}}`,
];
function ta(s){{try{{const d=new Date(s),x=(Date.now()-d)/1000;
  if(x<60)return Math.round(x)+'s';if(x<3600)return Math.round(x/60)+'m';
  return Math.round(x/3600)+'h ago';}}catch{{return '';}}}}
function esc(s){{return(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}}
function parseXML(xml){{
  try{{const doc=new DOMParser().parseFromString(xml,'text/xml');
    if(doc.querySelector('parsererror'))return[];
    return[...doc.querySelectorAll('item')].slice(0,6).map(it=>{{
      const txt=n=>{{const el=it.querySelector(n);const raw=(el?.textContent||el?.getAttribute('href')||'');return raw.split('<![CDATA[').join('').split(']]>').join('').trim();}};
      return{{title:txt('title'),link:txt('link'),pub:txt('pubDate')}};
    }});}}catch{{return[];}}}}
async function fetchFeed(f){{
  for(const px of PROXIES){{try{{
    const r=await fetch(px(f.rss),{{signal:AbortSignal.timeout(9000)}});
    if(!r.ok)continue;
    const ct=r.headers.get('content-type')||'';
    let xml='';
      if(ct.includes('json')){{const j=await r.json();xml=j.contents||j.data||'';}}
    else xml=await r.text();
    const items=parseXML(xml);
    if(items.length)return{{f,items}};
  }}catch{{}}}}
  return{{f,items:[]}};
}}
async function main(){{
  const statusEl=document.getElementById('status');
  const gridEl=document.getElementById('grid');
  const res=await Promise.all(FEEDS.map(fetchFeed));
  const arts=[];let n=0;
  res.forEach(({{f,items}})=>{{if(items.length){{n++;
    items.forEach(it=>arts.push({{title:it.title,link:it.link,
      time:ta(it.pub),src:f.name,col:f.color}}));}}
  }});
  if(!arts.length){{
    statusEl.innerHTML='<span style="color:#ff8c42">⚠ feeds blocked</span>';
    gridEl.innerHTML='<div class="err">Live feeds could not load in this viewer.<div class="srclinks">'+
      FEEDS.map(f=>`<a href="https://${{f.name.toLowerCase().replace(/\\s+/g,'')}}.com" target="_blank">${{f.name}}</a>`).join('')+
      '</div></div>';return;}}
  statusEl.innerHTML=`<div class="dot" style="background:#00e676"></div><span>${{n}} feed${{n>1?'s':''}} · ${{arts.length}} articles</span>`;
  gridEl.innerHTML=arts.slice(0,12).map(a=>`
    <div class="card">
      <div class="src" style="color:${{a.col}}">${{esc(a.src)}}</div>
      <div class="hl">${{esc(a.title).slice(0,110)}}</div>
      <div class="foot">
        <span class="ts">${{a.time}}</span>
        ${{a.link?`<a class="r" href="${{a.link}}" target="_blank" rel="noopener">Read →</a>`:''}}
      </div>
    </div>`).join('');}}
main();
</script></body></html>"""
        components.html(theatre_news_html, height=340, scrolling=False)

    st.markdown("---")

    # Map + gauges
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

    # Incidents + Factions
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

    # Timeline + Supply + Media
    tl_c, side_c = st.columns([2,1], gap="medium")
    with tl_c:
        st.markdown('<div class="sec-label">📅 Conflict Timeline</div>', unsafe_allow_html=True)
        st.plotly_chart(conflict_timeline_chart(C["timeline"]),use_container_width=True,config={"displayModeBar":False})
        st.markdown("""
        <div style="display:flex;gap:14px;margin-bottom:12px;flex-wrap:wrap">
          <span style="font-size:11px;color:#ff3d5a">● Escalation</span>
          <span style="font-size:11px;color:#00c8ff">● Milestone</span>
          <span style="font-size:11px;color:#00e676">● Diplomatic</span>
          <span style="font-size:11px;color:#ffb400">● Setback</span>
          <span style="font-size:11px;color:#9d6eff">● Ongoing</span>
        </div>""", unsafe_allow_html=True)
        tl_tc = {"escalation":"var(--red)","milestone":"var(--cyan)","diplomatic":"var(--green)","setback":"var(--amber)","ongoing":"var(--violet)"}
        for item in reversed(C["timeline"]):
            col = tl_tc.get(item["type"],"var(--muted)")
            st.markdown(f"""
            <div class="tl-item" style="border-left:1px solid var(--bord2)">
              <div style="position:absolute;left:-5px;top:4px;width:9px;height:9px;border-radius:50%;background:{col}"></div>
              <div class="tl-date">{item['date']}</div>
              <div class="tl-text">{item['event']}</div>
              <div class="tl-tag" style="color:{col}">{item['type'].upper()}</div>
            </div>""", unsafe_allow_html=True)

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

    # AI Sitrep
    st.markdown('<div class="sec-label">🤖 AI Situation Report Generator</div>', unsafe_allow_html=True)
    sr1, sr2 = st.columns([1,1], gap="medium")
    with sr1:
        sitrep_type = st.selectbox("Report type:", [
            "Executive Summary (3 paragraphs)",
            "Escalation Risk Assessment",
            "Humanitarian Impact Brief",
            "Supply Chain & External Support Analysis",
            "Media Bias & Information Environment",
            "Ceasefire / Diplomatic Prospects",
        ])
        if st.button(f"⚡  Generate Sitrep — {theatre.split('–')[0].strip()}", use_container_width=True):
            fac_s = "\n".join([f"  - {f['name']} ({f['side']}): {f['status']}, {f['territory_pct']}% territory, backed by {', '.join(f['support'])}" for f in C["factions"]])
            inc_s = "\n".join([f"  - {i['date']} [{i['type']}]: {i['title']} ({i['severity']}, {i['casualties']} cas.)" for i in C["incidents"][:5]])
            prompt = (f"Write a '{sitrep_type}' for the {theatre}.\n\n"
                      f"DATA:\nStatus: {C['status']} | Intensity: {C['intensity']} | Escalation: {C['escalation']}/100\n"
                      f"Casualties: {C['casualties_total']:,} | Displaced: {C['displaced']:,} | Ceasefire: {'Yes' if C['ceasefire'] else 'No'}\n\n"
                      f"FACTIONS:\n{fac_s}\n\nRECENT INCIDENTS:\n{inc_s}\n\n"
                      f"Plain text, professional intelligence style, no markdown, 250-380 words.")
            with st.spinner("Generating intelligence report…"):
                result = call_ai(prompt, st.session_state.ai_provider, st.session_state.ai_key)
            st.session_state.conflict_sitrep = result
    with sr2:
        if st.session_state.conflict_sitrep:
            st.markdown(f'<div class="ai-terminal">{st.session_state.conflict_sitrep}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="gcard" style="min-height:180px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;text-align:center">
              <div style="font-size:28px">📄</div>
              <div style="font-size:14px;color:var(--text2);font-weight:500">No report generated yet</div>
              <div style="font-size:12px;color:var(--muted)">Select a report type and click Generate.</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 2 — EARTH SIGNALS
# ══════════════════════════════════════════════════════════════
with tab_earth:
    st.markdown("""
    <div class="helper">
      <b>Earth Signals</b> shows live USGS seismic data, NASA EONET volcanic/wildfire events,
      and NOAA geomagnetic conditions. The global command map above already shows all layers.
    </div>""", unsafe_allow_html=True)

    mc, rc = st.columns([3,1], gap="medium")
    with mc:
        layers_e = []
        if show_seis and not eq_df.empty:
            ep = eq_df.copy()
            ep["color"] = ep["mag"].apply(lambda m: [255,55,85,220] if m>=5.5 else [255,180,0,200] if m>=4.5 else [0,230,118,175] if m>=3.5 else [0,200,255,150])
            ep["radius"] = (ep["mag"]**2.3*15000).clip(10000,240000)
            ep["tip"]   = ep.apply(lambda r: f"M{r['mag']} | {r['place']} | {r['depth_km']}km depth | {r['time']}", axis=1)
            layers_e.append(pdk.Layer("ScatterplotLayer",data=ep,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True))
        if show_volc and not eonet_df.empty:
            eo = eonet_df.copy(); eo["color"]=[[255,110,40,200]]*len(eo); eo["radius"]=70000
            eo["tip"] = eo.apply(lambda r: f"{r['title']} | {r['cat']}", axis=1)
            layers_e.append(pdk.Layer("ScatterplotLayer",data=eo,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True))
        if show_heat and not eq_df.empty:
            layers_e.append(pdk.Layer("HeatmapLayer",data=eq_df[["lat","lon","mag"]].rename(columns={"mag":"weight"}),get_position=["lon","lat"],get_weight="weight",radiusPixels=50,opacity=.45))

        st.markdown('<div class="sec-label">🗺 Earth Signals Map</div>', unsafe_allow_html=True)
        st.pydeck_chart(pdk.Deck(layers=layers_e,
            initial_view_state=pdk.ViewState(latitude=20,longitude=10,zoom=1.3),
            map_style=CARTO_DARK,
            tooltip={"text":"{tip}","style":{"backgroundColor":"#080f1c","color":"#e2ecf8","border":"1px solid rgba(0,200,255,.2)","fontFamily":"IBM Plex Mono","fontSize":"12px","padding":"10px","borderRadius":"8px"}},
            height=380), use_container_width=True)

        st.markdown('<div class="sec-label" style="margin-top:12px">📈 Geomagnetic Kp — 24 hours</div>', unsafe_allow_html=True)
        st.caption("Kp ≥ 5 = geomagnetic storm. Affects GPS, HF radio, and power grids.")
        st.plotly_chart(kp_chart(kp_data["series"]),use_container_width=True,config={"displayModeBar":False})

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
        mdf["color"] = mdf["sentiment"].map({"CRIT":[200,60,255,220],"HIGH":[157,110,255,190],"MED":[120,80,220,160]})
        mdf["radius"] = mdf["scale"] * 2200
        mdf["tip"] = mdf.apply(lambda r: f"{r['title']}\n{r['location']} · {r['size']} participants\n{r['type'].upper()} · Sentiment: {r['sentiment']}", axis=1)
        st.markdown('<div class="sec-label">🗺 Civil Movements Map</div>', unsafe_allow_html=True)
        st.pydeck_chart(pdk.Deck(
            layers=[pdk.Layer("ScatterplotLayer",data=mdf,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True)],
            initial_view_state=pdk.ViewState(latitude=25,longitude=20,zoom=1.3),
            map_style=CARTO_DARK,
            tooltip={"text":"{tip}","style":{"backgroundColor":"#080f1c","color":"#e2ecf8","border":"1px solid rgba(157,110,255,.25)","fontFamily":"IBM Plex Mono","fontSize":"12px","padding":"10px","borderRadius":"8px"}},
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
# TAB 4 — LIVE NEWS  +  LIVE TV STUDIO
# ══════════════════════════════════════════════════════════════
with tab_news:

    # ── YouTube channel registry ────────────────────────────
    # live_vid: permanent 24/7 live stream video ID (hardcoded as reliable fallback)
    # These are the well-known always-on streams each channel maintains.
    # With a YouTube Data API key the JS will re-resolve the current live ID automatically.
    YT_CHANNELS = [
        {"name":"Al Jazeera English",  "id":"UCNye-wNBqNL5ZzHSJdba7Xg","color":"#00873c","cat":"global",
         "live_vid":"XWq5kBlakcQ",
         "desc":"Qatar-based global news, 24/7 English"},
        {"name":"BBC News",             "id":"UC16niRr50-MSBwiO3YDb3RA","color":"#bb1919","cat":"global",
         "live_vid":"w_Ma8oQLmSM",
         "desc":"British public broadcaster — world news"},
        {"name":"DW News",              "id":"UCknLrEdhRCp1aegoMqRaCZg","color":"#003087","cat":"global",
         "live_vid":"F8xTSAtDJpA",
         "desc":"Deutsche Welle — German international news"},
        {"name":"France 24 English",   "id":"UCQfwfsi5VrQ8yKZ-UWmAoBw","color":"#002395","cat":"global",
         "live_vid":"h3MuIUNCCLI",
         "desc":"French international broadcaster in English"},
        {"name":"Euronews",             "id":"UCg2JZlAJZIxzxRDat2HVkFw","color":"#006fbf","cat":"global",
         "live_vid":"RABaBlFrHJ0",
         "desc":"Pan-European news in English"},
        {"name":"Sky News",             "id":"UCoMdktPbSTixAyNGwb-UYkQ","color":"#004f9f","cat":"conflict",
         "live_vid":"9Auq9mYxFEE",
         "desc":"UK breaking news & international coverage"},
        {"name":"WION",                 "id":"UCExCSExkE0M-kDblPqMFjGQ","color":"#e8520a","cat":"conflict",
         "live_vid":"Suj9hMOCCss",
         "desc":"World Is One News — South Asian perspective"},
        {"name":"TRT World",            "id":"UC7fWeaHhqgM4Ry-RMpM2YYw","color":"#e30a17","cat":"conflict",
         "live_vid":"ObfXqfr9tSI",
         "desc":"Turkish public broadcaster — global news"},
        {"name":"Times Now",            "id":"UC5pM_6w9V_KAOWiC5_A-FUg","color":"#e31837","cat":"conflict",
         "live_vid":"AbuWj7nS8k4",
         "desc":"Indian English news, international affairs"},
        {"name":"NASA TV",              "id":"UCLA_DiR1FfKNvjuUpBHmylQ","color":"#0b3d91","cat":"science",
         "live_vid":"21X5lGlDOfg",
         "desc":"NASA official — missions & Earth science"},
        {"name":"Al Arabiya English",   "id":"UC5xshE6wCNFWnqNu5XhBMEg","color":"#b8860b","cat":"conflict",
         "live_vid":"hQq7Q2MsFRg",
         "desc":"Saudi-owned pan-Arab news in English"},
        {"name":"Bloomberg TV",         "id":"UCIALMKvObZNtJ6AmdCLP7Lg","color":"#474747","cat":"global",
         "live_vid":"dp8PhLsUcFE",
         "desc":"Global markets, business, finance"},
        {"name":"Euronews (FR)",        "id":"UCDPXq59b4zeqoKlTkfaQYhg","color":"#4a9fd4","cat":"global",
         "live_vid":"VLGgPJLCvhM",
         "desc":"Euronews en français — 24/7"},
        {"name":"Al Jazeera Arabic",    "id":"UCSls-6_NBBBSvowKyMBLEUA","color":"#007a4d","cat":"conflict",
         "live_vid":"XsOt5SdGMU8",
         "desc":"Al Jazeera العربية — Arabic news stream"},
    ]

    YT_CAT_NAMES = {
        "ALL":"📺 All Channels","global":"🌐 Global Wire",
        "conflict":"⚔ Conflict / Defence","science":"🔬 Science",
    }
    CAT_TABS_NEWS = ["ALL","global","science","geopolitics","conflict","climate","spaceweather"]
    CAT_NAMES_ART = {
        "ALL":"All Sources","global":"🌐 Global","science":"🔬 Science",
        "geopolitics":"🗺 Geopolitics","conflict":"⚔ Conflict",
        "climate":"🌱 Climate","spaceweather":"☀ Space Weather",
    }

    sub_tv, sub_articles, sub_directory = st.tabs([
        "📺  Live TV Streams",
        "📰  Article Feeds",
        "📋  Source Directory",
    ])

    # ── SUB-TAB A: LIVE TV ───────────────────────────────────
    with sub_tv:
        st.markdown("""
        <div class="helper">
          <b>Live TV Studio</b> — click any channel to stream it live from YouTube.
          Channels actively broadcasting will play immediately. Add a free
          <b>YouTube Data API v3 key</b> below for automatic live-stream detection.
        </div>""", unsafe_allow_html=True)


    # ── Channel registry — direct HLS streams (no YouTube embed needed) ──
    # Official Akamai/CloudFront CDN streams. No embed restrictions.
    HLS_CHANNELS = [
        {"name":"Al Jazeera English","color":"#00873c","cat":"global",
         "hls":"https://live-hls-web-aje.getaj.net/AJE/index.m3u8",
         "web":"https://www.aljazeera.com/live",
         "desc":"Qatar-based global news, 24/7 English"},
        {"name":"DW News","color":"#003087","cat":"global",
         "hls":"https://dwamdstream102.akamaized.net/hls/live/2015525/dwstream102/stream01/streamPlaylist.m3u8",
         "web":"https://www.dw.com/en/media-center/live-tv/l-150330",
         "desc":"Deutsche Welle — German public broadcaster"},
        {"name":"France 24 English","color":"#002395","cat":"global",
         "hls":"https://live.france.tv/france-24-en/index.m3u8",
         "web":"https://www.france24.com/en/live-news",
         "desc":"French international broadcaster in English"},
        {"name":"TRT World","color":"#e30a17","cat":"conflict",
         "hls":"https://tv-trtworld.live.trt.com.tr/master.m3u8",
         "web":"https://www.trtworld.com/live",
         "desc":"Turkish public broadcaster — global news"},
        {"name":"Euronews","color":"#006fbf","cat":"global",
         "hls":"https://euronews-euronews-english-1-eu.rakuten.wurl.tv/playlist.m3u8",
         "web":"https://www.euronews.com/live",
         "desc":"Pan-European news in English"},
        {"name":"NHK World","color":"#003087","cat":"global",
         "hls":"https://cdn.nhkworld.jp/www11/nhkworld-tv/pre/hlscomp.m3u8",
         "web":"https://www3.nhk.or.jp/nhkworld/en/live",
         "desc":"Japan Broadcasting Corporation — English"},
        {"name":"CGTN English","color":"#c00","cat":"global",
         "hls":"https://news.cgtn.com/resource/live/english/cgtn-news.m3u8",
         "web":"https://www.cgtn.com/live",
         "desc":"China Global Television Network"},
        {"name":"Al Arabiya","color":"#b8860b","cat":"conflict",
         "hls":"https://live.alarabiya.net/alarabiapublish/alarabiya.smil/playlist.m3u8",
         "web":"https://www.alarabiya.net",
         "desc":"Saudi-owned pan-Arab news channel"},
        {"name":"Al Jazeera Arabic","color":"#007a4d","cat":"conflict",
         "hls":"https://live-hls-web-ajf.getaj.net/AJF/index.m3u8",
         "web":"https://www.aljazeera.net/live",
         "desc":"Al Jazeera العربية — Arabic stream"},
        {"name":"NASA TV","color":"#0b3d91","cat":"science",
         "hls":"https://nasa-i.akamaihd.net/hls/live/253565/NASA-NTV1-HLS/master.m3u8",
         "web":"https://www.nasa.gov/nasatv",
         "desc":"NASA — missions, Earth science, spacewalks"},
        {"name":"ABC News Live","color":"#00008b","cat":"global",
         "hls":"https://abcnewslive-abcnewslive.akamaized.net/hls/live/2028883/abcnewslive/master.m3u8",
         "web":"https://abcnews.go.com/live",
         "desc":"ABC News 24/7 live stream — USA"},
        {"name":"Bloomberg TV","color":"#474747","cat":"global",
         "hls":"https://cdn-videos.akamaized.net/btv/desktop/akamai/europe/live/primary.m3u8",
         "web":"https://www.bloomberg.com/live",
         "desc":"Global markets, business, finance"},
        {"name":"VOA News","color":"#003478","cat":"global",
         "hls":"https://voa-ingest.akamaized.net/hls/live/2033874/tvmc06/playlist.m3u8",
         "web":"https://www.voanews.com",
         "desc":"Voice of America — US international broadcaster"},
        {"name":"France 24 Arabic","color":"#4a9fd4","cat":"conflict",
         "hls":"https://live.france.tv/france-24-ar/index.m3u8",
         "web":"https://www.france24.com/ar",
         "desc":"France 24 عربي — 24/7 Arabic stream"},
    ]

    YT_CAT_NAMES = {
        "ALL":"All Channels","global":"Global Wire",
        "conflict":"Conflict / Middle East","science":"Science",
    }
    CAT_TABS_NEWS = ["ALL","global","science","geopolitics","conflict","climate","spaceweather"]
    CAT_NAMES_ART = {
        "ALL":"All Sources","global":"Global","science":"Science",
        "geopolitics":"Geopolitics","conflict":"Conflict",
        "climate":"Climate","spaceweather":"Space Weather",
    }

    sub_tv, sub_articles, sub_directory = st.tabs([
        "📺  Live TV Streams",
        "📰  Article Feeds",
        "📋  Source Directory",
    ])

    # ── SUB-TAB A: LIVE TV (HLS via hls.js) ─────────────────
    with sub_tv:
        hls_cats = list(dict.fromkeys([c["cat"] for c in HLS_CHANNELS]))
        hls_cat_sel = st.radio(
            "Filter:", ["ALL"] + hls_cats,
            format_func=lambda x: YT_CAT_NAMES.get(x, x.title()),
            horizontal=True, label_visibility="collapsed",
        )
        vis_ch = [c for c in HLS_CHANNELS if hls_cat_sel=="ALL" or c["cat"]==hls_cat_sel]
        ch_js  = json.dumps(vis_ch)

        tv_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#02040a;font-family:'DM Sans',system-ui,sans-serif;color:#e2ecf8;}}
#cg{{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:8px;padding:12px 12px 0;}}
.cb{{background:#0b1524;border:1px solid rgba(0,200,255,.12);border-radius:8px;
     padding:9px 11px;cursor:pointer;transition:all .18s;text-align:left;}}
.cb:hover{{border-color:rgba(0,200,255,.35);background:#0f1e35;}}
.cb.active{{border-color:var(--col,#00c8ff);background:rgba(0,200,255,.07);box-shadow:0 0 12px rgba(0,200,255,.08);}}
.cn{{font-size:12px;font-weight:600;color:#e2ecf8;line-height:1.3;margin-bottom:3px;}}
.cd{{font-size:10px;color:#4a6b85;line-height:1.3;}}
.ds{{width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle;}}
#pw{{margin:10px 12px 8px;background:#000;border-radius:10px;overflow:hidden;border:1px solid rgba(0,200,255,.15);}}
#pb{{display:flex;align-items:center;justify-content:space-between;padding:8px 14px;background:#070e1a;border-bottom:1px solid rgba(0,200,255,.1);}}
#np{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#e2ecf8;display:flex;align-items:center;gap:8px;}}
.lp{{background:#ff3d5a;color:#fff;font-size:9px;font-weight:700;padding:2px 7px;border-radius:20px;letter-spacing:.05em;animation:lpa 2s ease-in-out infinite;}}
@keyframes lpa{{0%,100%{{opacity:1}}50%{{opacity:.55}}}}
#pa{{display:flex;gap:8px;}}
.pb2{{background:transparent;border:1px solid rgba(0,200,255,.2);color:#00c8ff;font-family:'IBM Plex Mono',monospace;font-size:10px;padding:4px 10px;border-radius:5px;cursor:pointer;transition:background .15s;}}
.pb2:hover{{background:rgba(0,200,255,.1);}}
#vw{{width:100%;aspect-ratio:16/9;background:#000;display:block;}}
#sb{{padding:6px 14px;background:#060d18;font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6b85;border-top:1px solid rgba(0,200,255,.08);min-height:26px;display:flex;align-items:center;gap:6px;}}
.sdot{{width:5px;height:5px;border-radius:50%;flex-shrink:0;}}
.ok{{background:#00e676;box-shadow:0 0 5px #00e676;}}
.loading{{background:#ffb400;animation:lpa 1s ease-in-out infinite;}}
.err{{background:#ff3d5a;}}
</style></head><body>
<div id="cg"></div>
<div id="pw">
  <div id="pb">
    <div id="np"><span class="lp">● LIVE</span><span id="pname">Select a channel</span></div>
    <div id="pa">
      <button class="pb2" id="mbtn" onclick="doMute()">🔊 Unmute</button>
      <button class="pb2" onclick="doWeb()">↗ Website</button>
      <button class="pb2" onclick="doFS()">⛶ Fullscreen</button>
    </div>
  </div>
  <video id="vw" controls autoplay muted playsinline></video>
  <div id="sb"><div class="sdot loading" id="sdot"></div><span id="stxt">Ready — select a channel above</span></div>
</div>
<script src="https://cdn.jsdelivr.net/npm/hls.js@latest/dist/hls.min.js"></script>
<script>
const CH={ch_js};
let cur=null,muted=true,hls=null,curWeb='';

function renderGrid(){{
  document.getElementById('cg').innerHTML=CH.map((c,i)=>`
    <div class="cb" id="b${{i}}" style="--col:${{c.color}}" onclick="pick(${{i}})">
      <div class="cn"><span class="ds" style="background:${{c.color}}"></span>${{c.name}}</div>
      <div class="cd">${{c.desc.slice(0,52)}}</div>
    </div>`).join('');
}}

function setSt(txt,cls){{
  document.getElementById('stxt').textContent=txt;
  document.getElementById('sdot').className='sdot '+cls;
}}

function pick(i){{
  cur=i;
  document.querySelectorAll('.cb').forEach((b,j)=>b.classList.toggle('active',j===i));
  const c=CH[i]; curWeb=c.web;
  document.getElementById('pname').textContent=c.name;
  setSt('Connecting to '+c.name+'...','loading');
  const v=document.getElementById('vw');
  if(hls){{hls.destroy();hls=null;}}
  if(Hls.isSupported()){{
    hls=new Hls({{enableWorker:true,lowLatencyMode:true,backBufferLength:30}});
    hls.loadSource(c.hls);
    hls.attachMedia(v);
    hls.on(Hls.Events.MANIFEST_PARSED,()=>{{
      v.muted=muted;
      v.play().catch(()=>{{v.muted=true;muted=true;document.getElementById('mbtn').textContent='🔊 Unmute';v.play();}});
      setSt('● Live · '+c.name+(muted?' · click 🔊 Unmute for audio':''),'ok');
    }});
    hls.on(Hls.Events.ERROR,(e,d)=>{{
      if(d.fatal){{
        if(d.type===Hls.ErrorTypes.NETWORK_ERROR){{setSt('Network error — retrying...','loading');hls.startLoad();}}
        else if(d.type===Hls.ErrorTypes.MEDIA_ERROR){{setSt('Media error — recovering...','loading');hls.recoverMediaError();}}
        else{{setSt('Stream unavailable — try another channel','err');}}
      }}
    }});
  }}else if(v.canPlayType('application/vnd.apple.mpegurl')){{
    v.src=c.hls;v.muted=muted;v.play().catch(()=>{{v.muted=true;v.play();}});
    setSt('● Live · '+c.name+' (Safari HLS)','ok');
  }}else{{setSt('HLS not supported — visit: '+c.web,'err');}}
}}

function doMute(){{
  const v=document.getElementById('vw');
  muted=!muted;v.muted=muted;
  document.getElementById('mbtn').textContent=muted?'🔊 Unmute':'🔇 Mute';
}}
function doWeb(){{if(curWeb)window.open(curWeb,'_blank');}}
function doFS(){{
  const w=document.getElementById('pw');
  if(!document.fullscreenElement)w.requestFullscreen?.();
  else document.exitFullscreen?.();
}}

renderGrid();pick(0);
</script></body></html>"""

        components.html(tv_html, height=880, scrolling=False)
        st.caption("Streams delivered via official channel CDNs (Akamai/CloudFront). Video starts muted — click 🔊 Unmute for audio. If a stream fails, try another channel.")


    # ── SUB-TAB B: ARTICLE FEEDS ─────────────────────────────
    with sub_articles:
        cat_sel = st.radio(
            "Category:", CAT_TABS_NEWS,
            format_func=lambda x: CAT_NAMES_ART.get(x,x),
            horizontal=True, label_visibility="collapsed",
        )
        vis_src = [s for s in NEWS_SOURCES if cat_sel=="ALL" or s["cat"]==cat_sel]

        st.markdown('<div class="sec-label">📡 Live Article Feed</div>', unsafe_allow_html=True)
        st.caption("Fetched live in your browser — three CORS proxy fallbacks (allorigins → corsproxy → codetabs).")

        feeds_js = json.dumps([
            {"name":s["name"],"rss":s["rss"],
             "color":NEWS_CAT_COLOR.get(s["cat"],"#4a6b85"),"cat":s["cat"]}
            for s in vis_src[:4]
        ])

        art_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:#02040a;font-family:'DM Sans',system-ui,sans-serif;color:#e2ecf8;padding:12px;}}
#st{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#4a6b85;margin-bottom:14px;
      display:flex;align-items:center;gap:8px;min-height:18px;}}
.dot{{width:6px;height:6px;border-radius:50%;background:#00c8ff;animation:bl 1.2s ease-in-out infinite;flex-shrink:0;}}
@keyframes bl{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.g{{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
@media(max-width:560px){{.g{{grid-template-columns:1fr;}}}}
.c{{background:#0b1524;border:1px solid rgba(0,200,255,.12);border-radius:10px;
     padding:14px 16px;position:relative;overflow:hidden;transition:border-color .18s,transform .15s;}}
.c:hover{{border-color:rgba(0,200,255,.3);transform:translateY(-1px);}}
.c::after{{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;
            background:linear-gradient(180deg,var(--ac,#00c8ff),transparent);}}
.s{{font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;margin-bottom:6px;}}
.h{{font-size:13px;font-weight:600;color:#e2ecf8;line-height:1.45;margin-bottom:8px;}}
.f{{display:flex;align-items:center;justify-content:space-between;}}
.t{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6b85;}}
a.r{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#00c8ff;text-decoration:none;
     padding:3px 10px;border:1px solid rgba(0,200,255,.28);border-radius:5px;white-space:nowrap;}}
a.r:hover{{background:rgba(0,200,255,.1);}}
.err{{color:#ff8c42;font-family:'IBM Plex Mono',monospace;font-size:11px;padding:12px;
       border:1px solid rgba(255,140,66,.25);border-radius:8px;background:rgba(255,140,66,.05);line-height:1.6;}}
.sl{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px;}}
.sl a{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#00c8ff;text-decoration:none;
        padding:4px 12px;border:1px solid rgba(0,200,255,.25);border-radius:20px;}}
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
    ge.innerHTML='<div class="err">RSS feeds could not load in this browser context.<div class="sl">'+
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
        st.markdown('<div class="sec-label">📺 YouTube Live Channels</div>', unsafe_allow_html=True)
        yt_dir_cols = st.columns(4)
        for i, ch in enumerate(YT_CHANNELS):
            col = ch["color"]
            with yt_dir_cols[i % 4]:
                st.markdown(f"""
                <div class="src-directory-card" style="border-left:3px solid {col}">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
                    <div style="font-family:var(--fm);font-size:11px;font-weight:600;color:{col}">{ch['name']}</div>
                    <div class="badge" style="color:{col};border-color:{col}44;background:{col}15;font-size:8px">{ch['cat'].upper()}</div>
                  </div>
                  <div style="font-size:12px;color:var(--muted);margin-bottom:8px">{ch['desc']}</div>
                  <a href="https://www.youtube.com/channel/{ch['id']}" target="_blank"
                     class="news-link" style="font-size:10px">Watch on YouTube →</a>
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
                  <a href="https://{s.get('site','#')}" target="_blank"
                     class="news-link" style="font-size:10px">Visit {s.get('site',s['name'])} →</a>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 5 — TRAINING ARENA
# ══════════════════════════════════════════════════════════════
with tab_arena:
    st.markdown("""
    <div class="helper">
      <b>Training Arena</b> tests OSINT analysis skills with real-world intelligence scenarios.
      Correct answers earn XP and advance your analyst tier: Recruit → Analyst → Agent → Handler.
    </div>""", unsafe_allow_html=True)

    lc, cc2 = st.columns([1,2], gap="medium")
    with lc:
        st.markdown('<div class="sec-label">🏆 Leaderboard</div>', unsafe_allow_html=True)
        avts = ["background:rgba(255,61,90,.15);color:#ff3d5a","background:rgba(157,110,255,.15);color:#9d6eff",
                "background:rgba(255,180,0,.15);color:#ffb400","background:rgba(255,140,66,.15);color:#ff8c42",
                "background:rgba(74,107,133,.15);color:#4a6b85"]
        medals = ["🥇","🥈","🥉","④","⑤"]
        for i,(name,tier,sc,col) in enumerate(LEADERBOARD):
            st.markdown(f"""
            <div class="lb-row">
              <div style="font-size:16px;width:22px">{medals[i]}</div>
              <div class="lb-avatar" style="{avts[i]}">{name[:2].upper()}</div>
              <div style="flex:1">
                <div class="sig-title" style="color:{col};font-size:13px">{name}</div>
                <div class="sig-meta">{tier}</div>
              </div>
              <div style="font-family:var(--fd);font-size:18px;color:var(--green)">{sc:,}</div>
            </div>""", unsafe_allow_html=True)

        tn2,tc2,_ = get_tier(st.session_state.score)
        st.markdown(f"""
        <div style="margin:10px 4px 0">
          <div class="lb-row" style="background:rgba(157,110,255,.05);border:1px solid rgba(157,110,255,.22);border-radius:10px;padding:12px 14px">
            <div style="font-family:var(--fd);font-size:18px;color:var(--violet);width:32px">#142</div>
            <div class="lb-avatar" style="background:rgba(0,200,255,.12);color:var(--cyan)">YOU</div>
            <div style="flex:1">
              <div class="sig-title" style="color:#9d6eff">you</div>
              <div class="sig-meta">{tn2}</div>
            </div>
            <div style="font-family:var(--fd);font-size:18px;color:var(--green)">{st.session_state.score:,}</div>
          </div>
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-label" style="margin-top:16px">📈 Your Progress</div>', unsafe_allow_html=True)
        ac  = len(st.session_state.answered)
        cor = sum(1 for cid,a in st.session_state.answered.items()
                   for c in CHALLENGES if c["id"]==cid and a==c["correct"])
        acc_pct = int(cor/ac*100) if ac>0 else 0
        st.markdown(f"""
        <div class="m-panel">
          <div style="display:flex;justify-content:space-around;margin-bottom:10px">
            <div style="text-align:center">
              <div class="m-label">Attempted</div>
              <div class="m-val m-cyan" style="font-size:28px">{ac}/{len(CHALLENGES)}</div>
            </div>
            <div style="text-align:center">
              <div class="m-label">Correct</div>
              <div class="m-val m-green" style="font-size:28px">{cor}</div>
            </div>
            <div style="text-align:center">
              <div class="m-label">Accuracy</div>
              <div class="m-val m-violet" style="font-size:28px">{acc_pct}%</div>
            </div>
          </div>
          <div class="xp-track"><div class="xp-fill" style="width:{int(cor/len(CHALLENGES)*100)}%"></div></div>
        </div>""", unsafe_allow_html=True)

    with cc2:
        st.markdown('<div class="sec-label">🎯 Active Challenges</div>', unsafe_allow_html=True)
        for ch in CHALLENGES:
            done = ch["id"] in st.session_state.answered
            clues_html = "".join(
                f'<div class="clue"><span>▸</span>{c}</div>' for c in ch["clues"]
            )
            st.markdown(f"""
            <div class="ch-card">
              <div class="ch-header">
                <div class="ch-title">{ch['title']}</div>
                <div style="display:flex;gap:8px;align-items:center">
                  <div class="badge" style="color:{ch['color']};border-color:{ch['color']}44;background:{ch['color']}14">{ch['difficulty']}</div>
                  <div class="badge b-green">+{ch['pts']} XP</div>
                  {'<div class="badge b-green">✓ Done</div>' if done else ''}
                </div>
              </div>
              <div class="ch-body">
                <div class="ch-q">{ch['question']}</div>
                <div style="margin-bottom:12px">{clues_html}</div>
              </div>
            </div>""", unsafe_allow_html=True)

            if not done:
                sel = st.radio(f"Your answer:", ch["options"],
                                index=None, key=f"r_{ch['id']}", label_visibility="visible")
                if st.button("Submit answer →", key=f"b_{ch['id']}", disabled=(sel is None)):
                    idx = ch["options"].index(sel)
                    st.session_state.answered[ch["id"]] = idx
                    if idx == ch["correct"]:
                        st.session_state.score += ch["pts"]
                    st.rerun()
            else:
                chosen = st.session_state.answered[ch["id"]]
                if chosen == ch["correct"]:
                    st.success(f"✓ Correct! +{ch['pts']} XP — {ch['explain']}")
                else:
                    st.error(f"✗ Incorrect (you chose: '{ch['options'][chosen]}') — {ch['explain']}")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 6 — AI ANALYST
# ══════════════════════════════════════════════════════════════
with tab_ai:
    st.markdown("""
    <div class="helper">
      <b>AI Analyst</b> queries an LLM with live data injected automatically — current earthquakes,
      Kp index, all conflict escalation scores, and civil movement status.
      Configure your provider in the sidebar first.
    </div>""", unsafe_allow_html=True)

    al, ar = st.columns([1,1], gap="medium")
    with al:
        ready = (st.session_state.ai_provider in ("groq","openrouter") and st.session_state.ai_key) \
                or st.session_state.ai_provider == "ollama"
        status_color = "var(--green)" if ready else "var(--amber)"
        st.markdown(f"""
        <div class="gcard" style="margin-bottom:16px">
          <div style="display:flex;gap:14px;align-items:center">
            <div>
              <div class="m-label">Provider</div>
              <div style="font-size:16px;font-weight:600;color:var(--cyan)">{st.session_state.ai_provider.upper()}</div>
            </div>
            <div>
              <div class="m-label">Model</div>
              <div style="font-family:var(--fm);font-size:12px;color:var(--text2)">llama-3.1-8b-instant</div>
            </div>
            <div style="margin-left:auto">
              <div style="font-size:13px;font-weight:600;color:{status_color}">
                {'● Ready' if ready else '○ No API key — configure in sidebar'}
              </div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        tmpls = [
            "— or type your own below —",
            "Summarise the top 3 seismic risks right now",
            "Assess escalation probability for the New Delhi farmers protest",
            "Analyse the Israel-Iran war escalation trajectory",
            "What does the elevated Kp index mean for satellite operators?",
            "Compare risk levels across all 5 active conflict theatres",
            "Humanitarian risk assessment for all active conflict zones",
            "Assess Strait of Hormuz closure risk given current Israel-Iran situation",
        ]
        tmpl = st.selectbox("Quick-start prompts:", tmpls, label_visibility="visible")
        prompt = st.text_area("Your query:", value="" if tmpl==tmpls[0] else tmpl, height=130,
                               placeholder="Ask about current global events, seismic data, conflict status, or geopolitical risk…",
                               label_visibility="visible")
        inject = st.checkbox("Inject live data context (earthquakes, Kp, conflicts, movements)", value=True)

        if st.button("⚡  Run Analysis", use_container_width=True, disabled=not prompt.strip()):
            final = prompt
            if inject:
                top5 = eq_df.nlargest(5,"mag")[["mag","place","depth_km"]].to_dict("records")
                conf_ctx = {n:{"escalation":c["escalation"],"intensity":c["intensity"],
                                "casualties":c["casualties_total"],"ceasefire":c["ceasefire"]}
                             for n,c in CONFLICTS.items()}
                final += (f"\n\n[LIVE DATA — {utc_now}]\n"
                          f"Top earthquakes: {json.dumps(top5)}\n"
                          f"Kp: {kp_data['kp']}\n"
                          f"Conflicts: {json.dumps(conf_ctx)}\n"
                          f"Movements: {json.dumps([{k:m[k] for k in ('title','location','sentiment','size')} for m in MOVEMENTS])}")
            with st.spinner("Analysing…"):
                result = call_ai(final, st.session_state.ai_provider, st.session_state.ai_key)
            st.session_state.ai_output = result

        if st.session_state.ai_output:
            st.markdown(f'<div class="ai-terminal">{st.session_state.ai_output}</div>', unsafe_allow_html=True)
            if st.button("🗑  Clear"):
                st.session_state.ai_output = ""; st.rerun()

    with ar:
        st.markdown('<div class="sec-label">📊 Live Charts</div>', unsafe_allow_html=True)
        if not eq_df.empty:
            st.markdown("**Seismic Breakdown (24h)**")
            st.plotly_chart(mag_donut(eq_df),use_container_width=True,config={"displayModeBar":False})

        st.markdown("**Civil Sentiment**")
        snt = {"Critical":0,"High":0,"Medium":0}
        for m in MOVEMENTS:
            k = {"CRIT":"Critical","HIGH":"High","MED":"Medium"}[m["sentiment"]]
            snt[k] += 1
        fig_s = go.Figure(go.Bar(x=list(snt.keys()),y=list(snt.values()),
                                  marker_color=["#ff3d5a","#ff8c42","#ffb400"],marker_line_width=0,opacity=.85))
        fig_s.update_layout(height=150,margin=dict(l=0,r=0,t=10,b=0),**bg_chart(),xaxis=ax(),yaxis=ax())
        st.plotly_chart(fig_s,use_container_width=True,config={"displayModeBar":False})

        st.markdown("**Conflict Escalation Scores**")
        cnames = [n.split("–")[0].split(" ")[0][:10] for n in CONFLICTS]
        cescs  = [c["escalation"] for c in CONFLICTS.values()]
        ccols  = ["#ff3d5a" if e>=80 else "#ff8c42" if e>=60 else "#ffb400" if e>=40 else "#00e676" for e in cescs]
        fig_c = go.Figure(go.Bar(x=cnames,y=cescs,marker_color=ccols,marker_line_width=0,opacity=.85,
                                  text=cescs,textposition="outside",textfont=dict(size=10,color="#e2ecf8")))
        fig_c.update_layout(height=180,margin=dict(l=0,r=0,t=10,b=0),**bg_chart(),
                             xaxis=ax(),yaxis=dict(**ax(),range=[0,110]))
        st.plotly_chart(fig_c,use_container_width=True,config={"displayModeBar":False})

        st.markdown("**Recent Earthquakes**")
        st.dataframe(eq_df[["mag","place","depth_km","time"]].head(14).rename(
            columns={"mag":"Mag","place":"Location","depth_km":"Depth km","time":"UTC"}),
            use_container_width=True, height=200, hide_index=True)
