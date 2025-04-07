# main.py
import streamlit as st
import pandas as pd
from function import (
    limpiar_dataset,
    generar_reporte_all_brand_final,
    generar_reporte_shop_name_final,
    formatear_reporte_excel
)
import io

st.set_page_config(page_title="Reporte de Tiendas", layout="wide")
st.title("📊 Limpieza y Reporte de Tiendas")

st.markdown("""
👩‍💻 Genera tu dataset aquí:  
[🔗 Ir al Portal](https://dps-portal.intra.didiglobal.com/didifood?menuId=wM4lf-1EM&iframeRedirect=%2Fad_hoc_analysis%2Finsert.html%23%2F%3FcloneId%3D6657)
""")

uploaded_file = st.file_uploader("📂 Carga tu archivo Excel o CSV", type=["xlsx", "csv"])

if uploaded_file:
    file_type = uploaded_file.name.split('.')[-1]
    df = pd.read_excel(uploaded_file) if file_type == 'xlsx' else pd.read_csv(uploaded_file)


    df_clean = limpiar_dataset(df)

    # Selección de tipo de reporte
    st.markdown("---")
    st.header("📊 Reportes Semanales")
    tipo_reporte = st.radio("Selecciona el tipo de reporte:", ["Por Marca (all_brand)", "Por Tienda (shop_name)"])

    if tipo_reporte == "Por Marca (all_brand)":
        reporte = generar_reporte_all_brand_final(df_clean)
    else:
        reporte = generar_reporte_shop_name_final(df_clean)

# Reordenar métricas en el orden solicitado
    orden_metricas = [
        'Online Store', 'Active Stores', 'GMV', 'complete_order_cnt', 'pay_order_cnt',
        'Completion rate', 'ticket_promedio', 'B-cancel rate', 'r_burn', 'b2c_total', 'p2c_total', 'online rate %'
    ]
    reporte['Metric'] = pd.Categorical(reporte['Metric'], categories=orden_metricas, ordered=True)
    reporte = reporte.sort_values(['shop_name' if 'shop_name' in reporte.columns else 'all_brand', 'Metric'])

    # Mostrar resultados
    st.subheader("📋 Resultado del Reporte")
    st.dataframe(formatear_reporte_excel(reporte), use_container_width=True)

    # Guardar como Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        formatear_reporte_excel(reporte).to_excel(writer, index=False, sheet_name='Reporte')

    excel_buffer.seek(0)

    # Botón de descarga
    st.markdown("---")
    st.subheader("📥 Descargar Reporte")
    st.download_button(
        label="📥 Descargar como Excel",
        data=excel_buffer,
        file_name="reporte_tiendas_formateado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )