"""
Streamlit Dashboard — Renewable Energy Generation Forecasting
Hackathon Demo UI for KREDL/KSPDCL
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
import requests
from datetime import date, timedelta

st.set_page_config(
    page_title="EcoPower Forecast | KREDL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8000"

# ─────────────────────────────────────────────
# CSS Styling
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main { background: #0a0f1e; color: #e2e8f0; }

.metric-card {
    background: linear-gradient(135deg, #1a2744 0%, #0f1a35 100%);
    border: 1px solid #2d4a7a;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 6px 0;
}
.metric-card h3 { color: #64b5f6; font-size: 0.85rem; margin: 0 0 6px 0; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; }
.metric-card .value { font-size: 2rem; font-weight: 700; color: #ffffff; }
.metric-card .sub   { font-size: 0.8rem; color: #90a4ae; margin-top: 4px; }

.confidence-HIGH   { background: #0d3b2e; border: 1px solid #00e676; border-radius: 8px; padding: 4px 10px; color: #00e676; font-size: 0.75rem; font-weight: 600; }
.confidence-MEDIUM { background: #2e2a0d; border: 1px solid #ffd740; border-radius: 8px; padding: 4px 10px; color: #ffd740; font-size: 0.75rem; font-weight: 600; }
.confidence-LOW    { background: #3b0d0d; border: 1px solid #ff5252; border-radius: 8px; padding: 4px 10px; color: #ff5252; font-size: 0.75rem; font-weight: 600; }

.hero-title { font-size: 2.2rem; font-weight: 700; background: linear-gradient(90deg, #64b5f6, #00e5ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 4px; }
.hero-sub   { color: #78909c; font-size: 1rem; margin-bottom: 24px; }

.section-header { font-size: 1.1rem; font-weight: 600; color: #90caf9; border-bottom: 1px solid #1e3a5f; padding-bottom: 8px; margin: 20px 0 14px 0; }

.shap-bar-pos { background: linear-gradient(90deg, #00e676, #1de9b6); height: 14px; border-radius: 4px; }
.shap-bar-neg { background: linear-gradient(90deg, #ff5252, #ff4081); height: 14px; border-radius: 4px; }

.narrative-box {
    background: linear-gradient(135deg, #0d2137, #0a1628);
    border-left: 4px solid #00e5ff;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    color: #b0bec5;
    font-size: 0.95rem;
    line-height: 1.6;
}

.stButton > button {
    background: linear-gradient(135deg, #1565c0, #0d47a1);
    color: white; border: none; border-radius: 8px;
    padding: 10px 24px; font-weight: 600; width: 100%;
    transition: all 0.2s;
}
.stButton > button:hover { background: linear-gradient(135deg, #1976d2, #1565c0); transform: translateY(-1px); }

.stSelectbox label, .stDateInput label, .stNumberInput label { color: #90caf9 !important; font-weight: 600; }

div[data-testid="stSidebarContent"] { background: #0d1526; border-right: 1px solid #1e3a5f; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def check_api():
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        return r.json()
    except Exception:
        return None

def confidence_badge(flag: str) -> str:
    label = flag.replace("_CONFIDENCE", "").replace("_", " ")
    cls = "HIGH" if "HIGH" in flag else ("LOW" if "LOW" in flag else "MEDIUM")
    return f'<span class="confidence-{cls}">{label}</span>'

def plot_forecast(schedule_df: pd.DataFrame, plant_id: str, capacity_mw: float) -> go.Figure:
    fig = go.Figure()
    times = schedule_df["time_from"]

    # Uncertainty band
    fig.add_trace(go.Scatter(
        x=list(times) + list(times[::-1]),
        y=list(schedule_df["p90_mw"]) + list(schedule_df["p10_mw"][::-1]),
        fill="toself",
        fillcolor="rgba(100,181,246,0.12)",
        line=dict(color="rgba(255,255,255,0)"),
        name="P10–P90 Band",
        hoverinfo="skip",
    ))
    # P10
    fig.add_trace(go.Scatter(
        x=times, y=schedule_df["p10_mw"],
        line=dict(color="#42a5f5", width=1, dash="dot"),
        name="P10 (Pessimistic)", mode="lines",
    ))
    # P90
    fig.add_trace(go.Scatter(
        x=times, y=schedule_df["p90_mw"],
        line=dict(color="#ef9a9a", width=1, dash="dot"),
        name="P90 (Optimistic)", mode="lines",
    ))
    # P50 (scheduled)
    fig.add_trace(go.Scatter(
        x=times, y=schedule_df["scheduled_gen_mw"],
        line=dict(color="#00e5ff", width=3),
        name="P50 (Scheduled)", mode="lines",
        hovertemplate="<b>Block %{text}</b><br>Scheduled: %{y:.1f} MW<extra></extra>",
        text=schedule_df["block_no"],
    ))
    # Capacity reference line
    fig.add_hline(
        y=capacity_mw, line_dash="dash",
        line_color="rgba(255,193,7,0.4)", line_width=1,
        annotation_text=f"Capacity: {capacity_mw} MW",
        annotation_font_color="#ffc107",
    )

    fig.update_layout(
        title=dict(text=f"<b>24-Hour Generation Forecast — {plant_id}</b>",
                   font=dict(color="#e2e8f0", size=16)),
        xaxis=dict(title="Time", color="#78909c",
                   gridcolor="#1a2744", showgrid=True),
        yaxis=dict(title="Generation (MW)", color="#78909c",
                   gridcolor="#1a2744", showgrid=True, range=[0, capacity_mw * 1.1]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    bgcolor="rgba(0,0,0,0)", font=dict(color="#b0bec5")),
        paper_bgcolor="#0a0f1e",
        plot_bgcolor="#0d1526",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=60, b=40),
        height=420,
    )
    return fig

def plot_shap(drivers: list) -> go.Figure:
    names  = [d["feature"] for d in drivers]
    values = [d["shap_value"] for d in drivers]
    colors = ["#00e676" if v >= 0 else "#ff5252" for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=names,
        orientation="h",
        marker_color=colors,
        text=[f"{v:+.4f}" for v in values],
        textposition="outside",
        textfont=dict(color="#e2e8f0", size=11),
    ))
    fig.update_layout(
        title=dict(text="<b>Feature Contributions (SHAP Values)</b>",
                   font=dict(color="#e2e8f0", size=14)),
        xaxis=dict(title="SHAP Value (impact on PLF)", color="#78909c",
                   gridcolor="#1a2744", zeroline=True,
                   zerolinecolor="#455a64", zerolinewidth=2),
        yaxis=dict(color="#b0bec5", autorange="reversed"),
        paper_bgcolor="#0a0f1e", plot_bgcolor="#0d1526",
        margin=dict(l=10, r=60, t=50, b=40),
        height=320,
    )
    return fig

def plot_uncertainty_heatmap(schedule_df: pd.DataFrame) -> go.Figure:
    """Heatmap showing uncertainty band across 96 blocks."""
    fig = go.Figure(go.Bar(
        x=schedule_df["time_from"],
        y=schedule_df["uncertainty_band_mw"],
        marker=dict(
            color=schedule_df["uncertainty_band_mw"],
            colorscale=[[0, "#00e676"], [0.5, "#ffd740"], [1, "#ff5252"]],
            showscale=True,
            colorbar=dict(title="MW", thickness=12,
                          tickfont=dict(color="#90a4ae")),
        ),
        name="Uncertainty Band (P90–P10)",
    ))
    fig.update_layout(
        title=dict(text="<b>Uncertainty Band Across 96 Blocks</b>",
                   font=dict(color="#e2e8f0", size=14)),
        xaxis=dict(title="Time Block", color="#78909c", gridcolor="#1a2744"),
        yaxis=dict(title="Uncertainty (MW)", color="#78909c", gridcolor="#1a2744"),
        paper_bgcolor="#0a0f1e", plot_bgcolor="#0d1526",
        margin=dict(l=10, r=10, t=50, b=40), height=250,
    )
    return fig

# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ EcoPower Forecast")
    st.markdown("*AI-powered generation forecasting for Karnataka's renewable grid*")
    st.divider()

    # API status
    health = check_api()
    if health:
        st.success("✅ API Connected")
        col1, col2 = st.columns(2)
        col1.metric("SCADA", "✓" if health.get("scada_loaded") else "✗")
        col2.metric("NWP",   "✓" if health.get("nwp_loaded") else "✗")
    else:
        st.error("❌ API Offline — start with: `uvicorn src.api.main:app --reload`")

    st.divider()
    st.markdown("### 📤 Upload Data")
    scada_file = st.file_uploader("SCADA Generation CSV", type=["csv"], key="scada")
    nwp_file   = st.file_uploader("NWP Weather CSV",      type=["csv"], key="nwp")

    if scada_file and st.button("Upload SCADA"):
        try:
            r = requests.post(f"{API_URL}/upload/scada",
                              files={"file": ("scada.csv", scada_file, "text/csv")})
            data = r.json()
            if r.status_code == 200:
                st.success(f"Loaded {data.get('rows',0):,} rows, {data.get('plants',0)} plants")
            else:
                st.error(data.get("detail", "Upload failed"))
        except Exception as e:
            st.error(str(e))

    if nwp_file and st.button("Upload NWP"):
        try:
            r = requests.post(f"{API_URL}/upload/nwp",
                              files={"file": ("nwp.csv", nwp_file, "text/csv")})
            data = r.json()
            if r.status_code == 200:
                st.success(f"Loaded {data.get('rows',0):,} rows")
            else:
                st.error(data.get("detail", "Upload failed"))
        except Exception as e:
            st.error(str(e))

    st.divider()
    st.markdown("### ⚙️ Forecast Settings")
    plant_id   = st.text_input("Plant ID", value="PLANT_001")
    plant_type = st.selectbox("Plant Type", ["solar", "wind"])
    capacity   = st.number_input("Installed Capacity (MW)", min_value=1.0, value=100.0, step=10.0)
    fc_date    = st.date_input("Forecast Date", value=date.today() + timedelta(days=1))
    use_fallback = st.checkbox("Use Persistence Fallback (no NWP)")

# ─────────────────────────────────────────────
# Main Content
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">Karnataka Renewable Generation Forecast</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Physics-informed AI forecasting · P10/P50/P90 Quantiles · SHAP Explainability · SLDC-Compatible</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📈 Forecast", "🔍 Explainability", "📋 SLDC Schedule", "📊 Portfolio"])

# ─── TAB 1: FORECAST ────────────────────────
with tab1:
    if st.button("🚀 Generate Forecast", key="gen_fc"):
        with st.spinner("Running LightGBM quantile models..."):
            payload = {
                "plant_id": plant_id,
                "plant_type": plant_type,
                "installed_capacity_mw": capacity,
                "forecast_date": str(fc_date),
                "use_fallback": use_fallback,
            }
            try:
                r = requests.post(f"{API_URL}/predict/plant", json=payload, timeout=30)
                if r.status_code != 200:
                    st.error(f"API Error: {r.json().get('detail', r.text)}")
                else:
                    data = r.json()
                    schedule = pd.DataFrame(data["schedule"])
                    st.session_state["schedule"]     = schedule
                    st.session_state["forecast_meta"] = data
            except Exception as e:
                st.error(f"Connection error: {e}")

    if "schedule" in st.session_state:
        schedule = st.session_state["schedule"]
        meta     = st.session_state["forecast_meta"]

        # KPI cards
        st.markdown('<div class="section-header">📊 Forecast Summary</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        total_p50 = schedule["scheduled_gen_mw"].sum() * 0.25  # MWh (15-min blocks)
        avg_uncert = schedule["uncertainty_band_mw"].mean()
        peak_mw   = schedule["scheduled_gen_mw"].max()
        low_conf  = (schedule["confidence_flag"] == "LOW_CONFIDENCE").sum()

        c1.markdown(f"""<div class="metric-card"><h3>Total Energy (P50)</h3><div class="value">{total_p50:.1f}</div><div class="sub">MWh for {fc_date}</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-card"><h3>Peak Generation</h3><div class="value">{peak_mw:.1f}</div><div class="sub">MW (P50 max)</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="metric-card"><h3>Avg Uncertainty</h3><div class="value">{avg_uncert:.1f}</div><div class="sub">MW (P90–P10 band)</div></div>""", unsafe_allow_html=True)
        c4.markdown(f"""<div class="metric-card"><h3>Low Confidence Blocks</h3><div class="value">{low_conf}</div><div class="sub">of 96 blocks → reserve needed</div></div>""", unsafe_allow_html=True)

        # Main forecast chart
        st.markdown('<div class="section-header">📈 24-Hour Generation Forecast</div>', unsafe_allow_html=True)
        st.plotly_chart(plot_forecast(schedule, plant_id, capacity), use_container_width=True)

        # Uncertainty heatmap
        st.plotly_chart(plot_uncertainty_heatmap(schedule), use_container_width=True)

    else:
        st.info("👆 Configure plant settings in the sidebar, then click **Generate Forecast**.")

