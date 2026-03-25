import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from utils import data_engine
from modules import dashboard, gestion, importacion

# 1. CONFIGURACIÓN
st.set_page_config(page_title="SURA v7.5", layout="wide", initial_sidebar_state="expanded")

# 2. INYECCIÓN DE ESTILO AVANZADO (SIDEBAR CUSTOM)
st.markdown("""
    <style>
    /* Reset de márgenes y ocultar basura de Streamlit */
    .block-container { padding-top: 0rem !important; margin-top: -60px !important; }
    header, footer { visibility: hidden !important; }
    
    /* Estilizado del Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%) !important;
        border-right: 1px solid #30363d !important;
        min-width: 320px !important;
    }
    
    /* Título y Subtítulo SURA */
    .sidebar-title {
        color: #58a6ff;
        font-size: 28px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
        letter-spacing: 2px;
    }
    .sidebar-subtitle {
        color: #8b949e;
        font-size: 10px;
        text-align: center;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Estilo para los botones del Radio Menu */
    [data-testid="stSidebar"] .stRadio > label { display: none; } /* Oculta el label 'MENÚ' */
    [data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 10px;
        padding: 10px 0px;
    }
    
    /* Usuario Card */
    .user-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. RESCATE Y CONTROL DEL SIDEBAR
components.html("""
    <script>
    function forceSidebar() {
        const btn = window.parent.document.querySelector('button[aria-label="Expand sidebar"]');
        if (btn) btn.click();
    }
    setTimeout(forceSidebar, 300);
    window.parent.hardResetSura = function() {
        window.parent.localStorage.clear();
        window.parent.location.reload();
    }
    </script>
""", height=0)

# 4. CARGA DE DATOS
@st.cache_data(ttl=600)
def load_data():
    df = data_engine.load_sura_core_db(2026)
    rename_dict = {
        'whatsapp': 'Numero', 'WhatsApp': 'Numero', 'celular': 'Numero',
        'cap.': 'Monto', 'CAP': 'Monto', 'cap': 'Monto', 'monto': 'Monto'
    }
    return df.rename(columns=rename_dict)

df_core = load_data()

# 5. SIDEBAR PROFESIONAL
with st.sidebar:
    # Encabezado SURA
    st.markdown("<div class='sidebar-title'>SURA v7.5</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-subtitle'>Sistema Unificado de Registro Administrativo</div>", unsafe_allow_html=True)
    
    # Card de Usuario
    st.markdown(f"""
        <div class='user-card'>
            <span style='color: #8b949e; font-size: 12px;'>Operador Activo</span><br>
            <span style='color: white; font-weight: 600;'>{st.session_state.get('user_name', 'Leonardo Tavera')}</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Menú de Navegación
    menu = st.radio(
        "Navegación",
        ["📊 Dashboard", "📋 Gestión", "📤 Importación"],
        index=1,
        help="Selecciona un módulo de trabajo"
    )
    
    st.spacer = st.empty() # Espacio flexible
    st.divider()
    
    # Botón de mantenimiento
    if st.button("🚨 REPARAR INTERFAZ", use_container_width=True):
        components.html("<script>window.parent.hardResetSura();</script>", height=0)
    
    st.markdown("<p style='text-align:center; color:#444; font-size:10px;'>Muni Nuevo Chimbote &copy; 2026</p>", unsafe_allow_html=True)

# 6. ROUTER DE MÓDULOS
if not df_core.empty:
    if menu == "📊 Dashboard": dashboard.render(df_core)
    elif menu == "📋 Gestión": gestion.render(df_core)
    elif menu == "📤 Importación": importacion.render()