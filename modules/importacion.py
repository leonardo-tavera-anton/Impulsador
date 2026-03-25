import streamlit as st
import pandas as pd
import numpy as np
import time
from utils.data_engine import supabase 

def render():
    # --- UI DESIGN SYSTEM (SURA STYLE) ---
    st.markdown("""
        <style>
        .block-container { padding-top: 1rem !important; }
        
        /* Cabecera idéntica a Gestión */
        .sura-header {
            background: linear-gradient(90deg, #0D47A1 0%, #1E88E5 100%);
            padding: 20px 30px;
            border-radius: 12px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            border-left: 8px solid #64B5F6;
        }

        /* Glassmorphism para métricas */
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 15px !important;
        }
        
        .stExpander { border-radius: 12px !important; border: 1px solid #30363d !important; }
        </style>

        <div class="sura-header">
            <h2 style='margin:0; font-weight:700;'>📥 IMPORTACIÓN MASIVA</h2>
            <p style='margin:0; opacity:0.8;'>Motor de Auditoría Técnica SURA v7.5 | Nuevo Chimbote</p>
        </div>
    """, unsafe_allow_html=True)
    
    # --- PROTOCOLO DE SEGURIDAD ---
    with st.expander("🛡️ Protocolos de Validación Activos", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.info("**DNI**\n- Formato 8 dígitos\n- Limpieza de ceros")
        c2.info("**LIMPIEZA**\n- NaNs a 0.0\n- Nombres en Mayúsculas")
        c3.info("**INTEGRIDAD**\n- Filtro de duplicados\n- Upsert Seguro")

    # --- ZONA DE CARGA ---
    st.write("### 📁 Origen de Datos")
    archivo = st.file_uploader("", type=['xlsx', 'csv'], label_visibility="collapsed")
    
    if archivo:
        try:
            with st.status("🚀 Procesando con el Motor SURA...", expanded=True) as status:
                start_time = time.time()
                
                # Lectura
                if archivo.name.endswith('xlsx'):
                    df_raw = pd.read_excel(archivo)
                else:
                    df_raw = pd.read_csv(archivo)
                
                # Estandarización de columnas
                df_raw.columns = [str(c).lower().strip() for c in df_raw.columns]
                status.write("Analizando registros y normalizando tipos...")

                registros_procesados = []
                registros_omitidos = 0
                
                # Limpieza Blindada
                for _, row in df_raw.iterrows():
                    # Validación DNI
                    raw_dni = str(row.get('dni', '')).strip().split('.')[0]
                    if not raw_dni or raw_dni.lower() in ['none', 'nan', '']:
                        registros_omitidos += 1
                        continue
                    
                    dni_val = raw_dni.zfill(8)[:8]

                    # Funciones de normalización
                    def clean_num(val):
                        try:
                            v = float(val)
                            return v if not np.isnan(v) else 0.0
                        except: return 0.0

                    def clean_txt(val, default):
                        v = str(val).strip()
                        return v.upper() if v.lower() not in ["nan", "none", ""] else default

                    # Objeto Final (Sincronizado con nombres oficiales)
                    item = {
                        "dni": dni_val,
                        "nombre": clean_txt(row.get('nombre'), "SIN NOMBRE"),
                        "monto": clean_num(row.get('monto') or row.get('cap')),
                        "deuda": clean_num(row.get('deuda')),
                        "cuota": clean_num(row.get('cuota')),
                        "celular": clean_txt(row.get('celular') or row.get('whatsapp'), "0").split('.')[0],
                        "estado": clean_txt(row.get('estado'), "pendiente").lower()
                    }
                    registros_procesados.append(item)

                # Control de Duplicados
                df_temp = pd.DataFrame(registros_procesados)
                df_unicos = df_temp.drop_duplicates(subset=['dni'], keep='last')
                duplicados_removidos = len(df_temp) - len(df_unicos)
                
                status.update(label=f"✅ Auditoría finalizada en {time.time() - start_time:.2f}s", state="complete")

            # --- RESUMEN DE IMPORTACIÓN ---
            st.write("### 📋 Informe de Calidad")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Leídos", f"{len(df_raw):,}")
            m2.metric("Válidos", f"{len(df_unicos):,}", delta="OK")
            m3.metric("Sin DNI", f"{registros_omitidos}", delta_color="inverse")
            m4.metric("Duplicados", f"{duplicados_removidos}", delta_color="inverse")

            # Vista Previa
            st.dataframe(df_unicos, use_container_width=True, height=250)

            # --- BOTÓN DE ACCIÓN ---
            if st.button("🚀 INICIAR SUBIDA A SUPABASE", type="primary", use_container_width=True):
                prog_bar = st.progress(0)
                lista_final = df_unicos.to_dict(orient='records')
                total = len(lista_final)
                batch_size = 300 # Lotes grandes para velocidad
                
                try:
                    for i in range(0, total, batch_size):
                        batch = lista_final[i : i + batch_size]
                        # Asegúrate que el nombre de la tabla sea el correcto
                        supabase.table("clientes").upsert(batch).execute()
                        
                        prog = min((i + batch_size) / total, 1.0)
                        prog_bar.progress(prog)
                    
                    st.balloons()
                    st.success(f"🎉 ¡Éxito! {total} registros actualizados en Nuevo Chimbote.")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Error en sincronización: {e}")

        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

if __name__ == "__main__":
    render()