# main.py
import streamlit as st
import pandas as pd
from function import (
    # CAMBIO 1: Importamos las nuevas funciones y la lista de métricas
    limpiar_y_preparar_datos,
    generar_scorecard,
    formatear_reporte,
    METRICAS_ORDENADAS
)
import io

# --- Configuración de la página (sin cambios) ---
st.set_page_config(page_title="Reporte de Tiendas", layout="wide")
st.title("📊 Scorecard Semanal de Tiendas")

# --- Carga de Archivo ---
uploaded_file = st.file_uploader("📂 Carga tu archivo CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        
        # --- Procesamiento de Datos ---
        # CAMBIO 2: Usamos el nuevo nombre de la función de limpieza
        df_clean = limpiar_y_preparar_datos(df.copy())

        st.markdown("---")
        st.header("📊 Generar Reporte Semanal")
        
        tipo_reporte = st.radio(
            "Selecciona el nivel de agregación:", 
            ["Por Marca (brand_name)", "Por Tienda (shop_name)"]
        )

        # CAMBIO 3: Usamos la función 'generar_scorecard' para ambos casos
        if tipo_reporte == "Por Marca (brand_name)":
            reporte = generar_scorecard(df_clean, METRICAS_ORDENADAS, grouping_level='brand_name')
        else:
            reporte = generar_scorecard(df_clean, METRICAS_ORDENADAS, grouping_level='shop_name')

        # CAMBIO 4: Se ELIMINA el código de ordenamiento manual.
        # La función 'generar_scorecard' ya se encarga del ordenamiento y la estructura.
        # Esto hace que el main.py sea mucho más limpio.

        # --- Mostrar Resultados ---
        st.subheader("📋 Vista Previa del Reporte")
        # CAMBIO 5: Usamos la nueva función de formato
        st.dataframe(formatear_reporte(reporte), use_container_width=True, height=600)

        # Preparar archivo para descarga
        excel_buffer = io.BytesIO()
        # CAMBIO 6: Usamos la función de formato también para el Excel
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            formatear_reporte(reporte).to_excel(writer, index=False, sheet_name='Reporte')
        excel_buffer.seek(0)

        # --- Botón de Descarga ---
        st.markdown("---")
        st.download_button(
            label="📥 Descargar Reporte en Excel",
            data=excel_buffer,
            file_name="reporte_tiendas_formateado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
        st.warning("Asegúrate de que el archivo CSV tiene las columnas esperadas (stat_date, brand_name, etc.).")