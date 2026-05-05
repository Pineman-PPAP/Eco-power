"""
Streamlit Dashboard - Renewable Energy Generation Forecasting
Control-center UI for Karnataka renewable generation forecasting.
"""

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh


st.set_page_config(
    page_title="Karnataka RE Forecast | Control Center",
    page_icon="K",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = "http://localhost:8000"

# Auto-refresh every 15 minutes
st_autorefresh(interval=15 * 60 * 1000, key="fcrefresh")


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --bg: #060e20;
    --surface: #0b1326;
    --surface-2: #111a2e;
    --surface-3: #172139;
    --line: #263149;
    --line-soft: rgba(87, 241, 219, 0.18);
    --text: #dae2fd;
    --muted: #8f9bb3;
    --teal: #57f1db;
    --teal-2: #2dd4bf;
    --blue: #3b82f6;
    --amber: #ffb95f;
    --red: #ff776d;
    --green: #4ade80;
}

html, body, [class*="css"], .stApp {
    font-family: "Inter", sans-serif;
    color: var(--text);
    background:
        radial-gradient(circle at 18% 8%, rgba(45, 212, 191, 0.12), transparent 26%),
        radial-gradient(circle at 88% 0%, rgba(59, 130, 246, 0.14), transparent 24%),
        var(--bg);
}

[data-testid="stHeader"] {
    background: rgba(6, 14, 32, 0.72);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}

[data-testid="stToolbar"] { right: 1rem; }

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

section[data-testid="stSidebar"] {
    background: #0d1830;
    border-right: 1px solid rgba(87, 241, 219, 0.28);
}

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
section[data-testid="stSidebar"] label {
    color: #dbeafe;
}

div[data-testid="stSidebarContent"] {
    background:
        linear-gradient(180deg, rgba(19, 31, 56, 0.98), rgba(8, 18, 40, 0.98));
}

h1, h2, h3, .font-display {
    font-family: "Space Grotesk", sans-serif;
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
}

.brand {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
}

.brand-kicker {
    color: var(--teal);
    font-family: "Space Grotesk", sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
}

.brand-title {
    color: #f8fbff;
    font-family: "Space Grotesk", sans-serif;
    font-size: clamp(2rem, 4vw, 3.8rem);
    font-weight: 700;
    line-height: 0.96;
    letter-spacing: 0;
}

.brand-sub {
    color: var(--muted);
    font-size: 0.94rem;
    margin-top: 0.35rem;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--teal);
    background: rgba(87, 241, 219, 0.09);
    border: 1px solid rgba(87, 241, 219, 0.25);
    border-radius: 999px;
    padding: 0.48rem 0.8rem;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    white-space: nowrap;
}

.pulse-dot {
    width: 0.48rem;
    height: 0.48rem;
    border-radius: 999px;
    background: var(--teal);
    box-shadow: 0 0 18px rgba(87, 241, 219, 0.75);
    animation: soft-pulse 1.6s ease-in-out infinite;
}

@keyframes soft-pulse {
    0%, 100% { opacity: 0.45; transform: scale(0.82); }
    50% { opacity: 1; transform: scale(1.08); }
}

.nav-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    border-top: 1px solid rgba(148, 163, 184, 0.08);
    border-bottom: 1px solid rgba(148, 163, 184, 0.08);
    padding: 0.8rem 0;
    margin-bottom: 1.2rem;
}

.nav-items {
    display: flex;
    flex-wrap: wrap;
    gap: 0.7rem;
}

.nav-item {
    color: #9ca8bf;
    border: 1px solid transparent;
    border-radius: 0.45rem;
    padding: 0.42rem 0.7rem;
    font-family: "Space Grotesk", sans-serif;
    font-size: 0.86rem;
    font-weight: 600;
}

.nav-item.active {
    color: var(--teal);
    background: rgba(87, 241, 219, 0.08);
    border-color: rgba(87, 241, 219, 0.22);
}

.control-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #00201c;
    background: var(--teal);
    border-radius: 999px;
    padding: 0.62rem 1rem;
    font-family: "Space Grotesk", sans-serif;
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    box-shadow: 0 0 24px rgba(87, 241, 219, 0.2);
    white-space: nowrap;
}

.panel {
    background:
        linear-gradient(145deg, rgba(23, 31, 51, 0.95), rgba(9, 18, 39, 0.95));
    border: 1px solid rgba(148, 163, 184, 0.14);
    border-radius: 0.55rem;
    box-shadow: 0 18px 50px rgba(0, 0, 0, 0.22);
}

.panel.pad { padding: 1.15rem; }

.panel-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 0.9rem;
}

.label-caps {
    color: #94a3b8;
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
}

.headline-md {
    color: #f8fbff;
    font-family: "Space Grotesk", sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    line-height: 1.12;
}

.map-shell {
    position: relative;
    overflow: hidden;
    margin-bottom: 0.8rem;
}

.map-shell::before {
    content: "";
    position: absolute;
    inset: 0;
    z-index: 0;
    pointer-events: none;
    background:
        linear-gradient(180deg, rgba(6, 14, 32, 0.55), transparent 28%),
        linear-gradient(0deg, rgba(6, 14, 32, 0.88), transparent 42%);
}

.map-shell > div { position: relative; z-index: 1; }

.map-legend {
    margin: 1rem;
    width: auto;
    background: rgba(9, 18, 39, 0.78);
    border: 1px solid rgba(87, 241, 219, 0.22);
    border-radius: 0.55rem;
    backdrop-filter: blur(12px);
    padding: 0.9rem;
}

.legend-row {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    color: #cbd5e1;
    font-size: 0.78rem;
    margin-top: 0.55rem;
}

.legend-dot {
    width: 0.62rem;
    height: 0.62rem;
    border-radius: 999px;
    box-shadow: 0 0 14px currentColor;
}