# ─── TAB 2: EXPLAINABILITY ──────────────────
with tab2:
    st.markdown('<div class="section-header">🔍 SHAP Feature Attribution</div>', unsafe_allow_html=True)
    st.markdown("Select a specific forecast block to understand exactly **why** the model predicted that value.")

    if "schedule" not in st.session_state:
        st.info("Generate a forecast first (Tab 1).")
    else:
        schedule = st.session_state["schedule"]
        block_options = [f"Block {r['block_no']:02d} — {r['time_from']} ({r['scheduled_gen_mw']:.1f} MW)"
                         for _, r in schedule.iterrows()]
        selected = st.selectbox("Select Time Block to Explain", block_options)
        block_no = int(selected.split(" ")[1]) - 1
        selected_row = schedule.iloc[block_no]
        ts_str = f"{fc_date}T{selected_row['time_from']}:00"

        if st.button("🔬 Explain This Block"):
            with st.spinner("Computing SHAP values..."):
                try:
                    params = {
                        "timestamp": ts_str,
                        "plant_type": plant_type,
                        "installed_capacity_mw": capacity,
                    }
                    r = requests.get(
                        f"{API_URL}/explain/{plant_id}",
                        params=params, timeout=30
                    )
                    if r.status_code == 200:
                        st.session_state["explanation"] = r.json()
                    else:
                        st.error(r.json().get("detail", r.text))
                except Exception as e:
                    st.error(str(e))

        if "explanation" in st.session_state:
            exp = st.session_state["explanation"]

            col1, col2 = st.columns([2, 1])
            with col1:
                if exp.get("top_drivers"):
                    st.plotly_chart(plot_shap(exp["top_drivers"]), use_container_width=True)

            with col2:
                st.markdown("**Prediction Breakdown**")
                st.markdown(f"""
                - **Base value (PLF):** `{exp.get('base_value_plf', 'N/A')}`
                - **Predicted PLF:** `{exp.get('predicted_plf', 'N/A')}`
                - **Predicted MW:** `{exp.get('predicted_mw', 'N/A')} MW`
                """)
                st.markdown("**Top Drivers:**")
                for d in exp.get("top_drivers", []):
                    arrow = "🟢 ↑" if d["shap_value"] >= 0 else "🔴 ↓"
                    st.markdown(f"{arrow} **{d['feature']}** = `{d['value']:.3f}` → `{d['shap_value']:+.4f}`")

            st.markdown('<div class="narrative-box">💡 ' + exp.get("narrative", "") + '</div>', unsafe_allow_html=True)

