"""
OSINT ARENA v4 — Streamlit Application
========================================
Earth Signals · Civil Movements · Conflict Dashboard
Live News Feeds · AI Analyst · OSINT Challenges

NEW in v4:
  — Persistent full-width global map shown above ALL tabs (command view)
  — Map combines seismic, conflict incidents, civil movements, and supply arcs
  — Layer legend overlaid on map with live counts
  — User-friendly redesign: larger text, readable cards, clear section labels,
    helper tooltips, onboarding hints, friendlier sidebar

Tech stack:
  Frontend  : Streamlit + PyDeck + Plotly
  Maps      : PyDeck ScatterplotLayer / HeatmapLayer / ArcLayer
  AI/ML     : Groq / Ollama / OpenRouter via HTTP
  News      : RSS XML parsing (16 sources, 10-min cache)
  Caching   : st.cache_data TTL hierarchy (60s → 600s)
  Live data : USGS · NASA EONET · NOAA SWPC
"""

import streamlit as st
import pandas as pd
import numpy as np
import json, requests, re, html as html_lib
from datetime import datetime, timezone
import pydeck as pdk
import plotly.graph_objects as go

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OSINT ARENA — Global Intelligence",
    page_icon="🛰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=IBM+Plex+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

:root {
  --void:    #02040a;
  --deep:    #060d18;
  --panel:   #080f1c;
  --card:    #0b1524;
  --glass:   rgba(8,15,28,0.88);
  --border:  rgba(0,200,255,0.12);
  --bord2:   rgba(0,200,255,0.06);
  --bord3:   rgba(255,255,255,0.05);
  --cyan:    #00c8ff;
  --amber:   #ffb400;
  --red:     #ff3d5a;
  --green:   #00e676;
  --violet:  #9d6eff;
  --orange:  #ff8c42;
  --text:    #e2ecf8;
  --text2:   #a8c0d8;
  --muted:   #4a6b85;
  --dim:     #0f2035;
  --fd: 'Bebas Neue','Impact',sans-serif;
  --fm: 'IBM Plex Mono','Courier New',monospace;
  --fb: 'DM Sans',system-ui,sans-serif;
}

/* ── BASE ─────────────────────────────────────────────── */
html,body,[class*="css"],.stApp {
  font-family: var(--fb) !important;
  background: var(--void) !important;
  color: var(--text) !important;
}
.stApp::before {
  content:''; position:fixed; inset:0;
  background: repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.02) 3px,rgba(0,0,0,.02) 6px);
  pointer-events:none; z-index:9000;
}
.stApp::after {
  content:''; position:fixed; inset:0;
  background: radial-gradient(ellipse at center,transparent 55%,rgba(0,0,0,.45) 100%);
  pointer-events:none; z-index:9001;
}
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:var(--deep)}
::-webkit-scrollbar-thumb{background:rgba(0,200,255,.2);border-radius:2px}

/* ── SIDEBAR ──────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background: var(--deep) !important;
  border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p { color: var(--text) !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: var(--text) !important; }

/* ── TABS ─────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--deep) !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important; padding: 0 8px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  border-bottom: 3px solid transparent !important;
  font-family: var(--fb) !important; font-weight: 600 !important;
  font-size: 13px !important; letter-spacing: .06em !important;
  color: var(--muted) !important; padding: 14px 20px !important;
  transition: color .2s;
}
.stTabs [aria-selected="true"] {
  color: var(--cyan) !important;
  border-bottom-color: var(--cyan) !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text2) !important; }

/* ── METRICS ──────────────────────────────────────────── */
div[data-testid="stMetric"] {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px 20px !important;
}
div[data-testid="stMetricValue"] {
  font-family: var(--fm) !important; font-size: 24px !important;
  color: var(--cyan) !important; font-weight: 500 !important;
}
div[data-testid="stMetricLabel"] {
  font-family: var(--fb) !important; font-size: 11px !important;
  font-weight: 600 !important; letter-spacing: .1em !important;
  text-transform: uppercase !important; color: var(--muted) !important;
}
div[data-testid="stMetricDelta"] { font-size: 12px !important; }

/* ── BUTTONS ──────────────────────────────────────────── */
.stButton > button {
  background: transparent !important; border: 1px solid var(--border) !important;
  color: var(--text) !important; font-family: var(--fb) !important;
  font-weight: 600 !important; font-size: 13px !important;
  border-radius: 8px !important; padding: 10px 18px !important;
  transition: all .18s !important; letter-spacing: .04em !important;
}
.stButton > button:hover {
  border-color: var(--cyan) !important; color: var(--cyan) !important;
  background: rgba(0,200,255,.06) !important;
  box-shadow: 0 0 16px rgba(0,200,255,.12) !important;
}

/* ── FORM ELEMENTS ────────────────────────────────────── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stTextArea textarea {
  background: var(--card) !important; border: 1px solid var(--border) !important;
  color: var(--text) !important; font-family: var(--fm) !important;
  font-size: 13px !important; border-radius: 8px !important;
}
.stSelectbox label, .stTextInput label, .stTextArea label,
.stCheckbox label, .stToggle label {
  color: var(--text2) !important; font-size: 12px !important;
  font-weight: 500 !important; font-family: var(--fb) !important;
}
.stRadio > div { gap: 8px; flex-wrap: wrap; }
.stRadio > div > label {
  background: var(--card) !important; border: 1px solid var(--bord2) !important;
  border-radius: 8px !important; padding: 7px 14px !important;
  font-size: 12px !important; color: var(--text2) !important;
  text-transform: none !important; letter-spacing: 0 !important;
  font-weight: 500 !important; transition: border-color .15s;
}
.stRadio > div > label:hover { border-color: rgba(0,200,255,.2) !important; }
.stRadio [data-checked="true"] > label,
.stRadio [aria-checked="true"] > label {
  border-color: var(--cyan) !important;
  color: var(--cyan) !important;
  background: rgba(0,200,255,.07) !important;
}

/* ── ALERTS ───────────────────────────────────────────── */
.stSuccess { background:rgba(0,230,118,.07)!important; border:1px solid rgba(0,230,118,.25)!important; color:var(--green)!important; border-radius:10px!important; font-size:13px!important; }
.stError   { background:rgba(255,61,90,.07)!important;  border:1px solid rgba(255,61,90,.25)!important;  color:var(--red)!important;   border-radius:10px!important; font-size:13px!important; }
.stWarning { background:rgba(255,180,0,.07)!important;  border:1px solid rgba(255,180,0,.25)!important;  color:var(--amber)!important; border-radius:10px!important; font-size:13px!important; }
.stInfo    { background:rgba(0,200,255,.07)!important;  border:1px solid rgba(0,200,255,.25)!important;  color:var(--cyan)!important;  border-radius:10px!important; font-size:13px!important; }

/* ── DATAFRAME ────────────────────────────────────────── */
.stDataFrame [data-testid="stDataFrameResizable"] {
  border: 1px solid var(--border) !important;
  border-radius: 10px !important; overflow: hidden !important;
}
hr { border:none!important; border-top:1px solid var(--bord2)!important; margin:18px 0!important; }

/* ══════════════════════════════════════════════════════
   CUSTOM COMPONENTS
   ══════════════════════════════════════════════════════ */

/* WORDMARK */
.wordmark {
  font-family: var(--fd); font-size: 30px; letter-spacing: .16em; line-height:1;
  color: var(--cyan); text-shadow: 0 0 28px rgba(0,200,255,.45);
}
.wordmark em { color: var(--amber); font-style: normal; }

/* GLOBAL MAP WRAPPER */
.global-map-wrap {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 6px;
  position: relative;
}
.map-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 18px;
  border-bottom: 1px solid var(--bord2);
  background: rgba(6,13,24,0.6);
}
.map-title {
  font-family: var(--fd); font-size: 16px; letter-spacing: .14em;
  color: var(--cyan); text-shadow: 0 0 16px rgba(0,200,255,.3);
}
.map-legend {
  display: flex; gap: 16px; align-items: center;
  font-family: var(--fm); font-size: 10px; color: var(--muted);
}
.legend-item { display:flex; align-items:center; gap:5px; }
.legend-dot  { width:8px; height:8px; border-radius:50%; flex-shrink:0; }

/* SECTION LABEL */
.sec-label {
  font-family: var(--fb); font-size: 10px; font-weight: 700;
  letter-spacing: .18em; text-transform: uppercase; color: var(--muted);
  display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
}
.sec-label::after { content:''; flex:1; height:1px; background:var(--bord2); }

/* STATUS ROW */
.status-row {
  display: flex; align-items: center; gap: 20px;
  font-family: var(--fm); font-size: 11px; color: var(--muted);
  padding: 8px 0 14px; border-bottom: 1px solid var(--bord2); margin-bottom: 18px;
  flex-wrap: wrap;
}
.pulse { width:6px; height:6px; border-radius:50%; display:inline-block; margin-right:5px; animation:blink 2s ease-in-out infinite; }
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}
.p-cyan  { background:var(--cyan);   box-shadow:0 0 6px var(--cyan); }
.p-amber { background:var(--amber);  box-shadow:0 0 6px var(--amber); }
.p-red   { background:var(--red);    box-shadow:0 0 6px var(--red); animation-duration:.8s; }
.p-green { background:var(--green);  box-shadow:0 0 6px var(--green); }
.p-orange{ background:var(--orange); box-shadow:0 0 6px var(--orange); }
.utc-clock { margin-left:auto; font-family:var(--fd); font-size:15px; letter-spacing:.12em; color:var(--cyan); }

/* GLASS CARD */
.gcard {
  background: var(--glass); backdrop-filter: blur(8px);
  border: 1px solid var(--border); border-radius: 12px;
  padding: 16px 18px; margin-bottom: 10px; position: relative; overflow: hidden;
  transition: border-color .2s, box-shadow .2s;
}
.gcard:hover { border-color:rgba(0,200,255,.22); box-shadow:0 4px 24px rgba(0,200,255,.06); }
.gcard::before { content:''; position:absolute; top:0; left:0; right:0; height:1px; background:linear-gradient(90deg,transparent,rgba(0,200,255,.3),transparent); }
.gcard-crit { border-color:rgba(255,61,90,.35)!important; animation:crit-pulse 3s ease-in-out infinite; }
@keyframes crit-pulse { 0%,100%{box-shadow:0 0 18px rgba(255,61,90,.06)} 50%{box-shadow:0 0 28px rgba(255,61,90,.18)} }
.gcard-crit::before { background:linear-gradient(90deg,transparent,rgba(255,61,90,.45),transparent)!important; }

/* CONFLICT CARDS */
.conflict-card { background:var(--card); border:1px solid var(--bord2); border-radius:12px; overflow:hidden; margin-bottom:12px; transition:border-color .2s; }
.conflict-card:hover { border-color:rgba(255,61,90,.2); }
.cc-header { padding:12px 16px; border-bottom:1px solid var(--bord2); display:flex; align-items:center; justify-content:space-between; }
.cc-body   { padding:14px 16px; }
.cc-title  { font-family:var(--fd); font-size:16px; letter-spacing:.07em; color:var(--text); }

/* INCIDENT FEED */
.incident-row { display:flex; gap:12px; padding:12px 0; border-bottom:1px solid var(--bord2); transition:background .15s; }
.incident-row:hover { background:rgba(255,61,90,.03); border-radius:6px; padding-left:4px; }
.inc-icon { width:32px; height:32px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:15px; flex-shrink:0; }
.inc-body { flex:1; min-width:0; }
.inc-title { font-size:13px; font-weight:600; color:var(--text); line-height:1.4; }
.inc-meta  { font-family:var(--fm); font-size:11px; color:var(--muted); margin-top:3px; }
.inc-badge-row { display:flex; gap:5px; margin-top:6px; flex-wrap:wrap; }

