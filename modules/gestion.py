import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_engine import supabase

def render(df):
    # 1. CSS PARA DISEÑO COMPACTO Y RENDIMIENTO
    st.markdown("""
        <style>
        [data-testid="stDataEditor"] { width: fit-content !important; min-width: 100%; }
        .stCheckbox { margin-bottom: 0px; }
        /* Reduce el espacio entre filas para ver más datos */
        [data-testid="stDataEditor"] div { font-size: 14px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:15px; border-radius:10px; color:white; margin-bottom:15px;">
            <h3 style='margin:0;'>📋 GESTIÓN MULTIANUAL SURA v7.5</h3>
            <p style='margin:0; opacity:0.8;'>Control de Historial 2026 - 2040 | Nuevo Chimbote</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. SELECCIÓN DE PERIODO Y SEGURO
    c_ano, c_edit, c_empty = st.columns([1, 1.2, 2])
    with c_ano:
        anos_disponibles = [str(a) for a in range(2026, 2041)]
        ano_activo = st.selectbox("📅 Año", anos_disponibles, index=0)
    
    with c_edit:
        st.write("") 
        modo_edicion = st.toggle("🔓 Modo Edición", help="Activa para modificar meses o montos.")

    # 3. FILTROS COMPACTOS
    f1, f2 = st.columns([3, 1])
    with f1:
        busqueda = st.text_input("🔍 Buscar...", placeholder="Nombre, DNI o Celular")
    with f2:
        lista_estados = df['estado'].unique().tolist() if 'estado' in df.columns else []
        estado_filtro = st.multiselect("Estado", lista_estados)

    # 4. PROCESAMIENTO DE DATOS
    df_display = df.copy()
    df_display.insert(0, 'N°', range(1, len(df_display) + 1))
    
    meses_opciones = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    meses_full = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    def extraer_meses_por_ano(h, ano):
        if isinstance(h, dict) and ano in h:
            ano_data = h[ano]
            return [m[:3] for m, v in ano_data.items() if v == 1]
        return []

    df_display['Historial'] = df_display['historial'].apply(lambda h: extraer_meses_por_ano(h, ano_activo))

    # Filtros
    if busqueda:
        df_display = df_display[
            df_display['nombre'].str.contains(busqueda, case=False, na=False) | 
            df_display['dni'].str.contains(busqueda, na=False) |
            df_display['celular'].astype(str).str.contains(busqueda, na=False)
        ]
    if estado_filtro:
        df_display = df_display[df_display['estado'].isin(estado_filtro)]

    # 5. TABLA COMPACTA
    cols_bloqueadas = ["N°", "dni", "nombre"] if modo_edicion else ["N°", "dni", "nombre", "Historial", "monto", "deuda", "estado", "celular"]

    edited_df = st.data_editor(
        df_display[['N°', 'dni', 'nombre', 'celular', 'estado', 'Historial', 'monto', 'deuda']],
        column_config={
            "N°": st.column_config.NumberColumn("N°", width=40),
            "dni": st.column_config.TextColumn("DNI", width=100),
            "nombre": st.column_config.TextColumn("Nombre", width=250),
            "celular": st.column_config.TextColumn("Celular", width=110),
            "estado": st.column_config.TextColumn("Estado", width=120),
            "Historial": st.column_config.MultiselectColumn(f"Meses {ano_activo}", options=meses_opciones, width=200),
            "monto": st.column_config.NumberColumn("Monto", format="%.2f", width=85),
            "deuda": st.column_config.NumberColumn("Deuda", format="%.2f", width=85),
        },
        disabled=cols_bloqueadas,
        hide_index=True,
        use_container_width=True,
        key=f"gestion_v11_{ano_activo}"
    )

    # 6. GUARDADO MASIVO (UPSERT) - AQUÍ ESTÁ LA VELOCIDAD
    if modo_edicion:
        st.warning(f"⚠️ Estás en Modo Edición ({ano_activo}). Los cambios se aplicarán al guardar.")
        if st.button(f"🚀 GUARDAR TODO AL INSTANTE ({ano_activo})", type="primary", use_container_width=True):
            with st.status("Preparando envío masivo...") as status:
                
                payload_masivo = []
                
                for _, row in edited_df.iterrows():
                    dni_v = row['dni']
                    
                    # Recuperar historial previo del DataFrame original
                    fila_original = df[df['dni'] == dni_v]
                    historial_total = fila_original.iloc[0]['historial'] if not fila_original.empty else {}
                    if not isinstance(historial_total, dict): historial_total = {}
                    
                    # Actualizar el año seleccionado
                    lista_meses_ui = row['Historial']
                    historial_total[ano_activo] = {m: (1 if m[:3] in lista_meses_ui else 0) for m in meses_full}
                    
                    # Agregar a la lista masiva
                    payload_masivo.append({
                        "dni": dni_v,
                        "historial": historial_total,
                        "celular": str(row['celular']),
                        "estado": str(row['estado']),
                        "monto": float(row['monto']),
                        "deuda": float(row['deuda'])
                    })
                
                try:
                    # UPSERT envía todos los registros en una sola petición HTTP
                    if payload_masivo:
                        supabase.table("clientes").upsert(payload_masivo).execute()
                        status.update(label="✅ ¡Sincronización masiva exitosa!", state="complete")
                        st.cache_data.clear()
                        st.rerun()
                except Exception as e:
                    st.error(f"Error crítico durante el guardado: {e}")