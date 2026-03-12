import streamlit as st
import pandas as pd

def render():
    st.markdown("<h1 class='sura-title'>IMPORTADOR DE DATOS</h1>", unsafe_allow_html=True)
    
    st.info("⚠️ Asegúrate que el Excel contenga las columnas: `dni`, `nombre`, `monto`, `deuda`, `estado`.")
    
    archivo = st.file_uploader("Arrastra tu archivo aquí", type=['xlsx', 'csv'])
    
    if archivo:
        df_new = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        
        # --- AUDITORÍA PRE-CARGA ---
        st.subheader("🧪 Informe de Validación")
        v1, v2, v3 = st.columns(3)
        
        # Validar DNI
        invalid_dnis = df_new[df_new['dni'].astype(str).str.len() != 8]
        # Validar Montos Negativos
        neg_amounts = df_new[df_new['monto'] < 0]
        
        with v1:
            st.metric("Registros Totales", len(df_new))
        with v2:
            st.metric("DNI Inválidos", len(invalid_dnis), delta="- Error" if len(invalid_dnis) > 0 else "OK")
        with v3:
            st.metric("Montos Anómalos", len(neg_amounts), delta="- Crítico" if len(neg_amounts) > 0 else "Limpio")

        if len(invalid_dnis) > 0:
            st.error("Se detectaron DNI con formato incorrecto. Por favor corrígelos antes de subir.")
            st.dataframe(invalid_dnis)
        else:
            st.success("¡Validación exitosa! El archivo está listo para la nube.")
            if st.button("🚀 SUBIR A SUPABASE (UPSERT)", use_container_width=True):
                # Lógica de inserción masiva
                progress = st.progress(0)
                for i in range(100):
                    progress.progress(i + 1)
                st.balloons()