/* BADGE SYSTEM */
.badge {
  display:inline-flex; align-items:center; padding:3px 9px;
  border-radius:5px; font-family:var(--fm); font-size:10px;
  font-weight:500; letter-spacing:.05em; border:1px solid; white-space:nowrap;
}
.b-red    { color:var(--red);    border-color:rgba(255,61,90,.35);   background:rgba(255,61,90,.10); }
.b-amber  { color:var(--amber);  border-color:rgba(255,180,0,.35);   background:rgba(255,180,0,.10); }
.b-cyan   { color:var(--cyan);   border-color:rgba(0,200,255,.35);   background:rgba(0,200,255,.10); }
.b-green  { color:var(--green);  border-color:rgba(0,230,118,.35);   background:rgba(0,230,118,.10); }
.b-violet { color:var(--violet); border-color:rgba(157,110,255,.35); background:rgba(157,110,255,.10); }
.b-orange { color:var(--orange); border-color:rgba(255,140,66,.35);  background:rgba(255,140,66,.10); }
.b-muted  { color:var(--muted);  border-color:rgba(74,107,133,.35);  background:rgba(74,107,133,.10); }

/* TEXT STYLES */
.sig-title { font-size:14px; font-weight:600; color:var(--text); line-height:1.4; }
.sig-meta  { font-family:var(--fm); font-size:11px; color:var(--muted); margin-top:4px; line-height:1.5; }
.sig-body  { font-size:13px; color:var(--text2); line-height:1.6; }

/* SCALE / XP BARS */
.scale-wrap  { display:flex; align-items:center; gap:8px; margin-top:8px; }
.scale-track { flex:1; height:4px; background:var(--dim); border-radius:2px; overflow:hidden; }
.scale-fill  { height:100%; border-radius:2px; }
.xp-track { height:5px; background:var(--dim); border-radius:3px; overflow:hidden; margin-top:6px; }
.xp-fill  { height:100%; background:linear-gradient(90deg,var(--violet),var(--cyan)); border-radius:3px; }

/* METRIC PANEL */
.m-panel  { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px 18px; margin-bottom:10px; }
.m-label  { font-size:10px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); margin-bottom:6px; }
.m-val    { font-family:var(--fd); font-size:36px; letter-spacing:.04em; line-height:1; margin-bottom:4px; }
.m-sub    { font-family:var(--fm); font-size:11px; color:var(--muted); }
.m-cyan   { color:var(--cyan);   text-shadow:0 0 20px rgba(0,200,255,.3); }
.m-amber  { color:var(--amber);  text-shadow:0 0 20px rgba(255,180,0,.2); }
.m-red    { color:var(--red);    text-shadow:0 0 20px rgba(255,61,90,.25); }
.m-green  { color:var(--green);  text-shadow:0 0 20px rgba(0,230,118,.2); }
.m-violet { color:var(--violet); text-shadow:0 0 20px rgba(157,110,255,.2); }
.m-orange { color:var(--orange); text-shadow:0 0 20px rgba(255,140,66,.2); }

/* LEADERBOARD */
.lb-row { display:flex; align-items:center; gap:12px; padding:10px 14px; border-bottom:1px solid var(--bord2); transition:background .15s; }
.lb-row:hover { background:rgba(0,200,255,.03); }
.lb-avatar { width:32px; height:32px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; flex-shrink:0; }

/* CHALLENGE CARD */
.ch-card   { background:var(--card); border:1px solid var(--border); border-radius:14px; margin-bottom:16px; overflow:hidden; }
.ch-header { padding:12px 18px; border-bottom:1px solid var(--bord2); display:flex; align-items:center; justify-content:space-between; }
.ch-title  { font-family:var(--fd); font-size:16px; letter-spacing:.09em; color:var(--violet); }
.ch-body   { padding:16px 18px; }
.ch-q      { font-size:14px; color:var(--text); line-height:1.65; margin-bottom:14px; }
.clue      { display:flex; gap:8px; font-family:var(--fm); font-size:11px; color:var(--muted); margin-bottom:6px; line-height:1.5; }
.clue span { color:var(--violet); flex-shrink:0; }

