import streamlit as st
import pandas as pd
from utils.data_engine import supabase

def render():
    st.markdown("""
        <div style='background: linear-gradient(90deg, #1f6feb, #111e2f); padding:20px; border-radius:10px; color:white; margin-bottom:20px;'>
            <h2 style='margin:0;'>📤 MÓDULO DE IMPORTACIÓN</h2>
            <p style='margin:0; opacity:0.8;'>Actualización masiva de contribuyentes - Nuevo Chimbote 2026</p>
        </div>
    """, unsafe_allow_html=True)

    # El cargador de archivos ya no está bloqueado por otro login
    st.write("### 📁 Cargar origen de datos (Excel)")
    uploaded_file = st.file_uploader("Arrastra tu archivo .xlsx o .xls", type=["xlsx", "xls"], key="uploader_masivo")

    if uploaded_file:
        try:
            df_import = pd.read_excel(uploaded_file)
            
            # Normalización inmediata para que coincida con Supabase
            df_import.columns = [str(c).lower().strip() for c in df_import.columns]
            
            st.success(f"Archivo detectado: {len(df_import)} filas encontradas.")
            st.dataframe(df_import.head(10), width="stretch", hide_index=True)

            if st.button("🚀 INICIAR SINCRONIZACIÓN", type="primary", width="stretch"):
                with st.status("Sincronizando con Supabase...", expanded=True) as status:
                    # Convertir a lista de diccionarios para Upsert
                    records = df_import.to_dict(orient="records")
                    
                    # Subida por bloques para no saturar la API
                    batch_size = 200
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i+batch_size]
                        supabase.table("clientes").upsert(batch).execute()
                        status.write(f"Procesando: {min(i+batch_size, len(records))} / {len(records)}")
                    
                    status.update(label="✅ ¡Sincronización Completa!", state="complete")
                    st.balloons()
                    st.cache_data.clear() # Limpia el cache para que los otros tabs vean la data nueva
        
        except Exception as e:
            st.error(f"Error al procesar el Excel: {e}")