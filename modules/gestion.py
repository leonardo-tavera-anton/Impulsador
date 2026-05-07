import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_engine import supabase

MESES_NORMALES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_NEGATIVOS = [f"🔴 n.{m}" for m in MESES_NORMALES]
TODAS_LAS_OPCIONES = MESES_NORMALES + MESES_NEGATIVOS
MESES_FULL = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
              "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def render(df):
    st.markdown("""
        <style>
        [data-testid="stDataEditor"] { width: fit-content !important; min-width: 100%; }
        [data-testid="stDataEditor"] div { font-size: 13px; }
        .stSelectbox { margin-bottom: 0px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:15px; border-radius:10px; color:white; margin-bottom:15px;">
            <h3 style='margin:0;'>📋 GESTIÓN SURA v7.5 - INTELIGENTE</h3>
            <p style='margin:0; opacity:0.8;'>Nuevo Chimbote | Búsqueda Rápida y Guardado Automático</p>
        </div>
    """, unsafe_allow_html=True)

    c_ano, c_msg = st.columns([1, 3])
    with c_ano:
        anos_disponibles = [str(a) for a in range(2026, 2041)]
        ano_activo = st.selectbox("📅 Año de Gestión", anos_disponibles, index=0)
    with c_msg:
        st.write("") 
        st.success("⚡ **Autosave Activo:** Los cambios se guardan al instante al salir de la celda.")

    f1, f2 = st.columns([3, 1])
    with f1:
        busqueda = st.text_input("🔍 Buscar (Mueve al inicio sin lag)...", placeholder="Ej: Leonardo...")
    with f2:
        lista_estados = df['estado'].unique().tolist() if 'estado' in df.columns else []
        estado_filtro = st.multiselect("Filtrar Estado", lista_estados)

    df_display = df.copy()
    df_indexed = df.set_index('dni') if df.index.name != 'dni' else df

    def extraer_historial_completo(h, ano):
        seleccionados = []
        if isinstance(h, dict) and ano in h:
            for m_full, valor in h[ano].items():
                m_abr = m_full[:3]
                if valor == 1: seleccionados.append(m_abr)
                elif valor == 0: seleccionados.append(f"🔴 n.{m_abr}")
        return seleccionados

    df_display['Historial'] = df_display['historial'].apply(lambda h: extraer_historial_completo(h, ano_activo))

    if estado_filtro:
        df_display = df_display[df_display['estado'].isin(estado_filtro)]

    if busqueda:
        busqueda_lower = busqueda.lower()
        mask = (
            df_display['nombre'].str.lower().str.contains(busqueda_lower, na=False) | 
            df_display['dni'].str.contains(busqueda, na=False) |
            df_display['celular'].astype(str).str.contains(busqueda, na=False)
        )
        df_display = df_display.iloc[mask.argsort()[::-1]].reset_index(drop=True)
    else:
        df_display = df_display.reset_index(drop=True)

    df_display.insert(0, 'N°', range(1, len(df_display) + 1))
    df_visible = df_display[['N°', 'dni', 'nombre', 'celular', 'estado', 'Historial', 'monto', 'deuda']]

    def handle_autosave():
        key_editor = f"editor_v15_{ano_activo}"
        if key_editor in st.session_state:
            state = st.session_state[key_editor]
            if state["edited_rows"]:
                payload_masivo = []
                for row_idx, changes in state["edited_rows"].items():
                    actual_row = df_display.iloc[row_idx]
                    dni_v = actual_row['dni']
                    historial_total = df_indexed.at[dni_v, 'historial']
                    if not isinstance(historial_total, dict): historial_total = {}

                    lista_ui = changes.get('Historial', actual_row['Historial'])
                    dic_ano = {}
                    for m_f in MESES_FULL:
                        m_a = m_f[:3]
                        if m_a in lista_ui: dic_ano[m_f] = 1
                        elif f"🔴 n.{m_a}" in lista_ui: dic_ano[m_f] = 0
                    
                    historial_total[ano_activo] = dic_ano
                    payload_masivo.append({
                        "dni": dni_v,
                        "historial": historial_total,
                        "celular": str(changes.get('celular', actual_row['celular'])),
                        "estado": str(changes.get('estado', actual_row['estado'])),
                        "monto": float(changes.get('monto', actual_row['monto'])),
                        "deuda": float(changes.get('deuda', actual_row['deuda']))
                    })
                
                try:
                    if payload_masivo:
                        supabase.table("clientes").upsert(payload_masivo).execute()
                        st.toast(f"✅ Sincronizado: {len(payload_masivo)} fila(s)", icon="💾")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    st.data_editor(
        df_visible,
        column_config={
            "N°": st.column_config.NumberColumn("N°", width=40),
            "dni": st.column_config.TextColumn("DNI", width=100),
            "nombre": st.column_config.TextColumn("Nombre", width=250),
            "celular": st.column_config.TextColumn("Celular", width=110),
            "estado": st.column_config.TextColumn("Estado", width=120),
            "Historial": st.column_config.MultiselectColumn(
                f"Registro {ano_activo}", 
                options=TODAS_LAS_OPCIONES, 
                width=280,
                help="Selecciona Mes para 1, o 🔴 n.Mes para 0."
            ),
            "monto": st.column_config.NumberColumn("Monto", format="%.2f", width=85),
            "deuda": st.column_config.NumberColumn("Deuda", format="%.2f", width=85),
        },
        disabled=["N°", "dni", "nombre"],
        hide_index=True,
        use_container_width=True,
        key=f"editor_v15_{ano_activo}",
        on_change=handle_autosave
    )