/* NEWS CARDS */
.news-card { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px 18px; margin-bottom:12px; position:relative; overflow:hidden; transition:border-color .2s,transform .15s; }
.news-card:hover { border-color:rgba(0,200,255,.22); transform:translateY(-1px); box-shadow:0 4px 20px rgba(0,0,0,.3); }
.news-card::after { content:''; position:absolute; left:0; top:0; bottom:0; width:3px; }
.nc-seismic::after  { background:linear-gradient(180deg,var(--red),transparent); }
.nc-volcanic::after { background:linear-gradient(180deg,var(--orange),transparent); }
.nc-solar::after    { background:linear-gradient(180deg,var(--amber),transparent); }
.nc-civil::after    { background:linear-gradient(180deg,var(--violet),transparent); }
.nc-general::after  { background:linear-gradient(180deg,var(--cyan),transparent); }
.news-headline { font-size:14px; font-weight:600; color:var(--text); line-height:1.45; margin:8px 0 6px; }
.news-desc     { font-size:12px; color:var(--muted); line-height:1.6; margin-bottom:10px; }
.news-footer   { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.news-time     { font-family:var(--fm); font-size:10px; color:var(--muted); }
.news-source   { display:inline-flex; align-items:center; gap:5px; font-family:var(--fm); font-size:10px; font-weight:500; letter-spacing:.07em; text-transform:uppercase; }
.news-link     { font-family:var(--fm); font-size:10px; color:var(--cyan); text-decoration:none; padding:3px 10px; border:1px solid rgba(0,200,255,.25); border-radius:5px; transition:background .15s; }
.news-link:hover { background:rgba(0,200,255,.1); }
.src-pill { display:inline-flex; align-items:center; gap:6px; padding:4px 12px; background:var(--dim); border:1px solid var(--bord2); border-radius:20px; font-family:var(--fm); font-size:10px; color:var(--text2); }

/* TIMELINE */
.timeline { position:relative; padding-left:22px; }
.timeline::before { content:''; position:absolute; left:7px; top:0; bottom:0; width:1px; background:var(--bord2); }
.tl-item  { position:relative; margin-bottom:16px; }
.tl-dot   { position:absolute; left:-18px; top:4px; width:9px; height:9px; border-radius:50%; border:1.5px solid; }
.tl-date  { font-family:var(--fm); font-size:10px; color:var(--muted); margin-bottom:3px; }
.tl-text  { font-size:13px; color:var(--text); line-height:1.5; }
.tl-tag   { font-family:var(--fm); font-size:9px; margin-top:2px; }

/* AI TERMINAL */
.ai-terminal {
  background:#010710; border:1px solid var(--border); border-radius:10px;
  padding:18px; font-family:var(--fm); font-size:13px; color:var(--text);
  line-height:1.75; white-space:pre-wrap; min-height:180px;
}
.ai-terminal::before {
  content:'▸ ANALYSIS OUTPUT'; display:block;
  font-size:10px; letter-spacing:.2em; color:var(--muted);
  margin-bottom:12px; padding-bottom:10px; border-bottom:1px solid var(--bord2);
}

/* TICKER */
.ticker-wrap { background:var(--deep); border-top:1px solid var(--border); border-bottom:1px solid var(--bord2); overflow:hidden; padding:8px 0; }
.ticker-inner { display:inline-block; white-space:nowrap; animation:ticker-scroll 90s linear infinite; font-family:var(--fm); font-size:11px; color:var(--muted); }
@keyframes ticker-scroll { from{transform:translateX(0)} to{transform:translateX(-50%)} }
.t-sep { color:var(--cyan); margin:0 16px; }
.t-hi  { color:var(--text); }
.t-red { color:var(--red); }
.t-amb { color:var(--amber); }

/* HELPER TEXT */
.helper { font-size:12px; color:var(--muted); line-height:1.6; font-style:italic; padding:10px 14px; background:var(--dim); border-radius:8px; border-left:3px solid var(--bord2); margin-bottom:12px; }
.helper b { color:var(--text2); font-style:normal; }

/* SECTION DIVIDER */
.sb-div { height:1px; background:var(--bord2); margin:16px 0; }

/* ONBOARDING BANNER */
.onboard-banner {
  background:linear-gradient(135deg,rgba(0,200,255,.07),rgba(157,110,255,.07));
  border:1px solid rgba(0,200,255,.18); border-radius:12px; padding:16px 20px; margin-bottom:16px;
}
.onboard-title { font-family:var(--fd); font-size:18px; letter-spacing:.1em; color:var(--cyan); margin-bottom:6px; }
.onboard-body  { font-size:13px; color:var(--text2); line-height:1.65; }
.onboard-steps { display:flex; gap:12px; margin-top:10px; flex-wrap:wrap; }
.onboard-step  { display:flex; align-items:center; gap:7px; font-size:12px; color:var(--text2); background:var(--dim); border-radius:8px; padding:7px 12px; }
.onboard-step span { font-family:var(--fd); font-size:15px; color:var(--cyan); }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
for k, v in {
    "score": 2840, "answered": {}, "ai_provider": "groq", "ai_key": "",
    "ai_output": "", "conflict_sitrep": "",
    "selected_conflict": "Ukraine–Russia War",
    "show_onboard": True,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def get_tier(s):
    if s >= 10000: return "HANDLER", "b-red",    "#ff3d5a"
    if s >=  5000: return "AGENT",   "b-violet",  "#9d6eff"
    if s >=  2000: return "ANALYST", "b-cyan",    "#00c8ff"
    return                "RECRUIT", "b-green",   "#00e676"

def bg_chart():
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

def ax(color="#4a6b85", grid="#0f2035", sz=10):
    return dict(color=color, tickfont_size=sz, gridcolor=grid)

# ─────────────────────────────────────────────────────────────
# ══════════════ CONFLICT DATA ═════════════════════════════════
# ─────────────────────────────────────────────────────────────
CONFLICTS = {
"Ukraine–Russia War": {
  "status":"ACTIVE","intensity":"CRITICAL","start":"2022-02-24","region":"Eastern Europe",
  "escalation":87,"ceasefire":False,"casualties_total":350000,"displaced":14200000,
  "description":"Full-scale invasion of Ukraine by Russia. Ongoing frontline combat across eastern and southern oblasts.",
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
    {"type":"diplomatic","title":"UN Security Council emergency session","loc":"New York","lat":40.75,"lon":-73.98,"date":"2026-03-11","severity":"INFO","casualties":0},
  ],
  "timeline":[
    {"date":"2022-02-24","event":"Full-scale invasion begins","type":"escalation"},
    {"date":"2022-03-28","event":"Kyiv assault repelled — Russian withdrawal","type":"milestone"},
    {"date":"2022-11-11","event":"Kherson city liberated","type":"milestone"},
    {"date":"2023-06-04","event":"Ukrainian counteroffensive begins","type":"escalation"},
    {"date":"2024-02-17","event":"Avdiivka falls to Russian forces","type":"setback"},
    {"date":"2024-08-06","event":"Ukraine crosses border — Kursk incursion","type":"escalation"},
    {"date":"2025-11-20","event":"US authorises long-range missile strikes","type":"escalation"},
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
    {"name":"TASS","bias":"State/RU","reliability":25},{"name":"AP","bias":"Centre","reliability":91},
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
    {"type":"diplomatic","title":"ICJ interim order compliance review","loc":"The Hague","lat":52.08,"lon":4.3,"date":"2026-03-12","severity":"INFO","casualties":0},
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
    {"name":"Fox News","bias":"Right","reliability":62},{"name":"BBC","bias":"Centre","reliability":86},
  ],
},
"Sudan Civil War": {
  "status":"ACTIVE","intensity":"HIGH","start":"2023-04-15","region":"Sub-Saharan Africa",
  "escalation":74,"ceasefire":False,"casualties_total":15000,"displaced":8100000,
  "description":"Armed conflict between Sudanese Armed Forces (SAF) and Rapid Support Forces (RSF) across Sudan, including Darfur.",
  "factions":[
    {"name":"Sudanese Armed Forces","side":"SAF","color":"#1a9fff","territory_pct":55,"strength":"Med","weapons":["Su-25","T-72","Mi-24"],"support":["Egypt","Saudi Arabia"],"status":"Active"},
    {"name":"Rapid Support Forces","side":"RSF","color":"#ff3d5a","territory_pct":38,"strength":"High","weapons":["Technicals","ZU-23","Armour"],"support":["UAE","Wagner"],"status":"Advancing"},
    {"name":"Sudan Liberation Army","side":"SLA","color":"#ffb400","territory_pct":5,"strength":"Low","weapons":["Light arms"],"support":["None"],"status":"Active"},
  ],
  "incidents":[
    {"type":"airstrike","title":"SAF airstrike on RSF position — Omdurman","loc":"Omdurman","lat":15.65,"lon":32.48,"date":"2026-03-14","severity":"HIGH","casualties":18},
    {"type":"ground","title":"RSF advances in El Fasher, North Darfur","loc":"El Fasher","lat":13.63,"lon":25.35,"date":"2026-03-13","severity":"CRITICAL","casualties":42},
    {"type":"humanitarian","title":"MSF hospital shelled — Khartoum North","loc":"Khartoum","lat":15.5,"lon":32.53,"date":"2026-03-12","severity":"CRITICAL","casualties":9},
    {"type":"diplomatic","title":"Jeddah peace talks stall","loc":"Jeddah","lat":21.49,"lon":39.19,"date":"2026-03-10","severity":"MED","casualties":0},
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

INCIDENT_ICONS = {
    "airstrike":"💥","ground":"⚔️","drone":"🛸","naval":"⚓","rocket":"🚀",
    "cyber":"💻","diplomatic":"🤝","humanitarian":"🏥",
}
INCIDENT_COLORS = {
    "airstrike":"rgba(255,61,90,.18)","ground":"rgba(255,140,66,.15)",
    "drone":"rgba(157,110,255,.15)","naval":"rgba(0,200,255,.15)",
    "rocket":"rgba(255,180,0,.15)","cyber":"rgba(0,200,255,.12)",
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
     "clues":["Depth below 70km is classified as shallow — causes strong surface shaking","Japan sits on an active subduction zone (Pacific Ring of Fire)","Japan Meteorological Agency issued a Level 3 coastal alert immediately"],
     "options":["Volcanic co-eruption in the same region","Tsunami risk along the coastline within 300km","Ground liquefaction in inland agricultural valleys","Atmospheric pressure shockwave"],"correct":1,
     "explain":"Shallow subduction-zone quakes near coastlines carry the highest tsunami risk. JMA protocols auto-issue coastal warnings for any M6+ shallow event on the Pacific coast."},
    {"id":"c2","pts":400,"difficulty":"AGENT","color":"#9d6eff","title":"CIVIL UNREST ASSESSMENT",
     "question":"The New Delhi protest has mobilised 200,000+ people over 72 hours and is rated CRITICAL. Which indicator MOST reliably signals imminent escalation?",
     "clues":["ACLED data: protests lasting >72h have 3× higher escalation probability","Government has initiated no dialogue so far","Coordinated hashtag campaigns detected across 12 states simultaneously"],
     "options":["Aerial photograph showing crowd density","Mobile data traffic spike inside the protest zone","Absence of counter-protest groups in the area","Weather forecast showing rain in the next 24h"],"correct":1,
     "explain":"Mobile network traffic anomalies reveal real-time command-and-control coordination — a key ACLED escalation precursor identified in 78% of documented escalation cases."},
    {"id":"c3","pts":350,"difficulty":"ANALYST","color":"#ff3d5a","title":"CONFLICT INTELLIGENCE",
     "question":"Satellite imagery shows abnormal vehicle movement along a supply route 48 hours before a documented offensive. Which OSINT method best corroborates this finding?",
     "clues":["Vehicle movement signals logistics buildup — consistent with pre-attack staging","The 48-hour lead time matches standard pre-offensive preparation windows","Dual-use infrastructure makes attribution difficult from a single source alone"],
     "options":["Social media geolocation of unit photos","Nighttime light increase in forward staging areas","Radio frequency spectrum anomaly detection","All three used together — convergent OSINT methodology"],"correct":3,
     "explain":"Convergent OSINT — combining SAR imagery, SOCMINT, SIGINT, and NIGHTINT — dramatically reduces false-positive rates. No single source alone is sufficient for confident assessment."},
    {"id":"c4","pts":500,"difficulty":"HANDLER","color":"#ffb400","title":"MULTI-SOURCE FUSION",
     "question":"Correlating M5.8 Vanuatu + La Niña ENSO pattern + New Delhi civil movement: which systemic risk does this triad most strongly indicate?",
     "clues":["La Niña typically causes below-average monsoon rainfall over South Asia","The M5.8 quake risks disrupting irrigation and agricultural infrastructure","200,000+ farmers are actively protesting crop price policies"],
     "options":["Near-term currency devaluation in South Asia","Food security and agricultural supply chain stress","Regional tourism sector collapse","Technology export restrictions from India"],"correct":1,
     "explain":"Seismic disruption + La Niña drought stress + politically activated farming communities = compound food-security risk signal. This pattern preceded the 2010–11 Arab Spring food crises per World Bank analysis."},
]

LEADERBOARD = [
    ("vectorx","HANDLER",18450,"#ff3d5a"),("sigint_reaper","AGENT",16220,"#9d6eff"),
    ("phantomhex","AGENT",14875,"#ffb400"),("n0de_k1ller","ANALYST",13100,"#ff8c42"),
    ("ghost_proto","ANALYST",9800,"#3d5a75"),
]

NEWS_SOURCES = [
    {"name":"Reuters World","cat":"global","color":"#ff8c42","rss":"https://feeds.reuters.com/reuters/worldNews","desc":"Global wire, 170+ countries"},
    {"name":"BBC World","cat":"global","color":"#bb1919","rss":"http://feeds.bbci.co.uk/news/world/rss.xml","desc":"BBC international news"},
    {"name":"Al Jazeera","cat":"global","color":"#00873c","rss":"https://www.aljazeera.com/xml/rss/all.xml","desc":"Middle East & Global South"},
    {"name":"AP News","cat":"global","color":"#cc0000","rss":"https://rsshub.app/apnews/topics/apf-WorldNews","desc":"Associated Press breaking news"},
    {"name":"NASA JPL","cat":"science","color":"#0b3d91","rss":"https://www.jpl.nasa.gov/feeds/news","desc":"NASA Earth & space science"},
    {"name":"USGS News","cat":"science","color":"#4caf50","rss":"https://www.usgs.gov/news/science-news/rss.xml","desc":"Earthquakes, volcanoes, hazards"},
    {"name":"Phys.org Earth","cat":"science","color":"#1a7fc1","rss":"https://phys.org/rss-feed/earth-news/","desc":"Earth science research"},
    {"name":"Foreign Policy","cat":"geopolitics","color":"#8b1a1a","rss":"https://foreignpolicy.com/feed/","desc":"International affairs & strategy"},
    {"name":"The Diplomat","cat":"geopolitics","color":"#1a3a5c","rss":"https://thediplomat.com/feed/","desc":"Asia-Pacific geopolitics"},
    {"name":"Defense One","cat":"geopolitics","color":"#444","rss":"https://www.defenseone.com/rss/all/","desc":"Defence & security news"},
    {"name":"ACLED Updates","cat":"conflict","color":"#c00","rss":"https://acleddata.com/feed/","desc":"Armed conflict event data"},
    {"name":"ISW Daily","cat":"conflict","color":"#800020","rss":"https://understandingwar.org/rss.xml","desc":"Institute for Study of War"},
    {"name":"CSIS Analysis","cat":"conflict","color":"#003366","rss":"https://www.csis.org/rss/analysis","desc":"Center for Strategic Studies"},
    {"name":"Carbon Brief","cat":"climate","color":"#1b5e20","rss":"https://www.carbonbrief.org/feed","desc":"Climate policy & science"},
    {"name":"SpaceWeather","cat":"spaceweather","color":"#4a148c","rss":"https://spaceweather.com/index.xml","desc":"Solar activity & geomagnetic storms"},
    {"name":"NOAA SWPC","cat":"spaceweather","color":"#0d47a1","rss":"https://www.swpc.noaa.gov/news/rss.xml","desc":"NOAA Space Weather Prediction"},
]
CATEGORIES = ["ALL","global","science","geopolitics","conflict","climate","spaceweather"]
CAT_LABELS = {"ALL":"All Sources","global":"🌐 Global Wire","science":"🔬 Earth Science","geopolitics":"🗺 Geopolitics","conflict":"⚔ Conflict","climate":"🌱 Climate","spaceweather":"☀ Space Weather"}
CAT_COLORS = {"global":"b-orange","science":"b-green","geopolitics":"b-red","conflict":"b-red","climate":"b-green","spaceweather":"b-violet","ALL":"b-cyan"}
CAT_NC     = {"global":"nc-general","science":"nc-seismic","geopolitics":"nc-civil","conflict":"nc-seismic","climate":"nc-volcanic","spaceweather":"nc-solar","general":"nc-general"}

# ─────────────────────────────────────────────────────────────
# DATA FETCHERS
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def fetch_usgs():
    try:
        r = requests.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson", timeout=8)
        r.raise_for_status()
        rows = []
        for f in r.json()["features"][:50]:
            p, c = f["properties"], f["geometry"]["coordinates"]
            rows.append({"title":p.get("title","—"),"mag":round(p.get("mag",0),1),"place":p.get("place","?"),
                         "depth_km":round(c[2],1),"lon":c[0],"lat":c[1],"type":"seismic",
                         "time":datetime.fromtimestamp(p["time"]/1000,tz=timezone.utc).strftime("%H:%Mz"),"url":p.get("url","")})
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
                    rows.append({"title":e["title"],"cat":cat,"date":geo["date"][:10],"lon":geo["coordinates"][0],"lat":geo["coordinates"][1],"type":"eonet"})
        return pd.DataFrame(rows) if rows else _se()
    except:
        return _se()

@st.cache_data(ttl=180, show_spinner=False)
def fetch_kp():
    try:
        r = requests.get("https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json", timeout=6)
        r.raise_for_status()
        data = r.json()
        return {"kp": float(data[-1][1]), "series": [float(x[1]) for x in data[-24:] if len(x) > 1]}
    except:
        return {"kp": 3.7, "series": [1,2,1.5,2.3,3.1,3.7,2.8,2.1,1.8,2.5,3,3.7]*2}

@st.cache_data(ttl=600, show_spinner=False)
def fetch_rss(url, source, cat="general"):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        items = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
        arts = []
        for item in items[:8]:
            def g(tag, txt):
                m = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', txt, re.DOTALL | re.IGNORECASE)
                if m:
                    v = m.group(1).strip()
                    v = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', v, flags=re.DOTALL)
                    return html_lib.unescape(re.sub(r'<[^>]+>', '', v)).strip()
                return ""
            title = g("title", item); desc = g("description", item)
            link = g("link", item);   pub  = g("pubDate", item)
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(pub)
                age = datetime.now(tz=timezone.utc) - dt.astimezone(timezone.utc)
                age_s = f"{int(age.total_seconds()//3600)}h ago" if age.total_seconds() > 3600 else f"{int(age.total_seconds()//60)}m ago"
            except:
                age_s = "recent"
            if title and len(title) > 10:
                arts.append({"source":source,"category":cat,"title":title[:120],"desc":(desc or "")[:220],"link":link,"time":age_s})
        return arts
    except:
        return []

def _sq():
    rng = np.random.default_rng(42)
    lats = rng.uniform(-55,70,30); lons = rng.uniform(-170,170,30)
    mags = rng.uniform(2.5,6.8,30); d = rng.uniform(5,120,30)
    pl = ["California","Japan","Indonesia","Chile","Turkey","Philippines","Papua New Guinea","Peru","Mexico","Greece"]
    return pd.DataFrame({
        "title": [f"M{m:.1f} — {pl[i%len(pl)]}" for i,m in enumerate(mags)],
        "mag": np.round(mags,1), "place": [pl[i%len(pl)] for i in range(30)],
        "depth_km": np.round(d,1), "lon": np.round(lons,3), "lat": np.round(lats,3),
        "time": [f"{rng.integers(0,24):02d}:{rng.integers(0,60):02d}z" for _ in range(30)],
        "type":"seismic", "url":""
    })

def _se():
    return pd.DataFrame([
        {"title":"Kilauea — Active Lava","cat":"Volcanoes","date":"2026-03-14","lon":-155.2,"lat":19.4,"type":"eonet"},
        {"title":"Etna — SO₂ Plume","cat":"Volcanoes","date":"2026-03-13","lon":15.0,"lat":37.8,"type":"eonet"},
        {"title":"Texas Wildfires","cat":"Wildfires","date":"2026-03-12","lon":-101.0,"lat":32.5,"type":"eonet"},
    ])

# ─────────────────────────────────────────────────────────────
# GLOBAL MAP  ← shown persistently above all tabs
# ─────────────────────────────────────────────────────────────
def build_global_map(eq_df, eonet_df, show_seis, show_volc, show_mvmt, show_conf, show_supply, show_heat):
    """Combined world map: seismic + conflict incidents + civil movements + supply arcs."""
    layers = []

    # ── Seismic layer ────────────────────────────────────────
    if show_seis and not eq_df.empty:
        def mc(m):
            if m >= 5.5: return [255, 55, 85, 220]
            if m >= 4.5: return [255, 180, 0, 200]
            if m >= 3.5: return [0, 230, 118, 175]
            return [0, 200, 255, 150]
        ep = eq_df.copy()
        ep["color"]  = ep["mag"].apply(mc)
        ep["radius"] = (ep["mag"] ** 2.3 * 15000).clip(10000, 240000)
        ep["tip"]    = ep.apply(lambda r: f"⬡ SEISMIC  M{r['mag']} | {r['place']} | Depth {r['depth_km']}km | {r['time']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=ep, get_position=["lon","lat"],
                                 get_radius="radius", get_fill_color="color",
                                 get_line_color=[255,255,255,30], line_width_min_pixels=1,
                                 pickable=True, auto_highlight=True))

    # ── EONET / Volcanic layer ───────────────────────────────
    if show_volc and not eonet_df.empty:
        eo = eonet_df.copy()
        eo["color"]  = [[255, 110, 40, 200]] * len(eo)
        eo["radius"] = 70000
        eo["tip"]    = eo.apply(lambda r: f"▲ EONET  {r['title']} | {r['cat']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=eo, get_position=["lon","lat"],
                                 get_radius="radius", get_fill_color="color",
                                 pickable=True, auto_highlight=True))

    # ── Conflict incidents layer ─────────────────────────────
    if show_conf:
        conf_rows = []
        for cname, c in CONFLICTS.items():
            for inc in c["incidents"]:
                conf_rows.append({**inc, "conflict": cname})
        if conf_rows:
            cdf = pd.DataFrame(conf_rows)
            sev_col = {"CRITICAL":[255,40,70,230],"HIGH":[255,120,40,200],"MED":[255,170,0,170],"LOW":[0,220,110,150],"INFO":[0,190,255,120]}
            cdf["color"]  = cdf["severity"].map(sev_col)
            cdf["radius"] = cdf["severity"].map({"CRITICAL":100000,"HIGH":75000,"MED":55000,"LOW":40000,"INFO":30000})
            cdf["tip"]    = cdf.apply(lambda r: f"⚔ {r['conflict']} | {INCIDENT_ICONS.get(r['type'],'●')} {r['title']} | {r['loc']} | {r['severity']}", axis=1)
            layers.append(pdk.Layer("ScatterplotLayer", data=cdf, get_position=["lon","lat"],
                                     get_radius="radius", get_fill_color="color",
                                     pickable=True, auto_highlight=True))

    # ── Civil movements layer ────────────────────────────────
    if show_mvmt:
        mdf = pd.DataFrame(MOVEMENTS)
        mdf["color"]  = mdf["sentiment"].map({"CRIT":[200,60,255,200],"HIGH":[157,110,255,185],"MED":[120,80,220,165]})
        mdf["radius"] = mdf["scale"] * 1800
        mdf["tip"]    = mdf.apply(lambda r: f"✊ CIVIL  {r['title']} | {r['location']} | {r['size']} participants | {r['sentiment']}", axis=1)
        layers.append(pdk.Layer("ScatterplotLayer", data=mdf, get_position=["lon","lat"],
                                 get_radius="radius", get_fill_color="color",
                                 pickable=True, auto_highlight=True))

    # ── Supply arc layer ─────────────────────────────────────
    if show_supply:
        arc_rows = []
        for c in CONFLICTS.values():
            arc_rows.extend(c["supply_lines"])
        if arc_rows:
            adf = pd.DataFrame(arc_rows)
            adf["color"] = adf["type"].map({
                "Military Aid":[255,61,90,160], "Arms/Funding":[255,61,90,160],
                "RSF Support":[255,140,66,140], "SAF Support":[0,200,255,140],
                "Junta Support":[255,61,90,140],"Arms Supply":[255,180,0,140],
                "Humanitarian":[0,230,118,150],
            }).apply(lambda x: x if isinstance(x, list) else [74,107,133,120])
            layers.append(pdk.Layer("ArcLayer", data=adf,
                                     get_source_position=["from_lon","from_lat"],
                                     get_target_position=["to_lon","to_lat"],
                                     get_source_color="color", get_target_color="color",
                                     get_width=2, pickable=True, auto_highlight=True))

    # ── Heatmap layer ────────────────────────────────────────
    if show_heat and not eq_df.empty:
        layers.append(pdk.Layer("HeatmapLayer",
                                 data=eq_df[["lat","lon","mag"]].rename(columns={"mag":"weight"}),
                                 get_position=["lon","lat"], get_weight="weight",
                                 radiusPixels=50, opacity=0.45))

    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=22, longitude=18, zoom=1.4, pitch=0),
        map_style="mapbox://styles/mapbox/dark-v11",
        tooltip={"text": "{tip}", "style": {
            "backgroundColor": "#080f1c", "color": "#e2ecf8",
            "border": "1px solid rgba(0,200,255,.2)",
            "fontFamily": "IBM Plex Mono", "fontSize": "12px",
            "padding": "10px 14px", "borderRadius": "8px",
        }},
        height=420,
    )

