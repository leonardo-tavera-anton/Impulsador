import streamlit as st
import pandas as pd
import plotly.express as px
import io

def render(df):
    # 1. ESTILO SURA
    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
            <h2 style='margin:0;'>📊 DASHBOARD: TENDENCIAS Y DESEMBOLSOS</h2>
            <p style='margin:0; opacity:0.8;'>Análisis operativo Nuevo Chimbote 2026 | Total Registros: {len(df):,}</p>
        </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No hay datos disponibles.")
        return

    # --- NUEVO: BOTÓN DE DESCARGA RÁPIDA ---
    # Creamos el Excel en memoria para no saturar el servidor
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte_SURA')
    
    st.download_button(
        label="📥 Descargar Base de Datos Actual (Excel)",
        data=buffer.getvalue(),
        file_name="padron_sura_2026.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    st.divider()

    # 2. COLUMNAS DINÁMICAS
    cols = {c.lower(): c for c in df.columns}
    col_monto = cols.get('monto', 'monto') 
    col_deuda = cols.get('deuda', 'deuda')
    col_estado = cols.get('estado', 'estado')

    # 3. FILTRO EFICIENTE
    mask_desembolsos = df[col_estado].astype(str).str.contains('desembol', case=False, na=False)
    df_desembolsos = df.loc[mask_desembolsos]

    # 4. MÉTRICAS
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Clientes", f"{len(df):,}")
    with m2:
        cartera_total = df[col_monto].sum()
        st.metric("Cartera Total", f"S/ {cartera_total:,.2f}")
    with m3:
        st.metric("Total Desembolsados", f"{len(df_desembolsos):,}")

    st.divider()

    # 5. ANÁLISIS DE TENDENCIAS
    st.subheader("🎯 Tendencias de Retiro (Desembolsos)")
    
    if not df_desembolsos.empty:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            fig_trend = px.histogram(
                df_desembolsos, x=col_monto, nbins=25, 
                color_discrete_sequence=['#10b981']
            )
            fig_trend.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                font_color="white", margin=dict(t=10, b=0, l=0, r=0)
            )
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
            
        with col_b:
            st.markdown("**Top Montos Frecuentes**")
            top_montos = df_desembolsos[col_monto].value_counts().head(8)
            for monto, cant in top_montos.items():
                st.write(f"💰 **S/ {monto:,.0f}**: {cant} personas")

    # 6. COMPARATIVA GENERAL
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Deuda vs Capital")
        total_deuda = df[col_deuda].sum()
        if cartera_total > 0:
            fig_pie = px.pie(
                names=['Capital Neto', 'Deuda'], 
                values=[max(0, cartera_total - total_deuda), total_deuda],
                hole=0.4, color_discrete_sequence=['#3b82f6', '#ef4444']
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center")
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    with g2:
        st.subheader("Resumen de Estados")
        estado_counts = df[col_estado].value_counts().head(10)
        if not estado_counts.empty:
            fig_estados = px.bar(
                x=estado_counts.index, y=estado_counts.values,
                color=estado_counts.values, color_continuous_scale='Blues'
            )
            fig_estados.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
                font_color="white", coloraxis_showscale=False
            )
            st.plotly_chart(fig_estados, use_container_width=True, config={'displayModeBar': False})