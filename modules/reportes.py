import streamlit as st
import pandas as pd
import io
from datetime import datetime

def render(df):
    st.markdown("<h1 class='sura-title'>MOTOR DE EXTRACCIÓN</h1>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("No hay datos para exportar.")
        return

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        segmento = st.selectbox("Seleccione alcance:", ["TODOS LOS REGISTROS"] + st.session_state.custom_estados)
    with col_r2:
        columnas_req = st.multiselect("Columnas a incluir:", 
                                     options=df.columns.tolist(),
                                     default=['dni', 'nombre', 'monto', 'deuda', 'estado'])

    # Filtros
    df_export = df.copy() if segmento == "TODOS LOS REGISTROS" else df[df['estado'] == segmento]
    if columnas_req:
        df_export = df_export[columnas_req]
        
    st.markdown(f"**Vista previa ({len(df_export)} filas):**")
    st.dataframe(df_export.head(10), use_container_width=True)

    # Botón de Descarga Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='SURA_DATA')
    
    st.download_button(
        label="🟢 DESCARGAR EXCEL (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"SURA_Core_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )