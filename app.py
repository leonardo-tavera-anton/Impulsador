import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA CORE SURA
# ==========================================
st.set_page_config(
    page_title="SURA - Sistema Unificado de Registro de Activos",
    layout="wide",
    page_icon="🏢",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. CSS "MALDITO" V5.1 - SURA ENTERPRISE
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;700;900&display=swap');
    
    :root {
        --sura-green: #2ea043;
        --sura-dark-green: #238636;
        --bg-main: #0d1117;
        --bg-card: #161b22;
        --border-ui: #30363d;
        --text-bright: #f0f6fc;
    }

    .main { background-color: var(--bg-main); font-family: 'Inter', sans-serif; }

    .sura-logo-text {
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        background: linear-gradient(90deg, #ffffff, var(--sura-green));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        letter-spacing: -2px;
        margin-bottom: -10px;
    }

    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-ui);
        border-radius: 20px;
        padding: 25px !important;
        transition: 0.3s;
    }
    div[data-testid="stMetric"]:hover {
        border-color: var(--sura-green);
        box-shadow: 0 0 25px rgba(46, 160, 67, 0.2);
    }

    .sura-panel {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border: 1px solid var(--sura-green);
        border-radius: 24px;
        padding: 40px;
        margin-top: 20px;
        box-shadow: 0 25px 50px rgba(0,0,0,0.6);
    }

    .stButton>button {
        width: 100%; border-radius: 12px;
        background: linear-gradient(135deg, var(--sura-dark-green) 0%, var(--sura-green) 100%);
        color: white; border: none; font-weight: 800; height: 50px;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 1.5px; transition: 0.4s;
    }
    .stButton>button:hover {
        filter: brightness(1.2); transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(46, 160, 67, 0.4);
    }

    .consulta-card {
        background: #1c2128;
        border-left: 6px solid var(--sura-green);
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }

    [data-testid="stSidebar"] { background-color: #0b0e14; border-right: 1px solid var(--border-ui); }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. MOTOR DE DATOS (SURA ENGINE V5.1)
# ==========================================
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal, resolution=merge-duplicates"
}

@st.cache_data(ttl=60)
def load_sura_db():
    all_data = []
    # Manejo de paginación para los 6,952 registros
    for offset in range(0, 8000, 1000):
        try:
            r = requests.get(f"{URL}/rest/v1/clientes?select=*&order=nombre&offset={offset}&limit=1000", headers=HEADERS)
            batch = r.json()
            if not batch: break
            all_data.extend(batch)
        except: break
    
    df = pd.DataFrame(all_data)
    if not df.empty:
        # Normalización de datos
        for c in ['monto', 'cuota', 'deuda']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
        
        # Lógica de sincronización con el mes actual (Marzo 2026)
        def sync_check(h, mes, anio='2026'):
            try: return "✅" if h.get(anio, {}).get(mes) == 1 else "❌"
            except: return "❌"
        
        df['ENE'] = df['historial'].apply(lambda x: sync_check(x, 'enero'))
        df['FEB'] = df['historial'].apply(lambda x: sync_check(x, 'febrero'))
        df['MAR'] = df['historial'].apply(lambda x: sync_check(x, 'marzo'))
        
    return df

@st.cache_data
def get_config_estados():
    if 'custom_estados' not in st.session_state:
        st.session_state.custom_estados = ["aplica", "desembolso", "deudor", "no ahorro", "otro filtro", "multired vencida"]
    return st.session_state.custom_estados

# ==========================================
# 4. ESTRUCTURA DE NAVEGACIÓN
# ==========================================
df_main = load_sura_db()
estados_disponibles = get_config_estados()
mes_actual_nombre = "Marzo" # Sincronizado a Marzo 2026