# ─────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────
def kp_chart(s):
    f = go.Figure()
    f.add_trace(go.Scatter(x=list(range(len(s))), y=s, mode="lines",
                            line=dict(color="#00c8ff", width=2),
                            fill="tozeroy", fillcolor="rgba(0,200,255,.07)"))
    f.add_hline(y=5, line_dash="dash", line_color="rgba(255,61,90,.5)", line_width=1.5,
                annotation_text="Storm threshold (Kp 5)", annotation_font=dict(color="#ff3d5a", size=9))
    f.update_layout(height=90, margin=dict(l=0,r=0,t=0,b=0), **bg_chart(),
                    showlegend=False, xaxis=dict(visible=False),
                    yaxis=dict(visible=False, range=[0,9]))
    return f

def mag_hist(eq):
    f = go.Figure(go.Histogram(x=eq["mag"], nbinsx=14, marker_color="#00c8ff",
                                opacity=.65, marker_line_width=0))
    f.update_layout(height=150, margin=dict(l=0,r=0,t=0,b=0), **bg_chart(),
                    xaxis=dict(**ax(), title="Magnitude"), yaxis=dict(**ax()), bargap=.08)
    return f

def mv_bar(mv):
    df = pd.DataFrame(mv).sort_values("scale", ascending=True)
    colors = df["sentiment"].map({"CRIT":"#ff3d5a","HIGH":"#ff8c42","MED":"#ffb400"})
    f = go.Figure(go.Bar(y=df["location"].str.split(",").str[0],
                          x=df["scale"], orientation="h",
                          marker_color=colors, marker_line_width=0))
    f.update_layout(height=220, margin=dict(l=0,r=0,t=0,b=0), **bg_chart(),
                    xaxis=dict(**ax(), range=[0,100]), yaxis=dict(color="#dde8f5", tickfont_size=11))
    return f

def mag_donut(eq):
    b = {"M2.5–3.4": len(eq[(eq.mag>=2.5)&(eq.mag<3.5)]),
         "M3.5–4.4": len(eq[(eq.mag>=3.5)&(eq.mag<4.5)]),
         "M4.5–5.4": len(eq[(eq.mag>=4.5)&(eq.mag<5.5)]),
         "M5.5+":    len(eq[eq.mag>=5.5])}
    f = go.Figure(go.Pie(labels=list(b.keys()), values=list(b.values()), hole=.6,
                          marker_colors=["#00e676","#00c8ff","#ffb400","#ff3d5a"],
                          textfont_size=11, textinfo="label+percent"))
    f.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0), **bg_chart(), showlegend=False)
    return f

def escalation_gauge(val, label, color):
    f = go.Figure(go.Indicator(
        mode="gauge+number", value=val,
        gauge=dict(axis=dict(range=[0,100], tickcolor="#4a6b85", tickfont=dict(size=9,color="#4a6b85")),
                   bar=dict(color=color, thickness=.28), bgcolor="rgba(0,0,0,0)", borderwidth=0,
                   steps=[dict(range=[0,30],color="rgba(0,230,118,.07)"),
                           dict(range=[30,60],color="rgba(255,180,0,.07)"),
                           dict(range=[60,80],color="rgba(255,140,66,.07)"),
                           dict(range=[80,100],color="rgba(255,61,90,.07)")],
                   threshold=dict(line=dict(color=color,width=2),thickness=.75,value=val)),
        number=dict(font=dict(family="Bebas Neue",size=40,color=color)),
        title=dict(text=label, font=dict(family="IBM Plex Mono",size=9,color="#4a6b85")),
    ))
    f.update_layout(height=190, margin=dict(l=10,r=10,t=30,b=10), **bg_chart())
    return f

def conflict_timeline_chart(tl):
    type_colors = {"escalation":"#ff3d5a","milestone":"#00c8ff","diplomatic":"#00e676","setback":"#ffb400","ongoing":"#9d6eff"}
    colors = [type_colors.get(t["type"],"#4a6b85") for t in tl]
    events = [t["event"] for t in tl]
    dates  = [t["date"]  for t in tl]
    f = go.Figure()
    f.add_trace(go.Scatter(x=dates, y=[1]*len(dates), mode="lines",
                            line=dict(color="#0f2035", width=2), showlegend=False))
    f.add_trace(go.Scatter(x=dates, y=[1]*len(dates), mode="markers+text",
                            text=[e[:28]+"…" if len(e)>28 else e for e in events],
                            textposition="top center",
                            textfont=dict(size=9, color="#4a6b85"),
                            marker=dict(size=11, color=colors, line=dict(width=1.5, color="#0f2035")),
                            hovertext=events, hoverinfo="text+x", showlegend=False))
    f.update_layout(height=180, margin=dict(l=0,r=0,t=30,b=0), **bg_chart(), showlegend=False,
                    xaxis=dict(**ax()), yaxis=dict(visible=False))
    return f

def casualty_chart():
    names  = [n.split(" ")[0] for n in CONFLICTS.keys()]
    cas    = [c["casualties_total"] for c in CONFLICTS.values()]
    dis    = [c["displaced"]        for c in CONFLICTS.values()]
    f = go.Figure()
    f.add_trace(go.Bar(name="Casualties", x=names, y=cas, marker_color="#ff3d5a", opacity=.85, marker_line_width=0))
    f.add_trace(go.Bar(name="Displaced",  x=names, y=dis, marker_color="#ffb400", opacity=.7,  marker_line_width=0))
    f.update_layout(height=220, margin=dict(l=0,r=0,t=10,b=0), **bg_chart(), barmode="group",
                    legend=dict(font=dict(color="#4a6b85",size=10), bgcolor="rgba(0,0,0,0)"),
                    xaxis=ax(), yaxis=ax())
    return f

