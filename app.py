"""
OSINT ARENA v6
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

def build_global_map(eq_df, eonet_df, show_seis, show_volc, show_mvmt, show_conf, show_supply, show_heat):
    layers = []
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
    if show_volc and not eonet_df.empty:
        eo = eonet_df.copy()
        eo["color"]  = [[255,110,40,200]]*len(eo)
        eo["radius"] = 70000
        eo["tip"]    = eo.apply(lambda r: f"EONET  {r['title']} | {r['cat']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=eo, get_position=["lon","lat"],
                                 get_radius="radius", get_fill_color="color",
                                 pickable=True, auto_highlight=True))
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
    if show_mvmt:
        mdf = pd.DataFrame(MOVEMENTS)
        mdf["color"]  = mdf["sentiment"].map({"CRIT":[200,60,255,200],"HIGH":[157,110,255,185],"MED":[120,80,220,165]})
        mdf["radius"] = mdf["scale"] * 1800
        mdf["tip"]    = mdf.apply(lambda r:
            f"CIVIL  {r['title']} | {r['location']} | {r['size']} | {r['sentiment']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=mdf, get_position=["lon","lat"],
                                 get_radius="radius", get_fill_color="color",
                                 pickable=True, auto_highlight=True))
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
    if show_heat and not eq_df.empty:
        layers.append(pdk.Layer("HeatmapLayer",
                                 data=eq_df[["lat","lon","mag"]].rename(columns={"mag":"weight"}),
                                 get_position=["lon","lat"], get_weight="weight",
                                 radiusPixels=50, opacity=0.45))
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
    st.markdown('<p style="font-size:10px;color:var(--muted);letter-spacing:.14em;font-weight:700;margin-bottom:16px">GLOBAL INTELLIGENCE PLATFORM v6</p>', unsafe_allow_html=True)

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

c1,c2,c3,c4,c5 = st.columns(5)
with c1: st.metric("Active Conflicts",  active_conf,       delta="LIVE")
with c2: st.metric("Total Casualties",  f"{total_cas:,}",  delta="All theatres")
with c3: st.metric("Seismic (24h)",     len(eq_df),        delta=f"M5+: {len(m5p)}")
with c4: st.metric("Civil Movements",   len(MOVEMENTS),    delta=f"Critical: {len(crit_mv)}")
with c5: st.metric("Kp Index",          f"{kp:.1f}",       delta="Storm ≥5.0")
st.markdown("---")

# ─────────────────────────────────────────────
# GLOBAL MAP
# ─────────────────────────────────────────────
total_inc     = sum(len(c["incidents"]) for c in CONFLICTS.values())
crit_inc_cnt  = sum(1 for c in CONFLICTS.values() for i in c["incidents"] if i["severity"]=="CRITICAL")

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

    # Live theatre news
    with st.expander(f"📰 Live News — {theatre}", expanded=True):
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
#status{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#4a6b85;margin-bottom:10px;display:flex;align-items:center;gap:6px;}}
.dot{{width:5px;height:5px;border-radius:50%;background:#00c8ff;animation:blink 1.2s ease-in-out infinite;flex-shrink:0;}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;}}
@media(max-width:700px){{.grid{{grid-template-columns:1fr 1fr;}}}}
@media(max-width:450px){{.grid{{grid-template-columns:1fr;}}}}
.card{{background:#0b1524;border:1px solid rgba(0,200,255,.1);border-radius:9px;padding:12px 14px;border-left:3px solid {conflict_accent};transition:border-color .2s;}}
.card:hover{{border-color:rgba(0,200,255,.28);}}
.src{{font-family:'IBM Plex Mono',monospace;font-size:9px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:#4a6b85;margin-bottom:5px;}}
.hl{{font-size:12px;font-weight:600;color:#e2ecf8;line-height:1.4;margin-bottom:8px;}}
.foot{{display:flex;align-items:center;justify-content:space-between;}}
.ts{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#4a6b85;}}
a.r{{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#00c8ff;text-decoration:none;padding:2px 8px;border:1px solid rgba(0,200,255,.25);border-radius:4px;}}
a.r:hover{{background:rgba(0,200,255,.1);}}
.err{{color:#ff8c42;font-size:11px;font-family:'IBM Plex Mono',monospace;line-height:1.6;}}
.srclinks{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}}
.srclinks a{{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#00c8ff;text-decoration:none;padding:3px 10px;border:1px solid rgba(0,200,255,.25);border-radius:12px;}}
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
    items.forEach(it=>arts.push({{title:it.title,link:it.link,time:ta(it.pub),src:f.name,col:f.color}}));}}
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
COUNTRY_INSTABILITY = [
    {"country":"Sudan","score":89,"trend":"↑","U":28,"C":22,"S":20,"I":19,"region":"Africa"},
    {"country":"Myanmar","score":84,"trend":"→","U":26,"C":21,"S":19,"I":18,"region":"Asia"},
    {"country":"Haiti","score":83,"trend":"↑","U":27,"C":20,"S":18,"I":18,"region":"Americas"},
    {"country":"Yemen","score":82,"trend":"→","U":25,"C":22,"S":17,"I":18,"region":"Middle East"},
    {"country":"Syria","score":80,"trend":"↓","U":24,"C":20,"S":19,"I":17,"region":"Middle East"},
    {"country":"Somalia","score":78,"trend":"→","U":24,"C":19,"S":18,"I":17,"region":"Africa"},
    {"country":"DR Congo","score":77,"trend":"↑","U":23,"C":20,"S":17,"I":17,"region":"Africa"},
    {"country":"Libya","score":74,"trend":"→","U":22,"C":19,"S":17,"I":16,"region":"Africa"},
    {"country":"Ethiopia","score":71,"trend":"↑","U":21,"C":18,"S":17,"I":15,"region":"Africa"},
    {"country":"Mali","score":70,"trend":"↑","U":22,"C":18,"S":15,"I":15,"region":"Africa"},
    {"country":"Afghanistan","score":69,"trend":"→","U":21,"C":18,"S":15,"I":15,"region":"Asia"},
    {"country":"Iraq","score":62,"trend":"↓","U":19,"C":16,"S":14,"I":13,"region":"Middle East"},
    {"country":"Venezuela","score":61,"trend":"→","U":18,"C":16,"S":14,"I":13,"region":"Americas"},
    {"country":"Pakistan","score":58,"trend":"↑","U":17,"C":15,"S":13,"I":13,"region":"Asia"},
    {"country":"New Caledonia","score":44,"trend":"→","U":13,"C":11,"S":10,"I":10,"region":"Pacific"},
    {"country":"Palau","score":38,"trend":"→","U":10,"C":10,"S":9,"I":9,"region":"Pacific"},
]

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
    st.markdown("""
    <div class="helper">
      <b>Intel Dashboard</b> — Country instability indices, strategic risk overview,
      infrastructure cascade, force posture, supply chain chokepoints, and live intelligence feeds.
    </div>""", unsafe_allow_html=True)

    # ── Row 1: Country Instability | Strategic Risk | Intel Feed | Live Intel ──
    r1c1, r1c2, r1c3, r1c4 = st.columns([1.2, 1.2, 1.4, 1.2], gap="small")

    # Country Instability
    with r1c1:
        st.markdown("""
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
          <div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)">COUNTRY INSTABILITY</div>
        </div>""", unsafe_allow_html=True)
        region_filter = st.selectbox("Region", ["All","Africa","Middle East","Asia","Americas","Pacific"], label_visibility="collapsed", key="ci_reg")
        filtered = [c for c in COUNTRY_INSTABILITY if region_filter=="All" or c["region"]==region_filter]
        for c in filtered[:12]:
            sc = c["score"]
            col = "#ff3d5a" if sc>=75 else "#ff8c42" if sc>=60 else "#ffb400" if sc>=45 else "#00c8ff"
            trend_col = "#ff3d5a" if c["trend"]=="↑" else "#00e676" if c["trend"]=="↓" else "#4a6b85"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;padding:7px 10px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:5px;border-left:3px solid {col}">
              <div style="flex:1">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
                  <span style="font-size:12px;font-weight:600;color:var(--text)">{c['country']}</span>
                  <span style="font-family:var(--fm);font-size:13px;font-weight:700;color:{col}">{sc}
                    <span style="font-size:11px;color:{trend_col}">{c['trend']}</span>
                  </span>
                </div>
                <div style="height:3px;background:var(--dim);border-radius:2px;overflow:hidden;margin-bottom:4px">
                  <div style="height:100%;width:{sc}%;background:{col}88;border-radius:2px"></div>
                </div>
                <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">
                  U:{c['U']} C:{c['C']} S:{c['S']} I:{c['I']}
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    # Strategic Risk Overview
    with r1c2:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">STRATEGIC RISK OVERVIEW</div>', unsafe_allow_html=True)
        sr = STRATEGIC_RISK
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number", value=sr["score"],
            gauge=dict(
                axis=dict(range=[0,100], tickcolor="#4a6b85", tickfont=dict(size=8, color="#4a6b85")),
                bar=dict(color=sr["color"], thickness=.3),
                bgcolor="rgba(0,0,0,0)", borderwidth=0,
                steps=[
                    dict(range=[0,30], color="rgba(0,230,118,.06)"),
                    dict(range=[30,55], color="rgba(255,180,0,.06)"),
                    dict(range=[55,75], color="rgba(255,140,66,.06)"),
                    dict(range=[75,100], color="rgba(255,61,90,.07)"),
                ],
            ),
            number=dict(font=dict(family="Bebas Neue", size=52, color=sr["color"])),
            title=dict(text=sr["label"], font=dict(family="IBM Plex Mono", size=11, color=sr["color"])),
        ))
        gauge_fig.update_layout(height=200, margin=dict(l=10,r=10,t=20,b=0), **bg_chart())
        st.plotly_chart(gauge_fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(f'<div style="text-align:center;font-family:var(--fm);font-size:11px;color:var(--muted);margin-bottom:10px">TREND &nbsp;<span style="color:var(--text2);font-size:13px">⟶ {sr["trend"]}</span></div>', unsafe_allow_html=True)
        for comp in sr["components"]:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
              <div style="font-size:11px;color:var(--text2);width:148px;flex-shrink:0">{comp['name']}</div>
              <div style="flex:1;height:4px;background:var(--dim);border-radius:2px;overflow:hidden">
                <div style="height:100%;width:{comp['val']}%;background:{comp['col']};border-radius:2px"></div>
              </div>
              <div style="font-family:var(--fm);font-size:10px;color:{comp['col']};width:28px;text-align:right">{comp['val']}</div>
            </div>""", unsafe_allow_html=True)

    # Intel Feed
    with r1c3:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">INTEL FEED <span class="live-badge" style="margin-left:8px">● LIVE</span></div>', unsafe_allow_html=True)
        cat_colors = {"ALERT":"b-red","REPORT":"b-amber","BRIEF":"b-cyan"}
        tag_colors = {"MILITARY":"b-orange","CONFLICT":"b-red","UKRAINE":"b-cyan","IRAN":"b-amber","NUCLEAR":"b-violet","OSINT":"b-green","CYBER":"b-violet"}
        for item in INTEL_FEED_SOURCES:
            cc = cat_colors.get(item["cat"],"b-muted")
            tc = tag_colors.get(item["tag"],"b-muted")
            st.markdown(f"""
            <div style="background:var(--card);border:1px solid var(--bord2);border-radius:8px;padding:10px 12px;margin-bottom:7px;transition:border-color .2s"
                 onmouseover="this.style.borderColor='rgba(0,200,255,.22)'" onmouseout="this.style.borderColor='rgba(0,200,255,.06)'">
              <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px">
                <span style="font-family:var(--fm);font-size:9px;font-weight:700;letter-spacing:.08em;color:var(--muted)">{item['source'].upper()}</span>
                <div class="badge {cc}" style="font-size:8px">{item['cat']}</div>
                <div class="badge {tc}" style="font-size:8px">{item['tag']}</div>
              </div>
              <div style="font-size:12px;font-weight:600;color:var(--text);line-height:1.45;margin-bottom:5px">{item['title']}</div>
              <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">{item['time']}</div>
            </div>""", unsafe_allow_html=True)

    # Live Intelligence (tabbed: Military | Cyber)
    with r1c4:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">LIVE INTELLIGENCE</div>', unsafe_allow_html=True)
        intel_tab = st.radio("Intel type:", ["Military Activity","Cyber Threats"], horizontal=True, label_visibility="collapsed", key="intel_type")
        feed = INTEL_FEED_SOURCES if intel_tab == "Military Activity" else CYBER_FEED
        for item in (CYBER_FEED if intel_tab=="Cyber Threats" else INTEL_FEED_SOURCES[:6]):
            sector = item.get("sector","INTEL")
            sc_col = "#9d6eff" if sector=="Cyber" else "#ff8c42" if sector=="Military" else "#00c8ff"
            st.markdown(f"""
            <div style="border-bottom:1px solid var(--bord2);padding:9px 0">
              <div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-bottom:3px;display:flex;justify-content:space-between">
                <span style="color:{sc_col}">{item['source'].upper()}</span>
                <span>{item['time']}</span>
              </div>
              <div style="font-size:12px;color:var(--text);line-height:1.4">{item['title'][:90]}{'…' if len(item['title'])>90 else ''}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Row 2: Infrastructure Cascade | Force Posture ──────────
    r2c1, r2c2 = st.columns([1.6, 1.4], gap="medium")

    with r2c1:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:12px">INFRASTRUCTURE CASCADE</div>', unsafe_allow_html=True)
        ic_tabs = st.tabs(["🔌 Cables","🔴 Pipelines","⚓ Ports","🏭 Chokepoints","⚡ Power Grids"])
        ic_map = {"🔌 Cables":"cables","🔴 Pipelines":"pipelines","⚓ Ports":"ports","🏭 Chokepoints":"chokepoints","⚡ Power Grids":"power_grids"}
        for ic_tab, ic_key in zip(ic_tabs, ic_map.values()):
            with ic_tab:
                d = INFRA_CASCADE[ic_key]
                st.markdown(f"""
                <div style="display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap">
                  <div class="m-panel" style="padding:10px 14px;flex:1;min-width:80px;text-align:center">
                    <div class="m-label">Total</div>
                    <div class="m-val m-cyan" style="font-size:24px">{d['count']}</div>
                  </div>
                  <div class="m-panel" style="padding:10px 14px;flex:1;min-width:80px;text-align:center">
                    <div class="m-label">At Risk</div>
                    <div class="m-val m-red" style="font-size:24px">{d['at_risk']}</div>
                  </div>
                  <div class="m-panel" style="padding:10px 14px;flex:1;min-width:80px;text-align:center">
                    <div class="m-label">Risk %</div>
                    <div class="m-val m-amber" style="font-size:24px">{round(d['at_risk']/d['count']*100)}%</div>
                  </div>
                </div>""", unsafe_allow_html=True)
                for item in d["items"]:
                    r = item["risk"]
                    rc = "#ff3d5a" if r>=75 else "#ff8c42" if r>=55 else "#ffb400" if r>=35 else "#00e676"
                    sc_map = {"Cut":"b-red","Sabotaged":"b-red","Threatened":"b-red","Blockaded":"b-red","Contested":"b-amber","Degraded":"b-amber","Suspended":"b-amber","Reduced":"b-amber","At Risk":"b-amber","Active":"b-green"}
                    sb = sc_map.get(item.get("status",""),"b-muted")
                    extra = f'· {item.get("traffic_pct","")}% global trade' if item.get("traffic_pct") else f'· {item.get("region","")}' if item.get("region") else ""
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:5px;border-left:3px solid {rc}">
                      <div style="flex:1">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
                          <span style="font-size:12px;font-weight:600;color:var(--text)">{item['name']}</span>
                          <div style="display:flex;gap:5px;align-items:center">
                            <div class="badge {sb}" style="font-size:8px">{item.get('status','')}</div>
                            <span style="font-family:var(--fm);font-size:11px;font-weight:700;color:{rc}">{r}</span>
                          </div>
                        </div>
                        <div style="height:3px;background:var(--dim);border-radius:2px;overflow:hidden;margin-bottom:3px">
                          <div style="height:100%;width:{r}%;background:{rc}77"></div>
                        </div>
                        <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">{extra}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

    with r2c2:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:12px">FORCE POSTURE</div>', unsafe_allow_html=True)
        for fp in FORCE_POSTURE:
            r = fp["risk"]
            rc = "#ff3d5a" if r>=70 else "#ff8c42" if r>=50 else "#ffb400" if r>=35 else "#00c8ff"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:5px">
              <div style="width:34px;height:34px;border-radius:50%;background:{rc}22;border:2px solid {rc}55;display:flex;align-items:center;justify-content:center;flex-shrink:0">
                <span style="font-family:var(--fd);font-size:14px;color:{rc}">{r}</span>
              </div>
              <div style="flex:1;min-width:0">
                <div style="font-size:12px;font-weight:600;color:var(--text);margin-bottom:2px">{fp['activity']} – {fp['actors']}</div>
                <div style="font-family:var(--fm);font-size:10px;color:var(--muted)">{fp['signals']:,} signals →</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Row 3: Supply Chain Chokepoints ──────────────────────────
    st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:12px">SUPPLY CHAIN CHOKEPOINTS</div>', unsafe_allow_html=True)
    cp_cols = st.columns(3, gap="medium")
    for idx, cp in enumerate(CHOKEPOINTS):
        status_cls = "b-red" if cp["status"]=="red" else "b-amber" if cp["status"]=="amber" else "b-green"
        status_col = "#ff3d5a" if cp["status"]=="red" else "#ffb400" if cp["status"]=="amber" else "#00e676"
        wow_col    = "#ff3d5a" if cp["wow_change"]<0 else "#00e676"
        with cp_cols[idx % 3]:
            st.markdown(f"""
            <div style="background:var(--card);border:1px solid var(--bord2);border-left:3px solid {status_col};border-radius:10px;padding:14px 16px;margin-bottom:12px">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                <div style="font-family:var(--fd);font-size:15px;letter-spacing:.06em;color:var(--text)">{cp['name']}</div>
                <div class="badge {status_cls}">{cp['risk']}/100</div>
              </div>
              <div style="display:flex;gap:10px;margin-bottom:8px;font-family:var(--fm);font-size:10px;flex-wrap:wrap">
                <span style="color:var(--muted)">{cp['warnings']} warning(s)</span>
                <span style="color:var(--muted)">·</span>
                <span style="color:var(--muted)">{cp['ais_disruptions']} AIS disruption(s)</span>
                <span style="color:var(--muted)">·</span>
                <span style="color:var(--muted)">{cp['flow']}</span>
              </div>
              <div style="height:4px;background:var(--dim);border-radius:2px;overflow:hidden;margin-bottom:8px">
                <div style="height:100%;width:{cp['risk']}%;background:{status_col}88"></div>
              </div>
              <div style="font-family:var(--fm);font-size:10px;margin-bottom:6px">
                WoW change: <span style="color:{wow_col};font-weight:700">{'+' if cp['wow_change']>0 else ''}{cp['wow_change']}%</span>
              </div>
              <div style="font-size:11px;color:var(--text2);line-height:1.55;margin-bottom:8px">{cp['context'][:180]}</div>
              <div style="display:flex;gap:4px;flex-wrap:wrap">
                {''.join(f'<div class="badge b-muted" style="font-size:8px">{e}</div>' for e in cp['exports'])}
              </div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 6 — ECONOMIC & MARKETS
# ══════════════════════════════════════════════════════════════
with tab_econ:
    st.markdown("""
    <div class="helper">
      <b>Economic & Markets</b> — Economic indicators, trade policy, supply chain, financial data,
      fires tracker, layoffs, BTC ETF flows, market radar, and the <b>Pizza Index</b>.
    </div>""", unsafe_allow_html=True)

    # ── Row 1: Econ Indicators | Trade Policy | Supply Chain | Financial ──
    e1c1, e1c2, e1c3, e1c4 = st.columns([1,1.2,1.4,1], gap="small")

    # Economic Indicators
    with e1c1:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">ECONOMIC INDICATORS</div>', unsafe_allow_html=True)
        ind_tab_sel = st.radio("", ["Indicators","Oil","Gov"], horizontal=True, label_visibility="collapsed", key="econ_tab")
        if ind_tab_sel == "Indicators":
            for e in ECON_INDICATORS:
                chg_col = "#00e676" if e["up"] else "#ff3d5a"
                st.markdown(f"""
                <div style="padding:8px 10px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:5px">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:2px">{e['name']}</div>
                  <div style="display:flex;align-items:baseline;justify-content:space-between;gap:6px">
                    <div style="font-family:var(--fd);font-size:20px;color:var(--cyan)">{e['val']}</div>
                    <div style="font-family:var(--fm);font-size:10px;color:{chg_col}">{e['change']}</div>
                  </div>
                  <div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-top:2px">{e['ticker']} · {e['date']}</div>
                </div>""", unsafe_allow_html=True)
        elif ind_tab_sel == "Oil":
            for o in OIL_DATA:
                chg_col = "#00e676" if o["change"]>=0 else "#ff3d5a"
                st.markdown(f"""
                <div style="padding:8px 10px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:5px">
                  <div style="font-size:10px;color:var(--muted);margin-bottom:2px">{o['name']}</div>
                  <div style="display:flex;align-items:baseline;justify-content:space-between;gap:6px">
                    <div style="font-family:var(--fd);font-size:20px;color:var(--amber)">{o['val']:.2f} <span style="font-size:11px">{o['unit']}</span></div>
                    <div style="font-family:var(--fm);font-size:10px;color:{chg_col}">{'+' if o['change']>=0 else ''}{o['change']:.2f}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Government bond yields — connect FRED API for live data.")

    # Trade Policy
    with e1c2:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">TRADE POLICY</div>', unsafe_allow_html=True)
        tp_tab = st.radio("", ["Restrictions","Tariffs"], horizontal=True, label_visibility="collapsed", key="tp_tab")
        if tp_tab == "Restrictions":
            for t in TRADE_RESTRICTIONS:
                ic = "b-red" if t["impact"]=="Critical" else "b-orange" if t["impact"]=="High" else "b-amber"
                st.markdown(f"""
                <div style="padding:9px 12px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:6px">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
                    <span style="font-size:13px;font-weight:600;color:var(--text)">{t['country']}</span>
                    <span class="badge b-muted" style="font-size:8px">{t['type']}</span>
                  </div>
                  <div style="font-size:11px;color:var(--text2);margin-bottom:3px">{t['coverage']}</div>
                  <div style="display:flex;align-items:center;justify-content:space-between">
                    <div style="font-family:var(--fm);font-size:10px;color:var(--muted)">Avg tariff: {t['avg_rate']}%&nbsp;&nbsp;{t['year']}</div>
                    <div class="badge {ic}" style="font-size:8px">{t['impact']}</div>
                  </div>
                  <div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-top:3px">Source: WTO</div>
                </div>""", unsafe_allow_html=True)
        else:
            for t in TARIFFS:
                ic = "b-red" if t["impact"]=="Critical" else "b-orange" if t["impact"]=="High" else "b-amber" if t["impact"]=="Med" else "b-green"
                st.markdown(f"""
                <div style="padding:9px 12px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:6px">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:13px;font-weight:600;color:var(--text)">{t['route']}</span>
                    <span class="badge {ic}" style="font-size:8px">{t['impact']}</span>
                  </div>
                  <div style="display:flex;align-items:center;gap:10px">
                    <span style="font-family:var(--fd);font-size:22px;color:var(--red)">{t['rate']}%</span>
                    <span style="font-family:var(--fm);font-size:10px;color:var(--orange)">{t['change']}</span>
                  </div>
                  <div style="font-size:10px;color:var(--muted)">{t['sector']}</div>
                </div>""", unsafe_allow_html=True)

    # Supply Chain
    with e1c3:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px">SUPPLY CHAIN</div>', unsafe_allow_html=True)
        sc_tab = st.radio("", ["Chokepoints","Shipping","Critical Min"], horizontal=True, label_visibility="collapsed", key="sc_tab")
        if sc_tab == "Chokepoints":
            for cp in CHOKEPOINTS:
                sc = cp["status"]
                sc_col = "#ff3d5a" if sc=="red" else "#ffb400" if sc=="amber" else "#00e676"
                sb = "b-red" if sc=="red" else "b-amber" if sc=="amber" else "b-green"
                wow_col = "#ff3d5a" if cp["wow_change"]<0 else "#00e676"
                st.markdown(f"""
                <div style="padding:10px 12px;background:var(--card);border:1px solid var(--bord2);border-left:3px solid {sc_col};border-radius:8px;margin-bottom:7px">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
                    <span style="font-size:13px;font-weight:700;color:var(--text)">{cp['name']}</span>
                    <div style="display:flex;gap:5px;align-items:center">
                      <div class="badge {sb}" style="width:10px;height:10px;border-radius:50%;padding:0;border:none;background:{sc_col}"></div>
                      <span class="badge {sb}" style="font-size:9px">{cp['risk']}/100</span>
                    </div>
                  </div>
                  <div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-bottom:4px">
                    {cp['warnings']} warning(s) · {cp['ais_disruptions']} AIS disruption(s) · {cp['flow']}
                  </div>
                  <div style="height:3px;background:var(--dim);border-radius:2px;overflow:hidden;margin-bottom:5px">
                    <div style="height:100%;width:{cp['risk']}%;background:{sc_col}88"></div>
                  </div>
                  <div style="font-family:var(--fm);font-size:10px;margin-bottom:4px">
                    WoW: <span style="color:{wow_col};font-weight:700">{'+' if cp['wow_change']>0 else ''}{cp['wow_change']}%</span>
                  </div>
                  <div style="font-size:11px;color:var(--text2);line-height:1.5">{cp['context'][:130]}{'…' if len(cp['context'])>130 else ''}</div>
                  <div style="display:flex;gap:4px;flex-wrap:wrap;margin-top:5px">
                    {''.join(f'<span style="font-family:var(--fm);font-size:9px;color:var(--muted)">{e}{";" if i<len(cp["exports"])-1 else ""}</span>' for i,e in enumerate(cp["exports"]))}
                  </div>
                </div>""", unsafe_allow_html=True)
        elif sc_tab == "Shipping":
            st.info("Live shipping rate data — AIS stream integration coming soon.")
        else:
            st.info("Critical minerals tracker — coming soon.")

    # Financial
    with e1c4:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:6px">FINANCIAL <span class="live-badge" style="margin-left:6px">● LIVE</span></div>', unsafe_allow_html=True)
        st.markdown("**Crypto**")
        for c in CRYPTO_DATA:
            chg_col = "#00e676" if c["change"]>=0 else "#ff3d5a"
            st.markdown(f"""
            <div style="padding:7px 10px;background:var(--card);border:1px solid var(--bord2);border-radius:7px;margin-bottom:5px">
              <div style="display:flex;align-items:center;justify-content:space-between">
                <div>
                  <div style="font-size:11px;font-weight:600;color:var(--text)">{c['name']}</div>
                  <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">{c['ticker']}</div>
                </div>
                <div style="text-align:right">
                  <div style="font-family:var(--fm);font-size:12px;color:var(--text)">${c['val']:,.3f}</div>
                  <div style="font-family:var(--fm);font-size:10px;color:{chg_col}">{'+' if c['change']>=0 else ''}{c['change']:.2f}%</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("**Sector Heatmap**", unsafe_allow_html=False)
        sector_cols = st.columns(4)
        for i, s in enumerate(SECTOR_HEATMAP):
            col_ = "#00e676" if s["v"]>=0 else "#ff3d5a"
            bg_  = f"rgba({'0,230,118' if s['v']>=0 else '255,61,90'},.14)"
            with sector_cols[i % 4]:
                st.markdown(f"""
                <div style="padding:5px 6px;background:{bg_};border-radius:5px;margin-bottom:4px;text-align:center">
                  <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">{s['s']}</div>
                  <div style="font-family:var(--fm);font-size:10px;font-weight:700;color:{col_}">{'+' if s['v']>=0 else ''}{s['v']}%</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Row 2: Technology | Layoffs | Fires | Market Radar | BTC ETF ──
    e2c1, e2c2, e2c3, e2c4, e2c5 = st.columns([1.1, 1.1, 1.1, 0.9, 0.9], gap="small")

    with e2c1:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">TECHNOLOGY <span class="live-badge" style="margin-left:6px">● LIVE</span></div>', unsafe_allow_html=True)
        tech_items = [i for i in INTEL_FEED_SOURCES if i.get("tag") in ("CYBER","OSINT")] + CYBER_FEED[:4]
        for item in tech_items[:6]:
            st.markdown(f"""
            <div style="border-bottom:1px solid var(--bord2);padding:8px 0">
              <div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-bottom:3px;display:flex;justify-content:space-between">
                <span style="color:var(--violet)">{item.get('source','').upper()}</span>
                <span>{item.get('time','recent')}</span>
              </div>
              <div style="font-size:12px;color:var(--text);line-height:1.4">{item['title'][:88]}{'…' if len(item['title'])>88 else ''}</div>
            </div>""", unsafe_allow_html=True)

    with e2c2:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">LAYOFFS TRACKER <span class="live-badge" style="margin-left:6px">● LIVE</span></div>', unsafe_allow_html=True)
        for l in LAYOFFS:
            sc = "b-red" if l["severity"]=="Critical" else "b-orange" if l["severity"]=="High" else "b-amber"
            st.markdown(f"""
            <div style="padding:8px 10px;background:var(--card);border:1px solid var(--bord2);border-radius:7px;margin-bottom:5px">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px">
                <span style="font-size:12px;font-weight:600;color:var(--text)">{l['company']}</span>
                <div class="badge {sc}" style="font-size:8px">{l['severity'].upper()}</div>
              </div>
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div>
                  <span style="font-family:var(--fm);font-size:10px;color:var(--amber)">{l['count']} jobs</span>
                  <span style="font-family:var(--fm);font-size:9px;color:var(--muted)"> · {l['sector']} · {l['date']}</span>
                </div>
                <span style="font-family:var(--fm);font-size:9px;color:var(--muted)">{l['source']}</span>
              </div>
            </div>""", unsafe_allow_html=True)

    with e2c3:
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">FIRES / HOTSPOTS</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="display:grid;grid-template-columns:1fr 60px 44px 60px;gap:0;margin-bottom:6px">
          <div style="font-family:var(--fm);font-size:9px;font-weight:700;color:var(--muted);padding:4px 8px">REGION</div>
          <div style="font-family:var(--fm);font-size:9px;font-weight:700;color:var(--muted);text-align:right;padding:4px 4px">FIRES</div>
          <div style="font-family:var(--fm);font-size:9px;font-weight:700;color:var(--muted);text-align:right;padding:4px 4px">HIGH</div>
          <div style="font-family:var(--fm);font-size:9px;font-weight:700;color:var(--muted);text-align:right;padding:4px 8px">FRP</div>
        </div>""", unsafe_allow_html=True)
        for f in FIRES_DATA:
            intensity_col = "#ff3d5a" if f["high"]>50 else "#ff8c42" if f["high"]>20 else "#ffb400"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:1fr 60px 44px 60px;gap:0;background:var(--card);border:1px solid var(--bord2);border-radius:6px;margin-bottom:4px;border-left:3px solid {intensity_col}">
              <div style="font-size:11px;font-weight:600;color:var(--text);padding:6px 8px">{f['region']}</div>
              <div style="font-family:var(--fm);font-size:10px;color:var(--cyan);text-align:right;padding:6px 4px">{f['fires']:,}</div>
              <div style="font-family:var(--fm);font-size:10px;color:{intensity_col};text-align:right;padding:6px 4px">{f['high']}</div>
              <div style="font-family:var(--fm);font-size:10px;color:var(--muted);text-align:right;padding:6px 8px">{f['frp']//1000:.1f}k</div>
            </div>""", unsafe_allow_html=True)

    with e2c4:
        mr = MARKET_RADAR
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">MARKET RADAR</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px;text-align:center;margin-bottom:10px">
          <div style="font-size:11px;color:var(--muted);margin-bottom:4px">OVERALL</div>
          <div style="font-family:var(--fd);font-size:32px;letter-spacing:.08em;color:{mr['color']}">{mr['label']}</div>
          <div style="font-family:var(--fm);font-size:10px;color:var(--muted);margin-top:4px">{mr['posture']}</div>
        </div>
        <div style="padding:8px 10px;background:var(--card);border:1px solid var(--bord2);border-radius:7px;margin-bottom:5px">
          <div style="font-size:10px;color:var(--muted);margin-bottom:2px">Liquidity</div>
          <div style="font-family:var(--fm);font-size:12px;color:var(--text)">{mr['liquidity']}</div>
        </div>
        <div style="padding:8px 10px;background:var(--card);border:1px solid var(--bord2);border-radius:7px">
          <div style="font-size:10px;color:var(--muted);margin-bottom:2px">Flow</div>
          <div style="font-family:var(--fm);font-size:12px;color:var(--amber)">{mr['flow']}</div>
        </div>""", unsafe_allow_html=True)

    with e2c5:
        etf = BTC_ETF
        nf_col = "#00e676" if etf["net_flow"]>=0 else "#ff3d5a"
        st.markdown('<div style="font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:8px">BTC ETF TRACKER</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px">
            <div style="text-align:center">
              <div style="font-size:9px;color:var(--muted);margin-bottom:2px">Net Flow</div>
              <div style="font-family:var(--fd);font-size:22px;color:{nf_col}">${abs(etf['net_flow'])}M</div>
              <div class="badge {'b-red' if etf['net_flow']<0 else 'b-green'}" style="font-size:8px;margin-top:3px">{'NET OUTFLOW' if etf['net_flow']<0 else 'NET INFLOW'}</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:9px;color:var(--muted);margin-bottom:2px">Est. Flow</div>
              <div style="font-family:var(--fd);font-size:22px;color:var(--cyan)">${etf['est_flow']}M</div>
            </div>
          </div>
          <div style="font-size:9px;color:var(--muted);margin-bottom:6px;font-family:var(--fm)">TRACKED ETFs</div>
          <div style="display:flex;flex-wrap:wrap;gap:4px">
            {''.join(f'<div class="badge b-violet" style="font-size:8px">{e}</div>' for e in etf['etfs'])}
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── PIZZA INDEX ──────────────────────────────────────────────
    pz = PIZZA_INDEX
    pz_col = "#ff3d5a" if pz["score"]>=75 else "#ff8c42" if pz["score"]>=55 else "#ffb400" if pz["score"]>=35 else "#00e676"
    st.markdown(f"""
    <div style="background:var(--panel);border:1px solid var(--border);border-radius:14px;padding:20px 24px;margin-bottom:20px">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-bottom:16px">
        <div>
          <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
            <div style="font-size:10px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--muted)">🍕 PIZZA INDEX</div>
            <div class="badge b-muted" style="font-size:8px">PIZZAINT METHODOLOGY</div>
          </div>
          <div style="font-family:var(--fd);font-size:42px;letter-spacing:.06em;color:{pz_col};line-height:1">{pz['score']}</div>
          <div style="font-family:var(--fm);font-size:12px;color:{pz_col};margin-top:4px">{pz['label']}</div>
        </div>
        <div style="flex:1;max-width:520px;font-size:12px;color:var(--text2);line-height:1.7">{pz['description']}</div>
      </div>
      <div style="height:6px;background:var(--dim);border-radius:3px;overflow:hidden;margin-bottom:20px">
        <div style="height:100%;width:{pz['score']}%;background:linear-gradient(90deg,#00e676,#ffb400 45%,#ff8c42 70%,#ff3d5a);border-radius:3px"></div>
      </div>
    </div>""", unsafe_allow_html=True)

    pz_left, pz_right = st.columns([1.3, 1], gap="medium")
    with pz_left:
        st.markdown('<div class="sec-label">📦 Input Components</div>', unsafe_allow_html=True)
        for comp in pz["components"]:
            sc = comp["stress"]
            sc_col = "#ff3d5a" if sc>=80 else "#ff8c42" if sc>=60 else "#ffb400" if sc>=40 else "#00e676"
            chg_col = "#ff3d5a" if comp["change"]>0 else "#00e676"
            chg_sym = "▲" if comp["change"]>0 else "▼"
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:5px;border-left:3px solid {sc_col}">
              <div style="flex:1;min-width:0">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px">
                  <span style="font-size:12px;font-weight:600;color:var(--text)">{comp['name']}</span>
                  <div style="display:flex;align-items:center;gap:8px">
                    <span style="font-family:var(--fm);font-size:11px;color:var(--text2)">{comp['val']} <span style="color:var(--muted);font-size:9px">{comp['unit']}</span></span>
                    <span style="font-family:var(--fm);font-size:10px;color:{chg_col}">{chg_sym}{abs(comp['change']):.1f}%</span>
                    <span style="font-family:var(--fd);font-size:16px;color:{sc_col};min-width:28px;text-align:right">{sc}</span>
                  </div>
                </div>
                <div style="height:3px;background:var(--dim);border-radius:2px;overflow:hidden;margin-bottom:3px">
                  <div style="height:100%;width:{sc}%;background:{sc_col}88"></div>
                </div>
                <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">{comp['note']}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    with pz_right:
        st.markdown('<div class="sec-label">🌍 City Price Index</div>', unsafe_allow_html=True)
        max_stress = max(c["stress"] for c in pz["city_prices"])
        for city in sorted(pz["city_prices"], key=lambda x: -x["stress"]):
            sc = city["stress"]
            sc_col = "#ff3d5a" if sc>=80 else "#ff8c42" if sc>=60 else "#ffb400" if sc>=40 else "#00e676"
            pct_increase = round((city["price"]-city["baseline"])/city["baseline"]*100)
            st.markdown(f"""
            <div style="padding:9px 12px;background:var(--card);border:1px solid var(--bord2);border-radius:8px;margin-bottom:5px;border-left:3px solid {sc_col}">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
                <span style="font-size:12px;font-weight:600;color:var(--text)">{city['city']}</span>
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-family:var(--fm);font-size:12px;color:var(--text)">{city['price']} {city['currency']}</span>
                  <span style="font-family:var(--fm);font-size:10px;color:#ff8c42">+{pct_increase}%</span>
                  <span style="font-family:var(--fd);font-size:16px;color:{sc_col};min-width:28px;text-align:right">{sc}</span>
                </div>
              </div>
              <div style="height:4px;background:var(--dim);border-radius:2px;overflow:hidden">
                <div style="height:100%;width:{sc}%;background:{sc_col}88"></div>
              </div>
              <div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-top:3px">baseline {city['baseline']} {city['currency']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:12px 14px;background:rgba(255,140,66,.07);border:1px solid rgba(255,140,66,.25);border-radius:9px;margin-top:8px">
          <div style="font-size:10px;font-weight:700;letter-spacing:.12em;color:var(--orange);margin-bottom:5px">METHODOLOGY</div>
          <div style="font-size:11px;color:var(--text2);line-height:1.65">
            Inspired by <em>The Economist</em>'s Big Mac Index. Tracks real margherita pizza slice prices
            as a proxy for wheat supply disruption, energy costs, labour pressure, and consumer
            purchasing power stress. Scores above <b>60</b> indicate material supply-chain or
            geopolitical pressure on food affordability.
          </div>
        </div>""", unsafe_allow_html=True)
