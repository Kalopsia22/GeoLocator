"""
OSINT ARENA v3 — Streamlit Application
========================================
Earth Signals · Civil Movements · Conflict Dashboard
Live News Feeds · AI Analyst · OSINT Challenges

NEW in v3:
  — Conflict Dashboard: live theatre map, incident feed, escalation radar,
    faction tracker, timeline, risk matrix, ceasefire monitor, weapons/supply
    intelligence, media bias tracker, and AI situation report generator.

Aesthetic: Luxury Intelligence Operations Center
  — Deep void backgrounds, razor-sharp amber+cyan accent system
  — Glassmorphism panels, animated gradient borders on critical cards
  — Bebas Neue display · IBM Plex Mono data · DM Sans UI

Tech stack:
  Frontend    : Streamlit + PyDeck (deck.gl) + Plotly
  Maps        : PyDeck ScatterplotLayer / HeatmapLayer / ArcLayer
  AI/ML       : Groq / Ollama / OpenRouter via HTTP
  News Feeds  : RSS XML parsing (16 sources)
  Caching     : st.cache_data TTL hierarchy
  Live data   : USGS · NASA EONET · NOAA SWPC · ACLED (mock) · GDELT (mock)
"""

import streamlit as st
import pandas as pd
import numpy as np
import json, requests, re, html as html_lib
from datetime import datetime, timezone, timedelta
import pydeck as pdk
import plotly.graph_objects as go
import plotly.express as px
import math

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="OSINT ARENA",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --void:   #02040a;
  --deep:   #050b14;
  --panel:  #070e1a;
  --glass:  rgba(7,14,26,0.85);
  --border: rgba(0,200,255,0.10);
  --bord2:  rgba(0,200,255,0.06);
  --cyan:   #00c8ff;
  --amber:  #ffb400;
  --red:    #ff3d5a;
  --green:  #00e676;
  --violet: #9d6eff;
  --orange: #ff8c42;
  --text:   #dde8f5;
  --muted:  #3d5a75;
  --dim:    #0d1e30;
  --fd:     'Bebas Neue','Impact',sans-serif;
  --fm:     'IBM Plex Mono','Courier New',monospace;
  --fb:     'DM Sans',system-ui,sans-serif;
}

html,body,[class*="css"],.stApp { font-family:var(--fb)!important; background:var(--void)!important; color:var(--text)!important; }

.stApp::before {
  content:''; position:fixed; inset:0;
  background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,0.025) 3px,rgba(0,0,0,0.025) 6px);
  pointer-events:none; z-index:9000;
}
.stApp::after {
  content:''; position:fixed; inset:0;
  background:radial-gradient(ellipse at center,transparent 60%,rgba(0,0,0,0.5) 100%);
  pointer-events:none; z-index:9001;
}

::-webkit-scrollbar{width:3px;height:3px}
::-webkit-scrollbar-track{background:var(--deep)}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}

section[data-testid="stSidebar"]{background:var(--deep)!important;border-right:1px solid var(--border)!important;}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p{color:var(--text)!important;}

.stTabs [data-baseweb="tab-list"]{background:var(--deep)!important;border-bottom:1px solid var(--border)!important;gap:0!important;padding:0 4px;}
.stTabs [data-baseweb="tab"]{background:transparent!important;border-bottom:2px solid transparent!important;font-family:var(--fb)!important;font-weight:600!important;font-size:12px!important;letter-spacing:.1em!important;text-transform:uppercase!important;color:var(--muted)!important;padding:12px 16px!important;}
.stTabs [aria-selected="true"]{color:var(--cyan)!important;border-bottom-color:var(--cyan)!important;}

div[data-testid="stMetric"]{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px 18px!important;}
div[data-testid="stMetricValue"]{font-family:var(--fm)!important;font-size:22px!important;color:var(--cyan)!important;}
div[data-testid="stMetricLabel"]{font-family:var(--fb)!important;font-size:10px!important;font-weight:600!important;letter-spacing:.14em!important;text-transform:uppercase!important;color:var(--muted)!important;}
div[data-testid="stMetricDelta"]{font-size:11px!important;}

.stButton>button{background:transparent!important;border:1px solid var(--border)!important;color:var(--text)!important;font-family:var(--fb)!important;font-weight:600!important;font-size:12px!important;letter-spacing:.08em!important;border-radius:6px!important;padding:8px 16px!important;transition:all .18s!important;}
.stButton>button:hover{border-color:var(--cyan)!important;color:var(--cyan)!important;background:rgba(0,200,255,.06)!important;box-shadow:0 0 14px rgba(0,200,255,.12)!important;}

.stSelectbox>div>div,.stTextInput>div>div>input,.stTextArea textarea{background:var(--panel)!important;border:1px solid var(--border)!important;color:var(--text)!important;font-family:var(--fm)!important;font-size:12px!important;border-radius:6px!important;}
.stSelectbox label,.stTextInput label,.stTextArea label,.stRadio label,.stCheckbox label{color:var(--muted)!important;font-size:10px!important;letter-spacing:.12em!important;text-transform:uppercase!important;font-weight:600!important;}
.stRadio>div{gap:6px;}
.stRadio>div>label{background:var(--panel)!important;border:1px solid var(--bord2)!important;border-radius:5px!important;padding:5px 10px!important;font-size:11px!important;color:var(--text)!important;text-transform:none!important;letter-spacing:0!important;font-weight:400!important;}

.stSuccess{background:rgba(0,230,118,.07)!important;border:1px solid rgba(0,230,118,.25)!important;color:var(--green)!important;border-radius:8px!important;}
.stError{background:rgba(255,61,90,.07)!important;border:1px solid rgba(255,61,90,.25)!important;color:var(--red)!important;border-radius:8px!important;}
.stWarning{background:rgba(255,180,0,.07)!important;border:1px solid rgba(255,180,0,.25)!important;color:var(--amber)!important;border-radius:8px!important;}
.stInfo{background:rgba(0,200,255,.07)!important;border:1px solid rgba(0,200,255,.25)!important;color:var(--cyan)!important;border-radius:8px!important;}

.stDataFrame{background:var(--panel)!important;}
.stDataFrame [data-testid="stDataFrameResizable"]{border:1px solid var(--border)!important;border-radius:8px!important;overflow:hidden!important;}
hr{border:none!important;border-top:1px solid var(--bord2)!important;margin:14px 0!important;}

/* ── CUSTOM COMPONENTS ── */
.wordmark{font-family:var(--fd);font-size:32px;letter-spacing:.16em;line-height:1;color:var(--cyan);text-shadow:0 0 32px rgba(0,200,255,.45),0 0 64px rgba(0,200,255,.15);}
.wordmark em{color:var(--amber);font-style:normal;}

.sec-label{font-family:var(--fb);font-size:9px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);display:flex;align-items:center;gap:8px;margin-bottom:10px;}
.sec-label::after{content:'';flex:1;height:1px;background:var(--bord2);}

.status-row{display:flex;align-items:center;gap:22px;font-family:var(--fm);font-size:10px;color:var(--muted);padding:8px 0 12px;border-bottom:1px solid var(--bord2);margin-bottom:16px;}
.pulse{width:6px;height:6px;border-radius:50%;display:inline-block;margin-right:5px;animation:blink 2s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.p-cyan{background:var(--cyan);box-shadow:0 0 6px var(--cyan);}
.p-amber{background:var(--amber);box-shadow:0 0 6px var(--amber);}
.p-red{background:var(--red);box-shadow:0 0 6px var(--red);animation-duration:.8s;}
.p-green{background:var(--green);box-shadow:0 0 6px var(--green);}
.p-orange{background:var(--orange);box-shadow:0 0 6px var(--orange);}
.utc-clock{margin-left:auto;font-family:var(--fd);font-size:14px;letter-spacing:.12em;color:var(--cyan);}

/* GLASS CARD */
.gcard{background:var(--glass);backdrop-filter:blur(8px);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:8px;position:relative;overflow:hidden;transition:border-color .2s,box-shadow .2s;}
.gcard:hover{border-color:rgba(0,200,255,.22);box-shadow:0 0 20px rgba(0,200,255,.06);}
.gcard::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(0,200,255,.3),transparent);}
.gcard-crit{border-color:rgba(255,61,90,.35)!important;box-shadow:0 0 18px rgba(255,61,90,.08)!important;animation:crit-pulse 3s ease-in-out infinite;}
@keyframes crit-pulse{0%,100%{box-shadow:0 0 18px rgba(255,61,90,.08)}50%{box-shadow:0 0 28px rgba(255,61,90,.18)}}
.gcard-crit::before{background:linear-gradient(90deg,transparent,rgba(255,61,90,.45),transparent)!important;}
.gcard-amber{border-color:rgba(255,180,0,.3)!important;box-shadow:0 0 14px rgba(255,180,0,.06)!important;}
.gcard-amber::before{background:linear-gradient(90deg,transparent,rgba(255,180,0,.35),transparent)!important;}

/* CONFLICT-SPECIFIC CARDS */
.conflict-card{background:var(--panel);border:1px solid var(--bord2);border-radius:10px;padding:0;margin-bottom:10px;overflow:hidden;transition:border-color .2s;}
.conflict-card:hover{border-color:rgba(255,61,90,.2);}
.cc-header{padding:10px 14px;border-bottom:1px solid var(--bord2);display:flex;align-items:center;justify-content:space-between;}
.cc-body{padding:12px 14px;}
.cc-title{font-family:var(--fd);font-size:15px;letter-spacing:.08em;color:var(--text);}
.cc-subtitle{font-family:var(--fm);font-size:10px;color:var(--muted);}

/* INCIDENT FEED */
.incident-row{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid var(--bord2);transition:background .15s;}
.incident-row:hover{background:rgba(255,61,90,.03);border-radius:4px;padding-left:4px;}
.inc-icon{width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:13px;flex-shrink:0;}
.inc-body{flex:1;min-width:0;}
.inc-title{font-size:12px;font-weight:600;color:var(--text);line-height:1.35;}
.inc-meta{font-family:var(--fm);font-size:9px;color:var(--muted);margin-top:2px;}
.inc-badge-row{display:flex;gap:4px;margin-top:5px;flex-wrap:wrap;}

/* ESCALATION GAUGE */
.esc-gauge{text-align:center;padding:10px 0;}
.esc-val{font-family:var(--fd);font-size:52px;letter-spacing:.05em;line-height:1;}
.esc-label{font-family:var(--fm);font-size:10px;letter-spacing:.12em;text-transform:uppercase;margin-top:2px;}
.esc-bar{height:8px;background:var(--dim);border-radius:4px;overflow:hidden;margin-top:8px;}
.esc-fill{height:100%;border-radius:4px;}

/* FACTION ROW */
.faction-row{display:grid;grid-template-columns:24px 1fr auto auto auto;align-items:center;gap:10px;padding:9px 12px;border-bottom:1px solid var(--bord2);}
.faction-dot{width:10px;height:10px;border-radius:50%;}
.faction-name{font-size:12px;font-weight:600;color:var(--text);}
.faction-ctrl{font-family:var(--fm);font-size:10px;color:var(--muted);text-align:right;}

/* TIMELINE */
.timeline{position:relative;padding-left:20px;}
.timeline::before{content:'';position:absolute;left:6px;top:0;bottom:0;width:1px;background:var(--bord2);}
.tl-item{position:relative;margin-bottom:14px;}
.tl-dot{position:absolute;left:-17px;top:3px;width:8px;height:8px;border-radius:50%;border:1px solid;}
.tl-date{font-family:var(--fm);font-size:9px;color:var(--muted);margin-bottom:2px;}
.tl-text{font-size:12px;color:var(--text);line-height:1.45;}
.tl-tag{font-family:var(--fm);font-size:9px;color:var(--muted);}

/* RISK MATRIX */
.risk-cell{border-radius:5px;padding:4px 6px;font-family:var(--fm);font-size:9px;text-align:center;cursor:default;}

/* BADGES */
.badge{display:inline-flex;align-items:center;padding:2px 7px;border-radius:4px;font-family:var(--fm);font-size:9px;font-weight:500;letter-spacing:.06em;border:1px solid;white-space:nowrap;}
.b-red{color:var(--red);border-color:rgba(255,61,90,.35);background:rgba(255,61,90,.10);}
.b-amber{color:var(--amber);border-color:rgba(255,180,0,.35);background:rgba(255,180,0,.10);}
.b-cyan{color:var(--cyan);border-color:rgba(0,200,255,.35);background:rgba(0,200,255,.10);}
.b-green{color:var(--green);border-color:rgba(0,230,118,.35);background:rgba(0,230,118,.10);}
.b-violet{color:var(--violet);border-color:rgba(157,110,255,.35);background:rgba(157,110,255,.10);}
.b-orange{color:var(--orange);border-color:rgba(255,140,66,.35);background:rgba(255,140,66,.10);}
.b-muted{color:var(--muted);border-color:rgba(61,90,117,.4);background:rgba(61,90,117,.10);}

