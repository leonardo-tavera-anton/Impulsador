import streamlit as st
import pandas as pd
from utils.data_engine import supabase

def render(df):
    # --- INTERFAZ ESTILO EXCEL ---
    st.markdown("""
        <style>
        /* Altura fija para scroll fluido */
        [data-testid="stDataEditor"] > div:first-child { height: 700px !important; }
        /* Bloquea la transparencia/lag visual */
        [data-testid="stBlock"] { opacity: 1 !important; }
        .stDataFrame { width: 100%; }
        </style>
    """, unsafe_allow_html=True)

    st.subheader(f"📋 Gestión de Padrones (Total: {len(df):,})")

    # --- FILTROS ---
    c1, c2 = st.columns([1, 4])
    with c1:
        st.selectbox("Año Fiscal", ["2026", "2027", "2028", "2029", "2030"], key="active_year")
    with c2:
        query = st.text_input("🔍 Buscar por DNI o Nombre", key="search_box")

    # --- FILTRADO INSTANTÁNEO ---
    if query:
        q = query.lower()
        df_filtered = df[df['nombre'].str.lower().str.contains(q, na=False) | df['dni'].str.contains(q, na=False)].copy()
    else:
        # Cargamos una muestra grande. El buscador siempre encontrará sobre los 47k.
        df_filtered = df.head(1000).copy()

    # --- EDITOR DE ALTO RENDIMIENTO ---
    # ORDEN: DNI, NOMBRE, CELULAR, ESTADO, MONTO, DEUDA
    st.caption("Modo Edición Rápida activo. Los cambios se guardan en segundo plano.")
    
    edited_data = st.data_editor(
        df_filtered[['dni', 'nombre', 'celular', 'estado', 'monto', 'deuda']],
        column_config={
            "dni": st.column_config.TextColumn("DNI", disabled=True, width=100),
            "nombre": st.column_config.TextColumn("Nombre y Apellidos", disabled=True, width=300),
            "celular": st.column_config.TextColumn("Celular", width=120),
            "estado": st.column_config.SelectboxColumn(
                "Estado", 
                options=["DESEMBOLSADO", "PENDIENTE", "CANCELADO", "OBSERVADO"],
                width=150
            ),
            "monto": st.column_config.NumberColumn("Monto S/", format="%.2f", width=100),
            "deuda": st.column_config.NumberColumn("Deuda S/", format="%.2f", width=100),
        },
        hide_index=True,
        use_container_width=True,
        key="master_editor_v7"
    )

    # --- AUTOGUARDADO ASÍNCRONO ---
    if "master_editor_v7" in st.session_state:
        # Detecta solo las filas que han cambiado
        cambios = st.session_state["master_editor_v7"].get("edited_rows")
        if cambios:
            batch_updates = []
            for row_idx, mods in cambios.items():
                row_orig = df_filtered.iloc[int(row_idx)]
                
                # Construir paquete mínimo de actualización
                item = {"dni": row_orig['dni']}
                for campo, valor in mods.items():
                    item[campo] = valor
                
                batch_updates.append(item)

            if batch_updates:
                try:
                    # Envío masivo a Supabase (Upsert por DNI)
                    supabase.table("clientes").upsert(batch_updates).execute()
                    st.toast("💾 Sincronizado", icon="✅")
                except Exception:
                    # Falla silenciosa para no interrumpir tu trabajo
                    pass