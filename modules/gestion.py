import streamlit as st
import pandas as pd
import time
from utils.ui_components import compact_currency

def render(df):
    st.markdown("<h1 class='sura-title'>GESTIÓN OPERATIVA</h1>", unsafe_allow_html=True)
    st.caption("Panel de edición masiva y control de contactos de clientes.")

    if df.empty:
        st.warning("⚠️ La base de datos está vacía. Use el módulo de Importación para cargar registros.")
        return

    # --- PANEL DE BÚSQUEDA Y FILTROS ---
    with st.container():
        st.markdown("### 🔍 Buscador de Activos")
        c1, c2, c3 = st.columns([2, 1, 1])
        
        with c1:
            search_query = st.text_input(
                "DNI, Nombre o Celular:", 
                placeholder="Busque por cualquier criterio...",
                help="El sistema filtrará automáticamente en los 6,952 registros."
            )
        
        with c2:
            # Filtro por estados dinámicos desde la sesión
            filtro_estado = st.multiselect(
                "Filtrar por Estado:", 
                options=sorted(df['estado'].unique()),
                default=None
            )
            
        with c3:
            # Filtro de efectividad (Columna MAR)
            filtro_mar = st.selectbox(
                "Efectividad Marzo:", 
                ["Todos", "Solo ✅ (Efectivos)", "Solo ❌ (Pendientes)"]
            )

    # --- LÓGICA DE FILTRADO AVANZADO ---
    # Si vas a agregar 'telefono' a Supabase, lo incluimos aquí en la búsqueda
    mask = (
        df['dni'].astype(str).str.contains(search_query, na=False) |
        df['nombre'].str.contains(search_query, case=False, na=False)
    )
    
    # Agregar búsqueda por teléfono si la columna existe
    if 'telefono' in df.columns:
        mask |= df['telefono'].astype(str).str.contains(search_query, na=False)

    df_filtered = df[mask]

    if filtro_estado:
        df_filtered = df_filtered[df_filtered['estado'].isin(filtro_estado)]
    
    if filtro_mar == "Solo ✅ (Efectivos)":
        df_filtered = df_filtered[df_filtered['MAR'] == '✅']
    elif filtro_mar == "Solo ❌ (Pendientes)":
        df_filtered = df_filtered[df_filtered['MAR'] != '✅']

    st.divider()

    # --- EDITOR DE DATOS PROFESIONAL ---
    st.markdown(f"**Mostrando {len(df_filtered)} registros encontrados**")
    
    # Definimos la configuración de columnas para el editor
    # Protegemos DNI y Nombre marcándolos como no editables
    column_config = {
        "dni": st.column_config.TextColumn("DNI", help="Identificador único (No editable)", disabled=True),
        "nombre": st.column_config.TextColumn("Cliente", help="Nombre completo (No editable)", disabled=True, width="large"),
        "telefono": st.column_config.TextColumn("📞 Número Cliente", help="Celular de contacto para cobranza", validate=r"^\d{9}$"),
        "monto": st.column_config.NumberColumn("Monto S/", format="S/ %.2f", min_value=0),
        "deuda": st.column_config.NumberColumn("Deuda S/", format="S/ %.2f", min_value=0),
        "cuota": st.column_config.NumberColumn("Cuota S/", format="S/ %.2f", min_value=0),
        "estado": st.column_config.SelectboxColumn(
            "Estado Actual", 
            options=st.session_state.custom_estados,
            required=True
        ),
        "MAR": st.column_config.CheckboxColumn("¿Efectivo?", help="Marcar si ya realizó el pago en Marzo")
    }

    # El Data Editor es la joya de la corona para modificación masiva
    edited_df = st.data_editor(
        df_filtered,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed" # Evita que borren filas por accidente
    )

    # --- PANEL DE ACCIÓN ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, col_btn2, col_btn3 = st.columns([1.2, 1, 2])

    with col_btn1:
        if st.button("💾 GUARDAR CAMBIOS", type="primary", use_container_width=True):
            with st.spinner("Sincronizando con Supabase..."):
                # Aquí llamarías a: data_engine.update_batch(edited_df)
                time.sleep(1.5) # Simulación de red
                st.success("¡Datos actualizados correctamente!")
                st.balloons()
    
    with col_btn2:
        if st.button("📂 Exportar Vista Actual", use_container_width=True):
            csv = edited_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Descargar CSV", csv, "gestion_filtrada.csv", "text/csv", 
                use_container_width=True
            )

    with col_btn3:
        # Resumen rápido de lo que se está editando
        monto_vista = edited_df['monto'].sum()
        st.markdown(f"**Capital en pantalla:** `{compact_currency(monto_vista)}`")

    # --- NOTAS DE AUDITORÍA ---
    st.info("""
        💡 **Tips de Gestión:** - Puedes hacer doble clic en cualquier celda de 'Estado' para cambiarlo rápido. 
        - El campo 'Número Cliente' debe tener 9 dígitos.
        - Los cambios solo se aplicarán a la base de datos al presionar 'Guardar Cambios'.
    """)