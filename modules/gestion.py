import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_engine import supabase 

def render(df):
    # Lógica de Mes
    fecha = datetime.now()
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    mes_key = f"{meses[fecha.month-1]}-{str(fecha.year)[2:]}"

    # Título Estilo SURA
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1A237E, #0D47A1); padding:15px; border-radius:10px; color:white; margin-bottom:20px; border-left: 5px solid #58a6ff;">
            <h3 style='margin:0;'>📋 AUDITORÍA SURA v7.5</h3>
            <p style='margin:0; opacity:0.8;'>Contribuyentes Nuevo Chimbote | Periodo: {mes_key}</p>
        </div>
    """, unsafe_allow_html=True)

    # Filtros Rápidos
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        busc = st.text_input("Buscar DNI/Nombre", placeholder="Escriba aquí...", label_visibility="collapsed")
    with c2:
        est = st.multiselect("Estado", ["activo", "retiró", "pendiente", "cesante"], default=["activo", "pendiente"])
    with c3:
        audit = st.selectbox("Filtro", ["Todos", "Gestionados", "Pendientes"])

    # Procesar Vista
    df_view = df.copy()
    
    # Check de historial (JSONB de tu SQL)
    df_view['ok'] = df_view['historial'].apply(lambda x: x.get(mes_key, False))

    if busc:
        df_view = df_view[df_view['dni'].str.contains(busc) | df_view['nombre'].str.contains(busc, case=False, na=False)]
    if est:
        df_view = df_view[df_view['estado'].str.lower().isin([s.lower() for s in est])]
    if audit == "Gestionados":
        df_view = df_view[df_view['ok'] == True]
    elif audit == "Pendientes":
        df_view = df_view[df_view['ok'] == False]

    # Tabla Maestra
    res = st.data_editor(
        df_view,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_order=["dni", "nombre", "estado", "ok", "monto", "deuda"],
        column_config={
            "dni": st.column_config.TextColumn("DNI", disabled=True),
            "nombre": st.column_config.TextColumn("Nombre", disabled=True),
            "estado": st.column_config.SelectboxColumn("Estado", options=["activo", "retiró", "pendiente", "cesante"]),
            "ok": st.column_config.CheckboxColumn(f"Audit {mes_key.split('-')[0]}"),
            "monto": st.column_config.NumberColumn("Monto S/", format="%.2f"),
            "deuda": st.column_config.NumberColumn("Deuda S/", format="%.2f"),
        },
        key="editor_master_2026"
    )

    # Guardado
    if st.button("💾 SINCRONIZAR CON SUPABASE", type="primary", use_container_width=True):
        changes = st.session_state.editor_master_2026.get("edited_rows", {})
        if changes:
            try:
                for idx, vals in changes.items():
                    fila = df_view.iloc[int(idx)]
                    id_dni = fila['dni']
                    
                    # Si cambió el check de auditoría, actualizamos el JSONB
                    if 'ok' in vals:
                        nuevo_hist = fila['historial'].copy()
                        nuevo_hist[mes_key] = vals['ok']
                        vals['historial'] = nuevo_hist
                        del vals['ok']
                    
                    supabase.table("clientes").update(vals).eq("dni", id_dni).execute()
                
                st.success("Base de datos actualizada con éxito.")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error al subir: {e}")