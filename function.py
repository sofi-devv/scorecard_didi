import pandas as pd
import numpy as np

def limpiar_dataset(df):
    df.replace('-', 0, inplace=True)
    df.columns = [col.upper() if col.lower() == 'gmv' else col for col in df.columns]
    
    if 'GMV' in df.columns:
        df['GMV'] = df['GMV'].replace(',', '', regex=True)
        df['GMV'] = pd.to_numeric(df['GMV'], errors='coerce').fillna(0)
    else:
        df['GMV'] = 0

    def asignar_all_brand(brand):
        if brand in ["Plass Nueva Botella CO", "Plass Smoke & Vape Grocery_CO"]:
            return "Plass"
        elif brand in [
            "Cencosud(Jumbo) Grocery_CO", "Cencosud(Metro) Grocery_CO",
            "Cencosud(Jumbo Express) Grocery_CO", "Cencosud(EASY) Grocery_CO"
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
        elif brand == "Home Sentry Grocery_CO":
            return "Home Sentry"
        else:
            return brand

    df['all_brand'] = df['brand_name'].apply(asignar_all_brand)

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
        'b2c_total': 'b2c_total',
        'order_price': 'order_price',
    }
    df.rename(columns=columnas_renombrar, inplace=True)

    columnas_numericas = [
        'p2c_total', 'r_burn', 'pay_order_cnt', 'complete_order_cnt',
        'b_duty_cancel_order_cnt', 'b2c_total', 'order_price'
    ]
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = df[col].replace(',', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['pay_order_cnt'] = pd.to_numeric(df['pay_order_cnt'], errors='coerce').fillna(0)
    df['Online Store'] = pd.to_numeric(df['Online Store'], errors='coerce').fillna(0)
    df['Active Stores'] = ((df['Online Store'].astype(int) == 1) & (df['pay_order_cnt'] > 1)).astype(int)

    df['stat_date'] = pd.to_datetime(df['stat_date'], errors='coerce')
    df['week_number'] = df['stat_date'].dt.isocalendar().week

    return df

def formatear_reporte_excel(df):
    df_formateado = df.copy()
    columnas_pesos = ['GMV', 'ticket_promedio', 'order_price']
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

    for col in ['WoW', 'LW_vs_Avg_L4']:
        if col in df_formateado.columns:
            df_formateado[col] = df_formateado[col].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else x)

    return df_formateado

