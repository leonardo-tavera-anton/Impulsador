import streamlit as st
import pandas as pd
import numpy as np
import time
from utils.data_engine import supabase 

def render():
    # --- UI DESIGN SYSTEM (PREMIUM DARK) ---
    st.markdown("""
        <style>
        .main-title { 
            text-align: left; 
            color: #1E88E5; 
            font-weight: 800; 
            margin-bottom: 5px; 
            font-size: 2.5rem;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1rem;
        }
        /* Glassmorphism Cards */
        .metric-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            border-color: #1E88E5;
            box-shadow: 0 10px 30px rgba(30, 136, 229, 0.2);
        }
        /* Arreglo para métricas estándar de Streamlit */
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 15px !important;
            padding: 15px 20px !important;
        }
        </style>
        <h1 class='main-title'>📥 Importación Masiva</h1>
        <p class='subtitle'>Motor de Auditoría Técnica SURA v7.5</p>
    """, unsafe_allow_html=True)
    
    # --- PANEL DE PROTOCOLO (DISEÑO LIMPIO) ---
    with st.expander("🛡️ Protocolos de Validación Activos", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.markdown("**Estructura DNI**\n- Formateo a 8 dígitos\n- Limpieza de .0 flotantes")
        c2.markdown("**Sanitización JSON**\n- Conversión de NaNs a 0.0\n- Strings a Mayúsculas")
        c3.markdown("**Integridad DB**\n- Filtro de duplicados por DNI\n- Upsert dinámico")

    # --- CARGA DE ARCHIVOS ---
    st.markdown("### 📁 Origen de Datos")
    archivo = st.file_uploader("", type=['xlsx', 'csv'], help="Sube tu padrón municipal aquí")
    
    if archivo:
        try:
            with st.status("🚀 Ejecutando Motor de Auditoría...", expanded=True) as status:
                start_processing = time.time()
                
                # Lectura eficiente
                if archivo.name.endswith('xlsx'):
                    df_raw = pd.read_excel(archivo)
                else:
                    df_raw = pd.read_csv(archivo)
                
                df_raw.columns = [str(c).lower().strip() for c in df_raw.columns]
                status.update(label="Analizando registros y limpiando tipos de datos...", state="running")

                registros_procesados = []
                registros_omitidos = 0
                
                # Procesamiento Blindado
                for _, row in df_raw.iterrows():
                    # Validación DNI (Clave primaria)
                    raw_dni = str(row.get('dni', '')).strip().split('.')[0]
                    if not raw_dni or raw_dni.lower() in ['none', 'nan', '']:
                        registros_omitidos += 1
                        continue
                    
                    dni_val = raw_dni.zfill(8)[:8]

                    # Funciones de limpieza nativas
                    def clean_num(val):
                        try:
                            v = float(val)
                            return v if not np.isnan(v) else 0.0
                        except: return 0.0

                    def clean_txt(val, default):
                        v = str(val).strip()
                        return v.upper() if v.lower() not in ["nan", "none", ""] else default

                    # Creación de Objeto Seguro
                    item = {
                        "dni": dni_val,
                        "nombre": clean_txt(row.get('nombre'), "SIN NOMBRE"),
                        "monto": clean_num(row.get('monto')),
                        "deuda": clean_num(row.get('deuda')),
                        "cuota": clean_num(row.get('cuota')),
                        "celular": clean_txt(row.get('celular'), "0").split('.')[0],
                        "estado": clean_txt(row.get('estado'), "pendiente").lower()
                    }
                    registros_procesados.append(item)

                # Control de Duplicidad Pre-Carga
                df_temp = pd.DataFrame(registros_procesados)
                total_detectados = len(df_temp)
                df_unicos = df_temp.drop_duplicates(subset=['dni'], keep='last')
                
                lista_final = df_unicos.to_dict(orient='records')
                duplicados_removidos = total_detectados - len(df_unicos)
                
                status.update(label=f"Auditoría finalizada en {time.time() - start_processing:.2f}s", state="complete")

            # --- DASHBOARD DE RESULTADOS ---
            st.markdown("### 📋 Informe de Validación")
            m1, m2, m3, m4 = st.columns(4)
            
            m1.metric("Leídos", f"{len(df_raw):,}")
            m2.metric("Válidos", f"{len(df_unicos):,}", delta="Listo")
            m3.metric("Omitidos", f"{registros_omitidos}", delta="Sin DNI", delta_color="inverse")
            m4.metric("Duplicados", f"{duplicados_removidos}", delta="Filtrados", delta_color="inverse")

            # --- VISTA PREVIA PROFESIONAL ---
            tab1, tab2 = st.tabs(["💎 Datos Listos", "⚠️ Reporte de Calidad"])
            
            with tab1:
                st.dataframe(df_unicos, use_container_width=True, height=300)
            
            with tab2:
                if duplicados_removidos > 0 or registros_omitidos > 0:
                    st.error(f"Se detectaron {duplicados_removidos} registros con DNI duplicado. El sistema priorizará el último registro encontrado.")
                else:
                    st.success("La calidad de los datos es óptima para la sincronización.")

            st.divider()

            # --- ACCIÓN DE SINCRONIZACIÓN ---
            col_btn1, col_btn2 = st.columns([2, 1])
            with col_btn1:
                st.info(f"Confirmar subida masiva de **{len(df_unicos)}** registros a la tabla 'clientes'.")
            
            with col_btn2:
                if st.button("🚀 INICIAR SINCRONIZACIÓN", use_container_width=True, type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    batch_size = 250
                    total = len(lista_final)
                    
                    try:
                        for i in range(0, total, batch_size):
                            batch = lista_final[i : i + batch_size]
                            supabase.table("clientes").upsert(batch).execute()
                            
                            current_prog = min((i + batch_size) / total, 1.0)
                            progress_bar.progress(current_prog)
                            status_text.code(f"Procesando lote: {min(i+batch_size, total)} de {total}...")
                        
                        st.balloons()
                        st.success("🎉 Sincronización finalizada con éxito.")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Error en comunicación: {str(e)}")

        except Exception as e:
            st.error(f"Error fatal en el motor: {e}")

if __name__ == "__main__":
    render()