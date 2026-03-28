import streamlit as st
import pandas as pd
from utils.data_engine import supabase

def render():
    st.markdown("""
        <div style='background: #1f6feb; padding:20px; border-radius:10px; color:white; margin-bottom:20px;'>
            <h2 style='margin:0;'>📤 MÓDULO DE IMPORTACIÓN</h2>
            <p style='margin:0; opacity:0.8;'>SURA v7.5 | Auditoría Nuevo Chimbote 2026</p>
        </div>
    """, unsafe_allow_html=True)

    st.write("### 📁 1. Cargar archivo Excel")
    
    # Cargador de archivos
    file = st.file_uploader(
        "Arrastra tu archivo .xlsx aquí", 
        type=["xlsx", "xls"], 
        key="uploader_sura_v7"
    )

    # Si el archivo ya aparece como en tu foto:
    if file is not None:
        try:
            # Leemos el Excel
            df_import = pd.read_excel(file)
            
            # Limpiamos nombres de columnas (Pasamos a minúsculas: dni, nombre, monto...)
            df_import.columns = [str(c).lower().strip() for c in df_import.columns]
            
            st.success(f"✅ Archivo cargado correctamente: {len(df_import)} filas detectadas.")
            
            # Mostramos una vista previa para que estés seguro
            with st.expander("🔍 Ver vista previa de datos"):
                st.dataframe(df_import.head(10), use_container_width=True)

            st.divider()
            
            # --- EL BOTÓN DE SUBIDA ---
            st.write("### 🚀 2. Sincronizar con la nube")
            if st.button("🔥 INICIAR SUBIDA A SUPABASE", type="primary", use_container_width=True):
                with st.status("Subiendo datos a la base de datos...", expanded=True) as status:
                    # Convertimos a formato compatible con Supabase
                    records = df_import.to_dict(orient="records")
                    
                    # Subimos en bloques de 200 para que no explote
                    batch_size = 200
                    total = len(records)
                    
                    for i in range(0, total, batch_size):
                        batch = records[i:i+batch_size]
                        # El 'upsert' actualiza si el DNI ya existe
                        supabase.table("clientes").upsert(batch).execute()
                        status.write(f"Progreso: {min(i + batch_size, total)} de {total} filas...")
                    
                    status.update(label="✅ ¡Sincronización Exitosa!", state="complete")
                    st.balloons()
                    
                    # Limpiamos el caché para que el Dashboard vea los cambios
                    st.cache_data.clear()
                    st.success("¡Listo! Ya puedes ver los datos actualizados en la pestaña GESTIÓN.")

        except Exception as e:
            st.error(f"❌ Error al procesar el Excel: {e}")
            st.info("Asegúrate de que el archivo no esté protegido con contraseña.")
    else:
        st.info("Esperando archivo... El botón de subida aparecerá automáticamente al cargar el Excel.")