import streamlit as st
import pandas as pd
from utils.data_engine import supabase 
from modules import dashboard, gestion, importacion

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(
    page_title="SURA v7.5 - Leonardo Tavera",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos Globales para ocultar Sidebar y mejorar Tabs
st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .block-container { padding-top: 1rem !important; }
    header { visibility: hidden !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 15px; background-color: #0d1117; padding: 10px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { height: 45px; background-color: #161b22; border-radius: 5px; color: white; }
    .stTabs [aria-selected="true"] { background-color: #58a6ff !important; color: black !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CARGA DE DATOS CENTRALIZADA
@st.cache_data(ttl=300)
def load_data():
    try:
        response = supabase.table("clientes").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            # Forzamos minúsculas para evitar KeyError
            df.columns = [str(c).lower().strip() for c in df.columns]
            df['dni'] = df['dni'].astype(str)
            for col in ['monto', 'cuota', 'deuda']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        return df
    except Exception:
        return pd.DataFrame()

# 3. CONTROL DE ACCESO
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center;'>🔐 SURA v7.5</h1>", unsafe_allow_html=True)
    with st.container(border=True):
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR", width="stretch") if False else st.button("ENTRAR", width="stretch"):
                if u == "admin" and p == "chimbote2026":
                    st.session_state.auth = True
                    st.session_state.user_sura = "Leonardo Tavera"
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
else:
    # Header de Usuario
    head1, head2 = st.columns([4, 1])
    with head1:
        st.subheader(f"💎 SURA v7.5 | {st.session_state.user_sura}")
    with head2:
        if st.button("🔄 RECARGAR", width="stretch"):
            st.cache_data.clear()
            st.rerun()

    df_main = load_data()

    # 4. NAVEGACIÓN POR TABS
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📋 GESTIÓN", "📤 IMPORTACIÓN"])

    with tab1:
        if not df_main.empty:
            dashboard.render(df_main)
        else:
            st.info("Cargando dashboard o tabla vacía...")

    with tab2:
        if not df_main.empty:
            gestion.render(df_main)
        else:
            st.warning("No hay datos para gestionar actualmente.")

    with tab3:
        # La importación siempre está disponible
        importacion.render()