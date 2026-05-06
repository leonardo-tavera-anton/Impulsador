import streamlit as st
import pandas as pd
from utils.data_engine import supabase

def render():
    st.markdown("""
        <div style='background: #161b22; padding:20px; border-radius:10px; border: 1px solid #30363d; color:white; margin-bottom:20px;'>
            <h2 style='margin:0;'>📤 IMPORTACIÓN SURA v7.5</h2>
            <p style='margin:0; opacity:0.8;'>Limpieza Forzada y Carga Masiva (47K+)</p>
        </div>
    """, unsafe_allow_html=True)

    file = st.file_uploader("Sube el Excel de clientes", type=["xlsx", "xls"], key="final_uploader")

    if file:
        try:
            # Leemos el Excel (Pandas es muy eficiente aquí)
            df = pd.read_excel(file)
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # 1. LIMPIEZA VECTORIZADA (Rápida en 47k)
            if 'dni' in df.columns:
                df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                # Filtro rápido de nulos y vacíos
                df = df[df['dni'].notna() & (df['dni'] != 'nan') & (df['dni'] != '')]
            
            # Convertimos números de golpe
            for col in ['monto', 'cuota', 'deuda']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

            # 2. ELIMINACIÓN DE DUPLICADOS (Evita el Error 21000)
            df = df.drop_duplicates(subset=['dni'], keep='last')

            # 3. PREPARACIÓN DE COLUMNAS
            cols_db = ['dni', 'nombre', 'celular', 'monto', 'cuota', 'deuda', 'estado']
            df_final = df[[c for c in cols_db if c in df.columns]].copy()
            
            # Si no tienen historial, inicializamos con dict vacío
            # Nota: Si el cliente ya existe, el 'upsert' de Supabase mantendrá el historial 
            # de la DB si no lo enviamos en el payload.
            
            # Convertimos a lista de diccionarios (esta es la parte pesada)
            records = df_final.to_dict(orient="records")

            st.info(f"📋 **Pre-procesado:** {len(records):,} registros únicos listos para subir.")

            if st.button("🚀 INICIAR SUBIDA A SUPABASE", type="primary", use_container_width=True):
                with st.status("🚀 Procesando carga masiva...") as status:
                    # Con 47k, un batch de 500 es el punto dulce entre velocidad y estabilidad
                    batch_size = 500
                    total = len(records)
                    
                    for i in range(0, total, batch_size):
                        batch = records[i:i+batch_size]
                        # El .upsert() actualizará si el DNI existe o creará si es nuevo
                        supabase.table("clientes").upsert(batch).execute()
                        
                        progreso = min(i + batch_size, total)
                        status.write(f"🔄 Sincronizando... {progreso:,} de {total:,}")
                    
                    status.update(label="✅ ¡Base de datos actualizada con éxito!", state="complete")
                    
                    # LIMPIEZA CRÍTICA: Borrar el caché para que Dashboard y Gestión vean lo nuevo
                    st.cache_data.clear()
                    st.balloons()

        except Exception as e:
            st.error(f"❌ Error crítico en el procesamiento: {e}")