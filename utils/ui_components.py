import streamlit as st

def inject_sura_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap');
        :root { --sura-green: #2ea043; --bg-dark: #0d1117; --bg-card: #161b22; --border-ui: #30363d; }
        .stApp { background-color: var(--bg-dark); font-family: 'Plus Jakarta Sans', sans-serif; }
        .sura-title { font-weight: 800; background: linear-gradient(120deg, #ffffff, var(--sura-green));
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.8rem; }
        .metric-container { display: flex; gap: 20px; flex-wrap: wrap; margin: 25px 0; }
        .metric-card { background: var(--bg-card); border: 1px solid var(--border-ui);
            border-radius: 16px; padding: 24px; flex: 1; min-width: 240px; }
        .metric-label { color: #8b949e; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; }
        .metric-value { font-size: 2.2rem; font-weight: 800; color: white; margin: 10px 0; }
        .sura-badge { padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; }
        .badge-up { background: rgba(46, 160, 67, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.2); }
        .badge-down { background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.2); }
        </style>
    """, unsafe_allow_html=True)

def compact_currency(val):
    if val >= 1_000_000: return f"S/ {val/1_000_000:.2f}M"
    elif val >= 1_000: return f"S/ {val/1_000:.1f}k"
    return f"S/ {val:,.2f}"

def draw_custom_metric(label, value, delta, is_positive=True):
    b_class = "badge-up" if is_positive else "badge-down"
    return f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="sura-badge {b_class}">{delta}</div></div>'

def apply_plotly_theme(fig):
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#c9d1d9")
    return fig