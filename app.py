import streamlit as st
from utils import ui_components, data_engine
from modules import dashboard, gestion, auditoria, reportes

# Configuración Inicial
st.set_page_config(page_title="SURA CORE v7.0", layout="wide", page_icon="🏢")
ui_components.inject_sura_css()

if 'custom_estados' not in st.session_state:
    st.session_state.custom_estados = ["aplica", "desembolso", "deudor", "sin ahorros", "cesante"]

# Carga de Datos
df_core = data_engine.load_sura_core_db(2026)

# Sidebar
with st.sidebar:
    st.markdown("## SURA v7.0\n**Leonardo Tavera**")
    menu = st.radio("Navegación", ["📊 Dashboard", "📋 Gestión", "🔍 Auditoría", "📥 Reportes"])
    if st.button("🔄 Refrescar Datos"):
        st.cache_data.clear()
        st.rerun()

# Router
if menu == "📊 Dashboard":
    # Aquí llamarías a dashboard.render(df_core) una vez crees ese archivo
    st.info("Módulo Dashboard seleccionado")
elif menu == "📋 Gestión":
    gestion.render(df_core)
elif menu == "🔍 Auditoría":
    # Aquí llamarías a auditoria.render(df_core)
    st.info("Módulo Auditoría seleccionado")
elif menu == "📥 Reportes":
    # Aquí llamarías a reportes.render(df_core)
    st.info("Módulo Reportes seleccionado")