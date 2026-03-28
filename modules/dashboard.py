import streamlit as st
import pandas as pd
import plotly.express as px

def render(df):
    # 1. ESTILO SURA (Tu diseño original)
    st.markdown("""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:20px; border-radius:12px; color:white; margin-bottom:20px;">
            <h2 style='margin:0;'>📊 DASHBOARD: TENDENCIAS Y DESEMBOLSOS</h2>
            <p style='margin:0; opacity:0.8;'>Análisis operativo Nuevo Chimbote 2026</p>
        </div>
    """, unsafe_allow_html=True)

    # Si el dataframe viene vacío, abortamos para evitar más errores
    if df.empty:
        st.warning("No hay datos disponibles para mostrar en el Dashboard.")
        return

    # 2. SINCRONIZACIÓN DINÁMICA DE COLUMNAS (Solución al KeyError)
    # Buscamos las columnas ignorando mayúsculas/minúsculas
    cols = {c.lower(): c for c in df.columns}
    
    col_monto = cols.get('monto', df.columns[0]) # Si no existe 'monto', toma la primera columna por defecto
    col_deuda = cols.get('deuda', df.columns[0])
    col_estado = cols.get('estado', df.columns[0])

    # 3. LIMPIEZA DE DATOS SEGURA
    # Usamos .copy() para no afectar el dataframe original de otros módulos
    df_clean = df.copy()
    
    try:
        df_clean[col_monto] = pd.to_numeric(df_clean[col_monto], errors='coerce').fillna(0)
        df_clean[col_deuda] = pd.to_numeric(df_clean[col_deuda], errors='coerce').fillna(0)
    except Exception as e:
        st.error(f"Error al procesar valores numéricos: {e}")

    # 4. FILTRO DE DESEMBOLSOS
    # Buscamos cualquier estado que contenga "desembol"
    df_desembolsos = df_clean[df_clean[col_estado].astype(str).str.contains('desembol', case=False, na=False)]

    # 5. MÉTRICAS SUPERIORES
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Clientes", f"{len(df_clean):,}")
    with m2:
        st.metric("Cartera Total", f"S/ {df_clean[col_monto].sum():,.2f}")
    with m3:
        st.metric("Total Desembolsados", f"{len(df_desembolsos):,}")

    st.divider()

    # 6. ANÁLISIS DE TENDENCIAS
    st.subheader("🎯 Tendencias de Retiro (Desembolsos)")
    
    if not df_desembolsos.empty:
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            fig_trend = px.histogram(
                df_desembolsos, 
                x=col_monto, 
                nbins=15,
                title="Distribución de Montos Desembolsados",
                labels={col_monto: 'Monto del Retiro'},
                color_discrete_sequence=['#10b981']
            )
            fig_trend.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with col_b:
            st.markdown("**Top Montos Frecuentes**")
            top_montos = df_desembolsos[col_monto].value_counts().head(5)
            for monto, cant in top_montos.items():
                st.write(f"💰 **S/ {monto:,.0f}**: {cant} personas")
    else:
        st.info("No se detectaron registros con estados de 'Desembolso' para el análisis de tendencias.")

    st.divider()

    # 7. COMPARATIVA GENERAL
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Deuda vs Capital")
        total_monto = df_clean[col_monto].sum()
        total_deuda = df_clean[col_deuda].sum()
        
        # Evitar división por cero en el gráfico
        if total_monto > 0:
            fig_pie = px.pie(
                names=['Capital Neto', 'Deuda'], 
                values=[max(0, total_monto - total_deuda), total_deuda],
                hole=0.4,
                color_discrete_sequence=['#3b82f6', '#ef4444']
            )
            fig_pie.update_layout(showlegend=True, paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("Sin datos de capital.")

    with g2:
        st.subheader("Resumen de Estados")
        estado_counts = df_clean[col_estado].value_counts().head(6)
        if not estado_counts.empty:
            fig_estados = px.bar(
                x=estado_counts.index, 
                y=estado_counts.values,
                labels={'x': 'Etiqueta', 'y': 'Cantidad'},
                color=estado_counts.values,
                color_continuous_scale='Blues'
            )
            fig_estados.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_estados, use_container_width=True)