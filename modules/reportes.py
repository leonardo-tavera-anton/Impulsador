import streamlit as st
import pandas as pd
import io
import time
from datetime import datetime
# Asegúrate de que esta utilidad exista en tu proyecto
from utils.ui_components import compact_currency 

def render(df):
    st.markdown("""
        <style>
        .sura-title { color: #1E88E5; font-weight: bold; font-size: 2.5rem; }
        .metric-card { background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; border: 1px solid #333; }
        </style>
        <h1 class='sura-title'>CENTRO DE REPORTES</h1>
    """, unsafe_allow_html=True)
    st.caption("Generación de documentos ejecutivos y exportación de padrones operativos (v7.5).")

    if df is None or df.empty:
        st.warning("⚠️ No hay datos disponibles para generar reportes.")
        return

    # --- PANEL DE CONFIGURACIÓN ---
    with st.container(border=True):
        st.markdown("### ⚙️ Configuración del Reporte")
        c1, c2, c3 = st.columns([1, 1, 1])
        
        with c1:
            formato = st.selectbox("Formato de salida:", ["Excel (.xlsx)", "CSV (.csv)", "JSON (.json)"])
        with c2:
            segmento = st.multiselect("Filtrar por Estados:", options=df['estado'].unique(), default=None)
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            solo_con_cel = st.toggle("Solo con Celular", value=False)

    # --- FILTRADO ---
    df_export = df.copy()
    if segmento:
        df_export = df_export[df_export['estado'].isin(segmento)]
    if solo_con_cel:
        df_export = df_export[df_export['celular'].notna() & (df_export['celular'].astype(str).str.len() > 5)]

    # --- VISTA PREVIA (Actualizado a estándares 2026) ---
    st.divider()
    st.markdown(f"#### 📊 Vista previa del reporte ({len(df_export)} registros)")
    
    st.dataframe(
        df_export.head(15), 
        column_config={
            "monto": st.column_config.NumberColumn("Capital", format="S/ %.2f"),
            "deuda": st.column_config.NumberColumn("Deuda", format="S/ %.2f"),
            "celular": "📞 Contacto"
        },
        width="stretch", # Cambiado de use_container_width por actualización 2026
        hide_index=True
    )

    # --- GENERADOR DE ARCHIVOS ---
    output = io.BytesIO()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    nombre_archivo = f"SURA_Reporte_{timestamp}"

    if formato == "Excel (.xlsx)":
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export.to_excel(writer, index=False, sheet_name='Padron_Clientes')
            
            # Resumen Ejecutivo automático
            resumen = df_export.groupby('estado').agg({
                'dni': 'count', 'monto': 'sum', 'deuda': 'sum'
            }).rename(columns={'dni': 'Cant_Clientes'}).reset_index()
            resumen.to_excel(writer, index=False, sheet_name='Resumen_SURA')
            
            # Formato estético
            workbook = writer.book
            header_format = workbook.add_format({'bold': True, 'bg_color': '#1E88E5', 'font_color': 'white'})
            for sheet_name in ['Padron_Clientes', 'Resumen_SURA']:
                worksheet = writer.sheets[sheet_name]
                cols = df_export.columns if sheet_name == 'Padron_Clientes' else resumen.columns
                for col_num, value in enumerate(cols):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)
        
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        nombre_archivo += ".xlsx"

    elif formato == "CSV (.csv)":
        csv_data = df_export.to_csv(index=False).encode('utf-8-sig')
        output.write(csv_data)
        mime_type = "text/csv"
        nombre_archivo += ".csv"
    
    else: # JSON
        json_data = df_export.to_json(orient='records', indent=4).encode('utf-8')
        output.write(json_data)
        mime_type = "application/json"
        nombre_archivo += ".json"

    # --- BOTÓN DE DESCARGA (Actualizado a estándares 2026) ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_dl, col_stats = st.columns([1, 2])
    
    with col_dl:
        st.download_button(
            label="📥 DESCARGAR REPORTE",
            data=output.getvalue(),
            file_name=nombre_archivo,
            mime=mime_type,
            width="stretch", # Actualizado
            type="primary"
        )
    
    with col_stats:
        m_total = compact_currency(df_export['monto'].sum())
        d_total = compact_currency(df_export['deuda'].sum())
        st.info(f"💰 **Capital:** {m_total} | **Deuda:** {d_total}")

    st.divider()
    with st.expander("📝 Detalles de Auditoría"):
        st.write(f"Generado por: **Leonardo Tavera** | Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")