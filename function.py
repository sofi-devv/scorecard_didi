import io
import pandas as pd

def limpiar_dataset(df):
    import pandas as pd

    # 1. Reemplazar '-' por 0
    df.replace('-', 0, inplace=True)

    # 2. Normalizar nombre de columna GMV si está en minúscula
    df.columns = [col.upper() if col.lower() == 'gmv' else col for col in df.columns]
    if 'GMV' in df.columns:
        df['GMV'] = df['GMV'].replace(',', '', regex=True)
        df['GMV'] = pd.to_numeric(df['GMV'], errors='coerce').fillna(0)
    else:
        df['GMV'] = 0  # Crear columna si no existe

    # 3. Asignar columna 'all_brand'
    def asignar_all_brand(brand):
        if brand in ["Plass Nueva Botella CO", "Plass Smoke & Vape Grocery_CO"]:
            return "Plass"
        elif brand in [
            "Cencosud(Jumbo) Grocery_CO", 
            "Cencosud(Metro) Grocery_CO", 
            "Cencosud(Jumbo Express) Grocery_CO", 
            "Cencosud(EASY) Grocery_CO"
        ]:
            return "Cencosud"
        elif brand == "Euro Supermercados Grocery_CO":
            return "Euro"
        elif brand == "Mercado Zapatoca Grocery_CO":
            return "Zapatoca"
        elif brand == "Coopidrogas (FarmaExpress) Grocery_CO":
            return "Coopidrogas"
        elif brand == "Olimpica Grocery_CO":
            return "Olimpica"
        elif brand == "La Vaquita Grocery_CO":
            return "La Vaquita"
        else:
            return None

    df['all_brand'] = df['brand_name'].apply(asignar_all_brand)

    # 4. Renombrar columnas
    columnas_renombrar = {
        'is_online': 'Online Store',
        'p2c_total': 'p2c_total',
        'r_burn': 'r_burn',
        'pay_order_cnt': 'pay_order_cnt',
        'complete_order_cnt': 'complete_order_cnt',
        'Completion Rate': 'Completion Rate',
        '__Online Connection Rate': 'Online Connection Rate',
        'is_effective_online1': 'is_effective_online1',
        '__Item Pic Coverage%': 'Item Pic Coverage%',
        'b_duty_cancel_order_cnt': 'b_duty_cancel_order_cnt',
        'b2c_total': 'b2c_total'
    }
    df.rename(columns=columnas_renombrar, inplace=True)

    # 5. Asegurar tipos numéricos (las que sí estén)
    for col in ['p2c_total', 'r_burn', 'pay_order_cnt', 'complete_order_cnt', 'b_duty_cancel_order_cnt', 'b2c_total']:
        if col in df.columns:
            df[col] = df[col].replace(',', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 6. Crear columna 'Active Stores': online y con más de una orden
    df['pay_order_cnt'] = pd.to_numeric(df['pay_order_cnt'], errors='coerce').fillna(0)
    df['Online Store'] = pd.to_numeric(df['Online Store'], errors='coerce').fillna(0)
    df['Active Stores'] = ((df['Online Store'].astype(int) == 1) & (df['pay_order_cnt'] > 1)).astype(int)

    # 7. Convertir fecha y extraer semana
    df['stat_date'] = pd.to_datetime(df['stat_date'])
    df['week_number'] = df['stat_date'].dt.isocalendar().week

    return df


def generar_reporte_shop_name_final(df):
    import pandas as pd
    import numpy as np

    df = df.copy()

    # Asegurar tipos numéricos
    for col in ['pay_order_cnt', 'complete_order_cnt', 'b_duty_cancel_order_cnt',
                'cancel_order_cnt', 'r_burn', 'b2c_total', 'p2c_total', 'GMV']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['Online Store'] = pd.to_numeric(df['Online Store'], errors='coerce').fillna(0)
    df['Online Connection Rate'] = pd.to_numeric(df['Online Connection Rate'].str.replace('%', ''), errors='coerce').fillna(0)

    metrics = []

    # Online Store: tiendas online
    online = df[df['Online Store'] > 0].groupby(['shop_name', 'brand_name', 'week_number'])['shop_name'] \
                .nunique().reset_index(name='Value')
    online['Metric'] = 'Online Store'
    metrics.append(online)

    # Active Stores: tiendas con al menos una orden
    active = df[df['pay_order_cnt'] > 0].groupby(['shop_name', 'brand_name', 'week_number'])['shop_name'] \
                .nunique().reset_index(name='Value')
    active['Metric'] = 'Active Stores'
    metrics.append(active)

    # Otras métricas
    agg = df.groupby(['shop_name', 'brand_name', 'week_number']).agg({
        'GMV': 'sum',
        'complete_order_cnt': 'sum',
        'pay_order_cnt': 'sum',
        'b_duty_cancel_order_cnt': 'sum',
        'cancel_order_cnt': 'sum',
        'r_burn': 'sum',
        'b2c_total': 'sum',
        'p2c_total': 'sum',
        'Online Connection Rate': 'mean'
    }).reset_index()

    agg['Completion rate'] = agg['complete_order_cnt'] / agg['pay_order_cnt'].replace(0, np.nan)
    agg['ticket_promedio'] = agg['GMV'] / agg['complete_order_cnt'].replace(0, np.nan)
    agg['B-cancel rate'] = agg['b_duty_cancel_order_cnt'] / agg['cancel_order_cnt'].replace(0, np.nan)
    agg['r_burn'] = agg['r_burn'] / agg['GMV'].replace(0, np.nan)
    agg['b2c_total'] = agg['b2c_total'] / agg['GMV'].replace(0, np.nan)
    agg['p2c_total'] = agg['p2c_total'] / agg['GMV'].replace(0, np.nan)
    agg['online rate %'] = agg['Online Connection Rate'] / 100

    metricas_extra = [
        'GMV', 'complete_order_cnt', 'pay_order_cnt', 'Completion rate',
        'ticket_promedio', 'B-cancel rate', 'r_burn', 'b2c_total', 'p2c_total', 'online rate %'
    ]

    for metric in metricas_extra:
        temp = agg[['shop_name', 'brand_name', 'week_number', metric]].copy()
        temp.rename(columns={metric: 'Value'}, inplace=True)
        temp['Metric'] = metric
        metrics.append(temp)

    # Unir y pivotear
    full = pd.concat(metrics, ignore_index=True)
    df_pivot = full.pivot_table(index=['shop_name', 'brand_name', 'Metric'], columns='week_number', values='Value').reset_index()

    # Calcular WoW y LW_vs_Avg_L4
    semana_cols = sorted([col for col in df_pivot.columns if isinstance(col, int)])
    penultima, ultima = semana_cols[-2], semana_cols[-1]
    df_pivot['WoW'] = ((df_pivot[ultima] - df_pivot[penultima]) / df_pivot[penultima]) * 100
    df_pivot['LW_vs_Avg_L4'] = ((df_pivot[ultima] - df_pivot[semana_cols[:-1]].mean(axis=1)) / df_pivot[semana_cols[:-1]].mean(axis=1)) * 100

    # Alerta por tienda si más del 40% de métricas tienen WoW negativa
    alerta_dict = df_pivot.groupby('shop_name')['WoW'].apply(lambda x: (x < 0).mean() > 0.4).to_dict()
    df_pivot['Attention'] = df_pivot['shop_name'].map(lambda x: '🔴 Attention!' if alerta_dict.get(x, False) else '')

    return df_pivot


def generar_reporte_all_brand_final(df):
    import pandas as pd
    import numpy as np

    df = df.copy()

    # Asegurar tipos numéricos
    for col in ['pay_order_cnt', 'complete_order_cnt', 'b_duty_cancel_order_cnt',
                'cancel_order_cnt', 'r_burn', 'b2c_total', 'p2c_total', 'GMV']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['Online Store'] = pd.to_numeric(df['Online Store'], errors='coerce').fillna(0)
    df['Online Connection Rate'] = pd.to_numeric(df['Online Connection Rate'].str.replace('%', ''), errors='coerce').fillna(0)

    metrics = []

    # Online Store = cantidad de tiendas online activas por semana
    online = df[df['Online Store'] > 0].groupby(['all_brand', 'week_number'])['shop_name'].nunique().reset_index(name='Value')
    online['Metric'] = 'Online Store'
    metrics.append(online)

    # Active Stores = cantidad de tiendas activas con al menos una orden por semana
    active = df[df['pay_order_cnt'] > 0].groupby(['all_brand', 'week_number'])['shop_name'].nunique().reset_index(name='Value')
    active['Metric'] = 'Active Stores'
    metrics.append(active)

    # Métricas con suma o promedio
    agregaciones = {
        'GMV': 'sum',
        'complete_order_cnt': 'sum',
        'pay_order_cnt': 'sum',
        'b_duty_cancel_order_cnt': 'sum',
        'cancel_order_cnt': 'sum',
        'r_burn': 'sum',
        'b2c_total': 'sum',
        'p2c_total': 'sum',
        'Online Connection Rate': 'mean'
    }
    base = df.groupby(['all_brand', 'week_number']).agg(agregaciones).reset_index()

    base['Completion rate'] = base['complete_order_cnt'] / base['pay_order_cnt'].replace(0, np.nan)
    base['ticket_promedio'] = base['GMV'] / base['complete_order_cnt'].replace(0, np.nan)
    base['B-cancel rate'] = base['b_duty_cancel_order_cnt'] / base['cancel_order_cnt'].replace(0, np.nan)
    base['r_burn'] = base['r_burn'] / base['GMV'].replace(0, np.nan)
    base['b2c_total'] = base['b2c_total'] / base['GMV'].replace(0, np.nan)
    base['p2c_total'] = base['p2c_total'] / base['GMV'].replace(0, np.nan)
    base['online rate %'] = base['Online Connection Rate'] / 100

    metricas_extra = [
        'GMV', 'complete_order_cnt', 'pay_order_cnt', 'Completion rate',
        'ticket_promedio', 'B-cancel rate', 'r_burn', 'b2c_total', 'p2c_total', 'online rate %'
    ]

    for metric in metricas_extra:
        temp = base[['all_brand', 'week_number', metric]].copy()
        temp.rename(columns={metric: 'Value'}, inplace=True)
        temp['Metric'] = metric
        metrics.append(temp)

    # Unir y pivotear
    full = pd.concat(metrics, ignore_index=True)
    df_pivot = full.pivot_table(index=['all_brand', 'Metric'], columns='week_number', values='Value').reset_index()

    # Calcular WoW y LW_vs_Avg_L4
    semana_cols = sorted([col for col in df_pivot.columns if isinstance(col, int)])
    penultima, ultima = semana_cols[-2], semana_cols[-1]
    df_pivot['WoW'] = ((df_pivot[ultima] - df_pivot[penultima]) / df_pivot[penultima]) * 100
    df_pivot['LW_vs_Avg_L4'] = ((df_pivot[ultima] - df_pivot[semana_cols[:-1]].mean(axis=1)) / df_pivot[semana_cols[:-1]].mean(axis=1)) * 100

    # Alerta si más del 40% de métricas tienen WoW negativa por marca
    alerta_dict = df_pivot.groupby('all_brand')['WoW'].apply(lambda x: (x < 0).mean() > 0.4).to_dict()
    df_pivot['Attention'] = df_pivot['all_brand'].map(lambda x: '🔴 Attention!' if alerta_dict.get(x, False) else '')

    return df_pivot



def formatear_reporte_excel(df):
    df_formateado = df.copy()

    columnas_pesos = ['GMV', 'ticket_promedio']
    columnas_porcentaje = ['Completion rate', 'B-cancel rate', 'r_burn', 'b2c_total', 'p2c_total', 'online rate %', 'WoW', 'LW_vs_Avg_L4']

    for idx, row in df_formateado.iterrows():
        metric = row['Metric']
        for col in df_formateado.columns:
            if isinstance(col, int):
                val = df_formateado.at[idx, col]
                if pd.notnull(val):
                    if metric in columnas_pesos:
                        df_formateado.at[idx, col] = f"${val:,.0f}"
                    elif metric in columnas_porcentaje:
                        df_formateado.at[idx, col] = f"{val * 100:.1f}%"

    # Formato para columnas extra
    for col in ['WoW', 'LW_vs_Avg_L4']:
        if col in df_formateado.columns:
            df_formateado[col] = df_formateado[col].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else x)

    return df_formateado