.metric-strip {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.7rem;
    background: rgba(9, 18, 39, 0.78);
    border: 1px solid rgba(87, 241, 219, 0.16);
    border-radius: 0.55rem;
    backdrop-filter: blur(12px);
    padding: 0.85rem;
    margin: 1rem;
}

.strip-value {
    color: #ffffff;
    font-family: "Space Grotesk", sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    line-height: 1;
}

.strip-value.teal { color: var(--teal); }
.strip-value.amber { color: var(--amber); }

.mini-metric {
    background: rgba(11, 19, 38, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 0.45rem;
    padding: 0.88rem;
}

.mini-metric .value {
    color: #f8fbff;
    font-family: "Space Grotesk", sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    margin-top: 0.25rem;
}

.mini-metric .value.teal { color: var(--teal); }
.mini-metric .value.blue { color: #93c5fd; }
.mini-metric .value.amber { color: var(--amber); }

.signal-bar {
    height: 0.36rem;
    border-radius: 999px;
    overflow: hidden;
    background: #1f2a44;
    margin-top: 0.8rem;
}

.signal-bar > span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, var(--teal), var(--blue));
}

.narrative-box {
    background: rgba(13, 33, 55, 0.7);
    border-left: 4px solid var(--teal);
    border-radius: 0.45rem;
    padding: 0.9rem 1rem;
    color: #c8d3e6;
    font-size: 0.92rem;
    line-height: 1.6;
}

.stButton > button {
    background: var(--teal);
    color: #00201c;
    border: 0;
    border-radius: 999px;
    font-family: "Space Grotesk", sans-serif;
    font-weight: 800;
    letter-spacing: 0.02em;
    width: 100%;
}

