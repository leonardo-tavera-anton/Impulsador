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
    .stTabs [data-baseweb="tab-list"] { 
        gap: 15px; 
        background-color: #0d1117; 
        padding: 10px; 
        border-radius: 10px; 
    }
    .stTabs [data-baseweb="tab"] { 
        height: 45px; 
        background-color: #161b22; 
        border-radius: 5px; 
        color: white; 
        border: none;
        padding: 0px 20px;
    }
    .stTabs [aria-selected="true"] { 
        background-color: #58a6ff !important; 
        color: black !important; 
        font-weight: bold;
    }
    .stTextInput input {
        background-color: #0d1117;
        color: white;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CARGA DE DATOS CENTRALIZADA (PAGINACIÓN PARA > 1000 REGISTROS)
@st.cache_data(ttl=300)
def load_data():
    try:
        all_rows = []
        limit = 5000
        offset = 0
        
        while True:
            response = supabase.table("clientes").select("*").range(offset, offset + limit - 1).execute()
            data = response.data
            if not data:
                break
            all_rows.extend(data)
            if len(data) < limit:
                break
            offset += limit
            
        df = pd.DataFrame(all_rows)
        
        if not df.empty:
            df.columns = [str(c).lower().strip() for c in df.columns]
            df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            for col in ['monto', 'cuota', 'deuda']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            if 'historial' not in df.columns:
                df['historial'] = [{} for _ in range(len(df))]
                
        return df
    except Exception as e:
        st.error(f"Error crítico en carga de datos: {e}")
        return pd.DataFrame()

# 3. CONTROL DE ACCESO
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color: #58a6ff; margin-top: 50px;'>🔐 SURA v7.5</h1>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        with st.container(border=True):
            with st.form("login_form"):
                u = st.text_input("Usuario", placeholder="Ingrese su usuario")
                p = st.text_input("Clave", type="password", placeholder="••••••••")
                submit = st.form_submit_button("ENTRAR", use_container_width=True)
                
                if submit:
                    if u == "admin" and p == "admin":
                        st.session_state.auth = True
                        st.session_state.user_sura = "Leonardo Tavera"
                        st.success("Acceso concedido")
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
else:
    head1, head2 = st.columns([4, 1])
    with head1:
        st.markdown(f"### 💎 SURA v7.5 | <span style='color:#58a6ff;'>{st.session_state.user_sura}</span>", unsafe_allow_html=True)
    with head2:
        if st.button("🔄 RECARGAR DATA", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    df_main = load_data()

    # 4. NAVEGACIÓN POR TABS
    tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📋 GESTIÓN", "📤 IMPORTACIÓN"])

    with tab1:
        if not df_main.empty:
            dashboard.render(df_main)
        else:
            st.info("No hay datos para mostrar en el Dashboard.")

    with tab2:
        if not df_main.empty:
            gestion.render(df_main)
        else:
            st.warning("La tabla está vacía. Importe un archivo para comenzar.")

    with tab3:
        importacion.render()