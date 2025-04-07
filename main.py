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
st.markdown("##### ¿Tienes alguna sugerencia? Contáctame en D-Chat: ptorresrodriguez_i@didiglobal.com")

st.markdown("""
### 🧠 ¿Qué hace esta app?

Esta herramienta te permite cargar un dataset crudo de tiendas y **automáticamente limpiarlo, organizarlo y transformarlo** en reportes semanales por marca (`all_brand`) y por tienda (`shop_name`). Los reportes incluyen:

- 🚚 Métricas clave de desempeño (órdenes, GMV, cancelaciones, tasas, etc.)
- 📈 Análisis de variación semana a semana (WoW)
- 📊 Comparación contra el promedio de las últimas 4 semanas (LW_vs_Avg_L4)
- 🔴 Alertas automáticas si más del 40% de las métricas bajaron

---

### 🪄 ¿Qué obtendrás?

- Un archivo procesado y limpio
- Dos reportes: uno por **marca** y otro por **tienda**
- Una versión **formateada** para Excel, lista para compartir
- Indicadores claros y visuales sobre desempeño

---

### 📌 ¿Cómo usarla? Paso a paso:

1. **Descarga tu dataset crudo** desde el portal de análisis ad-hoc:
   [🔗 Ir al Portal](https://dps-portal.intra.didiglobal.com/didifood?menuId=wM4lf-1EM&iframeRedirect=%2Fad_hoc_analysis%2Finsert.html%23%2F%3FcloneId%3D6657)

2. **Carga el archivo .csv** en esta app.

3. Espera unos segundos mientras procesamos los datos.

4. Visualiza y descarga los reportes generados:

   - Reporte por `shop_name`
   - Reporte por `all_brand`
   - Versión formateada para Excel

---

""")


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
        'Completion rate', 'ticket_promedio', 'B-cancel rate', 'r_burn', 'b2c_total', 'p2c_total', 'online rate %', 'order_price'
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