.sig-title{font-size:13px;font-weight:600;color:var(--text);line-height:1.35;}
.sig-meta{font-family:var(--fm);font-size:10px;color:var(--muted);margin-top:3px;line-height:1.5;}

.scale-wrap{display:flex;align-items:center;gap:8px;margin-top:7px;}
.scale-track{flex:1;height:3px;background:var(--dim);border-radius:2px;overflow:hidden;}
.scale-fill{height:100%;border-radius:2px;}
.xp-track{height:4px;background:var(--dim);border-radius:3px;overflow:hidden;margin-top:5px;}
.xp-fill{height:100%;background:linear-gradient(90deg,var(--violet),var(--cyan));border-radius:3px;}

.lb-row{display:flex;align-items:center;gap:10px;padding:9px 12px;border-bottom:1px solid var(--bord2);transition:background .15s;}
.lb-row:hover{background:rgba(0,200,255,.03);}
.lb-avatar{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;flex-shrink:0;}

.ch-card{background:var(--panel);border:1px solid var(--border);border-radius:12px;margin-bottom:14px;overflow:hidden;}
.ch-header{padding:10px 16px;border-bottom:1px solid var(--bord2);display:flex;align-items:center;justify-content:space-between;}
.ch-title{font-family:var(--fd);font-size:14px;letter-spacing:.1em;color:var(--violet);}
.ch-body{padding:14px 16px;}
.ch-q{font-size:13px;color:var(--text);line-height:1.6;margin-bottom:12px;}
.clue{display:flex;gap:7px;font-family:var(--fm);font-size:10px;color:var(--muted);margin-bottom:5px;line-height:1.5;}
.clue span{color:var(--violet);flex-shrink:0;}

