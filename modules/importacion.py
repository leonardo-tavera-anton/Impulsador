import streamlit as st
import pandas as pd
from utils.data_engine import supabase

def render():
    st.markdown("""
        <div style='background: #161b22; padding:20px; border-radius:10px; border: 1px solid #30363d; color:white; margin-bottom:20px;'>
            <h2 style='margin:0;'>📤 IMPORTACIÓN SURA v7.5</h2>
            <p style='margin:0; opacity:0.8;'>Limpieza Forzada y Filtro de Duplicados</p>
        </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader("Sube el Excel de clientes", type=["xlsx", "xls"], key="final_uploader")

    if file:
        try:
            df = pd.read_excel(file)
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # 1. Limpiar DNI y descartar nulos
            if 'dni' in df.columns:
                df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df = df[df['dni'].notna()]
                df = df[df['dni'] != 'nan']
                df = df[df['dni'] != '']
            
            for col in ['monto', 'cuota', 'deuda']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            df['historial'] = [{} for _ in range(len(df))]

            cols_db = ['dni', 'nombre', 'celular', 'monto', 'cuota', 'deuda', 'estado', 'historial']
            df_final = df[[c for c in cols_db if c in df.columns]].copy()

            # --- SOLUCIÓN AL ERROR 21000 ---
            # Elimina las filas con DNI repetido, conservando el último que aparece en el Excel
            df_final = df_final.drop_duplicates(subset=['dni'], keep='last')

            def clean_dict(d):
                return {k: (v if pd.notnull(v) else None) for k, v in d.items()}

            records = [clean_dict(r) for r in df_final.to_dict(orient="records")]

            st.success(f"✅ {len(records)} registros únicos listos. Duplicados eliminados.")

            if st.button("🚀 SUBIR A SUPABASE", type="primary", use_container_width=True):
                with st.status("Sincronizando con la nube...") as status:
                    batch_size = 200
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i+batch_size]
                        supabase.table("clientes").upsert(batch).execute()
                        status.write(f"Cargando: {min(i+batch_size, len(records))} de {len(records)}")
                    
                    status.update(label="✅ ¡Sincronización Exitosa!", state="complete")
                    st.cache_data.clear()
                    st.balloons()

        except Exception as e:
            st.error(f"❌ Error crítico: {e}")