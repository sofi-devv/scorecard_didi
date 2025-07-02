import streamlit as st
import pandas as pd
from function import (
    limpiar_y_preparar_datos,
    generar_scorecard,
    formatear_reporte,
    METRICAS_ORDENADAS
)
import io

# --- Configuración de la página ---
st.set_page_config(page_title="Reporte de Marcas", layout="wide")
st.title("📊 Scorecard Semanal por Marca")

# --- INSTRUCCIONES PARA EL USUARIO ---
st.markdown("---")
st.subheader("Paso 1: Obtén tus datos del portal")

st.info(
    """
    Haz clic en el siguiente enlace para ir al portal de análisis de DiDi.
    Una vez allí, busca la opción para **exportar o descargar los datos como un archivo CSV o Excel.**
    """
)
st.markdown(
    "👉 **[Ir al Portal DPS de DiDi Food](https://dps-portal.intra.didiglobal.com/didifood?menuId=wM4lf-1EM&iframeRedirect=%2Fad_hoc_analysis%2Finsert.html%23%2F%3FcloneId%3D8675)**",
    unsafe_allow_html=True
)

st.warning("⚠️ **Importante:** Debes estar conectado a la red de DiDi o a la VPN para que el enlace funcione.")


# --- CARGA DE ARCHIVO ---
st.markdown("---")
st.subheader("Paso 2: Sube el archivo que descargaste")

uploaded_file = st.file_uploader(
    "📂 Arrastra o selecciona tu archivo (CSV o Excel)",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Formato de archivo no soportado. Por favor, sube un archivo CSV o Excel.")
            st.stop()

        # --- PROCESAMIENTO DE DATOS ---
        df_clean = limpiar_y_preparar_datos(df.copy())

        st.markdown("---")
        st.header("📊 Reporte por Marca Generado")
        
        reporte = generar_scorecard(df_clean, METRICAS_ORDENADAS, grouping_level='brand_name')
        
        # --- MOSTRAR RESULTADOS ---
        st.subheader("📋 Vista Previa del Reporte")
        reporte_con_estilo = formatear_reporte(reporte) # Guardamos el objeto con estilo en una variable
        st.dataframe(reporte_con_estilo, use_container_width=True, height=600)

        # --- Preparar archivo para descarga en Excel ---
        excel_buffer = io.BytesIO()

        ### CAMBIO CLAVE: Solución del error ###
        # Llamamos a .to_excel() directamente sobre el objeto Styler.
        # Esto es más simple y preserva los estilos (colores, barras) en el Excel.
        reporte_con_estilo.to_excel(
            excel_buffer, 
            engine='xlsxwriter', 
            index=False, 
            sheet_name='Reporte por Marca'
        )
        
        # --- BOTÓN DE DESCARGA ---
        st.markdown("---")
        st.download_button(
            label="📥 Descargar Reporte en Excel",
            data=excel_buffer,
            file_name="reporte_por_marca.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")
        st.warning("Asegúrate de que el archivo que subiste tiene las columnas esperadas (stat_date, brand_name, etc.).")