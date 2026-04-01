# 🌍 Global Intelligence Dashboard (OSINT)

A real-time, multi-domain intelligence dashboard built with **Streamlit** — designed to aggregate, visualize, and analyze **open-source intelligence (OSINT)** across geopolitical, economic, environmental, and cyber domains.

> ⚠️ This version is fully **deterministic and data-driven**.
> All AI/LLM-based components have been removed to ensure transparency, reproducibility, and performance.

---

## 🚀 Overview

The Global Intelligence Dashboard provides a unified interface for monitoring:

* Geopolitical conflicts
* Global signals intelligence
* Financial and commodity markets
* Natural disasters and earth events
* Cybersecurity threats
* Supply chain disruptions

All insights are derived from **live APIs, structured datasets, and rule-based analytics**.

---

## 🧩 Features

### ⚔️ Conflict Dashboard

* Live conflict tracking (ACLED-style datasets)
* Geospatial visualization of hotspots
* Instability scoring (rule-based)
* Country-level conflict summaries
* **Situation Report Export** (deterministic intelligence brief)

---

### 📡 Signals Intelligence (SIGINT)

* GDELT-based global signal monitoring
* Event clustering and trend tracking
* Tone and sentiment indicators (data-derived)
* Keyword and region filtering

---

### 📊 Market Intelligence

* Global indices and macro indicators
* Commodities tracking (oil, gold, etc.)
* Currency movements
* Market volatility signals

---

### 🌋 Earth Events Monitor

* Earthquakes, volcanic activity, extreme weather
* Real-time geospatial plotting
* Severity-based filtering
* Event clustering

---

### 🔐 Cyber Intelligence

* Cyber threat monitoring (feeds/APIs)
* Attack pattern visualization
* Incident categorization
* Temporal tracking of threats

---

### 🚢 Supply Chain Intelligence

* Trade routes and chokepoints
* Disruption indicators
* Logistics risk mapping
* Maritime/transport insights

---

### 🌐 Global Overview

* High-level synthesis across all modules
* Cross-domain signal alignment
* Rapid situational awareness dashboard

---

### 📁 Data Explorer

* Raw dataset inspection
* Filtering and slicing tools
* Export-ready structured views

---

## 🏗️ Architecture

```
Streamlit Frontend
        │
        ├── Data Processing Layer (Pandas, NumPy)
        │
        ├── API Integrations
        │     ├── Conflict Data (ACLED-style)
        │     ├── GDELT (SIGINT)
        │     ├── Market APIs
        │     ├── Earth Events APIs
        │     └── Cyber Feeds
        │
        ├── Visualization Layer
        │     ├── Plotly
        │     ├── PyDeck (Maps)
        │
        └── Rule-Based Analytics Engine
              ├── Instability Index
              ├── Risk Scoring
              └── Event Aggregation
```

> **Note:**
> This system does **not** include any AI/LLM inference layer. All outputs are deterministic and derived from structured data or predefined logic.

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/global-intelligence-dashboard.git
cd global-intelligence-dashboard
```

---

### 2. Install Dependencies

```bash
pip install streamlit pydeck plotly pandas numpy requests streamlit-autorefresh
```

---

### 3. Run the App

```bash
streamlit run app.py
```

---

## 📊 Data Sources

This dashboard integrates multiple open-source and public datasets:

* Conflict data (ACLED-style structured datasets)
* GDELT (Global Database of Events, Language, and Tone)
* Financial market APIs
* Geological and weather APIs
* Cyber threat intelligence feeds

> All data is subject to availability, latency, and source reliability.

---

## 📁 Project Structure

```
├── app.py                 # Main Streamlit application
├── README.md              # Documentation
├── data/                  # Local datasets (if any)
├── assets/                # Static files (icons, etc.)
└── utils/                 # Helper functions (optional)
```

---

## 📤 Situation Report (SitRep)

The dashboard includes a **Situation Report export feature**:

* Generates structured intelligence summaries
* Combines multiple data sources
* Fully **rule-based (non-AI)**
* Designed for quick operational briefings

---

## 🚫 Removed AI Components (v7 Update)

This version removes all AI-driven functionality to improve:

* Transparency
* Reproducibility
* Performance

### Removed Features:

* AI Analyst module
* Training Arena
* AI-generated Situation Reports
* AI provider configuration
* Analyst profile system
* All LLM-based processing

### Result:

* No probabilistic outputs
* Fully explainable system
* Faster execution and lower dependencies

---

## 🎯 Use Cases

* Geopolitical risk monitoring
* OSINT research and analysis
* Academic and policy research
* Financial market situational awareness
* Crisis and disaster monitoring
* Cyber threat tracking

---

## ⚠️ Disclaimer

This tool is intended for **informational and analytical purposes only**.

* Not a substitute for official intelligence or advisory systems
* Data accuracy depends on third-party sources
* Use responsibly in decision-making contexts

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **Data Processing:** Pandas, NumPy
* **Visualization:** Plotly, PyDeck
* **APIs:** REST-based integrations
* **Architecture:** Modular, rule-based analytics

---

## 📌 Future Improvements

* Enhanced data pipelines and caching
* Additional OSINT sources
* Improved geospatial analytics
* Custom alerting system
* Dashboard performance optimizations

---

## 🤝 Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

This project is licensed u