def generar_reporte_all_brand_final(df):
    df = df.copy()

    for col in ['pay_order_cnt', 'complete_order_cnt', 'b_duty_cancel_order_cnt',
                'cancel_order_cnt', 'r_burn', 'b2c_total', 'p2c_total', 'GMV', 'order_price']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['Online Store'] = pd.to_numeric(df['Online Store'], errors='coerce').fillna(0)
    df['Online Connection Rate'] = pd.to_numeric(df['Online Connection Rate'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)

    metrics = []

    online = df[df['Online Store'] > 0].groupby(['all_brand', 'week_number'])['shop_name'].nunique().reset_index(name='Value')
    online['Metric'] = 'Online Store'
    metrics.append(online)

    active = df[df['pay_order_cnt'] > 0].groupby(['all_brand', 'week_number'])['shop_name'].nunique().reset_index(name='Value')
    active['Metric'] = 'Active Stores'
    metrics.append(active)

    agregaciones = {
        'GMV': 'sum',
        'complete_order_cnt': 'sum',
        'pay_order_cnt': 'sum',
        'b_duty_cancel_order_cnt': 'sum',
        'cancel_order_cnt': 'sum',
        'r_burn': 'sum',
        'b2c_total': 'sum',
        'p2c_total': 'sum',
        'Online Connection Rate': 'mean',
        'order_price': 'sum'
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
        'ticket_promedio', 'B-cancel rate', 'r_burn', 'b2c_total',
        'p2c_total', 'online rate %', 'order_price'
    ]

    for metric in metricas_extra:
        if isinstance(metric, str) and metric.strip() in base.columns:
            temp = base[['all_brand', 'week_number', metric.strip()]].copy()
            temp = temp.rename(columns={metric.strip(): 'Value'})
            if not temp['Value'].isnull().all():
                temp['Metric'] = metric.strip()
                metrics.append(temp)

    full = pd.concat(metrics, ignore_index=True)
    df_pivot = full.pivot_table(index=['all_brand', 'Metric'], columns='week_number', values='Value').reset_index()

    semana_cols = sorted([col for col in df_pivot.columns if isinstance(col, int)])
    if len(semana_cols) >= 2:
        penultima, ultima = semana_cols[-2], semana_cols[-1]
        df_pivot['WoW'] = ((df_pivot[ultima] - df_pivot[penultima]) / df_pivot[penultima]) * 100
    else:
        df_pivot['WoW'] = np.nan

    if len(semana_cols) >= 4:
        df_pivot['LW_vs_Avg_L4'] = ((df_pivot[semana_cols[-1]] - df_pivot[semana_cols[-4:]].mean(axis=1)) / df_pivot[semana_cols[-4:]].mean(axis=1)) * 100
    else:
        df_pivot['LW_vs_Avg_L4'] = np.nan

    gmv_wow = df_pivot[df_pivot['Metric'] == 'GMV']
    alerta_dict = gmv_wow.set_index('shop_name')['WoW'] < 0
    df_pivot['Attention'] = df_pivot['shop_name'].map(lambda x: '🔴 Attention!' if alerta_dict.get(x, False) else '')

    return df_pivot

def generar_reporte_shop_name_final(df):
    df = df.copy()

    for col in ['pay_order_cnt', 'complete_order_cnt', 'b_duty_cancel_order_cnt',
                'cancel_order_cnt', 'r_burn', 'b2c_total', 'p2c_total', 'GMV', 'order_price']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['Online Store'] = pd.to_numeric(df['Online Store'], errors='coerce').fillna(0)
    df['Online Connection Rate'] = pd.to_numeric(df['Online Connection Rate'].astype(str).str.replace('%', ''), errors='coerce').fillna(0)

    metrics = []

    online = df[df['Online Store'] > 0].groupby(['shop_name', 'brand_name', 'week_number'])['shop_name'].nunique().reset_index(name='Value')
    online['Metric'] = 'Online Store'
    metrics.append(online)

    active = df[df['pay_order_cnt'] > 0].groupby(['shop_name', 'brand_name', 'week_number'])['shop_name'].nunique().reset_index(name='Value')
    active['Metric'] = 'Active Stores'
    metrics.append(active)

    agg = df.groupby(['shop_name', 'brand_name', 'week_number']).agg({
        'GMV': 'sum',
        'complete_order_cnt': 'sum',
        'pay_order_cnt': 'sum',
        'b_duty_cancel_order_cnt': 'sum',
        'cancel_order_cnt': 'sum',
        'r_burn': 'sum',
        'b2c_total': 'sum',
        'p2c_total': 'sum',
        'Online Connection Rate': 'mean',
        'order_price': 'sum'
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
        'ticket_promedio', 'B-cancel rate', 'r_burn', 'b2c_total',
        'p2c_total', 'online rate %', 'order_price'
    ]

    for metric in metricas_extra:
        if isinstance(metric, str) and metric.strip() in agg.columns:
            temp = agg[['shop_name', 'brand_name', 'week_number', metric.strip()]].copy()
            temp = temp.rename(columns={metric.strip(): 'Value'})
            if not temp['Value'].isnull().all():
                temp['Metric'] = metric.strip()
                metrics.append(temp)

    full = pd.concat(metrics, ignore_index=True)
    df_pivot = full.pivot_table(index=['shop_name', 'brand_name', 'Metric'], columns='week_number', values='Value').reset_index()

    semana_cols = sorted([col for col in df_pivot.columns if isinstance(col, int)])
    if len(semana_cols) >= 2:
        penultima, ultima = semana_cols[-2], semana_cols[-1]
        df_pivot['WoW'] = ((df_pivot[ultima] - df_pivot[penultima]) / df_pivot[penultima]) * 100
    else:
        df_pivot['WoW'] = np.nan

    if len(semana_cols) >= 4:
        df_pivot['LW_vs_Avg_L4'] = ((df_pivot[semana_cols[-1]] - df_pivot[semana_cols[-4:]].mean(axis=1)) / df_pivot[semana_cols[-4:]].mean(axis=1)) * 100
    else:
        df_pivot['LW_vs_Avg_L4'] = np.nan

    gmv_wow = df_pivot[df_pivot['Metric'] == 'GMV']
    alerta_dict = gmv_wow.set_index('shop_name')['WoW'] < 0
    df_pivot['Attention'] = df_pivot['shop_name'].map(lambda x: '🔴 Attention!' if alerta_dict.get(x, False) else '')

    return df_pivot