def media_bias_chart(sources):
    cols = []
    for s in sources:
        b = s["bias"].lower()
        if "state" in b or "junta" in b: cols.append("#ff3d5a")
        elif "pro-" in b:                 cols.append("#ffb400")
        elif "centre" in b or "center" in b: cols.append("#00c8ff")
        elif "left" in b:                 cols.append("#9d6eff")
        elif "right" in b:                cols.append("#ff8c42")
        else:                             cols.append("#4a6b85")
    f = go.Figure(go.Bar(x=[s["name"] for s in sources], y=[s["reliability"] for s in sources],
                          marker_color=cols, marker_line_width=0, opacity=.85,
                          text=[s["reliability"] for s in sources],
                          textfont=dict(size=9,color="#e2ecf8"), textposition="outside"))
    f.update_layout(height=180, margin=dict(l=0,r=0,t=10,b=30), **bg_chart(),
                    xaxis=dict(**ax(), tickangle=-30), yaxis=dict(**ax(), range=[0,105]))
    return f

# ─────────────────────────────────────────────────────────────
# AI CALLER
# ─────────────────────────────────────────────────────────────
def call_ai(prompt, provider, api_key):
    if provider == "groq" and api_key:
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                json={"model":"llama-3.1-8b-instant","max_tokens":400,
                      "messages":[{"role":"system","content":"You are a concise OSINT intelligence analyst. Respond in plain text only, no markdown, max 380 words."},
                                   {"role":"user","content":prompt}]}, timeout=15)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e: return f"[Groq error: {e}]"
    if provider == "ollama":
        try:
            r = requests.post("http://localhost:11434/api/generate",
                json={"model":"llama3","prompt":prompt,"stream":False}, timeout=25)
            return r.json().get("response","No response")
        except Exception as e: return f"[Ollama error — is it running? {e}]"
    if provider == "openrouter" and api_key:
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization":f"Bearer {api_key}","HTTP-Referer":"https://osint-arena.app","Content-Type":"application/json"},
                json={"model":"meta-llama/llama-3.1-8b-instruct:free","max_tokens":400,
                      "messages":[{"role":"user","content":prompt}]}, timeout=16)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e: return f"[OpenRouter error: {e}]"
    return "⚠  No AI provider configured. Select Groq, Ollama, or OpenRouter in the sidebar and add your API key."

# ─────────────────────────────────────────────────────────────
# FETCH LIVE DATA
# ─────────────────────────────────────────────────────────────
eq_df    = fetch_usgs()
eonet_df = fetch_eonet()
kp_data  = fetch_kp()
utc_now  = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="wordmark" style="margin-bottom:4px">OSINT<em>ARENA</em></div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;color:var(--muted);letter-spacing:.12em;font-weight:600;margin-bottom:16px">GLOBAL INTELLIGENCE PLATFORM</p>', unsafe_allow_html=True)

    tn, tc, tcol = get_tier(st.session_state.score)
    nt = {"RECRUIT":2000,"ANALYST":5000,"AGENT":10000,"HANDLER":10000}[tn]
    xp_pct = min(100, int(st.session_state.score / nt * 100))

    st.markdown(f"""
    <div class="m-panel">
      <div class="m-label">Your Analyst Profile</div>
      <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:6px">
        <div class="m-val m-violet" style="font-size:30px">{st.session_state.score:,}</div>
        <div class="badge {tc}" style="font-size:11px">{tn}</div>
      </div>
      <div class="xp-track"><div class="xp-fill" style="width:{xp_pct}%"></div></div>
      <div class="m-sub" style="margin-top:5px">{xp_pct}% complete — next tier at {nt:,} XP</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)

    # ── AI config ────────────────────────────────────────────
    st.markdown("#### 🤖 AI Provider")
    st.markdown('<p style="font-size:11px;color:var(--muted);margin-bottom:8px">Select a provider to enable AI analysis and situation reports.</p>', unsafe_allow_html=True)
    prov = st.selectbox("AI Provider", ["groq","ollama","openrouter","none"], label_visibility="collapsed")
    st.session_state.ai_provider = prov
    if prov in ("groq","openrouter"):
        st.session_state.ai_key = st.text_input("API Key", type="password", placeholder="Paste your API key here…", label_visibility="collapsed")
        if prov == "groq":
            st.markdown('<p style="font-size:11px;color:var(--muted)">Get a free key at console.groq.com</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="font-size:11px;color:var(--muted)">Get a free key at openrouter.ai</p>', unsafe_allow_html=True)
    elif prov == "ollama":
        st.info("Ollama runs locally. Start with: `ollama pull llama3 && ollama serve`")

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)

    # ── Map layer toggles ────────────────────────────────────
    st.markdown("#### 🗺 Global Map Layers")
    st.markdown('<p style="font-size:11px;color:var(--muted);margin-bottom:8px">Toggle what appears on the global command map above.</p>', unsafe_allow_html=True)
    show_seis  = st.toggle("🟦 Seismic Events",    value=True)
    show_volc  = st.toggle("🟠 Volcanic / EONET",  value=True)
    show_conf  = st.toggle("🔴 Conflict Incidents", value=True)
    show_mvmt  = st.toggle("🟣 Civil Movements",   value=True)
    show_supp  = st.toggle("⟶ Supply Arc Lines",   value=True)
    show_heat  = st.toggle("🌡 Heatmap Mode",       value=False)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)

    # ── Data status ──────────────────────────────────────────
    st.markdown("#### 📡 Live Data Status")
    data_ok = not eq_df.empty
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;gap:7px">
      <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text2)">
        <span class="pulse {'p-green' if data_ok else 'p-amber'}"></span>
        USGS Earthquakes <span style="color:var(--muted);font-size:11px;margin-left:auto">{len(eq_df)} events</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text2)">
        <span class="pulse {'p-green' if not eonet_df.empty else 'p-amber'}"></span>
        NASA EONET Events <span style="color:var(--muted);font-size:11px;margin-left:auto">{len(eonet_df)} events</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text2)">
        <span class="pulse p-amber"></span>
        NOAA Kp Index <span style="color:var(--muted);font-size:11px;margin-left:auto">Kp {kp_data['kp']:.1f}</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text2)">
        <span class="pulse p-cyan"></span>
        RSS Feeds <span style="color:var(--muted);font-size:11px;margin-left:auto">{len(NEWS_SOURCES)} sources</span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;font-size:12px;color:var(--text2)">
        <span class="pulse p-red"></span>
        Conflict Theatres <span style="color:var(--muted);font-size:11px;margin-left:auto">{len(CONFLICTS)} tracked</span>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="sb-div"></div>', unsafe_allow_html=True)
    if st.button("⟳  Refresh All Feeds", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
m5p          = eq_df[eq_df["mag"] >= 5.0]
crit_mv      = [m for m in MOVEMENTS if m["sentiment"] == "CRIT"]
kp           = kp_data["kp"]
active_conf  = len([c for c in CONFLICTS.values() if c["status"] == "ACTIVE"])
total_cas    = sum(c["casualties_total"] for c in CONFLICTS.values())

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
    <div style="font-size:11px;color:var(--muted);margin-top:2px">All times in UTC</div>
  </div>
</div>
<div class="status-row">
  <span><span class="pulse p-green"></span>Feeds Live</span>
  <span><span class="pulse p-red"></span>{active_conf} Active Conflicts</span>
  <span><span class="pulse p-cyan"></span>{len(eq_df)} Seismic Events (24h)</span>
  <span><span class="pulse p-{'red' if len(crit_mv)>0 else 'amber'}"></span>{len(crit_mv)} Critical Movements</span>
  <span><span class="pulse p-{'red' if kp>=5 else 'amber'}"></span>Kp {kp:.1f} {'⚠ Storm Watch' if kp>=5 else ''}</span>
</div>""", unsafe_allow_html=True)

# METRICS ROW
c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1: st.metric("Active Conflicts",    active_conf,           delta="LIVE MONITORING")
with c2: st.metric("Total Casualties",    f"{total_cas:,}",      delta="All theatres")
with c3: st.metric("Seismic Events (24h)",len(eq_df),            delta=f"M5.0+: {len(m5p)}")
with c4: st.metric("Civil Movements",     len(MOVEMENTS),        delta=f"Critical: {len(crit_mv)}")
with c5: st.metric("Geomagnetic Kp",      f"{kp:.1f}",           delta="Storm threshold: 5.0")
with c6: st.metric("Your Analyst XP",     f"{st.session_state.score:,}", delta=tn)

st.markdown("---")

# ═════════════════════════════════════════════════════════════
# PERSISTENT GLOBAL MAP  ← always visible above all tabs
# ═════════════════════════════════════════════════════════════
total_incidents = sum(len(c["incidents"]) for c in CONFLICTS.values())
conf_crit_inc   = sum(1 for c in CONFLICTS.values() for i in c["incidents"] if i["severity"]=="CRITICAL")

