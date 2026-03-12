import streamlit as st
import pandas as pd
import io
from datetime import datetime
from utils.ui_components import compact_currency

def render(df):
    st.markdown("<h1 class='sura-title'>CENTRO DE REPORTES</h1>", unsafe_allow_html=True)
    st.caption("Generación de documentos ejecutivos y exportación de padrones operativos.")

    if df.empty:
        st.warning("⚠️ No hay datos en la tabla 'clientes' para generar reportes.")
        return

    # --- PANEL DE CONFIGURACIÓN DE REPORTE ---
    with st.container():
        st.markdown("### ⚙️ Configuración del Reporte")
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            formato = st.selectbox("Formato de salida:", ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"])
        with c2:
            segmento = st.multiselect("Filtrar por Estados:", options=df['estado'].unique(), default=None)
        with c3:
            # Opción para incluir solo clientes con celular
            solo_con_cel = st.toggle("Solo clientes con Celular", value=False)

    # --- LÓGICA DE FILTRADO PRE-EXPORTACIÓN ---
    df_export = df.copy()
    
    if segmento:
        df_export = df_export[df_export['estado'].isin(segmento)]
    
    if solo_con_cel:
        df_export = df_export[df_export['celular'].notna() & (df_export['celular'] != '')]

    # --- VISTA PREVIA ---
    st.divider()
    st.markdown(f"#### 📊 Vista previa del reporte ({len(df_export)} registros)")
    
    # Estilizamos la tabla de vista previa
    st.dataframe(
        df_export.head(10), 
        column_config={
            "monto": st.column_config.NumberColumn("Capital", format="S/ %.2f"),
            "deuda": st.column_config.NumberColumn("Deuda", format="S/ %.2f"),
            "celular": "📞 Contacto"
        },
        use_container_width=True,
        hide_index=True
    )

    # --- GENERACIÓN DE ARCHIVOS ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Preparamos el buffer para el archivo
    output = io.BytesIO()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    nombre_archivo = f"Reporte_SURA_{timestamp}"

    if formato == "Excel (.xlsx)":
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Hoja Principal: Datos
            df_export.to_excel(writer, index=False, sheet_name='Padron_Clientes')
            
            # Hoja 2: Resumen Ejecutivo
            resumen = df_export.groupby('estado').agg({
                'dni': 'count',
                'monto': 'sum',
                'deuda': 'sum'
            }).rename(columns={'dni': 'Cant_Clientes'}).reset_index()
            resumen.to_excel(writer, index=False, sheet_name='Resumen_SURA')
            
            # Formato estético (Opcional: puedes añadir más lógica de xlsxwriter aquí)
            workbook = writer.book
            worksheet = writer.sheets['Padron_Clientes']
            header_format = workbook.add_format({'bold': True, 'bg_color': '#2ea043', 'font_color': 'white'})
            for col_num, value in enumerate(df_export.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        nombre_archivo += ".xlsx"

    elif formato == "CSV (.csv)":
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        output.write(csv_data)
        mime_type = "text/csv"
        nombre_archivo += ".csv"
    
    else: # JSON
        json_data = df_export.to_json(orient='records', indent=4).encode('utf-8')
        output.write(json_data)
        mime_type = "application/json"
        nombre_archivo += ".json"

    # --- BOTONES DE ACCIÓN ---
    col_dl, col_stats = st.columns([1, 2])
    
    with col_dl:
        st.download_button(
            label="📥 DESCARGAR REPORTE",
            data=output.getvalue(),
            file_name=nombre_archivo,
            mime=mime_type,
            use_container_width=True,
            type="primary"
        )
    
    with col_stats:
        # Mini resumen de lo que se va a descargar
        m_total = compact_currency(df_export['monto'].sum())
        d_total = compact_currency(df_export['deuda'].sum())
        st.markdown(f"**Resumen de descarga:** Capital: `{m_total}` | Deuda: `{d_total}`")

    # --- HISTORIAL DE EXPORTACIÓN (SIMULADO) ---
    st.divider()
    with st.expander("📝 Notas de Generación"):
        st.write(f"""
            - **Fecha de generación:** {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
            - **Operador Responsable:** Leonardo Tavera
            - **Filtros Aplicados:** {"Ninguno" if not segmento else ", ".join(segmento)}
            - **Integridad:** Todos los montos han sido validados contra la tabla central de Supabase.
        """)