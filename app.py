import streamlit as st
import pandas as pd
from utils.data_engine import load_sura_core_db

# 1. CONFIGURACIÓN (Mantenemos tu estilo pero optimizamos el layout)
st.set_page_config(
    page_title="SURA v7.5 - Leonardo Tavera",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos CSS (Tu diseño intacto)
st.markdown("""
    <style>
    [data-testid="stSidebarNavigation"] { display: none; }
    .block-container { padding-top: 1rem !important; }
    header { visibility: hidden !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    </style>
""", unsafe_allow_html=True)

# 2. SISTEMA DE LOGIN (Optimizado)
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color: #58a6ff;'>🔐 SURA v7.5</h1>", unsafe_allow_html=True)
    _, col_l2, _ = st.columns([1, 1.5, 1])
    with col_l2:
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("ENTRAR", use_container_width=True):
                if u == "admin" and p == "admin": # Cambiar por secrets en producción
                    st.session_state.auth = True
                    st.rerun()
                else:
                    st.error("Error de acceso")
else:
    # 3. CARGA DE DATOS (Usamos la función del Engine)
    # Al estar cacheada, no se descarga de nuevo al cambiar de tab
    df_main = load_sura_core_db()

    # 4. HEADER Y RECARGA
    c1, c2 = st.columns([4, 1])
    c1.subheader(f"💎 SURA v7.5 | Bienvenido, Leonardo")
    if c2.button("🔄 RECARGAR TODO", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    # 5. TABS CON IMPORTACIÓN "LAZY" (Solo carga el código necesario)
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📋 GESTIÓN", "📤 IMPORTACIÓN"])

    with tab1:
        from modules import dashboard
        dashboard.render(df_main)

    with tab2:
        from modules import gestion
        # Si la data es muy pesada, gestion.render se encarga del head(100)
        gestion.render(df_main)

    with tab3:
        from modules import importacion
        importacion.render()