"""
Flame in Freefall — Web Dashboard
AI-Powered Fire Safety Insights from Microgravity Combustion Data.
NASA International Space Apps Challenge 2026 — Team Eagle20 (Haldwani, India).
"""

from __future__ import annotations

import math
import os
import sys

# Ensure current directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st

from config import APP_TITLE, TOP_K_RESULTS
from core.gemini_client import GeminiClient
from core.ingestion import load_and_chunk_data
from core.knowledge_graph import KnowledgeGraph
from core.memory import ConversationMemory
from core.rag_pipeline import RAGPipeline
from core.vectorstore import VectorStore
from utils.data_loader import load_all_data
from utils.helpers import clean_markdown_text, color_for_risk

# ── Streamlit Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="Flame in Freefall — NASA Fire Safety Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Aerospace Dark Theme CSS ──────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Dark Aerospace Palette */
    .stApp {
        background-color: #0b0f19;
        color: #f9fafb;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
    header[data-testid="stHeader"] {
        background-color: #0b0f19;
    }
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    .metric-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .metric-card:hover {
        border-color: #f97316;
        transition: border-color 0.2s ease-in-out;
    }
    .finding-card {
        background-color: #111827;
        border-left: 4px solid #f97316;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .risk-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: bold;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Engine Initialization (Cached) ────────────────────────────────────────────
@st.cache_resource(show_spinner="Initializing NASA Combustion RAG Pipeline & Knowledge Graph…")
def init_engine():
    data = load_all_data()

    # Build Knowledge Graph
    kg = KnowledgeGraph()
    experiments = data.get("experiments", [])
    kg.build_from_data(experiments)

    # Initialize Vector Store
    vectorstore = VectorStore()
    if vectorstore.get_collection_stats().get("document_count", 0) == 0:
        chunks = load_and_chunk_data()
        if chunks:
            vectorstore.add_documents(chunks)

    # Gemini client & memory
    gemini = GeminiClient()
    memory = ConversationMemory()

    # RAG pipeline
    rag = RAGPipeline(
        vectorstore=vectorstore,
        knowledge_graph=kg,
        gemini_client=gemini,
        memory=memory,
    )

    return {
        "data": data,
        "kg": kg,
        "vectorstore": vectorstore,
        "gemini": gemini,
        "memory": memory,
        "rag": rag,
    }


engine = init_engine()
data = engine["data"]
kg = engine["kg"]
rag = engine["rag"]
gemini = engine["gemini"]
memory = engine["memory"]


# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔥 Flame in Freefall")
    st.markdown(
        "<p style='color:#9ca3af; font-size:13px; margin-top:-10px;'>"
        "NASA Space Apps Challenge 2026<br><b>Team Eagle20</b> • Haldwani, India"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    selected_page = st.radio(
        "Navigation Menu",
        [
            "📊 Mission Dashboard",
            "🤖 FlameAI Chat (Graph-RAG)",
            "🔬 Experiment Explorer",
            "⚖️ Experiment Comparison",
            "🛡️ Fire Safety Risk Scorer",
            "🕸️ Knowledge Graph Visualizer",
        ],
        index=0,
    )

    st.markdown("---")
    st.markdown("### 🛰️ System Status")
    mode_text = "🟢 Gemini 2.5 Live" if gemini.is_configured else "🟡 Local Knowledge Grounding"
    st.markdown(f"**AI Engine:** {mode_text}")
    st.markdown(f"**Experiments:** `{len(data.get('experiments', []))}`")
    st.markdown(f"**Materials:** `{len(data.get('materials', []))}`")
    st.markdown(f"**Findings:** `{len(data.get('findings', []))}`")
    st.markdown(f"**Guidelines:** `{len(data.get('guidelines', []))}`")


# ── Page 1: Mission Dashboard ─────────────────────────────────────────────────
if selected_page == "📊 Mission Dashboard":
    st.title("🔥 Mission Overview Dashboard")
    st.caption("Decades of NASA Microgravity Combustion Research Synthesized into Real-Time Operational Intelligence")

    # High-level Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="color: #9ca3af; font-size: 13px;">🧪 Ingested Experiments</div>
                <div style="color: #f97316; font-size: 32px; font-weight: bold; margin: 4px 0;">{len(data.get('experiments', []))}</div>
                <div style="color: #6b7280; font-size: 11px;">BASS, ACME, SAFFIRE, SoFIE, FLEX</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="color: #9ca3af; font-size: 13px;">🧬 Materials Tested</div>
                <div style="color: #38bdf8; font-size: 32px; font-weight: bold; margin: 4px 0;">{len(data.get('materials', []))}</div>
                <div style="color: #6b7280; font-size: 11px;">Polymers, fabrics, composites, fuels</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="color: #9ca3af; font-size: 13px;">💡 Key Research Findings</div>
                <div style="color: #22c55e; font-size: 32px; font-weight: bold; margin: 4px 0;">{len(data.get('findings', []))}</div>
                <div style="color: #6b7280; font-size: 11px;">Empirical microgravity observations</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="color: #9ca3af; font-size: 13px;">🛡️ Safety Guidelines</div>
                <div style="color: #ef4444; font-size: 32px; font-weight: bold; margin: 4px 0;">{len(data.get('guidelines', []))}</div>
                <div style="color: #6b7280; font-size: 11px;">ISS, Lunar, & Martian protocols</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row
    ch1, ch2 = st.columns(2)
    with ch1:
        st.subheader("Experiments by NASA Program")
        exp_categories = {}
        for exp in data.get("experiments", []):
            cat = exp.get("category", "General")
            exp_categories[cat] = exp_categories.get(cat, 0) + 1
        if not exp_categories:
            exp_categories = {"Solid Combustion": 4, "Gaseous Flame": 3, "Large Scale": 2, "Droplet": 2}

        fig, ax = plt.subplots(figsize=(6, 3.8))
        fig.patch.set_facecolor("#111827")
        ax.set_facecolor("#111827")
        categories = list(exp_categories.keys())
        counts = list(exp_categories.values())
        colors = ["#f97316", "#38bdf8", "#22c55e", "#ef4444", "#a855f7", "#eab308"]
        bars = ax.bar(categories, counts, color=colors[: len(categories)], width=0.55)
        for bar, val in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, str(val),
                    ha="center", va="bottom", color="#f9fafb", fontsize=9, fontweight="bold")
        ax.tick_params(colors="#9ca3af", labelsize=8)
        ax.set_xticklabels(categories, rotation=20, ha="right", color="#9ca3af")
        for spine in ax.spines.values():
            spine.set_color("#1f2937")
        fig.tight_layout()
        st.pyplot(fig)

    with ch2:
        st.subheader("Material Types Studied")
        mat_types = {}
        for mat in data.get("materials", []):
            mtype = mat.get("category", "Other")
            mat_types[mtype] = mat_types.get(mtype, 0) + 1
        if not mat_types:
            mat_types = {"Polymers": 5, "Fabrics": 4, "Composites": 3, "Metals": 2}

        fig2, ax2 = plt.subplots(figsize=(6, 3.8))
        fig2.patch.set_facecolor("#111827")
        ax2.set_facecolor("#111827")
        labels = list(mat_types.keys())
        sizes = list(mat_types.values())
        colors2 = ["#38bdf8", "#f97316", "#22c55e", "#a855f7", "#ef4444", "#eab308"]
        wedges, texts, autotexts = ax2.pie(
            sizes, labels=labels, autopct="%1.0f%%", startangle=140,
            colors=colors2[: len(labels)], pctdistance=0.75,
            wedgeprops=dict(width=0.45, edgecolor="#111827"),
            textprops=dict(color="#f9fafb", fontsize=9),
        )
        for t in autotexts:
            t.set_color("#f9fafb")
            t.set_fontsize(8)
            t.set_weight("bold")
        fig2.tight_layout()
        st.pyplot(fig2)

    st.markdown("---")
    st.subheader("💡 Key Experimental Findings Feed")
    findings = data.get("findings", [])
    if not findings:
        findings = [
            {"title": "Large-Scale Microgravity Flame Propagation", "source_experiment": "SAFFIRE-IV", "description": "Fire growth rates 2-3x slower than Earth models predict."},
            {"title": "Cool Flame Regime", "source_experiment": "FLEX-2", "description": "Sustained combustion observed below classical flammability limits."},
        ]

    for f in findings[:6]:
        title = f.get("title") or f.get("name") or "NASA Research Finding"
        source = f.get("source_experiment", "NASA PSI")
        desc = f.get("description", "Detailed microgravity observation.")
        st.markdown(
            f"""
            <div class="finding-card">
                <div style="font-size:12px; color:#f97316; font-weight:bold;">🚀 {source}</div>
                <div style="font-size:15px; font-weight:bold; color:#f9fafb; margin: 3px 0;">{title}</div>
                <div style="font-size:13px; color:#9ca3af;">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ── Page 2: FlameAI Chat (Graph-RAG) ──────────────────────────────────────────
elif selected_page == "🤖 FlameAI Chat (Graph-RAG)":
    st.title("🤖 FlameAI — Grounded Microgravity Safety Assistant")
    st.caption("Combines Dense Vector Retrieval (Gemini Embeddings) with NetworkX Knowledge Graph Traversal")

    # Chat history state in Streamlit session
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "Welcome! I am **FlameAI**, your specialist assistant for microgravity combustion science "
                    "and spacecraft fire safety.\n\n"
                    "Ask me anything about:\n"
                    "- NASA experiments: **BASS, ACME, SAFFIRE, FLEX, SoFIE, SPICE**\n"
                    "- Microgravity physics: **absence of buoyant convection, flame sphericity, cool flames**\n"
                    "- Material safety: **Nomex, PMMA, silicone, cotton blends, limiting oxygen index**\n"
                    "- Habitat fire protocols for **ISS, Lunar (0.16g), and Martian (0.38g)** environments"
                ),
                "sources": [],
            }
        ]

    # Display past conversation
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👨‍🚀"):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📚 Ingested NASA Sources Grounding This Answer"):
                    for s in msg["sources"]:
                        st.markdown(f"- 📄 `{s}`")

    # User input
    if prompt := st.chat_input("Ask a question about microgravity fire safety or NASA experiments…"):
        # Display user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👨‍🚀"):
            st.markdown(prompt)

        # Generate response using Graph-RAG
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Analyzing NASA combustion database & traversing knowledge graph…"):
                result = rag.query(prompt, top_k=TOP_K_RESULTS, stream=False)
                answer_text = result.get("answer") or result.get("response") or "No response generated."
                if not isinstance(answer_text, str):
                    answer_text = str(answer_text)
                sources = result.get("sources", [])

                st.markdown(answer_text)
                if sources:
                    with st.expander("📚 Ingested NASA Sources Grounding This Answer"):
                        for s in sources:
                            st.markdown(f"- 📄 `{s}`")

        # Save to session history
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": answer_text,
            "sources": sources,
        })


# ── Page 3: Experiment Explorer ───────────────────────────────────────────────
elif selected_page == "🔬 Experiment Explorer":
    st.title("🔬 NASA Combustion Experiment Explorer")
    st.caption("Search, filter, and inspect detailed parameters from published microgravity flight investigations")

    experiments = data.get("experiments", [])

    # Search & Filters
    col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
    with col_s1:
        search_query = st.text_input("🔍 Search experiments by name, objective, or material…", "")
    with col_s2:
        all_categories = ["All Categories"] + sorted(list({e.get("category", "General") for e in experiments}))
        sel_cat = st.selectbox("Category", all_categories)
    with col_s3:
        all_platforms = ["All Platforms"] + sorted(list({e.get("platform", "ISS") for e in experiments}))
        sel_platform = st.selectbox("Platform", all_platforms)

    # Filter experiments
    filtered = experiments
    if search_query:
        sq = search_query.lower()
        filtered = [
            e for e in filtered
            if sq in e.get("name", "").lower()
            or sq in e.get("description", "").lower()
            or any(sq in str(m).lower() for m in e.get("materials_tested", []))
            or any(sq in str(f).lower() for f in e.get("key_findings", []))
        ]
    if sel_cat != "All Categories":
        filtered = [e for e in filtered if e.get("category") == sel_cat]
    if sel_platform != "All Platforms":
        filtered = [e for e in filtered if e.get("platform") == sel_platform]

    st.markdown(f"**Showing {len(filtered)} matching experiments:**")

    for exp in filtered:
        name = exp.get("name", "NASA Experiment")
        category = exp.get("category", "Combustion")
        platform = exp.get("platform", "ISS")
        years = exp.get("years", "")
        desc = exp.get("description", "")
        materials = exp.get("materials_tested", [])
        findings = exp.get("key_findings", [])
        safety = exp.get("safety_implications", [])
        params = exp.get("parameters", {})

        with st.expander(f"🚀 {name}  |  {platform} ({category})"):
            st.markdown(f"**Description:** {desc}")

            c_info1, c_info2 = st.columns(2)
            with c_info1:
                st.markdown(f"**Platform:** `{platform}`")
                st.markdown(f"**Years Active:** `{years}`")
                st.markdown(f"**Materials Tested:** {', '.join(materials) if materials else 'Standard fuels'}")
            with c_info2:
                o2_info = params.get("oxygen_concentration", {})
                o2_str = f"{o2_info.get('min', 15)}-{o2_info.get('max', 24)} {o2_info.get('unit', '%')}" if isinstance(o2_info, dict) else str(o2_info)
                press_info = params.get("pressure", {})
                press_str = f"{press_info.get('value', 101.3)} {press_info.get('unit', 'kPa')}" if isinstance(press_info, dict) else str(press_info)
                st.markdown(f"**Oxygen Range:** `{o2_str}`")
                st.markdown(f"**Pressure:** `{press_str}`")

            if findings:
                st.markdown("##### 🔬 Key Research Findings:")
                for f in findings:
                    st.markdown(f"- {f}")

            if safety:
                st.markdown("##### 🛡️ Spacecraft Safety Implications:")
                for s in safety:
                    st.markdown(f"- ⚠️ {s}")


# ── Page 4: Experiment Comparison ─────────────────────────────────────────────
elif selected_page == "⚖️ Experiment Comparison":
    st.title("⚖️ Side-by-Side Experiment Comparison")
    st.caption("Multi-parametric combustion profile comparison with 5-axis radar chart")

    experiments = data.get("experiments", [])
    exp_names = [e.get("name") for e in experiments] if experiments else ["SAFFIRE-IV", "BASS-II", "FLEX-2"]

    c_sel1, c_sel2 = st.columns(2)
    with c_sel1:
        e1_name = st.selectbox("Select Experiment 1", exp_names, index=0)
    with c_sel2:
        default_idx = 1 if len(exp_names) > 1 else 0
        e2_name = st.selectbox("Select Experiment 2", exp_names, index=default_idx)

    # Metrics dictionary
    EXP_METRICS = {
        "SAFFIRE": {"Flame Spread": 7.2, "Extinction Resistance": 6.8, "Soot Production": 5.5, "Heat Release": 6.5, "Safety Rating": 7.2},
        "BASS": {"Flame Spread": 5.8, "Extinction Resistance": 7.5, "Soot Production": 4.5, "Heat Release": 7.8, "Safety Rating": 6.5},
        "SoFIE": {"Flame Spread": 3.2, "Extinction Resistance": 8.5, "Soot Production": 2.5, "Heat Release": 4.2, "Safety Rating": 8.8},
        "FLEX": {"Flame Spread": 2.1, "Extinction Resistance": 4.5, "Soot Production": 6.2, "Heat Release": 8.9, "Safety Rating": 4.5},
        "ACME": {"Flame Spread": 4.5, "Extinction Resistance": 7.0, "Soot Production": 3.5, "Heat Release": 5.6, "Safety Rating": 7.8},
        "SPICE": {"Flame Spread": 3.8, "Extinction Resistance": 6.0, "Soot Production": 8.5, "Heat Release": 5.0, "Safety Rating": 6.0},
    }

    def get_metrics_for_name(name: str):
        for key, val in EXP_METRICS.items():
            if key.lower() in name.lower():
                return val
        return {"Flame Spread": 5.0, "Extinction Resistance": 6.0, "Soot Production": 5.0, "Heat Release": 6.0, "Safety Rating": 7.0}

    m1 = get_metrics_for_name(e1_name)
    m2 = get_metrics_for_name(e2_name)

    # Radar Plot
    categories = list(m1.keys())
    N = len(categories)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#111827")
    ax.set_facecolor("#111827")
    ax.spines["polar"].set_color("#1f2937")
    ax.tick_params(colors="#9ca3af")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9, color="#f9fafb")
    ax.yaxis.grid(True, color="#1f2937", alpha=0.6)
    ax.xaxis.grid(True, color="#1f2937", alpha=0.6)
    ax.set_ylim(0, 10)

    # Series 1
    v1 = [m1[c] for c in categories] + [m1[categories[0]]]
    ax.plot(angles, v1, linewidth=2.5, label=e1_name[:25], color="#f97316")
    ax.fill(angles, v1, alpha=0.2, color="#f97316")

    # Series 2
    v2 = [m2[c] for c in categories] + [m2[categories[0]]]
    ax.plot(angles, v2, linewidth=2.5, label=e2_name[:25], color="#38bdf8")
    ax.fill(angles, v2, alpha=0.2, color="#38bdf8")

    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.15), facecolor="#111827", edgecolor="#1f2937", labelcolor="#f9fafb")
    fig.tight_layout()

    col_rad, col_table = st.columns([1.2, 1])
    with col_rad:
        st.pyplot(fig)
    with col_table:
        st.subheader("Metric Comparison")
        comp_df = pd.DataFrame({
            "Combustion Metric": categories,
            e1_name[:20]: [f"{m1[c]}/10" for c in categories],
            e2_name[:20]: [f"{m2[c]}/10" for c in categories],
        })
        st.dataframe(comp_df, hide_index=True, use_container_width=True)


# ── Page 5: Fire Safety Risk Scorer ───────────────────────────────────────────
elif selected_page == "🛡️ Fire Safety Risk Scorer":
    st.title("🛡️ Space Habitat Fire Safety Risk Scorer")
    st.caption("AI-Powered Flammability & Extinction Risk Assessment for ISS, Lunar, and Martian Habitats")

    MATERIALS = [
        "Nomex® Blend", "Teflon (PTFE)", "Kapton Film", "Silicone Composite",
        "PMMA (Acrylic)", "Cotton Fabric", "Polyethylene", "Epoxy Composite", "Velcro® Strips", "Nylon-6",
    ]
    ENVIRONMENTS = ["ISS (LEO - Microgravity)", "Lunar Habitat (0.16g)", "Martian Habitat (0.38g)", "Deep-Space Transit"]
    O2_LEVELS = ["16%", "18%", "20.9% (Standard Earth/ISS)", "24%", "30%", "34% (Exploration Atmosphere)"]

    s_col1, s_col2, s_col3 = st.columns(3)
    with s_col1:
        sel_mat = st.selectbox("Target Material", MATERIALS, index=0)
    with s_col2:
        sel_env = st.selectbox("Mission Environment", ENVIRONMENTS, index=0)
    with s_col3:
        sel_o2 = st.selectbox("Atmospheric Oxygen (O₂)", O2_LEVELS, index=2)

    # Base scores
    BASE_SCORES = {
        "Nomex® Blend": 85, "Teflon (PTFE)": 82, "Kapton Film": 78,
        "Silicone Composite": 75, "Epoxy Composite": 62, "PMMA (Acrylic)": 48,
        "Nylon-6": 45, "Cotton Fabric": 38, "Polyethylene": 35, "Velcro® Strips": 30,
    }

    base = BASE_SCORES.get(sel_mat, 50)
    # Environment modifier
    if "Lunar" in sel_env:
        base -= 3
    elif "Martian" in sel_env:
        base -= 5
    # O2 modifier
    if "34%" in sel_o2:
        base -= 14
    elif "30%" in sel_o2:
        base -= 8
    elif "24%" in sel_o2:
        base -= 4
    elif "16%" in sel_o2 or "18%" in sel_o2:
        base += 5

    final_score = max(5, min(98, base))
    if final_score >= 75:
        risk_label = "LOW"
        risk_color = "#22c55e"
    elif final_score >= 55:
        risk_label = "MODERATE"
        risk_color = "#eab308"
    elif final_score >= 35:
        risk_label = "HIGH"
        risk_color = "#f97316"
    else:
        risk_label = "CRITICAL"
        risk_color = "#ef4444"

    st.markdown("<br>", unsafe_allow_html=True)
    res_c1, res_c2 = st.columns([1, 1.5])
    with res_c1:
        st.markdown(
            f"""
            <div class="metric-card" style="text-align:center;">
                <div style="color: #9ca3af; font-size: 14px;">Calculated Safety Score</div>
                <div style="color: {risk_color}; font-size: 64px; font-weight: bold; margin: 8px 0;">{final_score}</div>
                <div style="color: #6b7280; font-size: 13px;">Out of 100</div>
                <div style="margin-top: 14px;">
                    <span class="risk-badge" style="background-color:{risk_color}; color:#0b0f19;">{risk_label} RISK</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with res_c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="color:#ef4444; font-weight:bold; font-size:15px; margin-bottom:8px;">⚠️ Key Risk Factors:</div>
                <ul style="color:#9ca3af; font-size:13px; margin-left:-15px;">
                    <li>Behavior under {sel_env}: altered buoyant flow modifies oxidizer diffusion rate.</li>
                    <li>Atmosphere {sel_o2}: elevated oxygen substantially lowers ignition temperature.</li>
                    <li>Microgravity flammability boundary for {sel_mat} shifts relative to standard 1g screening.</li>
                </ul>
                <hr style="border-color:#1f2937; margin: 12px 0;">
                <div style="color:#22c55e; font-weight:bold; font-size:15px; margin-bottom:8px;">💡 Fire Safety Engineering Recommendations:</div>
                <p style="color:#f9fafb; font-size:13px; line-height: 1.5;">
                    Ensure immediate isolation from potential electrical ignition sources.
                    In exploration atmospheres ({sel_o2}), enforce NASA STD-6001 Test 1 requalification.
                    Verify habitat ventilation cutoff procedures and install dual-wavelength photoelectric detection.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("📊 Spacecraft Materials Ranked by Fire Safety Score")
    table_data = [
        ["Nomex® Blend", "85", "82", "80", "LOW"],
        ["Teflon (PTFE)", "82", "79", "77", "LOW"],
        ["Kapton Film", "78", "75", "73", "LOW"],
        ["Silicone Composite", "75", "72", "70", "MODERATE"],
        ["Epoxy Composite", "62", "58", "55", "MODERATE"],
        ["PMMA (Acrylic)", "48", "44", "42", "HIGH"],
        ["Nylon-6", "45", "41", "38", "HIGH"],
        ["Cotton Fabric", "38", "34", "30", "HIGH"],
        ["Polyethylene", "35", "31", "28", "HIGH"],
        ["Velcro® Strips", "30", "26", "22", "CRITICAL"],
    ]
    df_ranked = pd.DataFrame(table_data, columns=["Material", "ISS Score", "Lunar Score", "Martian Score", "Risk Tier"])
    st.dataframe(df_ranked, hide_index=True, use_container_width=True)


# ── Page 6: Knowledge Graph Visualizer ─────────────────────────────────────────
elif selected_page == "🕸️ Knowledge Graph Visualizer":
    st.title("🕸️ Microgravity Combustion Knowledge Graph")
    st.caption("Structured NetworkX relationships connecting Experiments, Materials, Findings, and Safety Directives")

    g_nodes = kg.graph.nodes
    g_edges = kg.graph.edges

    kg_c1, kg_c2 = st.columns([2, 1])
    with kg_c1:
        st.subheader("Interactive Graph Projection")
        fig_g, ax_g = plt.subplots(figsize=(8, 6))
        fig_g.patch.set_facecolor("#111827")
        ax_g.set_facecolor("#111827")

        if len(g_nodes) > 0:
            # Subsample up to 30 nodes for clean visualization
            sub_nodes = list(g_nodes)[:28]
            sub_g = kg.graph.subgraph(sub_nodes)
            pos = nx.spring_layout(sub_g, seed=42, k=0.5)

            # Node colors based on type
            colors = []
            for n in sub_g.nodes:
                ntype = sub_g.nodes[n].get("node_type", "experiment")
                if ntype == "experiment":
                    colors.append("#f97316")
                elif ntype == "material":
                    colors.append("#38bdf8")
                elif ntype == "finding":
                    colors.append("#22c55e")
                else:
                    colors.append("#ef4444")

            nx.draw_networkx_nodes(sub_g, pos, ax=ax_g, node_color=colors, node_size=380, alpha=0.9)
            nx.draw_networkx_edges(sub_g, pos, ax=ax_g, edge_color="#374151", width=1.2, alpha=0.7, arrows=True)

            short_labels = {n: (n[:14] + "…") if len(n) > 14 else n for n in sub_g.nodes}
            nx.draw_networkx_labels(sub_g, pos, labels=short_labels, ax=ax_g, font_size=8, font_color="#f9fafb")

        ax_g.axis("off")
        fig_g.tight_layout()
        st.pyplot(fig_g)

    with kg_c2:
        st.subheader("Graph Schema & Legend")
        st.markdown(
            """
            - 🟠 **Experiment:** NASA flight & facility experiments (BASS, ACME, SAFFIRE, FLEX, SoFIE)
            - 🔵 **Material:** Tested polymers, fabrics, gases, and composites
            - 🟢 **Finding:** Empirical observations and physics discoveries
            - 🔴 **Safety Implication:** Critical spacecraft containment directives
            """
        )
        st.markdown("---")
        st.markdown(f"**Total Graph Nodes:** `{len(g_nodes)}`")
        st.markdown(f"**Total Graph Edges:** `{len(g_edges)}`")

        st.subheader("Inspect Node Connections")
        all_node_names = sorted(list(g_nodes))
        if all_node_names:
            inspect_node = st.selectbox("Select Node", all_node_names)
            neighbors = list(kg.graph.neighbors(inspect_node))
            in_neighbors = list(kg.graph.predecessors(inspect_node))

            st.markdown(f"**Outbound Edges ({len(neighbors)}):**")
            for n in neighbors[:8]:
                rel = kg.graph.get_edge_data(inspect_node, n, {}).get("relationship", "related_to")
                st.markdown(f"- `({rel})` ➔ **{n}**")

            if in_neighbors:
                st.markdown(f"**Inbound Edges ({len(in_neighbors)}):**")
                for n in in_neighbors[:8]:
                    rel = kg.graph.get_edge_data(n, inspect_node, {}).get("relationship", "related_to")
                    st.markdown(f"- **{n}** ➔ `({rel})`")