# ─── TAB 3: SLDC SCHEDULE ───────────────────
with tab3:
    st.markdown('<div class="section-header">📋 SLDC 96-Block Schedule</div>', unsafe_allow_html=True)
    if "schedule" not in st.session_state:
        st.info("Generate a forecast first (Tab 1).")
    else:
        schedule = st.session_state["schedule"]
        display_cols = ["block_no", "time_from", "time_to",
                        "scheduled_gen_mw", "p10_mw", "p90_mw",
                        "uncertainty_band_mw", "confidence_flag"]
        available = [c for c in display_cols if c in schedule.columns]

        # Color-coded confidence
        def highlight_confidence(row):
            if row.get("confidence_flag") == "LOW_CONFIDENCE":
                return ["background-color: #3b0d0d"] * len(row)
            elif row.get("confidence_flag") == "HIGH_CONFIDENCE":
                return ["background-color: #0d3b2e"] * len(row)
            return [""] * len(row)

        st.dataframe(
            schedule[available].style.apply(highlight_confidence, axis=1),
            use_container_width=True, height=400,
        )

        csv_bytes = schedule.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download SLDC Schedule (CSV)",
            data=csv_bytes,
            file_name=f"sldc_schedule_{plant_id}_{fc_date}.csv",
            mime="text/csv",
        )

