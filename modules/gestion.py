import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_engine import supabase

def render(df):
    # 1. CSS PARA DISEÑO COMPACTO Y LIMPIO
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
            <p style='margin:0; opacity:0.8;'>Nuevo Chimbote | Búsqueda Excel y Guardado Automático</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. SELECTOR DE AÑO Y AVISO DE AUTOSAVE
    c_ano, c_msg = st.columns([1, 3])
    with c_ano:
        anos_disponibles = [str(a) for a in range(2026, 2041)]
        ano_activo = st.selectbox("📅 Año de Gestión", anos_disponibles, index=0)
    with c_msg:
        st.write("") # Espaciador
        st.success("⚡ **Autosave Activo:** Los cambios se guardan al instante al salir de la celda.")

    # 3. FILTROS
    f1, f2 = st.columns([3, 1])
    with f1:
        busqueda = st.text_input("🔍 Buscar (Resalta y mueve al inicio)...", placeholder="Ej: Leonardo...")
    with f2:
        lista_estados = df['estado'].unique().tolist() if 'estado' in df.columns else []
        estado_filtro = st.multiselect("Filtrar Estado", lista_estados)

    # 4. PREPARACIÓN DE DATOS Y OPCIONES
    df_display = df.copy()
    
    meses_normales = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    meses_negativos = [f"🔴 n.{m}" for m in meses_normales]
    todas_las_opciones = meses_normales + meses_negativos
    meses_full = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    def extraer_historial_completo(h, ano):
        seleccionados = []
        if isinstance(h, dict) and ano in h:
            ano_data = h[ano]
            for m_full, valor in ano_data.items():
                m_abr = m_full[:3]
                if valor == 1: seleccionados.append(m_abr)
                elif valor == 0: seleccionados.append(f"🔴 n.{m_abr}")
        return seleccionados

    df_display['Historial'] = df_display['historial'].apply(lambda h: extraer_historial_completo(h, ano_activo))

    # Aplicar Filtro de Estado (Este sí oculta filas)
    if estado_filtro:
        df_display = df_display[df_display['estado'].isin(estado_filtro)]

    # --- LÓGICA DE BÚSQUEDA TIPO EXCEL ---
    if busqueda:
        busqueda_lower = busqueda.lower()
        # Columna temporal para marcar las filas que coinciden
        df_display['coincide'] = (
            df_display['nombre'].str.lower().str.contains(busqueda_lower, na=False) | 
            df_display['dni'].str.contains(busqueda, na=False) |
            df_display['celular'].astype(str).str.contains(busqueda, na=False)
        )
        # Ordenamos: Las coincidencias van al inicio. Reseteamos el index para que el Autosave no se confunda.
        df_display = df_display.sort_values('coincide', ascending=False).reset_index(drop=True)
        num_coincidencias = df_display['coincide'].sum()
        df_display = df_display.drop(columns=['coincide'])
    else:
        df_display = df_display.reset_index(drop=True)
        num_coincidencias = 0

    # Insertamos la numeración después de ordenar para que quede limpia (1, 2, 3...)
    df_display.insert(0, 'N°', range(1, len(df_display) + 1))
    
    # Preparamos las columnas exactas que van al editor
    df_visible = df_display[['N°', 'dni', 'nombre', 'celular', 'estado', 'Historial', 'monto', 'deuda']]
    
    # Aplicar color de fondo si hubo búsqueda
    if busqueda and num_coincidencias > 0:
        def resaltar_filas(row):
            # Pintamos de un tono dorado las filas que están al inicio (las que coinciden)
            if row.name < num_coincidencias:
                return ['background-color: rgba(255, 215, 0, 0.25)'] * len(row)
            return [''] * len(row)
        datos_editor = df_visible.style.apply(resaltar_filas, axis=1)
    else:
        datos_editor = df_visible

    # 5. FUNCIÓN DE GUARDADO AUTOMÁTICO (CALLBACK)
    def handle_autosave():
        key_editor = f"editor_v15_{ano_activo}"
        if key_editor in st.session_state:
            state = st.session_state[key_editor]
            
            if state["edited_rows"]:
                payload_masivo = []
                for row_idx, changes in state["edited_rows"].items():
                    actual_row = df_display.iloc[row_idx]
                    dni_v = actual_row['dni']
                    
                    historial_total = df[df['dni'] == dni_v].iloc[0]['historial']
                    if not isinstance(historial_total, dict): historial_total = {}

                    lista_ui = changes.get('Historial', actual_row['Historial'])
                    
                    dic_ano = {}
                    for m_f in meses_full:
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

    # 6. TABLA DE EDICIÓN CON AUTOSAVE Y FORMATO EXCEL
    st.data_editor(
        datos_editor,
        column_config={
            "N°": st.column_config.NumberColumn("N°", width=40),
            "dni": st.column_config.TextColumn("DNI", width=100),
            "nombre": st.column_config.TextColumn("Nombre", width=250),
            "celular": st.column_config.TextColumn("Celular", width=110),
            "estado": st.column_config.TextColumn("Estado", width=120),
            "Historial": st.column_config.MultiselectColumn(
                f"Registro {ano_activo}", 
                options=todas_las_opciones, 
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