st.markdown(f"""
<div class="map-header" style="background:var(--panel);border:1px solid var(--border);border-radius:14px 14px 0 0;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:14px">
    <div class="map-title">🌐 GLOBAL COMMAND VIEW</div>
    <div style="font-family:var(--fm);font-size:11px;color:var(--muted)">
      All active signals · Click any marker for details
    </div>
  </div>
  <div class="map-legend">
    <div class="legend-item"><div class="legend-dot" style="background:#00c8ff"></div><span>Seismic</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff6a28"></div><span>Volcanic</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#ff3d5a"></div><span>Conflict</span></div>
    <div class="legend-item"><div class="legend-dot" style="background:#9d6eff"></div><span>Civil</span></div>
    <div class="legend-item" style="margin-left:8px;padding-left:8px;border-left:1px solid var(--bord2)">
      <span class="pulse p-red"></span>{conf_crit_inc} CRITICAL
    </div>
    <div class="legend-item">
      <span class="pulse p-cyan"></span>{len(eq_df)} seismic
    </div>
    <div class="legend-item">
      <span class="pulse p-orange"></span>{total_incidents} incidents
    </div>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown('<div style="border:1px solid var(--border);border-top:none;border-radius:0 0 14px 14px;overflow:hidden;margin-bottom:20px">', unsafe_allow_html=True)
st.pydeck_chart(
    build_global_map(eq_df, eonet_df, show_seis, show_volc, show_mvmt, show_conf, show_supp, show_heat),
    use_container_width=True
)
st.markdown('</div>', unsafe_allow_html=True)

# TICKER
ticker_bits = (
    [f'<span class="t-red t-hi">⚔ {n}: {c["intensity"]}</span>' for n, c in CONFLICTS.items()] +
    [f'<span class="t-red">M{r.mag} {r.place[:28]}</span>' for _, r in eq_df.nlargest(5,"mag").iterrows()] +
    [f'<span class="t-amb">✊ {m["title"]} — {m["location"]}</span>' for m in MOVEMENTS[:4]]
)
tc_str = '<span class="t-sep"> ◈ </span>'.join(ticker_bits)
st.markdown(f'<div class="ticker-wrap"><div class="ticker-inner">{tc_str}<span class="t-sep"> ◈ </span>{tc_str}</div></div>', unsafe_allow_html=True)
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
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
      <b>How to use this tab:</b> Select a conflict theatre below to explore its incident map,
      faction breakdown, timeline, and supply lines. Use the AI Sitrep generator at the bottom
      to create intelligence reports for any theatre.
    </div>""", unsafe_allow_html=True)

    # Theatre selector
    theatre = st.radio(
        "Select a conflict theatre to analyse:",
        list(CONFLICTS.keys()),
        horizontal=True,
        key="theatre_sel",
    )
    st.session_state.selected_conflict = theatre
    C = CONFLICTS[theatre]

    int_col = {"CRITICAL":"m-red","HIGH":"m-orange","MED":"m-amber"}

    # Theatre overview strip
    o1,o2,o3,o4 = st.columns(4)
    esc = C["escalation"]
    esc_col = "#ff3d5a" if esc>=80 else "#ff8c42" if esc>=60 else "#ffb400" if esc>=40 else "#00e676"
    with o1: st.metric("Status",      C["status"],    delta=C["region"])
    with o2: st.metric("Intensity",   C["intensity"], delta=f"Since {C['start']}")
    with o3: st.metric("Casualties",  f"{C['casualties_total']:,}", delta="estimated total")
    with o4: st.metric("Displaced",   f"{C['displaced']:,}",        delta="persons")

    st.markdown(f"""
    <div class="gcard" style="margin:12px 0">
      <div style="font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:6px">{C['region']}</div>
      <div style="font-size:14px;color:var(--text2);line-height:1.7">{C['description']}</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Row 1: Theatre map + gauges
    map_c, esc_c, cas_c = st.columns([3,1,1], gap="medium")

    with map_c:
        st.markdown(f'<div class="sec-label">📍 Incident Map — {theatre}</div>', unsafe_allow_html=True)

        # Build theatre map
        inc_df = pd.DataFrame(C["incidents"])
        sev_col_map = {"CRITICAL":[255,40,70,230],"HIGH":[255,120,40,200],"MED":[255,170,0,170],"LOW":[0,220,110,150],"INFO":[0,190,255,120]}
        inc_df["color"]  = inc_df["severity"].map(sev_col_map)
        inc_df["radius"] = inc_df["severity"].map({"CRITICAL":60000,"HIGH":45000,"MED":35000,"LOW":25000,"INFO":20000})
        inc_df["tip"]    = inc_df.apply(lambda r: f"{INCIDENT_ICONS.get(r['type'],'●')} {r['title']}\n{r['loc']} · {r['date']}\nSeverity: {r['severity']} · Casualties: {r['casualties']}", axis=1)

        theatre_layers = [pdk.Layer("ScatterplotLayer", data=inc_df, get_position=["lon","lat"],
                                     get_radius="radius", get_fill_color="color",
                                     get_line_color=[255,255,255,40], line_width_min_pixels=1,
                                     pickable=True, auto_highlight=True)]
        if show_supp:
            adf = pd.DataFrame(C["supply_lines"])
            if not adf.empty:
                adf["color"] = adf["type"].map({
                    "Military Aid":[255,61,90,160],"Arms/Funding":[255,61,90,160],
                    "RSF Support":[255,140,66,140],"SAF Support":[0,200,255,140],
                    "Junta Support":[255,61,90,140],"Arms Supply":[255,180,0,140],
                    "Humanitarian":[0,230,118,150],
                }).apply(lambda x: x if isinstance(x,list) else [74,107,133,120])
                theatre_layers.append(pdk.Layer("ArcLayer", data=adf,
                    get_source_position=["from_lon","from_lat"],
                    get_target_position=["to_lon","to_lat"],
                    get_source_color="color", get_target_color="color",
                    get_width=2, pickable=True, auto_highlight=True))

        cx = np.mean([i["lon"] for i in C["incidents"]])
        cy = np.mean([i["lat"] for i in C["incidents"]])
        theatre_deck = pdk.Deck(layers=theatre_layers,
            initial_view_state=pdk.ViewState(latitude=cy, longitude=cx, zoom=4, pitch=20),
            map_style="mapbox://styles/mapbox/dark-v11",
            tooltip={"text":"{tip}","style":{"backgroundColor":"#080f1c","color":"#e2ecf8","border":"1px solid rgba(255,61,90,.3)","fontFamily":"IBM Plex Mono","fontSize":"12px","padding":"10px","borderRadius":"8px"}},
            height=380)
        st.pydeck_chart(theatre_deck, use_container_width=True)

    with esc_c:
        st.markdown('<div class="sec-label">Escalation Index</div>', unsafe_allow_html=True)
        st.plotly_chart(escalation_gauge(esc, "ESCALATION /100", esc_col),
                        use_container_width=True, config={"displayModeBar":False})
        esc_lbl = "CRITICAL" if esc>=80 else "HIGH" if esc>=60 else "ELEVATED" if esc>=40 else "LOW"
        st.markdown(f"""
        <div class="m-panel" style="text-align:center;padding:12px">
          <div class="badge {'b-red' if esc>=80 else 'b-orange' if esc>=60 else 'b-amber'}" style="font-size:11px">{esc_lbl} RISK</div>
          <div class="m-sub" style="margin-top:8px">Ceasefire active:</div>
          <div style="font-size:14px;font-weight:600;color:{'var(--green)' if C['ceasefire'] else 'var(--red)'}">
            {'✓ YES' if C['ceasefire'] else '✗ NONE'}
          </div>
        </div>""", unsafe_allow_html=True)

    with cas_c:
        st.markdown('<div class="sec-label">Human Cost</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="m-panel" style="text-align:center;padding:16px 12px;margin-bottom:10px">
          <div class="m-label">Est. Casualties</div>
          <div class="m-val m-red" style="font-size:28px">{C['casualties_total']:,}</div>
        </div>
        <div class="m-panel" style="text-align:center;padding:16px 12px">
          <div class="m-label">Displaced</div>
          <div class="m-val m-amber" style="font-size:28px">{C['displaced']:,}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Row 2: Incident Feed + Faction Tracker
    inc_c, fac_c = st.columns([3,2], gap="medium")

    with inc_c:
        st.markdown('<div class="sec-label">📋 Incident Feed</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:12px;color:var(--muted);margin-bottom:10px">Filter by incident type to focus on specific event categories.</p>', unsafe_allow_html=True)
        inc_filter = st.radio("Filter incidents by type:",
                               ["ALL","airstrike","ground","drone","naval","rocket","cyber","humanitarian","diplomatic"],
                               horizontal=True, label_visibility="visible", key="inc_filter")
        for inc in C["incidents"]:
            if inc_filter != "ALL" and inc["type"] != inc_filter:
                continue
            icon = INCIDENT_ICONS.get(inc["type"],"●")
            ic   = INCIDENT_COLORS.get(inc["type"],"rgba(74,107,133,.12)")
            sev  = SEV_BADGE.get(inc["severity"],"b-muted")
            cas_note = f"  ·  {inc['casualties']} casualties" if inc["casualties"] > 0 else ""
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
        st.markdown('<p style="font-size:12px;color:var(--muted);margin-bottom:10px">Key belligerents, territory control, and external support.</p>', unsafe_allow_html=True)
        for fac in C["factions"]:
            stat_badge = "b-red" if fac["status"] in ("Offensive","Advancing") else "b-cyan" if fac["status"] == "Defending" else "b-amber"
            st.markdown(f"""
            <div class="conflict-card">
              <div class="cc-header">
                <div style="display:flex;align-items:center;gap:8px">
                  <div style="width:10px;height:10px;border-radius:50%;background:{fac['color']};box-shadow:0 0 6px {fac['color']}55"></div>
                  <div class="cc-title">{fac['name']}</div>
                </div>
                <div class="badge {stat_badge}">{fac['status']}</div>
              </div>
              <div class="cc-body">
                <div style="display:flex;gap:16px;margin-bottom:10px;flex-wrap:wrap">
                  <div>
                    <div class="m-label" style="font-size:9px">Territory</div>
                    <div style="font-family:var(--fm);font-size:14px;color:{fac['color']};font-weight:500">{fac['territory_pct']}%</div>
                  </div>
                  <div>
                    <div class="m-label" style="font-size:9px">Strength</div>
                    <div style="font-family:var(--fm);font-size:14px;color:var(--text2)">{fac['strength']}</div>
                  </div>
                  <div>
                    <div class="m-label" style="font-size:9px">Backed by</div>
                    <div style="font-size:12px;color:var(--muted)">{', '.join(fac['support'][:3])}</div>
                  </div>
                </div>
                <div style="height:5px;background:var(--dim);border-radius:3px;overflow:hidden;margin-bottom:8px">
                  <div style="height:100%;width:{fac['territory_pct']}%;background:{fac['color']}66;border-radius:3px"></div>
                </div>
                <div style="font-size:12px;color:var(--muted)">Key assets: {', '.join(fac['weapons'][:3])}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Row 3: Timeline + Supply + Media
    tl_c, side_c = st.columns([2,1], gap="medium")

    with tl_c:
        st.markdown('<div class="sec-label">📅 Conflict Timeline</div>', unsafe_allow_html=True)
        st.plotly_chart(conflict_timeline_chart(C["timeline"]), use_container_width=True, config={"displayModeBar":False})

        # Legend
        st.markdown("""
        <div style="display:flex;gap:14px;margin-bottom:12px;flex-wrap:wrap">
          <div style="font-size:11px;color:#ff3d5a">● Escalation</div>
          <div style="font-size:11px;color:#00c8ff">● Milestone</div>
          <div style="font-size:11px;color:#00e676">● Diplomatic</div>
          <div style="font-size:11px;color:#ffb400">● Setback</div>
          <div style="font-size:11px;color:#9d6eff">● Ongoing</div>
        </div>""", unsafe_allow_html=True)

        tl_type_col = {"escalation":"var(--red)","milestone":"var(--cyan)","diplomatic":"var(--green)","setback":"var(--amber)","ongoing":"var(--violet)"}
        st.markdown('<div class="timeline">', unsafe_allow_html=True)
        for item in reversed(C["timeline"]):
            col = tl_type_col.get(item["type"], "var(--muted)")
            st.markdown(f"""
            <div class="tl-item">
              <div class="tl-dot" style="background:{col};border-color:{col}55"></div>
              <div class="tl-date">{item['date']}</div>
              <div class="tl-text">{item['event']}</div>
              <div class="tl-tag" style="color:{col}">{item['type'].upper()}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with side_c:
        st.markdown('<div class="sec-label">⟶ Supply & Support</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:12px;color:var(--muted);margin-bottom:10px">External actors providing material support to each side.</p>', unsafe_allow_html=True)
        for sl in C["supply_lines"]:
            is_mil = any(k in sl["type"] for k in ["Mil","Arms","RSF","Junta"])
            t_cls  = "b-red" if is_mil else "b-green"
            st.markdown(f"""
            <div class="gcard" style="padding:12px 14px;margin-bottom:8px">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
                <div class="badge {t_cls}">{sl['type']}</div>
                <div style="font-size:13px;font-weight:600;color:var(--text2)">{sl['provider']}</div>
              </div>
              <div class="sig-meta">Route: ({sl['from_lat']:.1f}°, {sl['from_lon']:.1f}°) → ({sl['to_lat']:.1f}°, {sl['to_lon']:.1f}°)</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-label" style="margin-top:16px">📰 Media Reliability</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:12px;color:var(--muted);margin-bottom:8px">Source reliability scores and editorial bias classification.</p>', unsafe_allow_html=True)
        st.plotly_chart(media_bias_chart(C["media_sources"]), use_container_width=True, config={"displayModeBar":False})
        st.markdown("""
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:4px">
          <div style="font-size:11px;color:#00c8ff">■ Centre</div>
          <div style="font-size:11px;color:#9d6eff">■ Centre-Left</div>
          <div style="font-size:11px;color:#ff8c42">■ Right/Party</div>
          <div style="font-size:11px;color:#ff3d5a">■ State media</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Row 4: Cross-theatre analytics + Risk matrix
    st.markdown('<div class="sec-label">📊 Cross-Theatre Analytics</div>', unsafe_allow_html=True)
    a1, a2 = st.columns([1,1], gap="medium")
    with a1:
        st.markdown("**Casualties & Displacement by Theatre**")
        st.plotly_chart(casualty_chart(), use_container_width=True, config={"displayModeBar":False})
    with a2:
        st.markdown("**Risk Assessment Matrix**")
        risk_dims   = ["Escalation","Humanitarian","Spillover","WMD Risk","Ceasefire","Intervention"]
        risk_scores = {
            "Ukraine–Russia War": [87,75,80,45,15,82],
            "Gaza Conflict":      [92,95,78,20,20,68],
            "Sudan Civil War":    [74,90,55,5,25,35],
            "Myanmar Civil War":  [68,72,40,5,30,22],
        }
        risk_cols = st.columns(len(CONFLICTS))
        for i, (cname, rcol) in enumerate(zip(CONFLICTS.keys(), risk_cols)):
            scores = risk_scores.get(cname, [50]*6)
            with rcol:
                short = cname.split("–")[0].split(" ")[0][:8]
                st.markdown(f'<div style="font-family:var(--fm);font-size:10px;color:var(--muted);margin-bottom:8px;text-align:center;font-weight:600">{short}</div>', unsafe_allow_html=True)
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
    st.markdown(f'<p style="font-size:13px;color:var(--text2);margin-bottom:12px">Generate an AI-authored intelligence brief for <b>{theatre}</b>. Requires an AI provider configured in the sidebar.</p>', unsafe_allow_html=True)
    sr1, sr2 = st.columns([1,1], gap="medium")
    with sr1:
        sitrep_type = st.selectbox("Report type", [
            "Executive Summary — 3 paragraphs",
            "Escalation Risk Assessment",
            "Humanitarian Impact Brief",
            "Supply Chain & External Support Analysis",
            "Media Bias & Information Environment Report",
            "Ceasefire / Diplomatic Prospects",
        ], label_visibility="visible")
        if st.button(f"⚡  Generate Sitrep for {theatre.split('–')[0].strip()}", use_container_width=True):
            fac_s = "\n".join([f"  - {f['name']} ({f['side']}): {f['status']}, {f['territory_pct']}% territory, backed by {', '.join(f['support'])}" for f in C["factions"]])
            inc_s = "\n".join([f"  - {i['date']} [{i['type']}]: {i['title']} ({i['severity']}, {i['casualties']} cas.)" for i in C["incidents"][:5]])
            prompt = (f"Write a '{sitrep_type}' for the {theatre}.\n\n"
                      f"CURRENT DATA:\nStatus: {C['status']} | Intensity: {C['intensity']} | Escalation: {C['escalation']}/100\n"
                      f"Casualties: {C['casualties_total']:,} | Displaced: {C['displaced']:,} | Ceasefire: {'Yes' if C['ceasefire'] else 'No'}\n\n"
                      f"FACTIONS:\n{fac_s}\n\nRECENT INCIDENTS:\n{inc_s}\n\n"
                      f"Plain text, professional intelligence style, no markdown, 250–380 words.")
            with st.spinner("Generating intelligence report…"):
                result = call_ai(prompt, st.session_state.ai_provider, st.session_state.ai_key)
            st.session_state.conflict_sitrep = result
    with sr2:
        if st.session_state.conflict_sitrep:
            st.markdown(f'<div class="ai-terminal">{st.session_state.conflict_sitrep}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="gcard" style="padding:24px;text-align:center;min-height:180px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px">
              <div style="font-size:28px">📄</div>
              <div style="font-size:14px;color:var(--text2);font-weight:500">No report generated yet</div>
              <div style="font-size:12px;color:var(--muted);max-width:280px">Select a report type and click Generate to create an AI-authored situation report for {theatre}.</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 2 — EARTH SIGNALS
# ══════════════════════════════════════════════════════════════
with tab_earth:
    st.markdown("""
    <div class="helper">
      <b>Earth Signals</b> monitors seismic activity (USGS), volcanic events (NASA EONET),
      and solar/geomagnetic conditions (NOAA SWPC) in near real-time.
      The global command map above already shows all these layers — this tab lets you explore them in depth.
    </div>""", unsafe_allow_html=True)

    mc, rc = st.columns([3,1], gap="medium")
    with mc:
        # Mini local map for earth-only signals
        layers_e = []
        if show_seis and not eq_df.empty:
            ep = eq_df.copy()
            ep["color"] = ep["mag"].apply(lambda m: [255,55,85,220] if m>=5.5 else [255,180,0,200] if m>=4.5 else [0,230,118,175] if m>=3.5 else [0,200,255,150])
            ep["radius"] = (ep["mag"]**2.3*15000).clip(10000,240000)
            ep["tip"] = ep.apply(lambda r: f"M{r['mag']} | {r['place']} | Depth {r['depth_km']}km | {r['time']}", axis=1)
            layers_e.append(pdk.Layer("ScatterplotLayer",data=ep,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True))
        if show_volc and not eonet_df.empty:
            eo = eonet_df.copy()
            eo["color"] = [[255,110,40,200]]*len(eo); eo["radius"] = 70000
            eo["tip"] = eo.apply(lambda r: f"▲ {r['title']} | {r['cat']}", axis=1)
            layers_e.append(pdk.Layer("ScatterplotLayer",data=eo,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True))
        if show_heat and not eq_df.empty:
            layers_e.append(pdk.Layer("HeatmapLayer",data=eq_df[["lat","lon","mag"]].rename(columns={"mag":"weight"}),get_position=["lon","lat"],get_weight="weight",radiusPixels=50,opacity=.45))

        st.markdown('<div class="sec-label">🗺 Earth Events Map</div>', unsafe_allow_html=True)
        st.pydeck_chart(pdk.Deck(layers=layers_e,
            initial_view_state=pdk.ViewState(latitude=20,longitude=10,zoom=1.3),
            map_style="mapbox://styles/mapbox/dark-v11",
            tooltip={"text":"{tip}","style":{"backgroundColor":"#080f1c","color":"#e2ecf8","border":"1px solid rgba(0,200,255,.2)","fontFamily":"IBM Plex Mono","fontSize":"12px","padding":"10px","borderRadius":"8px"}},
            height=380), use_container_width=True)

        st.markdown('<div class="sec-label" style="margin-top:12px">📈 Geomagnetic Kp Index — Last 24 Hours</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:12px;color:var(--muted);margin-bottom:6px">Kp ≥ 5 = geomagnetic storm. Affects satellite navigation, HF radio, and power grids.</p>', unsafe_allow_html=True)
        st.plotly_chart(kp_chart(kp_data["series"]), use_container_width=True, config={"displayModeBar":False})

    with rc:
        st.markdown('<div class="sec-label">📊 Magnitude Distribution</div>', unsafe_allow_html=True)
        if not eq_df.empty:
            st.plotly_chart(mag_hist(eq_df), use_container_width=True, config={"displayModeBar":False})

        st.markdown('<div class="sec-label">⚠ Significant Events — M4.5+</div>', unsafe_allow_html=True)
        top_q = eq_df[eq_df["mag"] >= 4.5].nlargest(12,"mag")
        for _, row in top_q.iterrows():
            m = row["mag"]
            bc = "b-red" if m>=5.5 else "b-amber" if m>=4.5 else "b-cyan"
            st.markdown(f"""
            <div class="gcard {'gcard-crit' if m>=5.5 else ''}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
                <div class="sig-title">{row['place'][:36]}</div>
                <div class="badge {bc}">M{m}</div>
              </div>
              <div class="sig-meta">Depth {row['depth_km']} km &nbsp;·&nbsp; {row['time']}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="sec-label" style="margin-top:12px">🌋 Active EONET Events</div>', unsafe_allow_html=True)
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
      <b>Civil Movements</b> tracks protests, strikes, and civil unrest events globally.
      Sentiment is rated MED / HIGH / CRIT based on size, duration, and government response.
      Filter by type below to focus on specific categories.
    </div>""", unsafe_allow_html=True)

    mv_map, mv_right = st.columns([3,1], gap="medium")
    with mv_map:
        mdf = pd.DataFrame(MOVEMENTS)
        mdf["color"]  = mdf["sentiment"].map({"CRIT":[200,60,255,220],"HIGH":[157,110,255,190],"MED":[120,80,220,160]})
        mdf["radius"] = mdf["scale"] * 2200
        mdf["tip"]    = mdf.apply(lambda r: f"✊ {r['title']}\n{r['location']} · {r['size']} participants\nType: {r['type'].upper()} · Sentiment: {r['sentiment']}", axis=1)
        st.markdown('<div class="sec-label">🗺 Movement Map</div>', unsafe_allow_html=True)
        st.pydeck_chart(pdk.Deck(
            layers=[pdk.Layer("ScatterplotLayer",data=mdf,get_position=["lon","lat"],get_radius="radius",get_fill_color="color",pickable=True,auto_highlight=True)],
            initial_view_state=pdk.ViewState(latitude=25,longitude=20,zoom=1.3),
            map_style="mapbox://styles/mapbox/dark-v11",
            tooltip={"text":"{tip}","style":{"backgroundColor":"#080f1c","color":"#e2ecf8","border":"1px solid rgba(157,110,255,.25)","fontFamily":"IBM Plex Mono","fontSize":"12px","padding":"10px","borderRadius":"8px"}},
            height=350), use_container_width=True)
        st.markdown('<div class="sec-label" style="margin-top:12px">📊 Mobilisation Scale</div>', unsafe_allow_html=True)
        st.plotly_chart(mv_bar(MOVEMENTS), use_container_width=True, config={"displayModeBar":False})

    with mv_right:
        ft = st.radio("Filter by type:", ["ALL","protest","strike","civil"],
                       horizontal=True, label_visibility="visible")
        st.markdown('<div class="sec-label">Active Events</div>', unsafe_allow_html=True)
        for m in MOVEMENTS:
            if ft != "ALL" and m["type"] != ft: continue
            is_crit = m["sentiment"] == "CRIT"
            sc = "b-red" if is_crit else "b-violet" if m["sentiment"]=="HIGH" else "b-amber"
            tc_ = "b-violet" if m["type"]=="civil" else "b-orange" if m["type"]=="protest" else "b-amber"
            fc  = "#ff3d5a" if is_crit else "#9d6eff" if m["sentiment"]=="HIGH" else "#ffb400"
            st.markdown(f"""
            <div class="gcard {'gcard-crit' if is_crit else ''}">
              <div class="sig-title">{m['title']}</div>
              <div class="sig-meta">{m['location']} &nbsp;·&nbsp; {m['age_h']}h ago</div>
              <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;align-items:center">
                <div class="badge {tc_}">{m['type'].upper()}</div>
                <div class="badge {sc}">{m['sentiment']}</div>
                <div style="font-size:12px;color:var(--text2);margin-left:2px">{m['size']}</div>
              </div>
              <div class="scale-wrap">
                <div class="scale-track">
                  <div class="scale-fill" style="width:{m['scale']}%;background:linear-gradient(90deg,{fc}66,{fc})"></div>
                </div>
                <div style="font-family:var(--fm);font-size:10px;color:var(--muted);min-width:24px">{m['scale']}</div>
              </div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 4 — LIVE NEWS
# ══════════════════════════════════════════════════════════════
with tab_news:
    st.markdown("""
    <div class="helper">
      <b>Live News Feeds</b> aggregates {n} RSS sources across {c} categories.
      Articles are cached for 10 minutes. When network access is unavailable, the source directory is shown below.
    </div>""".replace("{n}", str(len(NEWS_SOURCES))).replace("{c}", str(len(CATEGORIES)-1)), unsafe_allow_html=True)

    cat_f = st.radio("Filter by category:", CATEGORIES,
                      format_func=lambda x: CAT_LABELS.get(x,x),
                      horizontal=True, label_visibility="visible")
    vis_src = [s for s in NEWS_SOURCES if cat_f == "ALL" or s["cat"] == cat_f]

    # Source pills
    pills = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 18px">'
    for s in vis_src:
        pills += f'<div class="src-pill" style="border-left:3px solid {s["color"]}"><span style="color:{s["color"]};font-size:8px">●</span><span>{s["name"]}</span></div>'
    pills += '</div>'
    st.markdown(pills, unsafe_allow_html=True)

    with st.spinner(f"Loading {len(vis_src)} news feeds…"):
        all_art = []
        for s in vis_src:
            arts = fetch_rss(s["rss"], s["name"], s["cat"])
            for a in arts:
                a["src_color"] = s["color"]
            all_art.extend(arts)

    if not all_art:
        st.info("ℹ News feeds are unreachable in this environment. Here is the full source directory — all feeds will load when running locally with internet access.")
        sc2 = st.columns(2)
        for i, s in enumerate(NEWS_SOURCES):
            with sc2[i % 2]:
                st.markdown(f"""
                <div class="news-card nc-general" style="padding-left:20px">
                  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
                    <div class="news-source" style="color:{s['color']}">{s['name']}</div>
                    <div class="badge {CAT_COLORS.get(s['cat'],'b-muted')}">{s['cat']}</div>
                  </div>
                  <div style="font-size:13px;color:var(--text2);line-height:1.5;margin-bottom:8px">{s['desc']}</div>
                  <div style="font-family:var(--fm);font-size:10px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{s['rss'][:60]}…</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f'<p style="font-size:12px;color:var(--muted);margin-bottom:12px">{len(all_art)} articles loaded from {len(vis_src)} sources</p>', unsafe_allow_html=True)
        nl, nr = st.columns(2, gap="medium")
        for i, a in enumerate(all_art[:30]):
            nc  = CAT_NC.get(a.get("category","general"),"nc-general")
            cb  = CAT_COLORS.get(a.get("category",""),"b-muted")
            lh  = f'<a href="{a["link"]}" target="_blank" class="news-link">Read article →</a>' if a.get("link") else ""
            col = nl if i % 2 == 0 else nr
            with col:
                st.markdown(f"""
                <div class="news-card {nc}">
                  <div style="display:flex;align-items:center;justify-content:space-between;gap:8px">
                    <div class="news-source" style="color:{a['src_color']}">{a['source']}</div>
                    <div class="badge {cb}">{a.get('category','')}</div>
                  </div>
                  <div class="news-headline">{a['title']}</div>
                  <div class="news-desc">{a.get('desc','')[:200]}</div>
                  <div class="news-footer">
                    <div class="news-time">{a.get('time','')}</div>
                    {lh}
                  </div>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 5 — TRAINING ARENA
# ══════════════════════════════════════════════════════════════
with tab_arena:
    st.markdown("""
    <div class="helper">
      <b>Training Arena</b> tests your OSINT analysis skills with real-world intelligence scenarios.
      Each correct answer earns XP and advances your analyst tier: Recruit → Analyst → Agent → Handler.
    </div>""", unsafe_allow_html=True)

    lc, cc2 = st.columns([1,2], gap="medium")
    with lc:
        st.markdown('<div class="sec-label">🏆 Global Leaderboard</div>', unsafe_allow_html=True)
        avts = ["background:rgba(255,61,90,.15);color:#ff3d5a","background:rgba(157,110,255,.15);color:#9d6eff",
                "background:rgba(255,180,0,.15);color:#ffb400","background:rgba(255,140,66,.15);color:#ff8c42",
                "background:rgba(74,107,133,.15);color:#4a6b85"]
        medals = ["🥇","🥈","🥉","④","⑤"]
        for i, (name, tier, sc, col) in enumerate(LEADERBOARD):
            st.markdown(f"""
            <div class="lb-row">
              <div style="font-size:16px;width:22px">{medals[i]}</div>
              <div class="lb-avatar" style="{avts[i]}">{name[:2].upper()}</div>
              <div style="flex:1">
                <div class="sig-title" style="color:{col};font-size:13px">{name}</div>
                <div class="sig-meta">{tier}</div>
              </div>
              <div style="font-family:var(--fd);font-size:18px;letter-spacing:.04em;color:var(--green)">{sc:,}</div>
            </div>""", unsafe_allow_html=True)

        tn2, tc2, _ = get_tier(st.session_state.score)
        st.markdown(f"""
        <div style="margin:12px 4px 0">
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

        st.markdown('<div class="sec-label" style="margin-top:18px">📈 Your Progress</div>', unsafe_allow_html=True)
        ac  = len(st.session_state.answered)
        cor = sum(1 for cid, a in st.session_state.answered.items()
                   for c in CHALLENGES if c["id"] == cid and a == c["correct"])
        acc_pct = int(cor/ac*100) if ac > 0 else 0
        st.markdown(f"""
        <div class="m-panel">
          <div style="display:flex;justify-content:space-around;margin-bottom:10px">
            <div style="text-align:center">
              <div class="m-label">Attempted</div>
              <div class="m-val m-cyan" style="font-size:30px">{ac}/{len(CHALLENGES)}</div>
            </div>
            <div style="text-align:center">
              <div class="m-label">Correct</div>
              <div class="m-val m-green" style="font-size:30px">{cor}</div>
            </div>
            <div style="text-align:center">
              <div class="m-label">Accuracy</div>
              <div class="m-val m-violet" style="font-size:30px">{acc_pct}%</div>
            </div>
          </div>
          <div class="xp-track"><div class="xp-fill" style="width:{int(cor/len(CHALLENGES)*100)}%"></div></div>
          <div class="m-sub" style="margin-top:5px">Challenge completion: {cor}/{len(CHALLENGES)}</div>
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
                sel = st.radio(f"Your answer for '{ch['title']}':", ch["options"],
                                index=None, key=f"r_{ch['id']}", label_visibility="visible")
                if st.button(f"Submit answer →", key=f"b_{ch['id']}", disabled=(sel is None)):
                    idx = ch["options"].index(sel)
                    st.session_state.answered[ch["id"]] = idx
                    if idx == ch["correct"]:
                        st.session_state.score += ch["pts"]
                    st.rerun()
            else:
                chosen = st.session_state.answered[ch["id"]]
                if chosen == ch["correct"]:
                    st.success(f"✓ Correct! +{ch['pts']} XP earned — {ch['explain']}")
                else:
                    st.error(f"✗ Incorrect (you chose: '{ch['options'][chosen]}') — {ch['explain']}")
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 6 — AI ANALYST
# ══════════════════════════════════════════════════════════════
with tab_ai:
    st.markdown("""
    <div class="helper">
      <b>AI Analyst</b> lets you query an LLM with live data context automatically injected —
      current earthquakes, Kp index, conflict escalation scores, and civil movement status.
      Configure your provider in the sidebar first.
    </div>""", unsafe_allow_html=True)

    al, ar = st.columns([1,1], gap="medium")
    with al:
        ready = (st.session_state.ai_provider in ("groq","openrouter") and st.session_state.ai_key) \
                or st.session_state.ai_provider == "ollama"

        # Status card
        status_color = "var(--green)" if ready else "var(--amber)"
        status_text  = "Ready" if ready else "No API key — configure in sidebar"
        st.markdown(f"""
        <div class="gcard" style="margin-bottom:16px">
          <div style="display:flex;gap:14px;align-items:center">
            <div>
              <div class="m-label">AI Provider</div>
              <div style="font-size:16px;font-weight:600;color:var(--cyan)">{st.session_state.ai_provider.upper()}</div>
            </div>
            <div>
              <div class="m-label">Model</div>
              <div style="font-family:var(--fm);font-size:12px;color:var(--text2)">llama-3.1-8b-instant</div>
            </div>
            <div style="margin-left:auto">
              <div style="font-size:13px;font-weight:600;color:{status_color}">
                {'● ' if ready else '○ '}{status_text}
              </div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Template prompts
        st.markdown("**Quick-start prompts:**")
        tmpls = [
            "— or type your own query below —",
            "Summarise the top 3 seismic risks right now",
            "Assess escalation probability for the New Delhi protests",
            "What does an elevated Kp index mean for satellite operators?",
            "Compare risk levels across all 4 active conflict theatres",
            "Which regions face compound Earth + conflict risk today?",
            "Write a humanitarian risk assessment for active conflict zones",
        ]
        tmpl = st.selectbox("Choose a template prompt:", tmpls, label_visibility="visible")
        prompt = st.text_area(
            "Your query:",
            value="" if tmpl == tmpls[0] else tmpl,
            height=130,
            placeholder="Ask anything about current global events, seismic data, conflict status, or geopolitical risk…",
            label_visibility="visible",
        )
        inject = st.checkbox("Automatically inject live data context into this query", value=True,
                              help="Adds current earthquake data, Kp index, conflict escalation scores, and movement status to your prompt.")

        if st.button("⚡  Run Analysis", use_container_width=True, disabled=not prompt.strip()):
            final = prompt
            if inject:
                top5 = eq_df.nlargest(5,"mag")[["mag","place","depth_km"]].to_dict("records")
                conf_ctx = {n:{"escalation":c["escalation"],"intensity":c["intensity"],"casualties":c["casualties_total"]} for n,c in CONFLICTS.items()}
                final += (f"\n\n[LIVE DATA CONTEXT — {utc_now}]\n"
                          f"Top earthquakes: {json.dumps(top5)}\n"
                          f"Kp index: {kp_data['kp']}\n"
                          f"Conflict status: {json.dumps(conf_ctx)}\n"
                          f"Civil movements: {json.dumps([{k:m[k] for k in ('title','location','sentiment','size')} for m in MOVEMENTS])}")
            with st.spinner("Analysing with AI…"):
                result = call_ai(final, st.session_state.ai_provider, st.session_state.ai_key)
            st.session_state.ai_output = result

        if st.session_state.ai_output:
            st.markdown(f'<div class="ai-terminal">{st.session_state.ai_output}</div>', unsafe_allow_html=True)
            if st.button("🗑  Clear output"):
                st.session_state.ai_output = ""
                st.rerun()

    with ar:
        st.markdown('<div class="sec-label">📊 Live Situational Charts</div>', unsafe_allow_html=True)

        if not eq_df.empty:
            st.markdown("**Seismic Event Breakdown (24h)**")
            st.plotly_chart(mag_donut(eq_df), use_container_width=True, config={"displayModeBar":False})

        st.markdown("**Civil Movement Sentiment**")
        snt = {"CRIT":0,"HIGH":0,"MED":0}
        for m in MOVEMENTS:
            snt[m["sentiment"]] += 1
        fig_s = go.Figure(go.Bar(x=["Critical","High","Medium"], y=list(snt.values()),
                                  marker_color=["#ff3d5a","#ff8c42","#ffb400"], marker_line_width=0, opacity=.85))
        fig_s.update_layout(height=160, margin=dict(l=0,r=0,t=10,b=0), **bg_chart(), xaxis=ax(), yaxis=ax())
        st.plotly_chart(fig_s, use_container_width=True, config={"displayModeBar":False})

        st.markdown("**Conflict Escalation Scores**")
        conf_names = [n.split("–")[0].split(" ")[0][:10] for n in CONFLICTS.keys()]
        conf_escs  = [c["escalation"] for c in CONFLICTS.values()]
        conf_cols  = ["#ff3d5a" if e>=80 else "#ff8c42" if e>=60 else "#ffb400" if e>=40 else "#00e676" for e in conf_escs]
        fig_c = go.Figure(go.Bar(x=conf_names, y=conf_escs, marker_color=conf_cols, marker_line_width=0, opacity=.85,
                                  text=conf_escs, textposition="outside", textfont=dict(size=10,color="#e2ecf8")))
        fig_c.update_layout(height=180, margin=dict(l=0,r=0,t=10,b=0), **bg_chart(),
                             xaxis=ax(), yaxis=dict(**ax(), range=[0,110]))
        st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar":False})

        st.markdown("**Recent Earthquake Data**")
        disp = eq_df[["mag","place","depth_km","time"]].head(16).rename(
            columns={"mag":"Magnitude","place":"Location","depth_km":"Depth (km)","time":"Time (UTC)"})
        st.dataframe(disp, use_container_width=True, height=220, hide_index=True)