# ─── TAB 4: PORTFOLIO ───────────────────────
with tab4:
    st.markdown('<div class="section-header">📊 Portfolio Overview</div>', unsafe_allow_html=True)
    st.markdown("Enter multiple plants below to generate and compare forecasts across the fleet.")

    portfolio_input = st.text_area(
        "Plant definitions (one per line): plant_id, plant_type, capacity_mw",
        value="SOLAR_01,solar,50\nSOLAR_02,solar,100\nWIND_01,wind,75\nWIND_02,wind,120",
        height=100,
    )

    if st.button("🌐 Run Portfolio Forecast"):
        plants = []
        for line in portfolio_input.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 3:
                plants.append({
                    "plant_id": parts[0],
                    "plant_type": parts[1],
                    "installed_capacity_mw": float(parts[2]),
                })

        if not plants:
            st.warning("No valid plant definitions found.")
        else:
            with st.spinner(f"Forecasting {len(plants)} plants..."):
                try:
                    r = requests.post(f"{API_URL}/predict/portfolio", json={
                        "forecast_date": str(fc_date),
                        "plants": plants,
                    }, timeout=60)
                    if r.status_code == 200:
                        pdata = r.json()
                        st.session_state["portfolio"] = pdata
                        st.success(f"Forecasts generated for {pdata['n_plants']} plants")
                    else:
                        st.error(r.json().get("detail", r.text))
                except Exception as e:
                    st.error(str(e))

    if "portfolio" in st.session_state:
        pdata = st.session_state["portfolio"]
        # Aggregate totals chart
        totals = []
        for pid, sched in pdata["schedules"].items():
            df_s = pd.DataFrame(sched)
            totals.append({
                "plant_id": pid,
                "total_mwh_p50": df_s["scheduled_gen_mw"].sum() * 0.25,
                "peak_mw_p50":   df_s["scheduled_gen_mw"].max(),
                "avg_uncertainty": df_s["uncertainty_band_mw"].mean(),
            })
        totals_df = pd.DataFrame(totals)

        fig = px.bar(
            totals_df, x="plant_id", y="total_mwh_p50",
            color="avg_uncertainty",
            color_continuous_scale=[[0, "#00e676"], [0.5, "#ffd740"], [1, "#ff5252"]],
            labels={"total_mwh_p50": "Total Energy (MWh)", "avg_uncertainty": "Avg Uncertainty (MW)"},
            title="Portfolio Energy Forecast (P50) — Day Total",
        )
        fig.update_layout(
            paper_bgcolor="#0a0f1e", plot_bgcolor="#0d1526",
            font=dict(color="#e2e8f0"), title_font_color="#e2e8f0",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(totals_df, use_container_width=True)

# Footer
st.divider()
st.markdown(
    "<center style='color:#37474f;font-size:0.75rem;'>"
    "EcoPower Forecast · KREDL/KSPDCL Hackathon Prototype · "
    "LightGBM + SHAP · Physics-Informed Feature Engineering"
    "</center>",
    unsafe_allow_html=True,
)
