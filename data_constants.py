"""
data_constants.py — THE GEO-LOCATOR v8
========================================
Static reference datasets extracted from app.py as the first phase of the
v8 module split (conflicts, military/nuclear/infra sites, historical events,
news/media config, etc.). These are inert Python literals with no Streamlit
or network dependencies, so they were the lowest-risk slice to move out of
the 11k-line monolith first.

app.py imports everything from this module with `from data_constants import *`.
Splitting the live-fetcher functions and the UI/tab bodies into their own
modules is a larger, higher-risk follow-up (they depend heavily on
execution order and shared Streamlit session state) and is intentionally
NOT done in this pass.
"""

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


# ══════════════════════════════════════════════════════════════
# OIL & GAS FACILITY MAP — DEPENDENCIES
# ══════════════════════════════════════════════════════════════

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
    # ── Economic & Tech Milestones 2025-2026 ─────────────────────
    {"date":"2025-04-02","lat":38.9,"lon":-77.0,"type":"economic","severity":"HIGH","title":"US announces sweeping reciprocal tariff regime","tip":"2025-04-02 | TARIFFS\nUS announces broad reciprocal tariffs\nGlobal markets sell off — trade-war fears"},
    {"date":"2025-09-14","lat":31.23,"lon":121.47,"type":"economic","severity":"MED","title":"China-US trade truce extended amid chip export talks","tip":"2025-09-14 | TRADE\nChina-US trade truce extended\nSemiconductor export controls remain central issue"},
    {"date":"2025-07-22","lat":37.77,"lon":-122.42,"type":"tech","severity":"MED","title":"Frontier AI model release triggers new export-control debate","tip":"2025-07-22 | AI POLICY\nNew frontier AI model released\nRenewed debate over export controls & compute governance"},
    {"date":"2026-04-18","lat":23.7,"lon":90.4,"type":"natural","severity":"HIGH","title":"Bangladesh cyclone displaces 800,000+","tip":"2026-04-18 | CYCLONE\nBangladesh coastal cyclone\n800,000+ displaced — Bay of Bengal"},
    {"date":"2026-05-30","lat":1.35,"lon":103.82,"type":"economic","severity":"MED","title":"Major shipping lane disruption spikes container rates","tip":"2026-05-30 | SHIPPING\nStrait of Malacca congestion\nContainer freight rates spike 40%"},
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
    "atrocity":"⛔","maritime":"⚓","economic":"💹","tech":"🤖",
}

# ── Live Events GDELT fetcher ──────────────────────────────────────────────

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
