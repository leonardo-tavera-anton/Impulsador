import streamlit as st
from utils import ui_components, data_engine
from modules import dashboard, gestion, auditoria, reportes, importacion

# Configuración Maestra
st.set_page_config(page_title="SURA Digital v7.5", layout="wide", initial_sidebar_state="expanded")
ui_components.inject_sura_css()

# Manejo de Sesión
if 'user' not in st.session_state: st.session_state.user = "Leonardo Tavera"
if 'custom_estados' not in st.session_state:
    st.session_state.custom_estados = ["aplica", "desembolso", "deudor", "sin ahorros", "otro filtro", "cesante"]

# Carga de datos centralizada
try:
    df_core = data_engine.load_sura_core_db(2026)
except Exception as e:
    st.error(f"Fallo crítico en conexión: {e}")
    df_core = pd.DataFrame()

# Sidebar Pro
with st.sidebar:
    st.markdown(f"<h1 style='color:white'>SURA <span style='color:#2ea043'>v7.5</span></h1>", unsafe_allow_html=True)
    st.caption(f"👤 {st.session_state.user} | 📍 Nuevo Chimbote")
    st.divider()
    
    menu = st.radio("SISTEMA CENTRAL", [
        "📊 Dashboard General", 
        "📋 Gestión de Padrones", 
        "🔍 Auditoría de Calidad", 
        "📥 Centro de Reportes", 
        "📤 Importación Masiva"
    ], label_visibility="collapsed")
    
    st.divider()
    if st.button("🔄 Refrescar Base de Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Router de Módulos
if not df_core.empty:
    if menu == "📊 Dashboard General": dashboard.render(df_core)
    elif menu == "📋 Gestión de Padrones": gestion.render(df_core)
    elif menu == "🔍 Auditoría de Calidad": auditoria.render(df_core)
    elif menu == "📥 Centro de Reportes": reportes.render(df_core)
    elif menu == "📤 Importación Masiva": importacion.render()
else:
    st.warning("Esperando conexión con el servidor Supabase...")

# Footer estático
st.markdown("<br><hr><center><small>© 2026 SURA Digital - Desarrollado por Leonardo Tavera</small></center>", unsafe_allow_html=True)