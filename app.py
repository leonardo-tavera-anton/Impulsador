import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime
from utils import ui_components, data_engine
from modules import dashboard, gestion, auditoria, reportes, importacion

# 1. CONFIGURACIÓN MAESTRA
st.set_page_config(
    page_title="SURA Digital v7.5", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. TRUCO DE FUERZA BRUTA: JS PARA REABRIR SIEMPRE
# Este pequeño script busca el botón de "abrir" y le hace clic automáticamente si el sidebar está cerrado.
components.html(
    """
    <script>
    var container = window.parent.document.getElementById("root");
    var button = window.parent.document.querySelector('.st-emotion-cache-6q9sum.ef3ps4l2');
    if (button) {
        button.click();
    }
    </script>
    """,
    height=0,
)

# 3. CSS PARA FIJAR LA ESTRUCTURA Y QUITAR ESPACIOS
st.markdown("""
    <style>
    /* Bloqueamos el Sidebar para que sea estático y profesional */
    [data-testid="stSidebar"] {
        min-width: 300px !important;
        max-width: 300px !important;
        border-right: 1px solid #30363d !important;
    }

    /* OCULTAMOS LOS BOTONES DE CERRAR/ABRIR PARA QUE NO LO VUELVAS A CONTRAER */
    button[data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    
    /* ELIMINAR EL HUECO NEGRO DE ARRIBA */
    .block-container { 
        padding-top: 0rem !important; 
        margin-top: -35px !important; 
    }

    /* ESTÉTICA DARK PREMIUM */
    header, [data-testid="stDecoration"], footer {
        display: none !important;
    }
    
    [data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

# 4. CARGA DE DATOS (6,952 REGISTROS)
@st.cache_data(ttl=3600)
def get_data():
    return data_engine.load_sura_core_db(2026)

df_core = get_data()

# 5. SIDEBAR SIEMPRE VISIBLE
with st.sidebar:
    st.markdown("""
        <div style='background: #1f6feb; padding: 20px; border-radius: 10px; text-align: center;'>
            <h1 style='color:white; margin:0; font-size: 1.5rem;'>SURA v7.5</h1>
            <p style='color: white; opacity: 0.8; margin:0;'>Nuevo Chimbote 2026</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    menu = st.radio(
        "SISTEMA CENTRAL", 
        ["📊 Dashboard General", "📋 Gestión de Padrones", "🔍 Auditoría de Calidad", "📥 Centro de Reportes", "📤 Importación Masiva"],
        index=1
    )
    st.divider()
    st.sidebar.info(f"📦 Padrón: {len(df_core):,} registros")

# 6. ROUTER
if not df_core.empty:
    if menu == "📊 Dashboard General":
        dashboard.render(df_core)
    elif menu == "📋 Gestión de Padrones":
        gestion.render(df_core)
    elif menu == "🔍 Auditoría de Calidad":
        auditoria.render(df_core)
    elif menu == "📥 Centro de Reportes":
        reportes.render(df_core)
    elif menu == "📤 Importación Masiva":
        importacion.render()