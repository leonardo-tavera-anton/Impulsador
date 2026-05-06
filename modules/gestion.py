import streamlit as st
import pandas as pd
from utils.data_engine import supabase

# --- CONSTANTES DE MESES ---
MESES_NORMALES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
TODAS_LAS_OPCIONES = MESES_NORMALES + [f"🔴 n.{m}" for m in MESES_NORMALES]
MESES_FULL = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def render(df):
    # CSS para estabilidad visual y altura de Excel
    st.markdown("""
        <style>
        [data-testid="stDataEditor"] > div:first-child { height: 750px !important; }
        [data-testid="stBlock"] { opacity: 1 !important; }
        .stDataFrame { width: 100%; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"### 📋 GESTIÓN SURA v7.5 - Padrón Total ({len(df):,})")

    # --- FILTROS ---
    c1, c2 = st.columns([1, 3])
    with c1:
        ano_activo = st.selectbox("📅 Año Fiscal", [str(a) for a in range(2026, 2031)], key="year_sel")
    with c2:
        busqueda = st.text_input("🔍 Buscar en el padrón", placeholder="DNI o Nombre...", key="main_search")

    # --- FILTRADO ---
    if busqueda:
        b = busqueda.lower()
        df_filtered = df[df['nombre'].str.lower().str.contains(b, na=False) | df['dni'].str.contains(b, na=False)].copy()
    else:
        df_filtered = df.copy() # Aquí ves los 47,000 registros

    # --- PROCESAMIENTO DE HISTORIAL ---
    def extraer_meses(h, a):
        if isinstance(h, dict) and a in h:
            return [m[:3] if v == 1 else f"🔴 n.{m[:3]}" for m, v in h[a].items() if v is not None]
        return []

    df_filtered['Historial'] = df_filtered['historial'].apply(lambda x: extraer_meses(x, ano_activo))

    # --- FUNCIÓN DE AUTOGUARDADO (TIPO EXCEL) ---
    def handle_autosave():
        key = f"ed_master_{ano_activo}"
        if key in st.session_state:
            changes = st.session_state[key].get("edited_rows")
            if not changes: return
            
            payload = []
            for row_idx, mods in changes.items():
                # Acceso a la fila original
                row_orig = df_filtered.iloc[int(row_idx)]
                h_total = row_orig['historial']
                
                # Si se modificaron los meses del historial
                if 'Historial' in mods:
                    seleccion = mods['Historial']
                    dic_ano = {}
                    for m_f in MESES_FULL:
                        m_a = m_f[:3]
                        if m_a in seleccion: dic_ano[m_f] = 1
                        elif f"🔴 n.{m_a}" in seleccion: dic_ano[m_f] = 0
                        else: dic_ano[m_f] = None
                    h_total[ano_activo] = dic_ano

                # Construir paquete de actualización
                payload.append({
                    "dni": row_orig['dni'],
                    "historial": h_total,
                    "estado": str(mods.get('estado', row_orig['estado'])),
                    "monto": float(mods.get('monto', row_orig['monto'])),
                    "deuda": float(mods.get('deuda', row_orig['deuda'])),
                    "celular": str(mods.get('celular', row_orig['celular']))
                })

            if payload:
                try:
                    supabase.table("clientes").upsert(payload).execute()
                    st.toast("💾 Cambios guardados automáticamente", icon="✅")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # --- EL EDITOR (ORDEN SOLICITADO) ---
    st.data_editor(
        df_filtered[['dni', 'nombre', 'celular', 'estado', 'monto', 'deuda', 'Historial']],
        column_config={
            "dni": st.column_config.TextColumn("DNI", disabled=True, width=100),
            "nombre": st.column_config.TextColumn("Nombre y Apellidos", disabled=True, width=300),
            "celular": st.column_config.TextColumn("Celular", width=120),
            "estado": st.column_config.SelectboxColumn(
                "Estado", 
                options=["DESEMBOLSADO", "PENDIENTE", "CANCELADO", "OBSERVADO"],
                width=150
            ),
            "monto": st.column_config.NumberColumn("Monto", format="%.2f", width=100),
            "deuda": st.column_config.NumberColumn("Deuda", format="%.2f", width=100),
            "Historial": st.column_config.MultiselectColumn(
                f"Pagos {ano_activo}", 
                options=TODAS_LAS_OPCIONES, 
                width=350
            ),
        },
        hide_index=True,
        use_container_width=True,
        key=f"ed_master_{ano_activo}",
        on_change=handle_autosave
    )