.news-card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:10px;position:relative;overflow:hidden;transition:border-color .2s,transform .15s;}
.news-card:hover{border-color:rgba(0,200,255,.2);transform:translateY(-1px);}
.news-card::after{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;}
.nc-seismic::after{background:linear-gradient(180deg,var(--red),transparent);}
.nc-volcanic::after{background:linear-gradient(180deg,var(--orange),transparent);}
.nc-solar::after{background:linear-gradient(180deg,var(--amber),transparent);}
.nc-civil::after{background:linear-gradient(180deg,var(--violet),transparent);}
.nc-general::after{background:linear-gradient(180deg,var(--cyan),transparent);}
.news-headline{font-size:13px;font-weight:600;color:var(--text);line-height:1.4;margin:6px 0 5px;}
.news-desc{font-size:11px;color:var(--muted);line-height:1.55;margin-bottom:8px;}
.news-footer{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.news-time{font-family:var(--fm);font-size:9px;color:var(--muted);}
.news-link{font-family:var(--fm);font-size:9px;color:var(--cyan);text-decoration:none;letter-spacing:.05em;padding:2px 8px;border:1px solid rgba(0,200,255,.25);border-radius:3px;transition:background .15s;}
.news-source{display:inline-flex;align-items:center;gap:5px;font-family:var(--fm);font-size:9px;font-weight:500;letter-spacing:.08em;text-transform:uppercase;}
.src-pill{display:inline-flex;align-items:center;gap:5px;padding:3px 10px;background:var(--dim);border:1px solid var(--bord2);border-radius:20px;font-family:var(--fm);font-size:10px;color:var(--text);}

.ticker-wrap{background:var(--deep);border-top:1px solid var(--border);border-bottom:1px solid var(--bord2);overflow:hidden;padding:7px 0;}
.ticker-inner{display:inline-block;white-space:nowrap;animation:ticker-scroll 80s linear infinite;font-family:var(--fm);font-size:10px;color:var(--muted);}
@keyframes ticker-scroll{from{transform:translateX(0)}to{transform:translateX(-50%)}}
.t-sep{color:var(--cyan);margin:0 14px;}
.t-hi{color:var(--text);}
.t-red{color:var(--red);}
.t-amb{color:var(--amber);}

.ai-terminal{background:#020810;border:1px solid var(--border);border-radius:8px;padding:16px;font-family:var(--fm);font-size:12px;color:var(--text);line-height:1.7;white-space:pre-wrap;min-height:160px;position:relative;}
.ai-terminal::before{content:'> ANALYSIS OUTPUT';display:block;font-size:9px;letter-spacing:.2em;color:var(--muted);margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid var(--bord2);}

.m-panel{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:14px 16px;margin-bottom:10px;}
.m-label{font-size:9px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin-bottom:5px;}
.m-val{font-family:var(--fd);font-size:34px;letter-spacing:.05em;line-height:1;margin-bottom:3px;}
.m-sub{font-family:var(--fm);font-size:10px;color:var(--muted);}
.m-cyan{color:var(--cyan);text-shadow:0 0 20px rgba(0,200,255,.35);}
.m-amber{color:var(--amber);text-shadow:0 0 20px rgba(255,180,0,.25);}
.m-red{color:var(--red);text-shadow:0 0 20px rgba(255,61,90,.3);}
.m-green{color:var(--green);text-shadow:0 0 20px rgba(0,230,118,.25);}
.m-violet{color:var(--violet);text-shadow:0 0 20px rgba(157,110,255,.25);}
.m-orange{color:var(--orange);text-shadow:0 0 20px rgba(255,140,66,.25);}

.sb-divider{height:1px;background:var(--bord2);margin:14px 0;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k,v in {
    "score":2840,"answered":{},"ai_provider":"groq","ai_key":"",
    "ai_output":"","conflict_sitrep":"","selected_conflict":"Ukraine–Russia War",
}.items():
    if k not in st.session_state: st.session_state[k]=v


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_tier(s):
    if s>=10000: return "HANDLER","b-red","#ff3d5a"
    if s>=5000:  return "AGENT","b-violet","#9d6eff"
    if s>=2000:  return "ANALYST","b-cyan","#00c8ff"
    return "RECRUIT","b-green","#00e676"

def bg_chart():
    return dict(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")

def ax(color="#3d5a75",grid="#0d1e30",sz=9):
    return dict(color=color,tickfont_size=sz,gridcolor=grid)


# ─────────────────────────────────────────────
# ══════════════════════════════════════════════
# CONFLICT DATA  ← comprehensive mock dataset
# (wire in ACLED API / GDELT / ReliefWeb for live)
# ══════════════════════════════════════════════
# ─────────────────────────────────────────────

CONFLICTS = {
"Ukraine–Russia War": {
  "status":"ACTIVE","intensity":"CRITICAL","start":"2022-02-24","region":"Eastern Europe",
  "escalation":87,"ceasefire":False,"casualties_total":350000,"displaced":14200000,
  "description":"Full-scale invasion of Ukraine by Russian Federation. Ongoing frontline combat across eastern/southern oblasts.",
  "factions":[
    {"name":"Ukraine Armed Forces","side":"UA","color":"#1a9fff","territory_pct":68,"strength":"High","weapons":["F-16","HIMARS","M1 Abrams","Patriot PAC-3"],"support":["USA","NATO","EU"],"status":"Defending"},
    {"name":"Russian Federation Forces","side":"RU","color":"#ff3d5a","territory_pct":20,"strength":"High","weapons":["T-90M","Kalibr","Iskander","Shahed-136"],"support":["Belarus","Iran","DPRK"],"status":"Advancing"},
    {"name":"Wagner/Volunteer Corps","side":"RU","color":"#ff8c42","territory_pct":4,"strength":"Med","weapons":["Artillery","Armour"],"support":["Russia"],"status":"Active"},
  ],
  "incidents":[
    {"type":"airstrike","title":"Missile salvo targets Kyiv energy grid","loc":"Kyiv Oblast","lat":50.45,"lon":30.52,"date":"2026-03-14","severity":"CRITICAL","casualties":12},
    {"type":"ground","title":"Frontal assault near Avdiivka sector","loc":"Donetsk Oblast","lat":47.97,"lon":37.74,"date":"2026-03-14","severity":"HIGH","casualties":45},
    {"type":"drone","title":"Shahed drone swarm intercepted","loc":"Zaporizhzhia","lat":47.84,"lon":35.14,"date":"2026-03-13","severity":"HIGH","casualties":3},
    {"type":"naval","title":"Black Sea vessel incident — tanker seized","loc":"Black Sea","lat":44.5,"lon":32.5,"date":"2026-03-13","severity":"MED","casualties":0},
    {"type":"airstrike","title":"Kharkiv residential district strike","loc":"Kharkiv","lat":49.99,"lon":36.23,"date":"2026-03-12","severity":"CRITICAL","casualties":28},
    {"type":"cyber","title":"Power grid SCADA intrusion detected","loc":"Western Ukraine","lat":49.8,"lon":24.0,"date":"2026-03-12","severity":"HIGH","casualties":0},
    {"type":"ground","title":"Counterattack recaptures village","loc":"Kherson Oblast","lat":46.65,"lon":32.62,"date":"2026-03-11","severity":"MED","casualties":8},
    {"type":"diplomatic","title":"UN Security Council emergency session","loc":"New York","lat":40.75,"lon":-73.98,"date":"2026-03-11","severity":"INFO","casualties":0},
  ],
  "timeline":[
    {"date":"2022-02-24","event":"Full-scale invasion begins","type":"escalation"},
    {"date":"2022-03-28","event":"Kyiv assault repelled — Russian withdrawal","type":"milestone"},
    {"date":"2022-09-21","event":"Russian partial mobilisation declared","type":"escalation"},
    {"date":"2022-11-11","event":"Kherson city liberated by Ukraine","type":"milestone"},
    {"date":"2023-06-04","event":"Ukrainian counteroffensive begins","type":"escalation"},
    {"date":"2024-02-17","event":"Avdiivka falls to Russian forces","type":"setback"},
    {"date":"2024-08-06","event":"Ukraine crosses border — Kursk incursion","type":"escalation"},
    {"date":"2025-11-20","event":"US authorises long-range missile strikes","type":"escalation"},
    {"date":"2026-01-15","event":"Renewed frontline pressure in Donetsk","type":"ongoing"},
    {"date":"2026-03-10","event":"Largest missile salvo of 2026","type":"escalation"},
  ],
  "supply_lines":[
    {"from_lat":48.8,"from_lon":2.35,"to_lat":50.45,"to_lon":30.52,"type":"Military Aid","provider":"France"},
    {"from_lat":52.52,"from_lon":13.4,"to_lat":50.45,"to_lon":30.52,"type":"Military Aid","provider":"Germany"},
    {"from_lat":51.5,"from_lon":-0.1,"to_lat":50.45,"to_lon":30.52,"type":"Military Aid","provider":"UK"},
    {"from_lat":38.9,"from_lon":-77.0,"to_lat":50.45,"to_lon":30.52,"type":"Military Aid","provider":"USA"},
  ],
  "media_sources":[
    {"name":"Reuters","bias":"Centre","reliability":92,"coverage":"High"},
    {"name":"BBC","bias":"Centre-Left","reliability":88,"coverage":"High"},
    {"name":"RT","bias":"State/RU","reliability":28,"coverage":"High"},
    {"name":"Kyiv Independent","bias":"Pro-UA","reliability":74,"coverage":"High"},
    {"name":"TASS","bias":"State/RU","reliability":25,"coverage":"Med"},
    {"name":"AP","bias":"Centre","reliability":91,"coverage":"Med"},
  ],
},
"Gaza Conflict": {
  "status":"ACTIVE","intensity":"CRITICAL","start":"2023-10-07","region":"Middle East",
  "escalation":92,"ceasefire":False,"casualties_total":46000,"displaced":1900000,
  "description":"Israeli military operations in Gaza following Hamas October 7 attacks. Severe humanitarian crisis with ongoing ground and air operations.",
  "factions":[
    {"name":"Israel Defense Forces","side":"IL","color":"#1a9fff","territory_pct":72,"strength":"High","weapons":["F-35I","Iron Dome","Merkava IV","D9 bulldozer"],"support":["USA","UK"],"status":"Offensive"},
    {"name":"Hamas","side":"HA","color":"#ff3d5a","territory_pct":20,"strength":"Med","weapons":["Rockets","Tunnels","IEDs","RPG"],"support":["Iran","Hezbollah"],"status":"Defending"},
    {"name":"Palestinian Islamic Jihad","side":"HA","color":"#ff8c42","territory_pct":5,"strength":"Low","weapons":["Rockets","Mortars"],"support":["Iran"],"status":"Active"},
    {"name":"UNRWA / Aid Corridors","side":"HU","color":"#00e676","territory_pct":3,"strength":"N/A","weapons":[],"support":["UN","EU"],"status":"Constrained"},
  ],
  "incidents":[
    {"type":"airstrike","title":"IDF strikes Rafah crossing area","loc":"Rafah, Gaza","lat":31.28,"lon":34.25,"date":"2026-03-14","severity":"CRITICAL","casualties":35},
    {"type":"ground","title":"Ground forces advance in northern Gaza","loc":"Gaza City","lat":31.52,"lon":34.47,"date":"2026-03-14","severity":"HIGH","casualties":22},
    {"type":"humanitarian","title":"Aid convoy blocked at Kerem Shalom","loc":"Kerem Shalom","lat":31.23,"lon":34.3,"date":"2026-03-13","severity":"HIGH","casualties":0},
    {"type":"rocket","title":"Rocket barrage from Hezbollah — N. Israel","loc":"Northern Israel","lat":33.0,"lon":35.5,"date":"2026-03-13","severity":"HIGH","casualties":4},
    {"type":"diplomatic","title":"ICJ interim order compliance review","loc":"The Hague","lat":52.08,"lon":4.3,"date":"2026-03-12","severity":"INFO","casualties":0},
  ],
  "timeline":[
    {"date":"2023-10-07","event":"Hamas multi-front attack on Israel — 1,200 killed","type":"escalation"},
    {"date":"2023-10-09","event":"Israeli airstrikes begin, siege declared","type":"escalation"},
    {"date":"2023-10-27","event":"Israeli ground invasion begins","type":"escalation"},
    {"date":"2023-11-24","event":"Temporary ceasefire and hostage deal","type":"diplomatic"},
    {"date":"2024-02-12","event":"IDF advances on Rafah","type":"escalation"},
    {"date":"2024-05-07","event":"Rafah ground operation begins","type":"escalation"},
    {"date":"2025-01-19","event":"Ceasefire phase-1 agreement","type":"diplomatic"},
    {"date":"2025-03-18","event":"Ceasefire collapses — operations resume","type":"escalation"},
    {"date":"2026-03-14","event":"Ongoing operations Rafah + north Gaza","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":30.06,"from_lon":31.24,"to_lat":31.52,"to_lon":34.47,"type":"Humanitarian","provider":"Egypt/UN"},
    {"from_lat":38.9,"from_lon":-77.0,"to_lat":31.77,"to_lon":35.21,"type":"Military Aid","provider":"USA"},
    {"from_lat":35.69,"from_lon":51.39,"to_lat":31.28,"to_lon":34.25,"type":"Arms/Funding","provider":"Iran→Hamas"},
  ],
  "media_sources":[
    {"name":"Al Jazeera","bias":"Pro-Palestinian","reliability":72,"coverage":"High"},
    {"name":"Times of Israel","bias":"Pro-Israel","reliability":71,"coverage":"High"},
    {"name":"Reuters","bias":"Centre","reliability":91,"coverage":"High"},
    {"name":"Haaretz","bias":"Centre-Left","reliability":83,"coverage":"High"},
    {"name":"Fox News","bias":"Right","reliability":62,"coverage":"Med"},
    {"name":"BBC","bias":"Centre","reliability":86,"coverage":"High"},
  ],
},
"Sudan Civil War": {
  "status":"ACTIVE","intensity":"HIGH","start":"2023-04-15","region":"Sub-Saharan Africa",
  "escalation":74,"ceasefire":False,"casualties_total":15000,"displaced":8100000,
  "description":"Armed conflict between Sudanese Armed Forces (SAF) and Rapid Support Forces (RSF) paramilitary group across Sudan, including Darfur.",
  "factions":[
    {"name":"Sudanese Armed Forces","side":"SAF","color":"#1a9fff","territory_pct":55,"strength":"Med","weapons":["Su-25","Mi-24","T-72","Artillery"],"support":["Egypt","Saudi Arabia"],"status":"Active"},
    {"name":"Rapid Support Forces","side":"RSF","color":"#ff3d5a","territory_pct":38,"strength":"High","weapons":["Technicals","ZU-23","Mortars","Armour"],"support":["UAE","Wagner"],"status":"Advancing"},
    {"name":"Sudan Liberation Army","side":"SLA","color":"#ffb400","territory_pct":5,"strength":"Low","weapons":["Light arms"],"support":["None"],"status":"Active"},
  ],
  "incidents":[
    {"type":"airstrike","title":"SAF airstrike on RSF position — Omdurman","loc":"Omdurman","lat":15.65,"lon":32.48,"date":"2026-03-14","severity":"HIGH","casualties":18},
    {"type":"ground","title":"RSF advances in El Fasher, North Darfur","loc":"El Fasher","lat":13.63,"lon":25.35,"date":"2026-03-13","severity":"CRITICAL","casualties":42},
    {"type":"humanitarian","title":"MSF hospital shelled — Khartoum North","loc":"Khartoum","lat":15.5,"lon":32.53,"date":"2026-03-12","severity":"CRITICAL","casualties":9},
    {"type":"diplomatic","title":"Jeddah peace talks stall — no agreement","loc":"Jeddah, Saudi Arabia","lat":21.49,"lon":39.19,"date":"2026-03-10","severity":"MED","casualties":0},
  ],
  "timeline":[
    {"date":"2023-04-15","event":"Open fighting erupts in Khartoum","type":"escalation"},
    {"date":"2023-04-22","event":"Ceasefire agreed — immediately violated","type":"diplomatic"},
    {"date":"2023-06-01","event":"RSF seizes most of Khartoum","type":"setback"},
    {"date":"2023-10-26","event":"Darfur atrocities reported — UN warning","type":"escalation"},
    {"date":"2024-03-13","event":"El Fasher siege begins","type":"escalation"},
    {"date":"2025-01-10","event":"SAF recaptures parts of Khartoum","type":"milestone"},
    {"date":"2026-03-14","event":"RSF advancing in Darfur — famine risk","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":25.2,"from_lon":55.27,"to_lat":15.65,"to_lon":32.48,"type":"RSF Support","provider":"UAE"},
    {"from_lat":30.06,"from_lon":31.24,"to_lat":15.65,"to_lon":32.48,"type":"SAF Support","provider":"Egypt"},
  ],
  "media_sources":[
    {"name":"Sudan Tribune","bias":"Local","reliability":67,"coverage":"High"},
    {"name":"Reuters","bias":"Centre","reliability":91,"coverage":"Med"},
    {"name":"BBC","bias":"Centre","reliability":86,"coverage":"Med"},
    {"name":"Al Jazeera","bias":"Centre-Left","reliability":75,"coverage":"High"},
  ],
},
"Myanmar Civil War": {
  "status":"ACTIVE","intensity":"HIGH","start":"2021-02-01","region":"Southeast Asia",
  "escalation":68,"ceasefire":False,"casualties_total":50000,"displaced":2600000,
  "description":"Armed resistance against Myanmar military junta (SAC/Tatmadaw) by People's Defence Force, Ethnic Resistance Organisations, and civilian militias.",
  "factions":[
    {"name":"Tatmadaw / SAC","side":"JU","color":"#ff3d5a","territory_pct":45,"strength":"Med","weapons":["Yak-130","Mi-35","105mm","D30"],"support":["Russia","China"],"status":"Defending"},
    {"name":"People's Defence Force","side":"OP","color":"#00e676","territory_pct":35,"strength":"Med","weapons":["Drones","IEDs","Captured arms"],"support":["NUG","Diaspora"],"status":"Offensive"},
    {"name":"Ethnic Resistance Orgs","side":"OP","color":"#1a9fff","territory_pct":18,"strength":"Med","weapons":["Arty","Infantry"],"support":["PDF","NUG"],"status":"Advancing"},
  ],
  "incidents":[
    {"type":"airstrike","title":"Junta airstrike on PDF-held village","loc":"Sagaing Region","lat":21.9,"lon":95.98,"date":"2026-03-14","severity":"HIGH","casualties":14},
    {"type":"ground","title":"3BHA captures Hsipaw town","loc":"Shan State","lat":22.6,"lon":97.3,"date":"2026-03-13","severity":"HIGH","casualties":20},
    {"type":"humanitarian","title":"IDP camp shelled — 30,000 displaced","loc":"Kayah State","lat":19.74,"lon":97.34,"date":"2026-03-12","severity":"CRITICAL","casualties":7},
  ],
  "timeline":[
    {"date":"2021-02-01","event":"Military coup overthrows NLD government","type":"escalation"},
    {"date":"2021-03-27","event":"Military kills 114 protesters","type":"escalation"},
    {"date":"2021-09-07","event":"NUG declares People's Defensive War","type":"escalation"},
    {"date":"2023-10-27","event":"Operation 1027 — major opposition offensive","type":"milestone"},
    {"date":"2024-01-04","event":"Kokang region captured by MNDAA","type":"milestone"},
    {"date":"2024-04-11","event":"Myawaddy falls to resistance","type":"milestone"},
    {"date":"2026-03-14","event":"Resistance controls 60%+ of territory","type":"ongoing"},
  ],
  "supply_lines":[
    {"from_lat":39.9,"from_lon":116.39,"to_lat":21.9,"to_lon":95.98,"type":"Junta Support","provider":"China"},
    {"from_lat":55.75,"from_lon":37.61,"to_lat":16.87,"to_lon":96.19,"type":"Arms Supply","provider":"Russia"},
  ],
  "media_sources":[
    {"name":"Irrawaddy","bias":"Pro-Resistance","reliability":75,"coverage":"High"},
    {"name":"Myanmar Now","bias":"Pro-Resistance","reliability":70,"coverage":"High"},
    {"name":"Reuters","bias":"Centre","reliability":91,"coverage":"Med"},
    {"name":"Global New Light","bias":"State/Junta","reliability":22,"coverage":"Low"},
  ],
},
}

INCIDENT_ICONS = {
    "airstrike":"💥","ground":"⚔️","drone":"🛸","naval":"⚓","rocket":"🚀",
    "cyber":"💻","diplomatic":"🤝","humanitarian":"🏥",
}
INCIDENT_COLORS = {
    "airstrike":"rgba(255,61,90,.15)","ground":"rgba(255,140,66,.15)",
    "drone":"rgba(157,110,255,.15)","naval":"rgba(0,200,255,.15)",
    "rocket":"rgba(255,180,0,.15)","cyber":"rgba(0,200,255,.12)",
    "diplomatic":"rgba(0,230,118,.12)","humanitarian":"rgba(0,200,255,.1)",
}
SEV_BADGE = {"CRITICAL":"b-red","HIGH":"b-orange","MED":"b-amber","LOW":"b-green","INFO":"b-muted"}


# ─────────────────────────────────────────────
# LIVE DATA FETCHERS
# ─────────────────────────────────────────────
@st.cache_data(ttl=60,  show_spinner=False)
def fetch_usgs():
    try:
        r=requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",timeout=8)
        r.raise_for_status()
        rows=[]
        for f in r.json()["features"][:50]:
            p,c=f["properties"],f["geometry"]["coordinates"]
            rows.append({"title":p.get("title","—"),"mag":round(p.get("mag",0),1),"place":p.get("place","?"),
                         "depth_km":round(c[2],1),"lon":c[0],"lat":c[1],"type":"seismic",
                         "time":datetime.fromtimestamp(p["time"]/1000,tz=timezone.utc).strftime("%H:%Mz"),"url":p.get("url","")})
        return pd.DataFrame(rows)
    except: return _sq()

@st.cache_data(ttl=300, show_spinner=False)
def fetch_eonet():
    try:
        r=requests.get("https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=20",timeout=8)
        r.raise_for_status()
        rows=[]
        for e in r.json()["events"]:
            cat=e["categories"][0]["title"] if e["categories"] else "Other"
            if e["geometry"]:
                geo=e["geometry"][-1]
                if geo["type"]=="Point":
                    rows.append({"title":e["title"],"cat":cat,"date":geo["date"][:10],"lon":geo["coordinates"][0],"lat":geo["coordinates"][1],"type":"eonet"})
        return pd.DataFrame(rows) if rows else _se()
    except: return _se()

@st.cache_data(ttl=180, show_spinner=False)
def fetch_kp():
    try:
        r=requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json",timeout=6)
        r.raise_for_status()
        data=r.json()
        return {"kp":float(data[-1][1]),"series":[float(x[1]) for x in data[-24:] if len(x)>1]}
    except: return {"kp":3.7,"series":[1,2,1.5,2.3,3.1,3.7,2.8,2.1,1.8,2.5,3,3.7]*2}

@st.cache_data(ttl=600, show_spinner=False)
def fetch_rss(url,source,cat="general"):
    try:
        r=requests.get(url,timeout=10,headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        items=re.findall(r'<item>(.*?)</item>',r.text,re.DOTALL)
        arts=[]
        for item in items[:8]:
            def g(tag,txt):
                m=re.search(rf'<{tag}[^>]*>(.*?)</{tag}>',txt,re.DOTALL|re.IGNORECASE)
                if m:
                    v=m.group(1).strip()
                    v=re.sub(r'<!\[CDATA\[(.*?)\]\]>',r'\1',v,flags=re.DOTALL)
                    return html_lib.unescape(re.sub(r'<[^>]+>','',v)).strip()
                return ""
            title=g("title",item); desc=g("description",item); link=g("link",item); pub=g("pubDate",item)
            try:
                from email.utils import parsedate_to_datetime
                dt=parsedate_to_datetime(pub)
                age=datetime.now(tz=timezone.utc)-dt.astimezone(timezone.utc)
                age_s=f"{int(age.total_seconds()//3600)}h ago" if age.total_seconds()>3600 else f"{int(age.total_seconds()//60)}m ago"
            except: age_s="recent"
            if title and len(title)>10:
                arts.append({"source":source,"category":cat,"title":title[:120],"desc":(desc or "")[:220],"link":link,"time":age_s})
        return arts
    except: return []

def _sq():
    rng=np.random.default_rng(42); lats=rng.uniform(-55,70,30); lons=rng.uniform(-170,170,30)
    mags=rng.uniform(2.5,6.8,30); d=rng.uniform(5,120,30)
    pl=["California","Japan","Indonesia","Chile","Turkey","Philippines","Papua New Guinea","Peru","Mexico","Greece"]
    return pd.DataFrame({"title":[f"M{m:.1f} — {pl[i%len(pl)]}" for i,m in enumerate(mags)],"mag":np.round(mags,1),
        "place":[pl[i%len(pl)] for i in range(30)],"depth_km":np.round(d,1),
        "lon":np.round(lons,3),"lat":np.round(lats,3),
        "time":[f"{rng.integers(0,24):02d}:{rng.integers(0,60):02d}z" for _ in range(30)],"type":"seismic","url":""})

def _se():
    return pd.DataFrame([
        {"title":"Kilauea — Active Lava","cat":"Volcanoes","date":"2026-03-14","lon":-155.2,"lat":19.4,"type":"eonet"},
        {"title":"Etna — SO₂ Plume","cat":"Volcanoes","date":"2026-03-13","lon":15.0,"lat":37.8,"type":"eonet"},
        {"title":"Texas Wildfires","cat":"Wildfires","date":"2026-03-12","lon":-101.0,"lat":32.5,"type":"eonet"},
    ])

# STATIC DATA
MOVEMENTS=[
    {"id":"mv1","type":"protest","title":"Anti-austerity rally","location":"Athens, Greece","country":"GR","size":"40,000+","sentiment":"HIGH","scale":82,"lat":37.98,"lon":23.73,"age_h":2},
    {"id":"mv2","type":"strike","title":"Railway workers strike","location":"Paris, France","country":"FR","size":"National","sentiment":"MED","scale":55,"lat":48.85,"lon":2.35,"age_h":6},
    {"id":"mv3","type":"civil","title":"Democracy march","location":"Seoul, South Korea","country":"KR","size":"120,000+","sentiment":"HIGH","scale":90,"lat":37.57,"lon":126.98,"age_h":1},
    {"id":"mv4","type":"protest","title":"Climate blockades","location":"Berlin, Germany","country":"DE","size":"8,000","sentiment":"MED","scale":40,"lat":52.52,"lon":13.41,"age_h":18},
    {"id":"mv5","type":"strike","title":"Dockworkers walkout","location":"Buenos Aires","country":"AR","size":"Port-wide","sentiment":"MED","scale":48,"lat":-34.61,"lon":-58.38,"age_h":8},
    {"id":"mv6","type":"civil","title":"Farmers protest","location":"New Delhi, India","country":"IN","size":"200,000+","sentiment":"CRIT","scale":95,"lat":28.61,"lon":77.21,"age_h":3},
    {"id":"mv7","type":"protest","title":"Cost-of-living rally","location":"London, UK","country":"GB","size":"25,000","sentiment":"MED","scale":50,"lat":51.51,"lon":-0.12,"age_h":14},
]
CHALLENGES=[
    {"id":"c1","pts":250,"difficulty":"ANALYST","color":"#00c8ff","title":"SEISMIC TRAIL",
     "question":"A M6.1 earthquake struck N. Japan at 55km depth near the Pacific coast. PRIMARY secondary hazard?",
     "clues":["Depth <70km = shallow — high surface disruption","Pacific Ring of Fire: active subduction zone","JMA issued Level 3 coastal alert"],
     "options":["Volcanic co-eruption","Tsunami risk within 300km coastline","Liquefaction in inland valleys","Atmospheric pressure wave"],
     "correct":1,"explain":"Shallow subduction-zone quakes near coastlines carry the highest tsunami risk. JMA auto-issues coastal warnings for M6+ shallow events."},
    {"id":"c2","pts":400,"difficulty":"AGENT","color":"#9d6eff","title":"CIVIL UNREST ASSESSMENT",
     "question":"New Delhi protest: 200,000+ over 72h, CRITICAL. Which indicator MOST reliably signals imminent escalation?",
     "clues":["Duration >72h → escalation 3× baseline (ACLED)","Government response: no dialogue","Coordinated hashtags across 12 states"],
     "options":["Aerial crowd-density photograph","Mobile network traffic spike","Absence of counter-protests","Regional weather forecast"],
     "correct":1,"explain":"Mobile network traffic anomalies reveal real-time C2 coordination — key ACLED escalation precursor (78% correlation in documented cases)."},
    {"id":"c3","pts":350,"difficulty":"ANALYST","color":"#ff3d5a","title":"CONFLICT INTELLIGENCE",
     "question":"Satellite imagery shows abnormal vehicle movement along a supply route 48h before a documented offensive. Which OSINT method best corroborates this?",
     "clues":["Vehicle movement → logistics buildup signal","48h lead time consistent with pre-attack staging","Dual-use infrastructure complicates attribution"],
     "options":["Social media geolocation of unit photos","Nighttime light increase in forward areas","Radio frequency spectrum anomaly","All three used in combination — convergent OSINT"],
     "correct":3,"explain":"Convergent OSINT — combining SAR imagery, SOCMINT, SIGINT indicators, and NIGHTINT — dramatically reduces false positive rates. No single source is sufficient for confident assessment."},
    {"id":"c4","pts":500,"difficulty":"HANDLER","color":"#ffb400","title":"MULTI-SOURCE FUSION",
     "question":"Correlating M5.8 Vanuatu + La Niña ENSO + New Delhi civil movement — which systemic risk does this triad indicate?",
     "clues":["La Niña → below-average monsoon over South Asia","M5.8 disrupts agricultural infrastructure","200,000+ farmers protesting crop prices"],
     "options":["Currency devaluation","Food security / supply chain stress","Tourism collapse","Tech export restrictions"],
     "correct":1,"explain":"Multi-source fusion: seismic disruption + La Niña drought + politically active farming communities = compound food-security signal (cf. 2010–11 Arab Spring pre-conditions)."},
]
LEADERBOARD=[
    ("vectorx","HANDLER",18450,"#ff3d5a"),("sigint_reaper","AGENT",16220,"#9d6eff"),
    ("phantomhex","AGENT",14875,"#ffb400"),("n0de_k1ller","ANALYST",13100,"#ff8c42"),
    ("ghost_proto","ANALYST",9800,"#3d5a75"),
]
NEWS_SOURCES=[
    {"name":"Reuters World","cat":"global","color":"#ff8c42","rss":"https://feeds.reuters.com/reuters/worldNews","desc":"Global wire, 170+ countries"},
    {"name":"BBC World","cat":"global","color":"#bb1919","rss":"http://feeds.bbci.co.uk/news/world/rss.xml","desc":"BBC international"},
    {"name":"Al Jazeera","cat":"global","color":"#00873c","rss":"https://www.aljazeera.com/xml/rss/all.xml","desc":"Qatar-based, ME & Global South"},
    {"name":"AP News","cat":"global","color":"#cc0000","rss":"https://rsshub.app/apnews/topics/apf-WorldNews","desc":"Associated Press breaking"},
    {"name":"NASA JPL","cat":"science","color":"#0b3d91","rss":"https://www.jpl.nasa.gov/feeds/news","desc":"NASA Jet Propulsion Lab"},
    {"name":"USGS News","cat":"science","color":"#4caf50","rss":"https://www.usgs.gov/news/science-news/rss.xml","desc":"USGS hazards & science"},
    {"name":"Phys.org Earth","cat":"science","color":"#1a7fc1","rss":"https://phys.org/rss-feed/earth-news/","desc":"Earth science research"},
    {"name":"Foreign Policy","cat":"geopolitics","color":"#8b1a1a","rss":"https://foreignpolicy.com/feed/","desc":"International affairs"},
    {"name":"The Diplomat","cat":"geopolitics","color":"#1a3a5c","rss":"https://thediplomat.com/feed/","desc":"Asia-Pacific geopolitics"},
    {"name":"Defense One","cat":"geopolitics","color":"#444","rss":"https://www.defenseone.com/rss/all/","desc":"Defence & security"},
    {"name":"ACLED Updates","cat":"conflict","color":"#c00","rss":"https://acleddata.com/feed/","desc":"Armed conflict event data"},
    {"name":"ISW Daily","cat":"conflict","color":"#800020","rss":"https://understandingwar.org/rss.xml","desc":"Institute for Study of War"},
    {"name":"CSIS News","cat":"conflict","color":"#003366","rss":"https://www.csis.org/rss/analysis","desc":"Center for Strategic & Intl Studies"},
    {"name":"Carbon Brief","cat":"climate","color":"#1b5e20","rss":"https://www.carbonbrief.org/feed","desc":"Climate policy analysis"},
    {"name":"SpaceWeather","cat":"spaceweather","color":"#4a148c","rss":"https://spaceweather.com/index.xml","desc":"Solar activity & storms"},
    {"name":"NOAA SWPC","cat":"spaceweather","color":"#0d47a1","rss":"https://www.swpc.noaa.gov/news/rss.xml","desc":"NOAA Space Weather"},
]
CATEGORIES=["ALL","global","science","geopolitics","conflict","climate","spaceweather"]
CAT_LABELS={"ALL":"All Sources","global":"🌐 Global Wire","science":"🔬 Earth Science","geopolitics":"🗺 Geopolitics","conflict":"⚔ Conflict","climate":"🌱 Climate","spaceweather":"☀ Space Weather"}
CAT_COLORS={"global":"b-orange","science":"b-green","geopolitics":"b-red","conflict":"b-red","climate":"b-green","spaceweather":"b-violet","ALL":"b-cyan"}
CAT_NC={"global":"nc-general","science":"nc-seismic","geopolitics":"nc-civil","conflict":"nc-seismic","climate":"nc-volcanic","spaceweather":"nc-solar","general":"nc-general"}


# ─────────────────────────────────────────────
# CHART BUILDERS
# ─────────────────────────────────────────────
def kp_chart(s):
    f=go.Figure()
    f.add_trace(go.Scatter(x=list(range(len(s))),y=s,mode="lines",line=dict(color="#00c8ff",width=1.5),fill="tozeroy",fillcolor="rgba(0,200,255,.07)"))
    f.add_hline(y=5,line_dash="dash",line_color="rgba(255,61,90,.45)",line_width=1)
    f.update_layout(height=80,margin=dict(l=0,r=0,t=0,b=0),**bg_chart(),showlegend=False,xaxis=dict(visible=False),yaxis=dict(visible=False,range=[0,9]))
    return f

def mag_hist(eq):
    f=go.Figure(go.Histogram(x=eq["mag"],nbinsx=14,marker_color="#00c8ff",opacity=.65,marker_line_width=0))
    f.update_layout(height=140,margin=dict(l=0,r=0,t=0,b=0),**bg_chart(),xaxis=ax(),yaxis=ax(),bargap=.08)
    return f

def mv_bar(mv):
    df=pd.DataFrame(mv).sort_values("scale",ascending=True)
    cols=df["sentiment"].map({"CRIT":"#ff3d5a","HIGH":"#ff8c42","MED":"#ffb400"})
    f=go.Figure(go.Bar(y=df["location"].str.split(",").str[0],x=df["scale"],orientation="h",marker_color=cols,marker_line_width=0))
    f.update_layout(height=210,margin=dict(l=0,r=0,t=0,b=0),**bg_chart(),xaxis=ax(range=[0,100]),yaxis=dict(color="#dde8f5",tickfont_size=9))
    return f

def mag_donut(eq):
    b={"M2.5–3.4":len(eq[(eq.mag>=2.5)&(eq.mag<3.5)]),"M3.5–4.4":len(eq[(eq.mag>=3.5)&(eq.mag<4.5)]),
       "M4.5–5.4":len(eq[(eq.mag>=4.5)&(eq.mag<5.5)]),"M5.5+":len(eq[eq.mag>=5.5])}
    f=go.Figure(go.Pie(labels=list(b.keys()),values=list(b.values()),hole=.6,marker_colors=["#00e676","#00c8ff","#ffb400","#ff3d5a"],textfont_size=10,textinfo="label+percent"))
    f.update_layout(height=200,margin=dict(l=0,r=0,t=0,b=0),**bg_chart(),showlegend=False)
    return f

def escalation_gauge(val, label, color):
    """Returns a Plotly gauge figure."""
    f=go.Figure(go.Indicator(
        mode="gauge+number",value=val,
        gauge=dict(
            axis=dict(range=[0,100],tickcolor="#3d5a75",tickfont=dict(size=9,color="#3d5a75")),
            bar=dict(color=color,thickness=.25),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            steps=[
                dict(range=[0,30],color="rgba(0,230,118,.08)"),
                dict(range=[30,60],color="rgba(255,180,0,.08)"),
                dict(range=[60,80],color="rgba(255,140,66,.08)"),
                dict(range=[80,100],color="rgba(255,61,90,.08)"),
            ],
            threshold=dict(line=dict(color=color,width=2),thickness=.75,value=val)
        ),
        number=dict(font=dict(family="Bebas Neue",size=38,color=color),suffix=""),
        title=dict(text=label,font=dict(family="IBM Plex Mono",size=9,color="#3d5a75")),
    ))
    f.update_layout(height=180,margin=dict(l=10,r=10,t=30,b=10),**bg_chart())
    return f

def conflict_timeline_chart(tl):
    dates=[t["date"] for t in tl]
    events=[t["event"] for t in tl]
    types=[t["type"] for t in tl]
    type_colors={"escalation":"#ff3d5a","milestone":"#00c8ff","diplomatic":"#00e676","setback":"#ffb400","ongoing":"#9d6eff"}
    colors=[type_colors.get(t,"#3d5a75") for t in types]
    f=go.Figure()
    f.add_trace(go.Scatter(x=dates,y=[1]*len(dates),mode="markers+text",
        text=[e[:30]+"…" if len(e)>30 else e for e in events],
        textposition="top center",textfont=dict(size=9,color="#3d5a75"),
        marker=dict(size=10,color=colors,line=dict(width=1,color="#0d1e30")),
        hovertext=events,hoverinfo="text+x"))
    f.add_trace(go.Scatter(x=dates,y=[1]*len(dates),mode="lines",
        line=dict(color="#0d1e30",width=2),showlegend=False))
    f.update_layout(height=180,margin=dict(l=0,r=0,t=30,b=0),**bg_chart(),
        showlegend=False,xaxis=dict(color="#3d5a75",tickfont_size=9,gridcolor="#0d1e30"),
        yaxis=dict(visible=False),hovermode="x")
    return f

def casualty_comparison():
    conflicts=list(CONFLICTS.keys())
    cas=[CONFLICTS[c]["casualties_total"] for c in conflicts]
    dis=[CONFLICTS[c]["displaced"] for c in conflicts]
    short=[c.split(" ")[0][:12] for c in conflicts]
    f=go.Figure()
    f.add_trace(go.Bar(name="Casualties",x=short,y=cas,marker_color="#ff3d5a",marker_line_width=0,opacity=.8))
    f.add_trace(go.Bar(name="Displaced",x=short,y=dis,marker_color="#ffb400",marker_line_width=0,opacity=.6))
    f.update_layout(height=220,margin=dict(l=0,r=0,t=10,b=0),**bg_chart(),barmode="group",
        legend=dict(font=dict(color="#3d5a75",size=9),bgcolor="rgba(0,0,0,0)"),
        xaxis=ax(),yaxis=ax())
    return f

def intensity_scatter():
    conflicts=list(CONFLICTS.keys())
    esc=[CONFLICTS[c]["escalation"] for c in conflicts]
    cas=[CONFLICTS[c]["casualties_total"] for c in conflicts]
    dis=[CONFLICTS[c]["displaced"] for c in conflicts]
    cols=["#ff3d5a","#ff8c42","#ffb400","#00c8ff"]
    f=go.Figure(go.Scatter(
        x=esc,y=cas,mode="markers+text",
        text=[c.split(" ")[0] for c in conflicts],
        textposition="top center",
        textfont=dict(size=9,color="#3d5a75"),
        marker=dict(size=[d//50000 for d in dis],sizemin=12,color=cols,
                    line=dict(color="#0d1e30",width=1),opacity=.85),
        hovertext=conflicts,hoverinfo="text"
    ))
    f.update_layout(height=250,margin=dict(l=0,r=0,t=10,b=0),**bg_chart(),
        xaxis=dict(**ax(),title="Escalation Index"),yaxis=dict(**ax(),title="Estimated Casualties"),
        showlegend=False)
    return f

def media_bias_chart(sources):
    names=[s["name"] for s in sources]
    rel=[s["reliability"] for s in sources]
    cols=[]
    for s in sources:
        b=s["bias"].lower()
        if "state" in b or "junta" in b: cols.append("#ff3d5a")
        elif "pro-" in b: cols.append("#ffb400")
        elif "centre" in b or "center" in b: cols.append("#00c8ff")
        elif "left" in b: cols.append("#9d6eff")
        elif "right" in b: cols.append("#ff8c42")
        else: cols.append("#3d5a75")
    f=go.Figure(go.Bar(x=names,y=rel,marker_color=cols,marker_line_width=0,opacity=.8,
        text=rel,textfont=dict(size=9,color="#dde8f5"),textposition="outside"))
    f.update_layout(height=180,margin=dict(l=0,r=0,t=10,b=30),**bg_chart(),
        xaxis=dict(**ax(),tickangle=-30),yaxis=dict(**ax(),range=[0,105],title="Reliability %"),
        showlegend=False)
    return f

def supply_arc_layer(supply_lines):
    if not supply_lines: return []
    df=pd.DataFrame(supply_lines)
    df["color"]=df["type"].map({
        "Military Aid":[255,61,90,180],"Arms/Funding":[255,61,90,180],
        "RSF Support":[255,140,66,160],"SAF Support":[0,200,255,160],
        "Junta Support":[255,61,90,160],"Arms Supply":[255,180,0,160],
        "Humanitarian":[0,230,118,160],
    }).apply(lambda x: x if isinstance(x,list) else [61,90,117,140])
    return [pdk.Layer("ArcLayer",data=df,get_source_position=["from_lon","from_lat"],
                       get_target_position=["to_lon","to_lat"],get_source_color="color",
                       get_target_color="color",get_width=2,pickable=True,
                       auto_highlight=True)]

def build_conflict_map(conflict_key, show_supply=True):
    c=CONFLICTS[conflict_key]
    inc_df=pd.DataFrame(c["incidents"])
    sev_col={"CRITICAL":[255,61,90,230],"HIGH":[255,140,66,200],"MED":[255,180,0,180],"LOW":[0,230,118,150],"INFO":[0,200,255,120]}
    inc_df["color"]=inc_df["severity"].map(sev_col)
    inc_df["radius"]=inc_df["severity"].map({"CRITICAL":60000,"HIGH":45000,"MED":35000,"LOW":25000,"INFO":20000})
    inc_df["tip"]=inc_df.apply(lambda r:f"{INCIDENT_ICONS.get(r['type'],'●')} {r['title']} | {r['loc']} | {r['severity']} | {r['date']} | Casualties: {r['casualties']}",axis=1)
    layers=[pdk.Layer("ScatterplotLayer",data=inc_df,get_position=["lon","lat"],get_radius="radius",
                       get_fill_color="color",get_line_color=[255,255,255,40],line_width_min_pixels=1,
                       pickable=True,auto_highlight=True)]
    if show_supply:
        layers.extend(supply_arc_layer(c["supply_lines"]))
    cx=np.mean([i["lon"] for i in c["incidents"]])
    cy=np.mean([i["lat"] for i in c["incidents"]])
    return pdk.Deck(layers=layers,
                    initial_view_state=pdk.ViewState(latitude=cy,longitude=cx,zoom=4,pitch=20),
                    map_style="mapbox://styles/mapbox/dark-v11",
                    tooltip={"text":"{tip}","style":{"backgroundColor":"#070e1a","color":"#dde8f5","border":"1px solid rgba(255,61,90,.3)","fontFamily":"IBM Plex Mono","fontSize":"11px"}},
                    height=400)

def build_global_conflict_map():
    rows=[]
    for name,c in CONFLICTS.items():
        for inc in c["incidents"]:
            rows.append({**inc,"conflict":name})
    df=pd.DataFrame(rows)
    sev_col={"CRITICAL":[255,61,90,230],"HIGH":[255,140,66,200],"MED":[255,180,0,180],"LOW":[0,230,118,150],"INFO":[0,200,255,120]}
    df["color"]=df["severity"].map(sev_col)
    df["radius"]=df["severity"].map({"CRITICAL":90000,"HIGH":65000,"MED":50000,"LOW":35000,"INFO":25000})
    df["tip"]=df.apply(lambda r:f"⚔ {r['conflict']} | {r['title']} | {r['loc']} | {r['severity']}",axis=1)
    return pdk.Deck(
        layers=[pdk.Layer("ScatterplotLayer",data=df,get_position=["lon","lat"],get_radius="radius",
                           get_fill_color="color",pickable=True,auto_highlight=True)],
        initial_view_state=pdk.ViewState(latitude=30,longitude=30,zoom=1.8,pitch=0),
        map_style="mapbox://styles/mapbox/dark-v11",
        tooltip={"text":"{tip}","style":{"backgroundColor":"#070e1a","color":"#dde8f5","border":"1px solid rgba(255,61,90,.3)","fontFamily":"IBM Plex Mono","fontSize":"11px"}},
        height=360)

# ─────────────────────────────────────────────
# AI CALLER
# ─────────────────────────────────────────────
def call_ai(prompt,provider,api_key):
    if provider=="groq" and api_key:
        try:
            r=requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                json={"model":"llama-3.1-8b-instant","max_tokens":400,
                      "messages":[{"role":"system","content":"You are a concise OSINT intelligence analyst. Respond in plain text, no markdown, max 380 words."},
                                   {"role":"user","content":prompt}]},timeout=14)
            r.raise_for_status(); return r.json()["choices"][0]["message"]["content"]
        except Exception as e: return f"[Groq error: {e}]"
    if provider=="ollama":
        try:
            r=requests.post("http://localhost:11434/api/generate",json={"model":"llama3","prompt":prompt,"stream":False},timeout=25)
            return r.json().get("response","No response")
        except Exception as e: return f"[Ollama error: {e}]"
    if provider=="openrouter" and api_key:
        try:
            r=requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization":f"Bearer {api_key}","HTTP-Referer":"https://osint-arena.app","Content-Type":"application/json"},
                json={"model":"meta-llama/llama-3.1-8b-instruct:free","max_tokens":400,
                      "messages":[{"role":"user","content":prompt}]},timeout=16)
            r.raise_for_status(); return r.json()["choices"][0]["message"]["content"]
        except Exception as e: return f"[OpenRouter error: {e}]"
    return "⚠  Configure an AI provider in the sidebar (Groq / Ollama / OpenRouter)."


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
    st.markdown('<div class="wordmark">OSINT<em>ARENA</em></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;letter-spacing:.18em;color:var(--muted);font-weight:700;margin:4px 0 16px">INTELLIGENCE PLATFORM v3</div>', unsafe_allow_html=True)

    tn,tc,tcol=get_tier(st.session_state.score)
    nt={"RECRUIT":2000,"ANALYST":5000,"AGENT":10000,"HANDLER":10000}[tn]
    xp_pct=min(100,int(st.session_state.score/nt*100))
    st.markdown(f"""
    <div class="m-panel">
      <div class="m-label">Analyst Status</div>
      <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:5px">
        <div class="m-val m-violet" style="font-size:28px">{st.session_state.score:,}</div>
        <div class="badge {tc}">{tn}</div>
      </div>
      <div class="xp-track"><div class="xp-fill" style="width:{xp_pct}%"></div></div>
      <div class="m-sub" style="margin-top:4px">{xp_pct}% → {nt:,} XP</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-label">AI Configuration</div>', unsafe_allow_html=True)
    prov=st.selectbox("Provider",["groq","ollama","openrouter","none"])
    st.session_state.ai_provider=prov
    if prov in ("groq","openrouter"):
        st.session_state.ai_key=st.text_input("API Key",type="password",placeholder="sk-…")
    elif prov=="ollama":
        st.info("Ollama: localhost:11434")

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-label">Map Layers</div>', unsafe_allow_html=True)
    show_seis=st.toggle("Seismic Events",value=True)
    show_volc=st.toggle("Volcanic / EONET",value=True)
    show_mvmt=st.toggle("Civil Movements",value=True)
    show_heat=st.toggle("Heatmap Mode",value=False)
    show_supp=st.toggle("Supply Arc Lines",value=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;gap:5px">
      <div style="font-family:var(--fm);font-size:10px;color:var(--muted);display:flex;gap:7px;align-items:center"><span class="pulse p-green"></span>USGS Earthquake API</div>
      <div style="font-family:var(--fm);font-size:10px;color:var(--muted);display:flex;gap:7px;align-items:center"><span class="pulse p-green"></span>NASA EONET v3</div>
      <div style="font-family:var(--fm);font-size:10px;color:var(--muted);display:flex;gap:7px;align-items:center"><span class="pulse p-amber"></span>NOAA SWPC Kp-index</div>
      <div style="font-family:var(--fm);font-size:10px;color:var(--muted);display:flex;gap:7px;align-items:center"><span class="pulse p-cyan"></span>{len(NEWS_SOURCES)} RSS feeds (10min cache)</div>
      <div style="font-family:var(--fm);font-size:10px;color:var(--muted);display:flex;gap:7px;align-items:center"><span class="pulse p-red"></span>{len(CONFLICTS)} conflict theatres tracked</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    if st.button("⟳  Refresh All Feeds",use_container_width=True):
        st.cache_data.clear(); st.rerun()


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
m5p=eq_df[eq_df["mag"]>=5.0]; crit_mv=[m for m in MOVEMENTS if m["sentiment"]=="CRIT"]; kp=kp_data["kp"]
active_conflicts=len([c for c in CONFLICTS.values() if c["status"]=="ACTIVE"])
total_cas=sum(c["casualties_total"] for c in CONFLICTS.values())

st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:2px">
  <div>
    <div class="wordmark">OSINT<em>ARENA</em></div>
    <div style="font-size:10px;letter-spacing:.18em;color:var(--muted);font-weight:700;margin-top:2px">GLOBAL INTELLIGENCE OPERATIONS CENTER — v3</div>
  </div>
</div>
<div class="status-row">
  <span><span class="pulse p-green"></span>FEEDS LIVE</span>
  <span><span class="pulse p-cyan"></span>{len(eq_df)} SEISMIC 24H</span>
  <span><span class="pulse p-red"></span>{active_conflicts} ACTIVE CONFLICTS</span>
  <span><span class="pulse p-red"></span>{total_cas:,} TOTAL CASUALTIES</span>
  <span><span class="pulse p-{'red' if kp>=5 else 'amber'}"></span>Kp {kp:.1f}</span>
  <span class="utc-clock">{utc_now}</span>
</div>""", unsafe_allow_html=True)

# TICKER
ticker_bits=(
    [f'<span class="t-red t-hi">⚔ {n}: {c["intensity"]}</span>' for n,c in CONFLICTS.items()]+
    [f'<span class="t-red">M{r.mag} {r.place[:28]}</span>' for _,r in eq_df.nlargest(5,"mag").iterrows()]+
    [f'<span class="t-amb">✊ {m["title"]} — {m["location"]}</span>' for m in MOVEMENTS[:4]]
)
tc_str='<span class="t-sep"> ◈ </span>'.join(ticker_bits)
st.markdown(f'<div class="ticker-wrap"><div class="ticker-inner">{tc_str}<span class="t-sep"> ◈ </span>{tc_str}</div></div>',unsafe_allow_html=True)

# TOP METRICS
cols=st.columns(6)
with cols[0]: st.metric("Active Conflicts",active_conflicts,delta="LIVE")
with cols[1]: st.metric("Total Casualties",f"{total_cas:,}",delta="All theatres")
with cols[2]: st.metric("Seismic Events 24h",len(eq_df),delta=f"M5.0+: {len(m5p)}")
with cols[3]: st.metric("Civil Movements",len(MOVEMENTS),delta=f"Critical: {len(crit_mv)}")
with cols[4]: st.metric("Geomagnetic Kp",f"{kp:.1f}",delta="Storm if ≥5.0")
with cols[5]: st.metric("Analyst XP",f"{st.session_state.score:,}",delta=get_tier(st.session_state.score)[0])

st.markdown("---")


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab_conflict, tab_earth, tab_civil, tab_news, tab_arena, tab_ai = st.tabs([
    "⚔  CONFLICT DASHBOARD",
    "🌍  EARTH SIGNALS",
    "✊  CIVIL MOVEMENTS",
    "📡  LIVE NEWS",
    "🎯  ARENA",
    "🤖  AI ANALYST",
])


# ══════════════════════════════════════════════════════════════
# TAB 1 — CONFLICT DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab_conflict:

    # ── CONFLICT SELECTOR ROW ────────────────────────────────
    conflict_names=list(CONFLICTS.keys())
    sel_col1,sel_col2=st.columns([2,1],gap="medium")

    with sel_col1:
        st.markdown('<div class="sec-label">Select Theatre</div>', unsafe_allow_html=True)
        theatre_pills=st.radio("Theatre",conflict_names,horizontal=True,label_visibility="collapsed")
        st.session_state.selected_conflict=theatre_pills

    C=CONFLICTS[st.session_state.selected_conflict]

    with sel_col2:
        int_col={"CRITICAL":"m-red","HIGH":"m-orange","MED":"m-amber"}
        st.markdown(f"""
        <div class="m-panel" style="display:flex;align-items:center;gap:16px;padding:10px 16px">
          <div>
            <div class="m-label">Status</div>
            <div class="m-val {int_col.get(C['intensity'],'m-cyan')}" style="font-size:20px">{C['status']}</div>
          </div>
          <div>
            <div class="m-label">Intensity</div>
            <div class="m-val {int_col.get(C['intensity'],'m-cyan')}" style="font-size:20px">{C['intensity']}</div>
          </div>
          <div>
            <div class="m-label">Since</div>
            <div style="font-family:var(--fm);font-size:12px;color:var(--muted)">{C['start']}</div>
          </div>
          <div>
            <div class="m-label">Ceasefire</div>
            <div class="badge {'b-green' if C['ceasefire'] else 'b-red'}" style="font-size:11px">{'YES' if C['ceasefire'] else 'NO'}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ── DESCRIPTION ─────────────────────────────────────────
    st.markdown(f"""
    <div class="gcard" style="margin-bottom:12px">
      <div style="font-family:var(--fm);font-size:10px;color:var(--muted);margin-bottom:4px">{C['region'].upper()}</div>
      <div style="font-size:13px;color:var(--text);line-height:1.6">{C['description']}</div>
    </div>""", unsafe_allow_html=True)

    # ── ROW 1: MAP + ESCALATION + CASUALTIES ────────────────
    map_c, esc_c, cas_c = st.columns([3,1,1], gap="medium")

    with map_c:
        st.markdown('<div class="sec-label">Incident Map — ' + st.session_state.selected_conflict + '</div>', unsafe_allow_html=True)
        st.pydeck_chart(build_conflict_map(st.session_state.selected_conflict, show_supp), use_container_width=True)

    with esc_c:
        st.markdown('<div class="sec-label">Escalation Index</div>', unsafe_allow_html=True)
        esc=C["escalation"]
        esc_col="#ff3d5a" if esc>=80 else "#ff8c42" if esc>=60 else "#ffb400" if esc>=40 else "#00e676"
        esc_lbl="CRITICAL" if esc>=80 else "HIGH" if esc>=60 else "ELEVATED" if esc>=40 else "LOW"
        st.plotly_chart(escalation_gauge(esc,"ESCALATION INDEX /100",esc_col),use_container_width=True,config={"displayModeBar":False})
        st.markdown(f"""
        <div class="m-panel" style="text-align:center;padding:10px">
          <div class="badge {'b-red' if esc>=80 else 'b-orange' if esc>=60 else 'b-amber'}" style="font-size:11px;margin:auto">{esc_lbl}</div>
          <div class="m-sub" style="margin-top:6px">Ceasefire: <span style="color:{'var(--green)' if C['ceasefire'] else 'var(--red)'}">{'IN EFFECT' if C['ceasefire'] else 'NONE'}</span></div>
        </div>""", unsafe_allow_html=True)

    with cas_c:
        st.markdown('<div class="sec-label">Human Cost</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="m-panel" style="text-align:center;padding:14px 10px">
          <div class="m-label">Estimated Casualties</div>
          <div class="m-val m-red" style="font-size:26px">{C['casualties_total']:,}</div>
        </div>
        <div class="m-panel" style="text-align:center;padding:14px 10px">
          <div class="m-label">Displaced Persons</div>
          <div class="m-val m-amber" style="font-size:26px">{C['displaced']:,}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── ROW 2: INCIDENTS + FACTIONS ─────────────────────────
    inc_c, fac_c = st.columns([3,2], gap="medium")

    with inc_c:
        st.markdown('<div class="sec-label">Incident Feed — Recent Events</div>', unsafe_allow_html=True)
        inc_filter=st.radio("Incident type",["ALL","airstrike","ground","drone","naval","rocket","cyber","humanitarian","diplomatic"],
                             horizontal=True,label_visibility="collapsed",key="inc_filter")
        for inc in C["incidents"]:
            if inc_filter!="ALL" and inc["type"]!=inc_filter: continue
            icon=INCIDENT_ICONS.get(inc["type"],"●")
            ic=INCIDENT_COLORS.get(inc["type"],"rgba(61,90,117,.12)")
            sev_cls=SEV_BADGE.get(inc["severity"],"b-muted")
            cas_note=f"  ·  {inc['casualties']} cas." if inc["casualties"]>0 else ""
            st.markdown(f"""
            <div class="incident-row">
              <div class="inc-icon" style="background:{ic}">{icon}</div>
              <div class="inc-body">
                <div class="inc-title">{inc['title']}</div>
                <div class="inc-meta">{inc['loc']} &nbsp;·&nbsp; {inc['date']}{cas_note}</div>
                <div class="inc-badge-row">
                  <div class="badge {sev_cls}">{inc['severity']}</div>
                  <div class="badge b-muted">{inc['type'].upper()}</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    with fac_c:
        st.markdown('<div class="sec-label">Faction Tracker</div>', unsafe_allow_html=True)
        for fac in C["factions"]:
            st.markdown(f"""
            <div class="conflict-card">
              <div class="cc-header">
                <div style="display:flex;align-items:center;gap:8px">
                  <div style="width:10px;height:10px;border-radius:50%;background:{fac['color']}"></div>
                  <div class="cc-title">{fac['name']}</div>
                </div>
                <div class="badge {'b-red' if fac['status'] in ('Offensive','Advancing') else 'b-cyan' if fac['status']=='Defending' else 'b-amber'}">{fac['status']}</div>
              </div>
              <div class="cc-body" style="padding:10px 14px">
                <div style="display:flex;gap:12px;margin-bottom:8px;flex-wrap:wrap">
                  <div>
                    <div class="m-label" style="font-size:8px">Territory Control</div>
                    <div style="font-family:var(--fm);font-size:12px;color:{fac['color']}">{fac['territory_pct']}%</div>
                  </div>
                  <div>
                    <div class="m-label" style="font-size:8px">Strength</div>
                    <div style="font-family:var(--fm);font-size:12px;color:var(--text)">{fac['strength']}</div>
                  </div>
                  <div>
                    <div class="m-label" style="font-size:8px">Support</div>
                    <div style="font-family:var(--fm);font-size:11px;color:var(--muted)">{', '.join(fac['support'][:3])}</div>
                  </div>
                </div>
                <div class="scale-track" style="height:4px;margin:4px 0 6px">
                  <div class="scale-fill" style="width:{fac['territory_pct']}%;background:{fac['color']}55"></div>
                </div>
                <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">Key assets: {', '.join(fac['weapons'][:3])}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── ROW 3: TIMELINE + SUPPLY ARCS ───────────────────────
    tl_c, supply_c = st.columns([2,1], gap="medium")

    with tl_c:
        st.markdown('<div class="sec-label">Conflict Timeline</div>', unsafe_allow_html=True)
        st.plotly_chart(conflict_timeline_chart(C["timeline"]),use_container_width=True,config={"displayModeBar":False})
        st.markdown('<div class="sec-label" style="margin-top:8px">Chronological Events</div>', unsafe_allow_html=True)
        tl_type_col={"escalation":"var(--red)","milestone":"var(--cyan)","diplomatic":"var(--green)","setback":"var(--amber)","ongoing":"var(--violet)"}
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        for item in reversed(C["timeline"]):
            col=tl_type_col.get(item["type"],"var(--muted)")
            st.markdown(f"""
            <div class="tl-item">
              <div class="tl-dot" style="background:{col};border-color:{col}44"></div>
              <div class="tl-date">{item['date']}</div>
              <div class="tl-text">{item['event']}</div>
              <div class="tl-tag" style="color:{col}">{item['type'].upper()}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with supply_c:
        st.markdown('<div class="sec-label">Supply & Support Lines</div>', unsafe_allow_html=True)
        for sl in C["supply_lines"]:
            t_col="#ff3d5a" if "Mil" in sl["type"] or "Arms" in sl["type"] or "RSF" in sl["type"] or "Junta" in sl["type"] else "#00e676"
            st.markdown(f"""
            <div class="gcard" style="padding:10px 12px;margin-bottom:6px">
              <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
                <div class="badge {'b-red' if t_col=='#ff3d5a' else 'b-green'}">{sl['type']}</div>
                <div style="font-family:var(--fm);font-size:10px;color:var(--muted)">{sl['provider']}</div>
              </div>
              <div class="sig-meta" style="margin-top:5px">
                ({sl['from_lat']:.1f}, {sl['from_lon']:.1f}) → ({sl['to_lat']:.1f}, {sl['to_lon']:.1f})
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-label" style="margin-top:14px">Media Reliability</div>', unsafe_allow_html=True)
        st.plotly_chart(media_bias_chart(C["media_sources"]),use_container_width=True,config={"displayModeBar":False})

        # Bias legend
        st.markdown("""
        <div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:4px">
          <div style="font-family:var(--fm);font-size:9px;color:#00c8ff">■ Centre</div>
          <div style="font-family:var(--fm);font-size:9px;color:#9d6eff">■ Centre-Left</div>
          <div style="font-family:var(--fm);font-size:9px;color:#ff8c42">■ Right</div>
          <div style="font-family:var(--fm);font-size:9px;color:#ffb400">■ Pro-party</div>
          <div style="font-family:var(--fm);font-size:9px;color:#ff3d5a">■ State media</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── ROW 4: CROSS-CONFLICT ANALYTICS ─────────────────────
    st.markdown('<div class="sec-label">Cross-Theatre Analytics</div>', unsafe_allow_html=True)
    cc1,cc2,cc3=st.columns(3,gap="medium")

    with cc1:
        st.markdown("**Casualties & Displacement**")
        st.plotly_chart(casualty_comparison(),use_container_width=True,config={"displayModeBar":False})

    with cc2:
        st.markdown("**Escalation vs Casualties**")
        st.plotly_chart(intensity_scatter(),use_container_width=True,config={"displayModeBar":False})

    with cc3:
        st.markdown("**Global Conflict Map**")
        st.pydeck_chart(build_global_conflict_map(),use_container_width=True)

    st.markdown("---")

    # ── ROW 5: RISK MATRIX ──────────────────────────────────
    st.markdown('<div class="sec-label">Risk Assessment Matrix</div>', unsafe_allow_html=True)
    risk_cols=st.columns(len(CONFLICTS),gap="small")
    risk_dims=["Escalation","Humanitarian","Regional Spillover","Nuclear/WMD","Ceasefire Probability","External Intervention"]
    risk_scores={
        "Ukraine–Russia War":  [87,75,80,45,15,82],
        "Gaza Conflict":       [92,95,78,20,20,68],
        "Sudan Civil War":     [74,90,55,5,25,35],
        "Myanmar Civil War":   [68,72,40,5,30,22],
    }
    for i,(cname,rcol) in enumerate(zip(CONFLICTS.keys(),risk_cols)):
        scores=risk_scores.get(cname,[50]*6)
        with rcol:
            short=cname.split(" ")[0]
            st.markdown(f'<div style="font-family:var(--fm);font-size:10px;color:var(--muted);margin-bottom:8px;text-align:center">{short}</div>',unsafe_allow_html=True)
            for dim,sc in zip(risk_dims,scores):
                bg="rgba(255,61,90,.25)" if sc>=75 else "rgba(255,140,66,.2)" if sc>=50 else "rgba(255,180,0,.15)" if sc>=30 else "rgba(0,230,118,.12)"
                col="#ff3d5a" if sc>=75 else "#ff8c42" if sc>=50 else "#ffb400" if sc>=30 else "#00e676"
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:5px 8px;margin-bottom:4px;border-radius:5px;background:{bg}">
                  <div style="font-family:var(--fm);font-size:9px;color:var(--muted)">{dim[:16]}</div>
                  <div style="font-family:var(--fd);font-size:14px;color:{col}">{sc}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── AI SITREP ────────────────────────────────────────────
    st.markdown('<div class="sec-label">AI Situation Report Generator</div>', unsafe_allow_html=True)
    sitrep_col1,sitrep_col2=st.columns([1,1],gap="medium")

    with sitrep_col1:
        sitrep_type=st.selectbox("Report type",[
            "Executive Summary — 3 paragraphs",
            "Escalation Risk Assessment",
            "Humanitarian Impact Brief",
            "Supply Chain & External Support Analysis",
            "Media Bias & Information Environment Report",
            "Ceasefire / Diplomatic Prospects",
        ],label_visibility="visible")
        if st.button("⚡  Generate Sitrep",use_container_width=True):
            fac_summary="\n".join([f"  - {f['name']} ({f['side']}): {f['status']}, {f['territory_pct']}% territory, supported by {', '.join(f['support'])}" for f in C["factions"]])
            inc_summary="\n".join([f"  - {i['date']} {i['type']}: {i['title']} ({i['severity']}, {i['casualties']} cas.)" for i in C["incidents"][:5]])
            prompt=(f"You are an OSINT analyst. Write a '{sitrep_type}' for the {st.session_state.selected_conflict}.\n\n"
                    f"CONFLICT DATA:\nStatus: {C['status']} | Intensity: {C['intensity']} | Escalation index: {C['escalation']}/100\n"
                    f"Casualties: {C['casualties_total']:,} | Displaced: {C['displaced']:,}\n"
                    f"Ceasefire: {'Yes' if C['ceasefire'] else 'No'}\n\n"
                    f"FACTIONS:\n{fac_summary}\n\n"
                    f"RECENT INCIDENTS:\n{inc_summary}\n\n"
                    f"Write in plain text, professional intelligence style, no markdown. 250-380 words.")
            with st.spinner("Generating sitrep…"):
                result=call_ai(prompt,st.session_state.ai_provider,st.session_state.ai_key)
            st.session_state.conflict_sitrep=result

    with sitrep_col2:
        if st.session_state.conflict_sitrep:
            st.markdown(f'<div class="ai-terminal">{st.session_state.conflict_sitrep}</div>',unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="gcard" style="padding:20px;text-align:center">
              <div style="font-family:var(--fm);font-size:22px;color:var(--muted);margin-bottom:8px">⚔</div>
              <div style="font-family:var(--fm);font-size:11px;color:var(--muted)">Select a report type and click Generate Sitrep.<br>Configure an AI provider in the sidebar to enable.</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 2 — EARTH SIGNALS
# ══════════════════════════════════════════════════════════════
with tab_earth:
    def build_earth_map(eq,eo,mv,heat):
        def mc(m):
            if m>=5.5: return [255,55,85,230]
            if m>=4.5: return [255,180,0,210]
            if m>=3.5: return [0,230,118,185]
            return [0,200,255,160]
        layers=[]
        if not eq.empty:
            ep=eq.copy(); ep["color"]=ep["mag"].apply(mc); ep["radius"]=(ep["mag"]**2.3*16000).clip(12000,260000)
            ep["tip"]=ep.apply(lambda r:f"⬡ M{r['mag']} | {r['place']} | {r['depth_km']}km | {r['time']}",axis=1)
            layers.append(pdk.Layer("ScatterplotLayer",data=ep,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",get_line_color=[255,255,255,40],line_width_min_pixels=1,pickable=True,auto_highlight=True))
        if not eo.empty:
            eo2=eo.copy(); eo2["color"]=[[255,120,50,200]]*len(eo2); eo2["radius"]=75000
            eo2["tip"]=eo2.apply(lambda r:f"▲ {r['title']}",axis=1)
            layers.append(pdk.Layer("ScatterplotLayer",data=eo2,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True))
        if mv:
            mdf=pd.DataFrame(MOVEMENTS); mdf["color"]=mdf["sentiment"].map({"CRIT":[255,55,85,230],"HIGH":[224,92,42,200],"MED":[255,180,0,180]})
            mdf["radius"]=mdf["scale"]*2000; mdf["tip"]=mdf.apply(lambda r:f"✊ {r['title']} | {r['location']}",axis=1)
            layers.append(pdk.Layer("ScatterplotLayer",data=mdf,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True))
        if heat and not eq.empty:
            layers.append(pdk.Layer("HeatmapLayer",data=eq[["lat","lon","mag"]].rename(columns={"mag":"weight"}),get_position=["lon","lat"],get_weight="weight",radiusPixels=48,opacity=.5))
        return pdk.Deck(layers=layers,initial_view_state=pdk.ViewState(latitude=20,longitude=10,zoom=1.3),
                        map_style="mapbox://styles/mapbox/dark-v11",
                        tooltip={"text":"{tip}","style":{"backgroundColor":"#070e1a","color":"#dde8f5","border":"1px solid rgba(0,200,255,.2)","fontFamily":"IBM Plex Mono","fontSize":"11px"}},height=430)

    mc,rc=st.columns([3,1],gap="medium")
    with mc:
        st.pydeck_chart(build_earth_map(eq_df if show_seis else pd.DataFrame(),eonet_df if show_volc else pd.DataFrame(),show_mvmt,show_heat),use_container_width=True)
        st.markdown('<div class="sec-label" style="margin-top:10px">Geomagnetic Kp — 24h</div>',unsafe_allow_html=True)
        st.plotly_chart(kp_chart(kp_data["series"]),use_container_width=True,config={"displayModeBar":False})
    with rc:
        st.markdown('<div class="sec-label">Magnitude Distribution</div>',unsafe_allow_html=True)
        if not eq_df.empty: st.plotly_chart(mag_hist(eq_df),use_container_width=True,config={"displayModeBar":False})
        st.markdown('<div class="sec-label">M4.5+ Events</div>',unsafe_allow_html=True)
        for _,row in eq_df[eq_df["mag"]>=4.5].nlargest(10,"mag").iterrows():
            m=row["mag"]; bc="b-red" if m>=5.5 else "b-amber" if m>=4.5 else "b-cyan"
            st.markdown(f'<div class="gcard {"gcard-crit" if m>=5.5 else ""}"><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px"><div class="sig-title">{row["place"][:34]}</div><div class="badge {bc}">M{m}</div></div><div class="sig-meta">Depth {row["depth_km"]}km · {row["time"]}</div></div>',unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 3 — CIVIL MOVEMENTS
# ══════════════════════════════════════════════════════════════
with tab_civil:
    mc2,rc2=st.columns([3,1],gap="medium")
    with mc2:
        mdf=pd.DataFrame(MOVEMENTS); mdf["color"]=mdf["sentiment"].map({"CRIT":[255,55,85,230],"HIGH":[224,92,42,200],"MED":[255,180,0,180]})
        mdf["radius"]=mdf["scale"]*2200; mdf["tip"]=mdf.apply(lambda r:f"✊ {r['title']} | {r['location']} | {r['size']}",axis=1)
        st.pydeck_chart(pdk.Deck(layers=[pdk.Layer("ScatterplotLayer",data=mdf,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True)],
                                  initial_view_state=pdk.ViewState(latitude=25,longitude=20,zoom=1.3),
                                  map_style="mapbox://styles/mapbox/dark-v11",
                                  tooltip={"text":"{tip}","style":{"backgroundColor":"#070e1a","color":"#dde8f5","border":"1px solid rgba(157,110,255,.25)","fontFamily":"IBM Plex Mono","fontSize":"11px"}},height=380),use_container_width=True)
        st.markdown('<div class="sec-label" style="margin-top:10px">Scale by Location</div>',unsafe_allow_html=True)
        st.plotly_chart(mv_bar(MOVEMENTS),use_container_width=True,config={"displayModeBar":False})
    with rc2:
        ft=st.radio("Filter",["ALL","protest","strike","civil"],horizontal=True,label_visibility="collapsed")
        st.markdown('<div class="sec-label">Active Movements</div>',unsafe_allow_html=True)
        for m in MOVEMENTS:
            if ft!="ALL" and m["type"]!=ft: continue
            ic=m["sentiment"]=="CRIT"; sc="b-red" if ic else "b-orange" if m["sentiment"]=="HIGH" else "b-amber"
            tc_="b-violet" if m["type"]=="civil" else "b-orange" if m["type"]=="protest" else "b-amber"
            fc="#ff3d5a" if ic else "#ff8c42" if m["sentiment"]=="HIGH" else "#ffb400"
            st.markdown(f'<div class="gcard {"gcard-crit" if ic else ""}"><div class="sig-title">{m["title"]}</div><div class="sig-meta">{m["location"]} · {m["age_h"]}h ago</div><div style="display:flex;gap:5px;margin-top:6px;flex-wrap:wrap"><div class="badge {tc_}">{m["type"].upper()}</div><div class="badge {sc}">{m["sentiment"]}</div><div class="sig-meta" style="margin:0;align-self:center">{m["size"]}</div></div><div class="scale-wrap"><div class="scale-track"><div class="scale-fill" style="width:{m["scale"]}%;background:linear-gradient(90deg,{fc}88,{fc})"></div></div><div style="font-family:var(--fm);font-size:9px;color:var(--muted)">{m["scale"]}</div></div></div>',unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 4 — LIVE NEWS
# ══════════════════════════════════════════════════════════════
with tab_news:
    st.markdown(f'<div class="sec-label">{len(NEWS_SOURCES)} Configured Sources</div>',unsafe_allow_html=True)
    cat_f=st.radio("Category",CATEGORIES,format_func=lambda x:CAT_LABELS.get(x,x),horizontal=True,label_visibility="collapsed")
    vis_src=[s for s in NEWS_SOURCES if cat_f=="ALL" or s["cat"]==cat_f]
    pills='<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px">'
    for s in vis_src: pills+=f'<div class="src-pill" style="border-left:2px solid {s["color"]}"><span style="color:{s["color"]};font-size:7px">●</span><span style="font-size:10px">{s["name"]}</span></div>'
    pills+='</div>'; st.markdown(pills,unsafe_allow_html=True)
    with st.spinner(f"Fetching {len(vis_src)} feeds…"):
        all_art=[]
        for s in vis_src:
            arts=fetch_rss(s["rss"],s["name"],s["cat"])
            for a in arts: a["src_color"]=s["color"]
            all_art.extend(arts)
    if not all_art:
        st.info("News feeds unreachable (network offline). Showing source directory.")
        sc2=st.columns(2)
        for i,s in enumerate(NEWS_SOURCES):
            with sc2[i%2]:
                st.markdown(f'<div class="news-card nc-general" style="padding-left:18px"><div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px"><div class="news-source" style="color:{s["color"]}">{s["name"]}</div><div class="badge {CAT_COLORS.get(s["cat"],"b-muted")}">{s["cat"]}</div></div><div style="font-size:11px;color:var(--muted);line-height:1.4">{s["desc"]}</div><div style="font-family:var(--fm);font-size:9px;color:var(--muted);margin-top:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{s["rss"][:55]}…</div></div>',unsafe_allow_html=True)
    else:
        nl,nr=st.columns(2,gap="medium")
        for i,a in enumerate(all_art[:30]):
            nc=CAT_NC.get(a.get("category","general"),"nc-general"); cb=CAT_COLORS.get(a.get("category",""),"b-muted")
            lh=f'<a href="{a["link"]}" target="_blank" class="news-link">READ →</a>' if a.get("link") else ""
            col=nl if i%2==0 else nr
            with col: st.markdown(f'<div class="news-card {nc}"><div style="display:flex;align-items:center;justify-content:space-between;gap:8px"><div class="news-source" style="color:{a["src_color"]}">{a["source"]}</div><div class="badge {cb}">{a.get("category","")}</div></div><div class="news-headline">{a["title"]}</div><div class="news-desc">{a.get("desc","")[:180]}</div><div class="news-footer"><div class="news-time">{a.get("time","")}</div>{lh}</div></div>',unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 5 — ARENA CHALLENGES
# ══════════════════════════════════════════════════════════════
with tab_arena:
    lc,cc2=st.columns([1,2],gap="medium")
    with lc:
        st.markdown('<div class="sec-label">Leaderboard</div>',unsafe_allow_html=True)
        avts=["background:rgba(255,61,90,.15);color:#ff3d5a","background:rgba(157,110,255,.15);color:#9d6eff","background:rgba(255,180,0,.15);color:#ffb400","background:rgba(255,140,66,.15);color:#ff8c42","background:rgba(61,90,117,.15);color:#3d5a75"]
        for i,(name,tier,sc,col) in enumerate(LEADERBOARD):
            st.markdown(f'<div class="lb-row"><div style="font-size:15px;width:20px">{"🥇🥈🥉④⑤"[i*2:i*2+2]}</div><div class="lb-avatar" style="{avts[i]}">{name[:2].upper()}</div><div style="flex:1"><div class="sig-title" style="color:{col};font-size:12px">{name}</div><div class="sig-meta">{tier}</div></div><div style="font-family:var(--fd);font-size:16px;color:var(--green)">{sc:,}</div></div>',unsafe_allow_html=True)
        tn2,tc2,_=get_tier(st.session_state.score)
        st.markdown(f'<div style="margin:12px 8px 0"><div class="lb-row" style="background:rgba(157,110,255,.04);border:1px solid rgba(157,110,255,.2);border-radius:8px;padding:10px 12px"><div style="font-family:var(--fd);font-size:16px;color:var(--violet);width:28px">#142</div><div class="lb-avatar" style="background:rgba(0,200,255,.12);color:var(--cyan)">YOU</div><div style="flex:1"><div class="sig-title" style="color:#9d6eff;font-size:12px">you</div><div class="sig-meta">{tn2}</div></div><div style="font-family:var(--fd);font-size:16px;color:var(--green)">{st.session_state.score:,}</div></div></div>',unsafe_allow_html=True)
        ac=len(st.session_state.answered); cor=sum(1 for cid,a in st.session_state.answered.items() for c in CHALLENGES if c["id"]==cid and a==c["correct"])
        st.markdown(f'<div class="m-panel" style="margin-top:14px"><div style="display:flex;justify-content:space-between"><div><div class="m-label">Attempted</div><div class="m-val m-cyan" style="font-size:26px">{ac}/{len(CHALLENGES)}</div></div><div><div class="m-label">Correct</div><div class="m-val m-green" style="font-size:26px">{cor}</div></div></div><div class="xp-track" style="margin-top:10px"><div class="xp-fill" style="width:{int(cor/len(CHALLENGES)*100)}%"></div></div></div>',unsafe_allow_html=True)
    with cc2:
        st.markdown('<div class="sec-label">Challenges</div>',unsafe_allow_html=True)
        for ch in CHALLENGES:
            done=ch["id"] in st.session_state.answered
            st.markdown(f'<div class="ch-card"><div class="ch-header"><div class="ch-title">{ch["title"]}</div><div style="display:flex;gap:7px;align-items:center"><div class="badge" style="color:{ch["color"]};border-color:{ch["color"]}44;background:{ch["color"]}15">{ch["difficulty"]}</div><div class="badge b-green">+{ch["pts"]} XP</div></div></div><div class="ch-body"><div class="ch-q">{ch["question"]}</div>{"".join(f\'<div class="clue"><span>▸</span>{c}</div>\' for c in ch["clues"])}</div></div>',unsafe_allow_html=True)
            if not done:
                sel=st.radio(f"a{ch['id']}",ch["options"],index=None,key=f"r_{ch['id']}",label_visibility="collapsed")
                if st.button("Submit",key=f"b_{ch['id']}",disabled=(sel is None)):
                    idx=ch["options"].index(sel); st.session_state.answered[ch["id"]]=idx
                    if idx==ch["correct"]: st.session_state.score+=ch["pts"]
                    st.rerun()
            else:
                chosen=st.session_state.answered[ch["id"]]
                if chosen==ch["correct"]: st.success(f"✓ CORRECT +{ch['pts']} XP — {ch['explain']}")
                else: st.error(f"✗ Incorrect ('{ch['options'][chosen]}') — {ch['explain']}")
            st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 6 — AI ANALYST
# ══════════════════════════════════════════════════════════════
with tab_ai:
    al,ar=st.columns([1,1],gap="medium")
    with al:
        ready=(st.session_state.ai_provider in ("groq","openrouter") and st.session_state.ai_key) or st.session_state.ai_provider=="ollama"
        st.markdown(f'<div class="gcard"><div style="display:flex;gap:10px;align-items:center"><div style="display:flex;flex-direction:column;gap:3px;font-family:var(--fm);font-size:10px;color:var(--muted)"><span>Provider: <span style="color:var(--cyan)">{st.session_state.ai_provider.upper()}</span></span><span>Model: <span style="color:var(--violet)">llama-3.1-8b-instant</span></span></div><div style="margin-left:auto"><div class="badge {"b-green" if ready else "b-muted"}"><span class="pulse {"p-green" if ready else "p-amber"}" style="margin-right:4px"></span>{"READY" if ready else "NO KEY"}</div></div></div></div>',unsafe_allow_html=True)
        tmpls=["— select —","Summarise top 3 seismic risks","Assess New Delhi protest escalation","Kp index impact on satellite ops","Cross-theatre conflict risk comparison","Which regions have compound Earth + conflict risk?","Humanitarian risk assessment across all active conflicts"]
        tmpl=st.selectbox("Template",tmpls,label_visibility="collapsed")
        prompt=st.text_area("Query",value="" if tmpl==tmpls[0] else tmpl,height=110,placeholder="Enter OSINT query…",label_visibility="collapsed")
        inject=st.checkbox("Inject live context (seismic + conflicts + movements)",value=True)
        if st.button("⚡  Run Analysis",use_container_width=True):
            if prompt.strip():
                final=prompt
                if inject:
                    top5=eq_df.nlargest(5,"mag")[["mag","place","depth_km"]].to_dict("records")
                    conf_ctx={n:{"escalation":c["escalation"],"intensity":c["intensity"],"casualties":c["casualties_total"]} for n,c in CONFLICTS.items()}
                    final+=(f"\n\n[LIVE CONTEXT — {utc_now}]\nTop quakes: {json.dumps(top5)}\nKp: {kp_data['kp']}\n"
                            f"Conflicts: {json.dumps(conf_ctx)}\nMovements: {json.dumps([{k:m[k] for k in ('title','location','sentiment')} for m in MOVEMENTS])}")
                with st.spinner("Querying analyst…"):
                    result=call_ai(final,st.session_state.ai_provider,st.session_state.ai_key)
                st.session_state.ai_output=result
        if st.session_state.ai_output:
            st.markdown(f'<div class="ai-terminal">{st.session_state.ai_output}</div>',unsafe_allow_html=True)
    with ar:
        st.markdown('<div class="sec-label">Situational Overview</div>',unsafe_allow_html=True)
        if not eq_df.empty:
            st.plotly_chart(mag_donut(eq_df),use_container_width=True,config={"displayModeBar":False})
        snt={"CRIT":0,"HIGH":0,"MED":0}
        for m in MOVEMENTS: snt[m["sentiment"]]+=1
        fig_s=go.Figure(go.Bar(x=list(snt.keys()),y=list(snt.values()),marker_color=["#ff3d5a","#ff8c42","#ffb400"],marker_line_width=0))
        fig_s.update_layout(height=150,title_text="Movement Sentiment",title_font=dict(color="#3d5a75",size=10),margin=dict(l=0,r=0,t=22,b=0),**bg_chart(),xaxis=ax(),yaxis=ax())
        st.plotly_chart(fig_s,use_container_width=True,config={"displayModeBar":False})
        st.markdown('<div class="sec-label" style="margin-top:8px">Earthquake Data</div>',unsafe_allow_html=True)
        st.dataframe(eq_df[["mag","place","depth_km","time"]].head(16).rename(columns={"mag":"Mag","place":"Location","depth_km":"Depth km","time":"Time"}),use_container_width=True,height=220,hide_index=True)
