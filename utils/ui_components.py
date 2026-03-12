import streamlit as st

def inject_sura_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
        :root {
            --sura-green: #2ea043; --sura-bright-green: #3fb950;
            --bg-dark: #0d1117; --bg-card: #161b22;
            --border-ui: #30363d; --text-muted: #8b949e;
        }
        .stApp { background-color: var(--bg-dark); font-family: 'Inter', sans-serif; }
        .sura-title {
            font-weight: 900; background: linear-gradient(90deg, #ffffff, var(--sura-bright-green));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-size: 2.5rem; letter-spacing: -1px; margin-bottom: 20px;
        }
        .metric-card {
            background: var(--bg-card); border: 1px solid var(--border-ui);
            border-radius: 12px; padding: 15px; flex: 1; min-width: 200px;
            transition: transform 0.2s;
        }
        .metric-card:hover { transform: translateY(-2px); border-color: var(--sura-green); }
        .metric-label { color: var(--text-muted); font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
        .metric-value { font-size: 1.8rem; font-weight: 800; color: white; margin: 5px 0; }
        .sura-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; display: inline-block; }
        .badge-up { background: rgba(63, 185, 80, 0.15); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.3); }
        .badge-down { background: rgba(255, 123, 114, 0.15); color: #ff7b72; border: 1px solid rgba(255, 123, 114, 0.3); }
        </style>
    """, unsafe_allow_html=True)

def compact_currency(value):
    if value >= 1_000_000: return f"S/ {value/1_000_000:.2f}M"
    elif value >= 1_000: return f"S/ {value/1_000:.1f}k"
    return f"S/ {value:,.0f}"

def draw_custom_metric(label, value, delta, is_positive=True):
    badge_class = "badge-up" if is_positive else "badge-down"
    arrow = "↑" if is_positive else "↓"
    return f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="sura-badge {badge_class}">{arrow} {delta}</div>
        </div>
    """

def apply_plotly_theme(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(22, 27, 34, 0.5)',
        font_color="#c9d1d9", margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig