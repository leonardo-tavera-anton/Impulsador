import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from utils.ui_components import draw_custom_metric, compact_currency, apply_plotly_theme

def render(df):
    st.markdown("<h1 class='sura-title'>INTELIGENCIA DE DATOS SURA</h1>", unsafe_allow_html=True)
    st.caption("Panel de Control Gerencial | Monitoreo en Tiempo Real | 2026")

    if df.empty:
        st.error("No se detectaron datos vinculados en Supabase.")
        return

    # --- 1. INDICADORES CLAVE (KPIs) ---
    total_monto = df['monto'].sum()
    total_deuda = df['deuda'].sum()
    mar_check = len(df[df.get('MAR') == '✅']) if 'MAR' in df.columns else 0
    efectividad = (mar_check / len(df) * 100) if len(df) > 0 else 0

    m_html = '<div class="metric-container">'
    m_html += draw_custom_metric("Capital Operativo", compact_currency(total_monto), f"{len(df):,} Activos", True)
    m_html += draw_custom_metric("Riesgo de Cartera", compact_currency(total_deuda), f"S/ {df['deuda'].mean():.0f} Prom.", False)
    m_html += draw_custom_metric("Efectividad Operativa", f"{efectividad:.1f}%", "Cumplimiento", efectividad > 85)
    m_html += '</div>'
    st.markdown(m_html, unsafe_allow_html=True)

    # --- FILA 1: VOLUMETRÍA Y COMPOSICIÓN ---
    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📊 1. Distribución de Capital (Donut)")
        # Gráfico 1: Distribución por monto
        fig1 = px.pie(df, names='estado', values='monto', hole=0.5,
                     color_discrete_sequence=px.colors.sequential.Greens_r)
        fig1.update_traces(textinfo='percent+label')
        st.plotly_chart(apply_plotly_theme(fig1), use_container_width=True)

    with c2:
        st.subheader("📂 2. Jerarquía de Activos (Treemap)")
        # Gráfico 2: Vista jerárquica de volumen
        fig2 = px.treemap(df, path=[px.Constant("SURA"), 'estado'], values='monto',
                         color='monto', color_continuous_scale='Greens')
        st.plotly_chart(apply_plotly_theme(fig2), use_container_width=True)

    # --- FILA 2: EFICIENCIA Y PIPELINE ---
    st.divider()
    c3, c4 = st.columns([1, 1.5])

    with c3:
        st.subheader("🎯 3. Meta de Efectividad (Gauge)")
        # Gráfico 3: Tacómetro de cumplimiento
        fig3 = go.Figure(go.Indicator(
            mode = "gauge+number", value = efectividad,
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#2ea043"}}
        ))
        st.plotly_chart(apply_plotly_theme(fig3), use_container_width=True)

    with c4:
        st.subheader("📈 4. Pareto de Operaciones (Impacto)")
        # Gráfico 4: Frecuencia por estado
        counts = df['estado'].value_counts().reset_index()
        counts.columns = ['Estado', 'Cant']
        fig4 = px.bar(counts, x='Estado', y='Cant', color='Cant', text_auto=True,
                     color_continuous_scale='Darkmint')
        st.plotly_chart(apply_plotly_theme(fig4), use_container_width=True)

    # --- FILA 3: RIESGO FINANCIERO ---
    st.divider()
    st.subheader("🔍 Análisis de Riesgo y Dispersión")
    c5, c6 = st.columns(2)

    with c5:
        st.subheader("💸 5. Correlación Monto vs Deuda (Scatter)")
        # Gráfico 5: Matriz de dispersión con tendencia
        df_sample = df.sample(min(1500, len(df)))
        fig5 = px.scatter(df_sample, x='monto', y='deuda', color='estado', size='deuda',
                         hover_data=['nombre'], opacity=0.6)
        st.plotly_chart(apply_plotly_theme(fig5), use_container_width=True)

    with c6:
        st.subheader("📉 6. Variabilidad de Cuotas (Box Plot)")
        # Gráfico 6: Dispersión estadística de cuotas
        fig6 = px.box(df, x='estado', y='cuota', color='estado',
                     notched=True, points="outliers")
        st.plotly_chart(apply_plotly_theme(fig6), use_container_width=True)

    # --- FILA 4: ESTADÍSTICA AVANZADA ---
    st.divider()
    c7, c8 = st.columns(2)

    with c7:
        st.subheader("📊 7. Densidad de Créditos (Histogram)")
        # Gráfico 7: Frecuencia de tamaños de crédito
        fig7 = px.histogram(df, x="monto", nbins=30, color_discrete_sequence=['#3fb950'])
        st.plotly_chart(apply_plotly_theme(fig7), use_container_width=True)

    with c8:
        st.subheader("📡 8. Embudo de Gestión (Funnel)")
        # Gráfico 8: Pipeline operativo
        fig8 = px.funnel(counts.head(5), x='Cant', y='Estado')
        st.plotly_chart(apply_plotly_theme(fig8), use_container_width=True)

    # --- FILA 5: RELACIONES Y TOTALES ---
    st.divider()
    c9, c10 = st.columns([1.5, 1])

    with c9:
        st.subheader("🌡️ 9. Mapa de Correlación (Heatmap)")
        # Gráfico 9: Relación entre variables numéricas
        corr = df[['monto', 'deuda', 'cuota']].corr()
        fig9 = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='Greens')
        st.plotly_chart(apply_plotly_theme(fig9), use_container_width=True)

    with c10:
        st.subheader("💰 10. Deuda Acumulada (Sunburst)")
        # Gráfico 10: Concentración de deuda
        fig10 = px.sunburst(df, path=['estado'], values='deuda',
                          color='deuda', color_continuous_scale='Reds')
        st.plotly_chart(apply_plotly_theme(fig10), use_container_width=True)

    st.markdown("---")
    st.caption("✅ Todos los indicadores han sido procesados bajo la arquitectura SURA v7.5.")