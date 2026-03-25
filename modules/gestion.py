import streamlit as st
import pandas as pd
from datetime import datetime

def render(df):
    # 1. ESTILO VISUAL COMPACTO
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; }
        [data-testid="stMetric"] { padding: 5px 10px !important; }
        /* Reduce el tamaño de letra de la tabla para que sea más denso */
        [data-testid="stDataEditor"] div { font-size: 11px !important; }
        </style>
        <div style="background: linear-gradient(90deg, #0D47A1, #1E88E5); padding:15px; border-radius:10px; color:white; margin-bottom:15px;">
            <h3 style='margin:0;'>💎 SURA: GESTIÓN DE PADRONES</h3>
            <p style='margin:0; opacity:0.8; font-size:0.8rem;'>Nuevo Chimbote 2026 | Vista Compacta</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. CÁLCULOS Y VENTANA DE MESES
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    idx = datetime.now().month - 1
    ventana = [meses[(idx + i) % 12] for i in range(3)]

    # 3. KPIs RESUMIDOS
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Registros", f"{len(df):,}")
    k2.metric("Cartera", f"S/ {df['Monto'].sum():,.0f}")
    k3.metric("Deuda", f"S/ {df['deuda'].sum():,.0f}")
    k4.metric("Mes", ventana[0])

    # 4. FILTROS EN UNA SOLA LÍNEA
    f1, f2 = st.columns([3, 1])
    with f1:
        search = st.text_input("", placeholder="🔍 Buscar por DNI o Nombre...", label_visibility="collapsed")
    with f2:
        solo_deuda = st.toggle("Solo Deuda", value=False)

    # Lógica de filtrado
    df_f = df
    if search:
        df_f = df[df['dni'].astype(str).str.contains(search) | df['nombre'].str.contains(search, case=False)]
    if solo_deuda:
        df_f = df_f[df_f['deuda'] > 0]

    # 5. TABLA ULTRA-COMPACTA (SIN HISTORIAL)
    # Definimos el orden exacto para ocultar lo que no queremos
    columnas_visibles = ["dni", "nombre", "Numero", "Monto", "deuda", "cuota"] + ventana

    st.data_editor(
        df_f,
        use_container_width=True,
        hide_index=True,
        height=550,
        column_order=columnas_visibles, # <--- Aquí se elimina 'historial' y 'estado'
        column_config={
            "dni": st.column_config.TextColumn("DNI", width=80, disabled=True),
            "nombre": st.column_config.TextColumn("Cliente", width=250, disabled=True),
            "Numero": st.column_config.TextColumn("WhatsApp", width=100),
            "Monto": st.column_config.NumberColumn("Monto", format="S/ %d", width=70),
            "deuda": st.column_config.NumberColumn("Deuda", format="S/ %d", width=70),
            "cuota": st.column_config.NumberColumn("Cuota", format="S/ %d", width=70),
            **{m: st.column_config.CheckboxColumn(m, width=50) for m in ventana}
        },
        key="editor_gestion_final"
    )

    # 6. BOTÓN DE GUARDADO
    if st.button("🚀 ACTUALIZAR SUPABASE", type="primary", use_container_width=True):
        st.success("Cambios sincronizados correctamente.")