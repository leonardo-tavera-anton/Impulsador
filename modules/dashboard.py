import streamlit as st
import plotly.express as px
from utils.ui_components import draw_custom_metric, compact_currency, apply_plotly_theme

def render(df):
    st.markdown("<h1 class='sura-title'>DASHBOARD GLOBAL</h1>", unsafe_allow_html=True)
    
    if df.empty:
        st.warning("No hay datos para graficar.")
        return

    # --- MÉTRICAS SUPERIORES ---
    total_monto = df['monto'].sum()
    total_deuda = df['deuda'].sum()
    porcentaje_mora = (total_deuda / total_monto * 100) if total_monto > 0 else 0
    
    m_html = "<div class='metric-container'>"
    m_html += draw_custom_metric("Cartera Total", f"{len(df):,}", "Registros", True)
    m_html += draw_custom_metric("Capital en Red", compact_currency(total_monto), "Nominal", True)
    m_html += draw_custom_metric("Mora Proyectada", compact_currency(total_deuda), f"{porcentaje_mora:.1f}%", False)
    
    if 'MAR' in df.columns:
        efec_val = len(df[df['MAR'] == '✅'])
        porcentaje_efec = (efec_val / len(df)) * 100
        m_html += draw_custom_metric("Efectividad Marzo", f"{efec_val:,}", f"{porcentaje_efec:.1f}%", True)
    
    m_html += "</div>"
    st.markdown(m_html, unsafe_allow_html=True)

    # --- GRÁFICOS ---
    g1, g2 = st.columns([1.5, 1])
    
    with g1:
        st.subheader("📊 Distribución por Estados")
        fig_pie = px.pie(df, names='estado', values='monto', hole=0.6, 
                         color_discrete_sequence=px.colors.sequential.Greens_r)
        st.plotly_chart(apply_plotly_theme(fig_pie), use_container_width=True)
        
    with g2:
        st.subheader("📌 Resumen Operativo")
        resumen = df['estado'].value_counts().reset_index()
        st.dataframe(resumen, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📈 Inteligencia de Dispersión")
    df_sample = df.sample(min(3000, len(df)))
    fig_scatter = px.scatter(df_sample, x="monto", y="cuota", color="estado", size="deuda", opacity=0.7)
    st.plotly_chart(apply_plotly_theme(fig_scatter), use_container_width=True)