import streamlit as st
import pandas as pd
import plotly.express as px

def render(df):
    # 1. ESTILO SURA
    st.markdown("""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
            <h2 style='margin:0;'>📊 DASHBOARD: TENDENCIAS Y DESEMBOLSOS</h2>
            <p style='margin:0; opacity:0.8;'>Análisis operativo Nuevo Chimbote 2026</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. SINCRONIZACIÓN DE COLUMNAS
    col_monto = 'Monto' if 'Monto' in df.columns else 'monto'
    col_deuda = 'deuda' if 'deuda' in df.columns else 'DEUDA'
    col_estado = 'estado' if 'estado' in df.columns else 'ESTADO'

    # Asegurar que los montos sean numéricos
    df[col_monto] = pd.to_numeric(df[col_monto], errors='coerce').fillna(0)
    df[col_deuda] = pd.to_numeric(df[col_deuda], errors='coerce').fillna(0)

    # 3. FILTRO DE DESEMBOLSOS (Tu solicitud específica)
    # Filtramos filas que contengan "desembol" en su etiqueta de estado
    df_desembolsos = df[df[col_estado].astype(str).str.contains('desembol', case=False, na=False)]

    # 4. MÉTRICAS SUPERIORES
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Clientes", f"{len(df):,}")
    with m2:
        st.metric("Cartera Total", f"S/ {df[col_monto].sum():,.0f}")
    with m3:
        st.metric("Total Desembolsados", f"{len(df_desembolsos):,}")

    st.divider()

    # 5. ANÁLISIS DE TENDENCIAS (MONTOS QUE MÁS RETIRAN)
    st.subheader("🎯 Tendencias de Retiro (Desembolsos)")
    
    if not df_desembolsos.empty:
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            # Gráfico de barras de los montos más frecuentes en desembolsos
            # Agrupamos por rangos para detectar esos de "20 mil y tanto"
            fig_trend = px.histogram(
                df_desembolsos, 
                x=col_monto, 
                nbins=15,
                title="Distribución de Montos Desembolsados",
                labels={col_monto: 'Monto del Retiro'},
                color_discrete_sequence=['#10b981']
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with col_b:
            st.markdown("**Top Montos Frecuentes**")
            # Mostramos los montos que más se repiten en desembolsos
            top_montos = df_desembolsos[col_monto].value_counts().head(5)
            for monto, cant in top_montos.items():
                st.write(f"💰 **S/ {monto:,.0f}**: {cant} personas")
    else:
        st.warning("No se encontraron registros con la etiqueta 'desembolso'.")

    st.divider()

    # 6. COMPARATIVA GENERAL
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Deuda vs Capital")
        fig_pie = px.pie(
            names=['Monto Neto', 'Deuda'], 
            values=[df[col_monto].sum() - df[col_deuda].sum(), df[col_deuda].sum()],
            hole=0.4,
            color_discrete_sequence=['#3b82f6', '#ef4444']
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        st.subheader("Resumen de Estados")
        # Verificamos qué etiquetas son las más comunes
        estado_counts = df[col_estado].value_counts().head(6)
        fig_estados = px.bar(
            x=estado_counts.index, 
            y=estado_counts.values,
            labels={'x': 'Etiqueta', 'y': 'Cantidad'},
            color=estado_counts.values,
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_estados, use_container_width=True)