import streamlit as st
import pandas as pd

def render(df):
    st.markdown("<h1 class='sura-title'>AUDITORÍA DE DATOS</h1>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("No hay datos para auditar.")
        return

    col_a1, col_a2 = st.columns(2)
    
    # Detección de errores
    nulos_estado = df['estado'].replace("", pd.NA).isna().sum()
    duplicados = df.duplicated(subset=['dni']).sum()

    with col_a1:
        st.metric("Estados sin asignar", nulos_estado, delta="Revisar" if nulos_estado > 0 else "OK", delta_color="inverse")
    with col_a2:
        st.metric("DNI Duplicados", duplicados, delta="Conflicto" if duplicados > 0 else "Limpio", delta_color="inverse")

    st.divider()
    st.subheader("⚠️ Alertas de Negocio")
    
    # Regla: Deuda mayor al monto
    alerta_deuda = df[df['deuda'] > df['monto']]
    if not alerta_deuda.empty:
        st.error(f"Se encontraron {len(alerta_deuda)} registros donde la deuda supera al monto.")
        st.dataframe(alerta_deuda[['dni', 'nombre', 'monto', 'deuda']], use_container_width=True)
    else:
        st.success("No hay inconsistencias de deuda/monto.")