with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🏢</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #f0f6fc;'>SURA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 0.8em; color: #8b949e;'>Sistema Unificado de Registro de Activos</p>", unsafe_allow_html=True)
    st.divider()
    
    st.info(f"**Operador:** Leonardo")
    
    menu = st.radio("MENÚ PRINCIPAL", [
        "📈 Dashboard Global", 
        "📋 Gestión de Padrones", 
        "🔍 Consulta de Activos", 
        "⚙️ Configuraciones SURA",
        "📥 Importación Masiva"
    ])
    
    st.divider()
    if st.button("🚀 Sincronizar Sistema"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# MÓDULO 1: DASHBOARD GLOBAL (REAL-TIME)
# ==========================================
if menu == "📈 Dashboard Global":
    st.markdown("<h1 class='sura-logo-text'>DASHBOARD GLOBAL</h1>", unsafe_allow_html=True)
    
    if not df_main.empty:
        c1, c2, c3, c4 = st.columns(4)
        # Sincronizado con Supabase: 6952 registros
        c1.metric("Activos Totales", f"{len(df_main):,}")
        c2.metric("Valor del Sistema", f"S/ {df_main['monto'].sum():,.2f}")
        c3.metric("Deuda Acumulada", f"S/ {df_main['deuda'].sum():,.2f}")
        # Sincronizado con Marzo
        c4.metric(f"Efectividad {mes_actual_nombre}", f"{len(df_main[df_main['MAR'] == '✅']):,}")
        
        st.divider()
        
        col_graf_1, col_graf_2 = st.columns([2, 1])
        with col_graf_1:
            st.subheader("📊 Distribución por Estado de Activo")
            conteo = df_main['estado'].value_counts().reset_index()
            fig = px.bar(conteo, x='estado', y='count', color='estado', 
                         color_discrete_sequence=px.colors.qualitative.G10)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#fff", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_graf_2:
            st.subheader("📌 Resumen Operativo")
            st.dataframe(df_main['estado'].value_counts(), use_container_width=True)

# ==========================================
# MÓDULO 2: GESTIÓN DE PADRONES
# ==========================================
elif menu == "📋 Gestión de Padrones":
    st.markdown("<h1 class='sura-logo-text'>GESTIÓN DE PADRONES</h1>", unsafe_allow_html=True)
    
    if not df_main.empty:
        search = st.text_input("🔍 Filtro por Titular o DNI:", placeholder="Escriba para buscar entre los 6,952 registros...")
        
        df_f = df_main.copy()
        if search:
            df_f = df_main[df_main['nombre'].str.contains(search, case=False) | df_main['dni'].astype(str).str.contains(search)]

        st.markdown("### Seleccione un registro para editar")
        # Tabla con 2 meses de guía como pediste
        table_sel = st.dataframe(
            df_f[["dni", "nombre", "monto", "cuota", "deuda", "estado", "FEB", "MAR"]],
            column_config={
                "dni": "DNI/ID", "nombre": st.column_config.TextColumn("TITULAR", width="large"),
                "monto": st.column_config.NumberColumn("MONTO", format="S/ %.2f"),
                "FEB": st.column_config.TextColumn("FEB", width="small"),
                "MAR": st.column_config.TextColumn("MAR", width="small"),
            },
            hide_index=True, use_container_width=True, on_select="rerun", selection_mode="single-row", key="table_v5_1"
        )

        if len(table_sel.selection.rows) > 0:
            idx = table_sel.selection.rows[0]
            data_row = df_f.iloc[idx]
            
            full_data = df_main[df_main["dni"] == data_row["dni"]].iloc[0]
            hist_master = full_data.get('historial', {})
            if not isinstance(hist_master, dict): hist_master = {}

            st.markdown("<div class='sura-panel'>", unsafe_allow_html=True)
            st.subheader(f"🛠️ Ficha de Gestión: {data_row['nombre']}")
            
            with st.form("form_sura_v5_1"):
                c_a, c_b, c_c = st.columns(3)
                with c_a:
                    u_nom = st.text_input("Titular del Activo", value=data_row['nombre'])
                    u_est = st.selectbox("Estado Operativo", estados_disponibles, 
                                       index=estados_disponibles.index(data_row['estado']) if data_row['estado'] in estados_disponibles else 0)
                with c_b:
                    u_mon = st.number_input("Monto Asignado", value=float(data_row['monto']))
                    u_cuo = st.number_input("Cuota", value=float(data_row['cuota']))
                with c_c:
                    u_deu = st.number_input("Deuda", value=float(data_row['deuda']))
                    u_yr = st.selectbox("Año Fiscal (2026 - 2060)", [str(y) for y in range(2026, 2061)])

                st.divider()
                st.markdown("#### 📅 Registro Mensual Completo")
                meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
                h_yr = hist_master.get(u_yr, {})
                
                m_cols = st.columns(4)
                new_checks = {}
                for i, m in enumerate(meses):
                    with m_cols[i % 4]:
                        val = st.checkbox(m.capitalize(), value=h_yr.get(m) == 1, key=f"chk_{m}")
                        new_checks[m] = 1 if val else 0
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("💾 GUARDAR CAMBIOS (TABLA + MESES)"):
                    with st.spinner("Actualizando Supabase..."):
                        hist_final = hist_master.copy()
                        hist_final[u_yr] = new_checks
                        hist_final["ultimo_por"] = "Leonardo"
                        hist_final["fecha_act"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        payload = {
                            "dni": str(data_row['dni']), "nombre": u_nom.upper(),
                            "monto": u_mon, "cuota": u_cuo, "deuda": u_deu,
                            "estado": u_est, "historial": hist_final
                        }
                        
                        r = requests.post(f"{URL}/rest/v1/clientes", headers=HEADERS, json=[payload])
                        if r.status_code in [200, 201, 204]:
                            st.success("✅ Registro SURA actualizado.")
                            st.cache_data.clear()
                            st.rerun()

# ==========================================
# MÓDULO 3: CONSULTA DE ACTIVOS (PRO)
# ==========================================
elif menu == "🔍 Consulta de Activos":
    st.markdown("<h1 class='sura-logo-text'>CONSULTA TÉCNICA</h1>", unsafe_allow_html=True)
    dni_q = st.text_input("Ingrese DNI para búsqueda profunda:")
    
    if dni_q:
        res = df_main[df_main['dni'].astype(str) == dni_q]
        if not res.empty:
            item = res.iloc[0]
            st.markdown(f"""
                <div class="consulta-card">
                    <h2 style="color:#2ea043; margin-top:0; border-bottom:1px solid #30363d; padding-bottom:10px;">{item['nombre']}</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 30px; margin-top:20px;">
                        <div>
                            <p style="color:#8b949e; font-size:0.9em; margin-bottom:5px;">IDENTIFICADOR</p>
                            <p style="font-size:1.4em; font-weight:800; font-family:'JetBrains Mono';">{item['dni']}</p>
                        </div>
                        <div>
                            <p style="color:#8b949e; font-size:0.9em; margin-bottom:5px;">ESTADO OPERATIVO</p>
                            <p style="font-size:1.4em; font-weight:800; color:#2ea043;">{str(item['estado']).upper()}</p>
                        </div>
                        <div>
                            <p style="color:#8b949e; font-size:0.9em; margin-bottom:5px;">MONTO DE ACTIVO</p>
                            <p style="font-size:1.4em; font-weight:800;">S/ {item['monto']:,.2f}</p>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("📂 Historial de Procedimientos (Vista Técnica)"):
                st.write(item['historial'])
        else:
            st.error("❌ Registro no localizado en la red SURA.")

# ==========================================
# MÓDULO 4: CONFIGURACIONES SURA
# ==========================================
elif menu == "⚙️ Configuraciones SURA":
    st.markdown("<h1 class='sura-logo-text'>CONFIGURACIONES</h1>", unsafe_allow_html=True)
    
    st.subheader("🛠️ Catálogo de Estados")
    st.write("Personaliza los estados disponibles para la clasificación de activos.")
    
    col_add, col_list = st.columns([1, 1])
    with col_add:
        new_st = st.text_input("Nombre del nuevo Estado:")
        if st.button("➕ Registrar Estado"):
            if new_st and new_st.lower() not in st.session_state.custom_estados:
                st.session_state.custom_estados.append(new_st.lower())
                st.success(f"Estado '{new_st}' integrado.")
                st.rerun()
    
    with col_list:
        st.write("**Lista Maestra de Estados:**")
        for e in st.session_state.custom_estados:
            st.code(e)

# ==========================================
# MÓDULO 5: IMPORTACIÓN
# ==========================================
elif menu == "📥 Importación Masiva":
    st.markdown("<h1 class='sura-logo-text'>IMPORTACIÓN</h1>", unsafe_allow_html=True)
    f = st.file_uploader("Cargar Base de Datos Externa (.xlsx)", type=["xlsx"])
    if f:
        df_new = pd.read_excel(f)
        st.write(f"Pre-visualización de registros: {len(df_new)}")
        st.dataframe(df_new.head())
        if st.button("🚀 INICIAR CARGA MASIVA A SUPABASE"):
            st.info("Procesando registros en lotes de 1000...")