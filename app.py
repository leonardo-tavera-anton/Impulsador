import streamlit as st
import pandas as pd
from utils import ui_components, data_engine
from modules import dashboard, gestion, auditoria, reportes, importacion

# 1. Configuración Maestra
st.set_page_config(
    page_title="SURA Digital v7.5", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Inyectar estilos personalizados
ui_components.inject_sura_css()

# 2. Manejo de Sesión (Estado Global)
if 'user' not in st.session_state: 
    st.session_state.user = "Leonardo Tavera"
if 'custom_estados' not in st.session_state:
    st.session_state.custom_estados = ["aplica", "desembolso", "deudor", "sin ahorros", "otro filtro", "cesante"]

# 3. Carga de datos centralizada
# Si falla o está vacía, devolvemos un DataFrame con estructura pero sin filas
try:
    df_core = data_engine.load_sura_core_db(2026)
except Exception as e:
    st.error(f"Fallo crítico en conexión: {e}")
    df_core = pd.DataFrame(columns=['dni', 'nombre', 'monto', 'deuda', 'estado'])

# 4. Sidebar Pro
with st.sidebar:
    st.markdown(f"<h1 style='color:white'>SURA <span style='color:#2ea043'>v7.5</span></h1>", unsafe_allow_html=True)
    st.caption(f"👤 {st.session_state.user} | 📍 Nuevo Chimbote")
    st.divider()
    
    menu = st.radio(
        "SISTEMA CENTRAL", 
        [
            "📊 Dashboard General", 
            "📋 Gestión de Padrones", 
            "🔍 Auditoría de Calidad", 
            "📥 Centro de Reportes", 
            "📤 Importación Masiva"
        ],
        index=0
    )
    
    st.divider()
    if st.button("🔄 Refrescar Base de Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# 5. Router de Módulos (Lógica Inteligente)
# Caso A: El usuario quiere importar datos (No requiere que la DB tenga filas)
if menu == "📤 Importación Masiva":
    importacion.render()

# Caso B: El usuario quiere ver módulos que requieren información
else:
    if df_core.empty:
        # Aquí mostramos el aviso pero permitimos que el resto de la app viva
        st.warning("📡 Conexión establecida, pero la tabla está vacía.")
        st.info("💡 Por favor, dirígete al módulo **'Importación Masiva'** para cargar el padrón de clientes.")
        
        # Opcional: Mostrar una imagen o placeholder para que no se vea vacío
        st.image("https://via.placeholder.com/800x400.png?text=Esperando+Carga+de+Datos", use_container_width=True)
    else:
        # Si hay datos, cargamos el módulo correspondiente normalmente
        if menu == "📊 Dashboard General":
            dashboard.render(df_core)
        elif menu == "📋 Gestión de Padrones":
            gestion.render(df_core)
        elif menu == "🔍 Auditoría de Calidad":
            auditoria.render(df_core)
        elif menu == "📥 Centro de Reportes":
            reportes.render(df_core)

# 6. Footer estático profesional
st.markdown(
    """
    <br><hr>
    <div style='text-align: center; color: #666;'>
        <small>© 2026 SURA Digital - Sistema de Gestión Municipal<br>
        Desarrollado por <b>Leonardo Tavera</b> en Nuevo Chimbote</small>
    </div>
    """, 
    unsafe_allow_html=True
)