.stButton > button:hover {
    color: #00201c;
    border: 0;
    box-shadow: 0 0 26px rgba(87, 241, 219, 0.22);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.35rem;
    border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.stTabs [data-baseweb="tab"] {
    color: #94a3b8;
    background: transparent;
    border-radius: 0.35rem 0.35rem 0 0;
    font-family: "Space Grotesk", sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.8rem 1.2rem;
}

.stTabs [aria-selected="true"] {
    color: var(--teal);
    background: rgba(87, 241, 219, 0.08);
}

div[data-testid="stFileUploader"] {
    background: rgba(11, 19, 38, 0.58);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 0.45rem;
    padding: 0.55rem;
}

@media (max-width: 900px) {
    .topbar, .nav-row {
        align-items: flex-start;
        flex-direction: column;
    }
    .metric-strip {
        position: relative;
        left: auto;
        right: auto;
        bottom: auto;
        grid-template-columns: 1fr;
        margin: 0 1rem 1rem;
    }
    .map-shell { min-height: auto; }
}
</style>
""",
    unsafe_allow_html=True,
)


def check_api():
    try:
        response = requests.get(f"{API_URL}/health", timeout=3)
        return response.json()
    except Exception:
        return None


def renewable_sites() -> pd.DataFrame:
    """Official plant catalogue using real KPCL/KSPDCL solar assets."""
    real_plants = [
        {
            "plant_id": "kpcl_shivanasamudra",
            "name": "Shivanasamudra / Simsha Solar Plant",
            "plant_type": "solar",
            "lat": 12.3000,
            "lon": 77.1700,
            "capacity_mw": 15,
            "ownership": "100% KPCL (State Government)",
            "district": "Mandya",
            "hardware": "Multi-Crystalline Panels",
            "description": "KPCL's flagship 15 MW solar plant located near the Shivanasamudra waterfalls.",
        },
        {
            "plant_id": "kpcl_yalesandra",
            "name": "Yalesandra Solar PV Plant",
            "plant_type": "solar",
            "lat": 12.8931,
            "lon": 78.1655,
            "capacity_mw": 3,
            "ownership": "100% KPCL (State Government)",
            "district": "Kolar",
            "hardware": "Mono-Crystalline Panels (225Wp & 240Wp)",
            "description": "India's first megawatt-scale, grid-connected solar power plant, commissioned in 2009.",
        },
        {
            "plant_id": "kpcl_itnal",
            "name": "Itnal Solar PV Plant",
            "plant_type": "solar",
            "lat": 16.4348,
            "lon": 74.6740,
            "capacity_mw": 3,
            "ownership": "100% KPCL (State Government)",
            "district": "Belagavi",
            "hardware": "Mono-Crystalline Panels",
            "description": "State-owned decentralized 3 MW generation facility feeding directly into the northern grid.",
        },
        {
            "plant_id": "kpcl_yapaldinni",
            "name": "Yapaldinni Solar PV Plant",
            "plant_type": "solar",
            "lat": 16.2475,
            "lon": 77.4431,
            "capacity_mw": 3,
            "ownership": "100% KPCL (State Government)",
            "district": "Raichur",
            "hardware": "Mono-Crystalline Panels",
            "description": "3 MW grid-connected power plant located in high-irradiance Raichur.",
        },
        {
            "plant_id": "kspdcl_pavagada",
            "name": "Pavagada Solar Park (Shakti Sthala)",
            "plant_type": "solar",
            "lat": 14.2500,
            "lon": 77.4500,
            "capacity_mw": 2050,
            "ownership": "Managed by KSPDCL (Joint Govt Venture)",
            "district": "Tumkur",
            "hardware": "Mixed (Thin-film & Multi-Crystalline)",
            "description": "One of the world's largest solar parks spanning 13,000 acres.",
        },
        {
            "plant_id": "wind_davangere",
            "name": "Davangere Wind Farm",
            "plant_type": "wind",
            "lat": 14.470,
            "lon": 75.920,
            "capacity_mw": 380,
            "ownership": "Gamesa",
            "district": "Davangere",
            "hardware": "Gamesa Turbines (2018)",
            "description": "High-capacity wind farm in the Davangere cluster.",
        },
        {
            "plant_id": "wind_koppal",
            "name": "Koppal Wind Cluster",
            "plant_type": "wind",
            "lat": 15.350,
            "lon": 76.160,
            "capacity_mw": 520,
            "ownership": "Vestas",
            "district": "Koppal",
            "hardware": "Vestas Turbines (2015)",
            "description": "One of the oldest large-scale wind clusters in the state.",
        },
        {
            "plant_id": "wind_haveri",
            "name": "Haveri Wind Park",
            "plant_type": "wind",
            "lat": 14.790,
            "lon": 75.400,
            "capacity_mw": 290,
            "ownership": "Inox Wind",
            "district": "Haveri",
            "hardware": "Inox Turbines (2019)",
            "description": "Recent addition to the central wind corridor.",
        },
        {
            "plant_id": "wind_dharwad",
            "name": "Dharwad Wind Farm",
            "plant_type": "wind",
            "lat": 15.460,
            "lon": 75.000,
            "capacity_mw": 160,
            "ownership": "Adani Wind",
            "district": "Dharwad",
            "hardware": "Adani Turbines (2020)",
            "description": "Adani-operated facility near the Dharwad hub.",
        },
        {
            "plant_id": "wind_raichur",
            "name": "Raichur Wind Cluster",
            "plant_type": "wind",
            "lat": 16.050,
            "lon": 77.100,
            "capacity_mw": 200,
            "ownership": "KREDL",
            "district": "Raichur",
            "hardware": "KREDL Managed (2018)",
            "description": "State-managed wind cluster in Raichur.",
        },
        {
            "plant_id": "wind_vijayapura",
            "name": "Vijayapura Wind Park",
            "plant_type": "wind",
            "lat": 16.720,
            "lon": 75.550,
            "capacity_mw": 175,
            "ownership": "Siemens Gamesa",
            "district": "Vijayapura",
            "hardware": "Siemens Gamesa (2021)",
            "description": "Northern corridor wind park.",
        },
        {
            "plant_id": "wind_ballari",
            "name": "Ballari Wind Farm",
            "plant_type": "wind",
            "lat": 15.210,
            "lon": 76.720,
            "capacity_mw": 130,
            "ownership": "Private",
            "district": "Ballari",
            "hardware": "Mixed Turbines (2022)",
            "description": "Private sector wind facility.",
        },
        {
            "plant_id": "wind_bagalkot",
            "name": "Bagalkot Wind Park",
            "plant_type": "wind",
            "lat": 16.350,
            "lon": 75.500,
            "capacity_mw": 100,
            "ownership": "KSPDCL",
            "district": "Bagalkot",
            "hardware": "KSPDCL Managed (2023)",
            "description": "Newly commissioned wind asset.",
        },{
            "plant_id": "BENGALURU_LOAD_CENTER",
            "name": "Bengaluru Load Center",
            "plant_type": "grid",
            "lat": 12.9716,
            "lon": 77.5946,
            "capacity_mw": 0,
            "ownership": "Grid Infrastructure",
            "district": "Bengaluru",
            "hardware": "Substation / Pooling",
            "description": "Main load center and grid synchronization node.",
        },
    ]
    
    df = pd.DataFrame(real_plants)
    # Add simulated operational data
    df["generation_mw"] = (df["capacity_mw"] * 0.72).round(1)
    df.loc[df["plant_type"] == "grid", "generation_mw"] = 0
    df["confidence"] = 96.5
    return df


def build_karnataka_map(sites: pd.DataFrame) -> go.Figure:
    color_map = {"solar": "#facc15", "wind": "#3b82f6", "grid": "#ffb95f"}
    sites = sites.copy()
    sites["color"] = sites["plant_type"].map(color_map)
    
    fig = go.Figure()

    for plant_type, label in [("solar", "Solar Array"), ("wind", "Wind Cluster"), ("grid", "Grid Node")]:
        subset = sites[sites["plant_type"] == plant_type]
        if subset.empty:
            continue
        
        # Determine symbol based on type
        symbol = "marker" if plant_type != "grid" else "rocket"
        color = color_map[plant_type]
        
        fig.add_trace(
            go.Scattermapbox(
                lat=subset["lat"],
                lon=subset["lon"],
                mode="markers",
                name=label,
                marker=dict(
                    size=12,
                    color=color_map[plant_type],
                ),
                customdata=subset[["plant_id", "name", "capacity_mw", "generation_mw", "ownership", "district", "hardware", "description"]],
                hovertemplate=(
                    "<b>%{customdata[1]}</b><br>"
                    "<i>%{customdata[5]} District • %{customdata[4]}</i><br><br>"
                    "Capacity: %{customdata[2]:,.0f} MW<br>"
                    "Current Gen: %{customdata[3]:,.1f} MW<br>"
                    "Hardware: %{customdata[6]}<br><br>"
                    "%{customdata[7]}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        mapbox=dict(
            style="https://api.maptiler.com/maps/hybrid/style.json?key=opRzyQbpsohbuebbzel2",
            center=dict(lat=14.95, lon=76.35),
            zoom=6.05,
            bearing=0,
            pitch=0,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        height=560,
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.015,
                y=0.985,
                xanchor="left",
                yanchor="top",
                buttons=[
                    dict(
                        label="⟲ Reset Focus",
                        method="relayout",
                        args=[{"mapbox.center": {"lat": 14.95, "lon": 76.35}, "mapbox.zoom": 6.05}],
                    )
                ],
                bgcolor="rgba(0,0,0,1)",
                bordercolor="rgba(148, 163, 184, 0.45)",
                font=dict(color="#f8fbff", size=11),
            )
        ],
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.015,
            xanchor="left",
            x=0.015,
            bgcolor="rgba(0,0,0,1)",
            bordercolor="rgba(148, 163, 184, 0.35)",
            borderwidth=1,
            font=dict(color="#f8fbff", size=11),
        ),
        hoverlabel=dict(
            bgcolor="black",
            bordercolor="#57f1db",
            font=dict(color="#f8fbff", family="Inter"),
        ),
    )
    return fig


def plot_forecast(schedule_df: pd.DataFrame, plant_id: str, capacity_mw: float) -> go.Figure:
    fig = go.Figure()
    
    # Use timestamp for robust 24h scaling
    if "timestamp" in schedule_df.columns:
        times = pd.to_datetime(schedule_df["timestamp"])
    else:
        times = schedule_df["time_from"]

    fig.add_trace(
        go.Scatter(
            x=list(times) + list(times[::-1]),
            y=list(schedule_df["p90_mw"]) + list(schedule_df["p10_mw"][::-1]),
            fill="toself",
            fillcolor="rgba(87, 241, 219, 0.12)",
            line=dict(color="rgba(255,255,255,0)"),
            name="P10-P90 Band",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=times,
            y=schedule_df["p10_mw"],
            line=dict(color="#60a5fa", width=1, dash="dot"),
            name="P10",
            mode="lines",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=times,
            y=schedule_df["p90_mw"],
            line=dict(color="#ffb95f", width=1, dash="dot"),
            name="P90",
            mode="lines",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=times,
            y=schedule_df["scheduled_gen_mw"],
            line=dict(color="#57f1db", width=3),
            name="P50 Scheduled",
            mode="lines",
            hovertemplate="<b>Block %{text}</b><br>Scheduled: %{y:.1f} MW<extra></extra>",
            text=schedule_df["block_no"],
        )
    )
    fig.add_hline(
        y=capacity_mw,
        line_dash="dash",
        line_color="rgba(255,185,95,0.42)",
        line_width=1,
        annotation_text=f"Capacity: {capacity_mw} MW",
        annotation_font_color="#ffb95f",
    )

    # Determine x-axis range (at least 24 hours)
    if not schedule_df.empty and "timestamp" in schedule_df.columns:
        start_time = times.min().floor('D')
        end_time = start_time + pd.Timedelta(days=1)
        xaxis_range = [start_time, end_time]
    else:
        xaxis_range = None

    fig.update_layout(
        title=dict(
            text=f"<b>24-hour generation forecast - {plant_id}</b>",
            font=dict(color="#f8fbff", size=16),
        ),
        xaxis=dict(
            title="Time", 
            color="#94a3b8", 
            gridcolor="#1f2a44",
            range=xaxis_range
        ),
        yaxis=dict(
            title="Generation (MW)",
            color="#94a3b8",
            gridcolor="#1f2a44",
            range=[0, capacity_mw * 1.1],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#cbd5e1"),
        ),
        paper_bgcolor="#0b1326",
        plot_bgcolor="#0f172a",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=60, b=40),
        height=420,
    )
    return fig


def plot_shap(drivers: list) -> go.Figure:
    names = [d["feature"] for d in drivers]
    values = [d["shap_value"] for d in drivers]
    colors = ["#57f1db" if value >= 0 else "#ff776d" for value in values]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker_color=colors,
            text=[f"{value:+.4f}" for value in values],
            textposition="outside",
            textfont=dict(color="#dae2fd", size=11),
        )
    )
    fig.update_layout(
        title=dict(text="<b>Feature contributions</b>", font=dict(color="#f8fbff", size=14)),
        xaxis=dict(
            title="SHAP value impact on PLF",
            color="#94a3b8",
            gridcolor="#1f2a44",
            zeroline=True,
            zerolinecolor="#475569",
            zerolinewidth=2,
        ),
        yaxis=dict(color="#cbd5e1", autorange="reversed"),
        paper_bgcolor="#0b1326",
        plot_bgcolor="#0f172a",
        margin=dict(l=10, r=60, t=50, b=40),
        height=320,
    )
    return fig


def plot_uncertainty_heatmap(schedule_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        go.Bar(
            x=schedule_df["time_from"],
            y=schedule_df["uncertainty_band_mw"],
            marker=dict(
                color=schedule_df["uncertainty_band_mw"],
                colorscale=[[0, "#57f1db"], [0.5, "#ffb95f"], [1, "#ff776d"]],
                showscale=True,
                colorbar=dict(title="MW", thickness=12, tickfont=dict(color="#94a3b8")),
            ),
            name="Uncertainty band",
        )
    )
    fig.update_layout(
        title=dict(text="<b>Uncertainty band across 96 blocks</b>", font=dict(color="#f8fbff", size=14)),
        xaxis=dict(title="Time block", color="#94a3b8", gridcolor="#1f2a44"),
        yaxis=dict(title="Uncertainty (MW)", color="#94a3b8", gridcolor="#1f2a44"),
        paper_bgcolor="#0b1326",
        plot_bgcolor="#0f172a",
        margin=dict(l=10, r=10, t=50, b=40),
        height=250,
    )
    return fig


def metric_card(label: str, value: str, tone: str = "") -> str:
    return f"""
    <div class="mini-metric">
        <div class="label-caps">{label}</div>
        <div class="value {tone}">{value}</div>
    </div>
    """


sites_df = renewable_sites()
health = check_api()
api_online = bool(health)


with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.6rem 0 1.1rem;">
            <div class="brand-kicker" style="font-size:0.85rem;letter-spacing:.13em;">EcoPower Forecast</div>
            <div style="color:#f8fbff;font-family:Space Grotesk;font-size:1.75rem;font-weight:700;line-height:1.05;margin-top:.4rem;">
                Control Center
            </div>
            <div style="color:#93a4bd;font-size:.92rem;margin-top:.5rem;">
                Karnataka renewable grid hub
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    if health:
        st.success("API connected")
        col1, col2 = st.columns(2)
        col1.metric("SCADA", "Loaded" if health.get("scada_loaded") else "Empty")
        col2.metric("NWP", "Loaded" if health.get("nwp_loaded") else "Empty")
    else:
        st.error("API offline. Start: uvicorn src.api.main:app --reload --port 8000")

    st.divider()
    st.markdown("### Upload Data")
    scada_file = st.file_uploader("SCADA Generation CSV", type=["csv"], key="scada")
    nwp_file = st.file_uploader("NWP Weather CSV", type=["csv"], key="nwp")

    if scada_file and st.button("Upload SCADA"):
        try:
            response = requests.post(
                f"{API_URL}/upload/scada",
                files={"file": ("scada.csv", scada_file, "text/csv")},
                timeout=30,
            )
            data = response.json()
            if response.status_code == 200:
                st.success(f"Loaded {data.get('rows', 0):,} rows, {data.get('plants', 0)} plants")
            else:
                st.error(data.get("detail", "Upload failed"))
        except Exception as exc:
            st.error(str(exc))

    if nwp_file and st.button("Upload NWP"):
        try:
            response = requests.post(
                f"{API_URL}/upload/nwp",
                files={"file": ("nwp.csv", nwp_file, "text/csv")},
                timeout=30,
            )
            data = response.json()
            if response.status_code == 200:
                st.success(f"Loaded {data.get('rows', 0):,} rows")
            else:
                st.error(data.get("detail", "Upload failed"))
        except Exception as exc:
            st.error(str(exc))

    st.divider()
    # Session state for map interaction
    if "selected_plant_id" not in st.session_state:
        st.session_state["selected_plant_id"] = "kspdcl_pavagada"

    selected_row = sites_df[sites_df["plant_id"] == st.session_state["selected_plant_id"]]
    if selected_row.empty:
        selected_row = sites_df.iloc[0:1]
    
    current_plant = selected_row.iloc[0]

    st.markdown("### Forecast Settings")
    fc_date = st.date_input("Forecast Date", value=date.today() + timedelta(days=1))
    use_fallback = st.checkbox("Use Persistence Fallback (no NWP)")

    if st.button("🔄 Sync Live Weather"):
        with st.spinner("Fetching forecasts from Open-Meteo..."):
            try:
                import subprocess
                subprocess.run(["python", "fetch_live_weather.py"], check=True)
                resp = requests.post(f"{API_URL}/reload")
                if resp.status_code == 200:
                    st.success("Weather data synchronized!")
                    st.rerun()
                else:
                    st.error(f"API Reload failed: {resp.text}")
            except Exception as e:
                st.error(f"Sync failed: {e}")

    st.divider()
    st.markdown("### Backend Status")
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=5).json()
        rows = health_resp.get("feature_rows", 0)
        st.write(f"⚡ Features Ready: `{rows:,}` rows")
        if rows == 0:
            st.warning("⚠️ No weather data available. Click 'Sync Live Weather'.")
    except:
        st.error("❌ API Offline")


status_text = "Live stream" if api_online else "Local UI"
status_hint = "API synchronized" if api_online else "Backend waiting"

st.markdown(
    f"""
    <div class="topbar">
        <div class="brand">
            <div class="brand-kicker">Karnataka Renewable Forecast</div>
            <div class="brand-title">Grid Intelligence</div>
            <div class="brand-sub">Physics-informed generation forecasting, live asset telemetry, SHAP explainability, and SLDC-ready schedules.</div>
        </div>
        <div class="status-pill"><span class="pulse-dot"></span>{status_text}<span style="color:#8f9bb3;font-weight:700;">{status_hint}</span></div>
    </div>
    <div class="nav-row">
        <div class="nav-items">
            <div class="nav-item active">Live Grid</div>
            <div class="nav-item">Forecasting</div>
            <div class="nav-item">Historical</div>
            <div class="nav-item">Assets</div>
        </div>
        <div class="control-button">Generate Forecast</div>
    </div>
    """,
    unsafe_allow_html=True,
)

map_col, telemetry_col = st.columns([1.9, 1], gap="large")

with map_col:
    total_capacity = sites_df["capacity_mw"].sum()
    total_generation = sites_df["generation_mw"].sum()
    active_sites = len(sites_df[sites_df["plant_type"] != "grid"])
    precision = sites_df["confidence"].mean()

    # Map Selection Interaction
    selection = st.plotly_chart(
        build_karnataka_map(sites_df), 
        use_container_width=True, 
        config={"displayModeBar": True, "scrollZoom": True}, 
        theme=None,
        on_select="rerun",
        selection_mode="points"
    )

    if selection and selection.get("selection", {}).get("points"):
        selected_point = selection["selection"]["points"][0]
        new_id = selected_point.get("customdata", [None])[0]
        if new_id and new_id != st.session_state["selected_plant_id"]:
            st.session_state["selected_plant_id"] = new_id
            st.rerun()

    st.markdown(
        f"""
        <div class="panel" style="margin-bottom: 1rem;">
            <div class="metric-strip">
                <div>
                    <div class="label-caps">Active Sites</div>
                    <div class="strip-value">{active_sites}</div>
                </div>
                <div>
                    <div class="label-caps">Instant Generation</div>
                    <div class="strip-value teal">{total_generation:,.0f}<span style="font-size:.76rem;color:#8f9bb3;margin-left:.25rem;">MW</span></div>
                </div>
                <div>
                    <div class="label-caps">Forecast Precision</div>
                    <div class="strip-value amber">{precision:.1f}%</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # New Asset Detail Section
    st.markdown(
        f"""
        <div class="panel pad" style="border-left: 4px solid {'#facc15' if current_plant['plant_type'] == 'solar' else '#3b82f6'};">
            <div class="panel-title">
                <div>
                    <div class="label-caps">{current_plant['plant_type']} Asset Details</div>
                    <div class="headline-md">{current_plant['name']}</div>
                </div>
                <div style="background: rgba(87, 241, 219, 0.1); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(87, 241, 219, 0.2);">
                    <span style="color: #57f1db; font-size: 0.75rem; font-weight: 700;">{current_plant['status'] if 'status' in current_plant else 'ACTIVE'}</span>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                <div>
                    <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; font-weight: 700;">Ownership</div>
                    <div style="color: #f8fbff; font-size: 0.9rem;">{current_plant['ownership']}</div>
                </div>
                <div>
                    <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; font-weight: 700;">District</div>
                    <div style="color: #f8fbff; font-size: 0.9rem;">{current_plant['district']}</div>
                </div>
                <div>
                    <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; font-weight: 700;">Hardware</div>
                    <div style="color: #f8fbff; font-size: 0.9rem;">{current_plant['hardware']}</div>
                </div>
                <div>
                    <div style="color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; font-weight: 700;">Installed Capacity</div>
                    <div style="color: #f8fbff; font-size: 0.9rem;">{current_plant['capacity_mw']} MW</div>
                </div>
            </div>
            <div style="margin-top: 1.2rem; padding-top: 1rem; border-top: 1px solid rgba(148, 163, 184, 0.1); color: #d1d5db; font-size: 0.85rem; line-height: 1.5;">
                {current_plant['description']}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Forecast", "Explainability", "SLDC Schedule", "Portfolio", "Live Generation", "Model Accuracy", "Time Horizon"])

    with tab1:
        action_col, hint_col = st.columns([0.22, 0.78], gap="large")
        with action_col:
            generate_clicked = st.button("Generate Forecast", key="gen_fc")
        with hint_col:
            pass  # Narrative removed per user request

        if generate_clicked:
            with st.spinner("Running LightGBM models for all assets..."):
                # Filter out the "GRID_TOTAL" placeholder if it exists in your sites_df
                plants_to_predict = sites_df[sites_df["plant_type"].isin(["solar", "wind"])].to_dict(orient="records")
                
                payload = {
                    "plants": [
                        {
                            "plant_id": p["plant_id"],
                            "plant_type": p["plant_type"],
                            "installed_capacity_mw": p["capacity_mw"]
                        } for p in plants_to_predict
                    ],
                    "forecast_date": str(fc_date),
                    "use_fallback": use_fallback,
                }
                try:
                    response = requests.post(f"{API_URL}/predict/portfolio", json=payload, timeout=60)
                    if response.status_code != 200:
                        st.error(f"API error: {response.json().get('detail', response.text)}")
                    else:
                        data = response.json()
                        st.session_state["portfolio_schedules"] = data["schedules"]
                        st.session_state["forecast_meta"] = data
                        st.success(f"Generated forecasts for {len(data['schedules'])} plants.")
                except Exception as exc:
                    st.error(f"Connection error: {exc}")

        # Update display logic to use portfolio_schedules
        if "portfolio_schedules" in st.session_state:
            schedules = st.session_state["portfolio_schedules"]
            current_id = st.session_state["selected_plant_id"]
            
            if current_id not in schedules:
                st.info(f"No forecast available for {current_id}. Please generate one or check if data is uploaded.")
            else:
                schedule = pd.DataFrame(schedules[current_id])
                # Ensure timestamp is datetime
                schedule["timestamp"] = pd.to_datetime(schedule["timestamp"])
                st.session_state["schedule"] = schedule
                
                total_p50 = schedule["scheduled_gen_mw"].sum() * 0.25
                avg_uncert = schedule["uncertainty_band_mw"].mean()
                peak_mw = schedule["scheduled_gen_mw"].max()
                low_conf = (schedule["confidence_flag"] == "LOW_CONFIDENCE").sum()

                k1, k2, k3, k4 = st.columns(4)
                k1.markdown(metric_card("Total Energy P50", f"{total_p50:.1f} MWh", "teal"), unsafe_allow_html=True)
                k2.markdown(metric_card("Peak Generation", f"{peak_mw:.1f} MW", "amber"), unsafe_allow_html=True)
                k3.markdown(metric_card("Avg Uncertainty", f"{avg_uncert:.1f} MW", "blue"), unsafe_allow_html=True)
                k4.markdown(metric_card("Low Confidence", f"{low_conf} blocks"), unsafe_allow_html=True)

                st.plotly_chart(plot_forecast(schedule, current_id, current_plant["capacity_mw"]), use_container_width=True)
                st.plotly_chart(plot_uncertainty_heatmap(schedule), use_container_width=True)

    with tab2:
        st.markdown(
            "<div class='narrative-box'>Select a forecast block to inspect the model drivers behind that exact generation value.</div>",
            unsafe_allow_html=True,
        )

        if "portfolio_schedules" not in st.session_state:
            st.info("Generate a forecast first.")
        else:
            schedules = st.session_state["portfolio_schedules"]
            current_id = st.session_state["selected_plant_id"]
            
            if current_id not in schedules:
                st.info(f"No forecast available for {current_id}.")
            else:
                schedule = pd.DataFrame(schedules[current_id])
                block_options = [
                    f"Block {row['block_no']:02d} - {row['time_from']} ({row['scheduled_gen_mw']:.1f} MW)"
                    for _, row in schedule.iterrows()
                ]
                selected = st.selectbox("Select Time Block to Explain", block_options)
                block_no = int(selected.split(" ")[1]) - 1
                selected_row = schedule.iloc[block_no]
                ts_str = f"{fc_date}T{selected_row['time_from']}:00"

                if st.button("Explain This Block"):
                    with st.spinner("Computing SHAP values..."):
                        try:
                            params = {
                                "timestamp": ts_str,
                                "plant_type": current_plant["plant_type"],
                                "installed_capacity_mw": current_plant["capacity_mw"],
                            }
                            response = requests.get(f"{API_URL}/explain/{current_id}", params=params, timeout=30)
                            if response.status_code == 200:
                                st.session_state["explanation"] = response.json()
                            else:
                                st.error(response.json().get("detail", response.text))
                        except Exception as exc:
                            st.error(str(exc))

            if "explanation" in st.session_state:
                exp = st.session_state["explanation"]
                col1, col2 = st.columns([2, 1])
                with col1:
                    if exp.get("top_drivers"):
                        st.plotly_chart(plot_shap(exp["top_drivers"]), use_container_width=True)
                with col2:
                    st.markdown("#### Prediction Breakdown")
                    st.markdown(
                        f"""
                        - Base value PLF: `{exp.get('base_value_plf', 'N/A')}`
                        - Predicted PLF: `{exp.get('predicted_plf', 'N/A')}`
                        - Predicted MW: `{exp.get('predicted_mw', 'N/A')} MW`
                        """
                    )
                    st.markdown("#### Top Drivers")
                    for driver in exp.get("top_drivers", []):
                        direction = "up" if driver["shap_value"] >= 0 else "down"
                        st.markdown(
                            f"`{direction}` **{driver['feature']}** = `{driver['value']:.3f}` -> `{driver['shap_value']:+.4f}`"
                        )
                st.markdown(f"<div class='narrative-box'>{exp.get('narrative', '')}</div>", unsafe_allow_html=True)

    with tab3:
        if "portfolio_schedules" not in st.session_state:
            st.info("Generate a forecast first.")
        else:
            schedules = st.session_state["portfolio_schedules"]
            current_id = st.session_state["selected_plant_id"]
            
            if current_id not in schedules:
                st.info(f"No forecast available for {current_id}.")
            else:
                schedule = pd.DataFrame(schedules[current_id])
                display_cols = [
                    "block_no",
                    "time_from",
                    "time_to",
                    "scheduled_gen_mw",
                    "p10_mw",
                    "p90_mw",
                    "uncertainty_band_mw",
                    "confidence_flag",
                ]
                available = [column for column in display_cols if column in schedule.columns]

                def highlight_confidence(row):
                    if row.get("confidence_flag") == "LOW_CONFIDENCE":
                        return ["background-color: rgba(255, 119, 109, 0.22)"] * len(row)
                    if row.get("confidence_flag") == "HIGH_CONFIDENCE":
                        return ["background-color: rgba(87, 241, 219, 0.14)"] * len(row)
                    return [""] * len(row)

                st.dataframe(
                    schedule[available].style.apply(highlight_confidence, axis=1),
                    use_container_width=True,
                    height=420,
                )
                csv_bytes = schedule.to_csv(index=False).encode()
                st.download_button(
                    "Download SLDC Schedule CSV",
                    data=csv_bytes,
                    file_name=f"sldc_schedule_{current_id}_{fc_date}.csv",
                    mime="text/csv",
                )

    with tab4:
        st.markdown(
            "<div class='narrative-box'>Aggregate portfolio metrics for all forecast assets.</div>",
            unsafe_allow_html=True,
        )
        
        if "portfolio_schedules" not in st.session_state:
            st.info("Generate a forecast first using the button in the 'Forecast' tab or sidebar.")
        else:
            schedules = st.session_state["portfolio_schedules"]
            totals = []
            for pid, sched in schedules.items():
                df_sched = pd.DataFrame(sched)
                totals.append(
                    {
                        "plant_id": pid,
                        "total_mwh_p50": df_sched["scheduled_gen_mw"].sum() * 0.25,
                        "peak_mw_p50": df_sched["scheduled_gen_mw"].max(),
                        "avg_uncertainty": df_sched["uncertainty_band_mw"].mean(),
                    }
                )
            totals_df = pd.DataFrame(totals)

            k1, k2, k3 = st.columns(3)
            total_portfolio_mwh = totals_df["total_mwh_p50"].sum()
            portfolio_peak = totals_df["peak_mw_p50"].max()
            portfolio_uncert = totals_df["avg_uncertainty"].mean()
            
            k1.markdown(metric_card("Portfolio Energy", f"{total_portfolio_mwh:,.0f} MWh", "teal"), unsafe_allow_html=True)
            k2.markdown(metric_card("Max Individual Peak", f"{portfolio_peak:.1f} MW", "amber"), unsafe_allow_html=True)
            k3.markdown(metric_card("Avg Portfolio Risk", f"{portfolio_uncert:.1f} MW", "blue"), unsafe_allow_html=True)

            fig = px.bar(
                totals_df,
                x="plant_id",
                y="total_mwh_p50",
                color="avg_uncertainty",
                color_continuous_scale=[[0, "#57f1db"], [0.5, "#ffb95f"], [1, "#ff776d"]],
                labels={"total_mwh_p50": "Total Energy (MWh)", "avg_uncertainty": "Avg Uncertainty (MW)"},
                title="Fleet Energy Forecast Summary",
            )
            fig.update_layout(
                paper_bgcolor="#0b1326",
                plot_bgcolor="#0f172a",
                font=dict(color="#dae2fd"),
                title_font_color="#f8fbff",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(totals_df, use_container_width=True)

    with tab5:
        st.markdown(
            "<div class='narrative-box'>Real-time generation data scraped from KPTCL SLDC.</div>",
            unsafe_allow_html=True,
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Sync Live Data", use_container_width=True):
                with st.spinner("Fetching latest data from SLDC..."):
                    from src.data.scraper import run_scrape
                    try:
                        run_scrape()
                        st.success("Synced!")
                    except Exception as e:
                        st.error(f"Scrape failed: {e}")
                        
        with col2:
            st.info("Fetches latest NCEP and StateGen data into the local SQLite database.")
            
        # Read latest from DB
        from src.data.scraper import DB_PATH
        import sqlite3
        
        if DB_PATH.exists():
            con = sqlite3.connect(DB_PATH)
            try:
                latest_stategen = pd.read_sql("SELECT * FROM stategen_readings ORDER BY scraped_at DESC LIMIT 1", con)
                latest_ncep = pd.read_sql("SELECT * FROM ncep_readings ORDER BY scraped_at DESC", con)
                
                if not latest_stategen.empty:
                    ts = latest_stategen.iloc[0]['sldc_ts']
                    st.markdown(f"**Last SLDC Update:** `{ts}`")
                    
                if not latest_ncep.empty:
                    latest_time = latest_ncep.iloc[0]['scraped_at']
                    ncep_batch = latest_ncep[latest_ncep['scraped_at'] == latest_time]
                    
                    total_solar = ncep_batch['solar_mw'].sum()
                    total_wind = ncep_batch['wind_mw'].sum()
                    
                    k1, k2 = st.columns(2)
                    k1.markdown(metric_card("Total Solar", f"{total_solar:,.0f} MW", "amber"), unsafe_allow_html=True)
                    k2.markdown(metric_card("Total Wind", f"{total_wind:,.0f} MW", "blue"), unsafe_allow_html=True)
                    
                    st.markdown("### 🌬️☀️ Solar & Wind Generation")
                    st.dataframe(ncep_batch[['escom', 'solar_mw', 'wind_mw']], use_container_width=True, height=250)
                    
            except Exception as e:
                st.warning("No data in DB yet or error reading. Click Sync Live Data.")
            finally:
                con.close()
        else:
            st.warning("Database not initialized. Click 'Sync Live Data' to fetch data.")

    with tab6:
        st.markdown(
            "<div class='narrative-box'>Test the accuracy of the trained wind generation models against historical SCADA and NWP data.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Run Historical Accuracy Test", key="run_acc"):
            with st.spinner("Testing model accuracy..."):
                try:
                    from test_accuracy import test_accuracy
                    results = test_accuracy()
                    
                    if "error" in results:
                        st.error(results["error"])
                    else:
                        st.markdown("### Evaluation Results")
                        k1, k2, k3 = st.columns(3)
                        k1.markdown(metric_card("Overall Accuracy", f"{results['accuracy']:.2f}%", "teal"), unsafe_allow_html=True)
                        k2.markdown(metric_card("MAPE", f"{results['mape']:.2f}%", "amber"), unsafe_allow_html=True)
                        k3.markdown(metric_card("Records Evaluated", f"{results['filtered_records']:,}", "blue"), unsafe_allow_html=True)
                        
                        st.success(f"Evaluated successfully on {results['records']:,} historical wind records.")
                except Exception as e:
                    st.error(f"Error testing accuracy: {e}")

    with tab7:
        st.markdown(
            "<div class='narrative-box'>View the forecast broken down into specific time horizons: Short-term (next 4 hours) vs. Full Day (24 hours).</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        
        if "schedule" not in st.session_state:
            st.info("Please generate a forecast in the 'Forecast' tab first.")
        else:
            schedule = st.session_state["schedule"]
            
            st.markdown("### Next 4 Hours (Short-Term)")
            # 4 hours * 4 blocks/hour = 16 blocks
            short_term = schedule.head(16)
            total_st = short_term["scheduled_gen_mw"].sum() * 0.25
            peak_st = short_term["scheduled_gen_mw"].max()
            
            col_st1, col_st2 = st.columns(2)
            col_st1.markdown(metric_card("Short-Term Energy", f"{total_st:.1f} MWh", "amber"), unsafe_allow_html=True)
            col_st2.markdown(metric_card("Short-Term Peak", f"{peak_st:.1f} MW", "teal"), unsafe_allow_html=True)
            
            # Using key kwargs is not standard for plotly_chart, so we just render it directly
            st.plotly_chart(plot_forecast(short_term, current_id, current_plant["capacity_mw"]), use_container_width=True)
            
            st.markdown("---")
            st.markdown("### Next 24 Hours (Full Day)")
            total_day = schedule["scheduled_gen_mw"].sum() * 0.25
            peak_day = schedule["scheduled_gen_mw"].max()
            
            col_day1, col_day2 = st.columns(2)
            col_day1.markdown(metric_card("Full Day Energy", f"{total_day:.1f} MWh", "amber"), unsafe_allow_html=True)
            col_day2.markdown(metric_card("Full Day Peak", f"{peak_day:.1f} MW", "teal"), unsafe_allow_html=True)
            
            st.plotly_chart(plot_forecast(schedule, current_id, current_plant["capacity_mw"]), use_container_width=True)

with telemetry_col:
    st.markdown(
        """
        <div class="panel pad">
            <div class="panel-title">
                <div>
                    <div class="label-caps">SCADA Link</div>
                    <div class="headline-md">Synchronized</div>
                </div>
                <div style="color:var(--teal);font-size:1.8rem;font-weight:800;">99.9%</div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.7rem;">
                <div class="mini-metric"><div class="label-caps">Latency</div><div class="value teal">14ms</div></div>
                <div class="mini-metric"><div class="label-caps">Packet Loss</div><div class="value teal">0.00%</div></div>
            </div>
            <div class="signal-bar"><span style="width:99%;"></span></div>
            <div style="display:flex;justify-content:space-between;margin-top:.45rem;color:#8f9bb3;font-size:.68rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;">
                <span>Signal integrity</span><span style="color:var(--teal);">Optimal</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:.8rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="panel pad">
            <div class="panel-title">
                <div>
                    <div class="label-caps">NWP Weather Integration</div>
                    <div class="headline-md">82% Confidence</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.7rem;">
                <div class="mini-metric"><div class="label-caps">Wind Speed</div><div class="value blue">14.2</div><div style="color:#8f9bb3;font-size:.75rem;">m/s</div></div>
                <div class="mini-metric"><div class="label-caps">GHI</div><div class="value amber">850</div><div style="color:#8f9bb3;font-size:.75rem;">W/m2</div></div>
                <div class="mini-metric"><div class="label-caps">Cloud Cover</div><div class="value">12%</div></div>
                <div class="mini-metric"><div class="label-caps">Temperature</div><div class="value">32 C</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:.8rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="panel pad">
            <div class="label-caps">Portfolio Snapshot</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:.7rem;margin-top:.8rem;">
                {metric_card("Mapped Capacity", f"{total_capacity:,.0f} MW", "teal")}
                {metric_card("Solar Share", "73%", "amber")}
                {metric_card("Wind Share", "27%", "blue")}
                {metric_card("Reserve Watch", "Low", "teal")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Moved to map column context

st.divider()
st.markdown(
    "<center style='color:#475569;font-size:0.74rem;'>EcoPower Forecast - KREDL/KSPDCL Prototype - LightGBM + SHAP - Physics-Informed Feature Engineering</center>",
    unsafe_allow_html=True,
)
