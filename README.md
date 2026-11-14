# 🔥 Flame in Freefall
### AI-Powered Fire Safety Insights from Microgravity Combustion Data
**NASA International Space Apps Challenge 2026 — Local Event: Haldwani, India**  
**Team:** Eagle20  
**Challenge:** *Flame in Freefall: AI-Powered Fire Safety Insights from Microgravity Combustion Data*

---

## 🌌 Overview

For decades, NASA has studied how flames and fire behave in microgravity through experiments aboard the International Space Station (ISS), the Space Shuttle, drop towers, and uncrewed Cygnus cargo vehicles. As humanity prepares for long-duration missions back to the Moon (Artemis) and onto Mars, understanding microgravity combustion physics is vital to crew survival.

However, the volume and complexity of NASA physical sciences results makes them difficult to find, compare, and synthesize.

**Flame in Freefall** is an interactive, desktop Super Intelligence (SI) dashboard that:
1. **Summarizes** decades of NASA microgravity combustion experiments.
2. **Ranks** findings and materials by relevance and risk.
3. **Interprets** physics findings into actionable fire safety guidelines for lunar and Martian habitats.
4. **Reasons** using a hybrid **Graph-RAG** architecture grounded in real NASA data.

---

## 🏗️ System Architecture

```
                                  +---------------------------------+
                                  |   NASA PSI & NTRS Repositories  |
                                  |  (BASS, ACME, SAFFIRE, SoFIE)   |
                                  +----------------+----------------+
                                                   |
                                                   v
                                  +----------------+----------------+
                                  |     Data Ingestion Pipeline     |
                                  | (Overlapping Semantic Chunking) |
                                  +--------+---------------+--------+
                                           |               |
                    +----------------------+               +---------------------+
                    v                                                            v
+---------------------------------------+                +---------------------------------------+
|        Vector Store (Semantic)        |                |        Knowledge Graph (NetworkX)     |
|   - ChromaDB / NumPy Cosine Search    |                |   - Experiment -> Material Edges      |
|   - Gemini text-embedding-004         |                |   - Condition -> Finding Edges        |
+-------------------+-------------------+                +-------------------+-------------------+
                    |                                                        |
                    +----------------------+        +------------------------+
                                           v        v
                                  +----------------+----------------+
                                  |          RAG Pipeline           |
                                  |    - Context Fusion             |
                                  |    - Multi-Turn Memory (JSON)   |
                                  |    - Google Gemini 2.5 Flash    |
                                  +----------------+----------------+
                                                   |
                                                   v
                 +---------------------------------+---------------------------------+
                 |                                                                   |
                 v                                                                   v
+----------------------------------+                              +----------------------------------+
|      Modern CustomTkinter UI     |                              |      Scientific Visualizations   |
| - Mission Overview Dashboard     |                              | - Matplotlib Radar Profiles      |
| - Grounded FlameAI Chat          |                              | - NetworkX Interactive Graph     |
| - Experiment Explorer & Filters  |                              | - Flammability Risk Gauges       |
| - Side-by-Side Experiment Diff   |                              | - Material Flammability Index    |
| - Habitat Fire Safety Scorer     |                              |                                  |
+----------------------------------+                              +----------------------------------+
```

---

## ✨ Key Features

### 1. 📊 Mission Overview Dashboard
- High-level mission stat cards: Ingested Experiments, Materials Tested, Key Findings, and Safety Guidelines.
- Real-time dark-themed Matplotlib charts showing experiment distributions across NASA programs and material types.
- Live feed of key experimental insights with direct attribution.

### 2. 🤖 FlameAI Chat (Hybrid Graph-RAG Pipeline)
- Conversational assistant powered by **Google Gemini API** (`gemini-2.5-flash`).
- **Graph-Augmented Retrieval (Graph-RAG):** Combines dense vector similarity with knowledge graph entity traversal to eliminate hallucinations.
- Cites real NASA datasets and research papers for every answer.
- Multi-turn conversation memory with persistence.

### 3. 🔬 Experiment Explorer
- Search and browse 12+ major NASA combustion experiments (BASS, BASS-II, ACME-BRE, SAFFIRE I-III, FLEX-2, SPICE, SoFIE).
- Filter by category, test materials, atmospheric pressure, and oxygen concentrations.
- Detailed card view with flammability boundaries, flame sphericity, and spread rates.

### 4. ⚖️ Side-by-Side Experiment Comparison
- Compare two NASA experiments across key combustion parameters:
  - Flame Spread Rate
  - Extinction Time
  - Soot Yield
  - Heat Release Rate
  - Overall Safety Score
- Interactive **5-axis radar chart** comparing combustion metrics visually.

### 5. 🛡️ Fire Safety Risk Scorer for Space Habitats
- Custom assessment tool tailored for **ISS (LEO)**, **Lunar Habitats (0.16g)**, and **Martian Habitats (0.38g)**.
- Select target materials (e.g. Nomex®, PMMA, Silicone, Kapton, Cotton) and ambient oxygen levels (up to exploration 34% O₂).
- Generates safety scores (0-100), key risk factors, and engineering recommendations.
- Ranked safety tables for habitat structural materials.

### 6. 🕸️ Knowledge Graph Visualizer
- Interactive NetworkX graph visualizer showing the web of connections between:
  - 🟠 Experiments
  - 🔵 Materials
  - 🟢 Findings
  - 🔴 Safety Implications
- Clickable nodes with detailed properties sidebar.

---

## 📂 NASA Combustion Datasets Covered

Our knowledge base incorporates published experimental findings from NASA's Physical Sciences Informatics (PSI) system and NASA Technical Reports Server (NTRS):

| Experiment | Facility / Platform | Primary Research Focus |
|------------|---------------------|------------------------|
| **BASS / BASS-II** | ISS Microgravity Science Glovebox (MSG) | Burning & extinction limits of solid polymers (PMMA, cotton) under forced airflow |
| **ACME (BRE, CLD, s-Flame)** | ISS Combustion Integrated Rack (CIR) | Gaseous diffusion flames, flame lift-off, and electric-field suppression |
| **SAFFIRE I – VI** | Northrop Grumman Cygnus Spacecraft | Real-scale spacecraft fire propagation and atmospheric depletion dynamics |
| **FLEX / FLEX-2** | ISS Multi-user Droplet Combustion App. | Droplet combustion, radiative extinction, and discovery of low-temperature cool flames |
| **SPICE** | ISS CIR | Smoke point, soot volume fractions, and agglomeration in microgravity coflows |
| **SoFIE** | ISS CIR | Solid fuel ignition and extinction under exploration atmosphere conditions |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10 or higher
- Windows 10/11 (or macOS / Linux with Tkinter support)

### 2. Installation
Clone or navigate to the repository directory:
```bash
cd spaceappchallenge
```

Install requirements:
```bash
pip install -r requirements.txt
```

*(Note: The application has built-in offline fallbacks using NumPy and Scikit-Learn if ChromaDB or Google GenAI are not yet installed).*

### 3. Configure Gemini API Key (Optional but Recommended)
Open `.env` in the project root and add your Google Gemini API key:
```env
GEMINI_API_KEY=AIzaSy...your_actual_key_here
```
> **Tip:** You can obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/). If no key is set, the application operates in local knowledge grounding mode.

### 4. Run the Dashboard
Launch the desktop application:
```bash
python main.py
```

---

## 👥 Team Eagle20
- **Hackathon:** NASA Space Apps Challenge 2026
- **Location:** Haldwani, Uttarakhand, India
- **Motto:** *Born to soar. Built to dominate.*
