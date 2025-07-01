import pandas as pd
import numpy as np

METRICAS_ORDENADAS = [
    'Signed stores', 'Online Store', 'Active Stores', 'GMV', 'Real pay price',
    'Complete_order_cnt', 'Pay_order_cnt', 'Ticket_promedio', 'Completion rate',
    'B-cancel rate', 'C Cancel Rate', 'D Cancel Rate', 'P Cancel Rate', 'r_burn',
    'b2c_total', 'p2c_total', 'Online Connection Rate'
]

def limpiar_y_preparar_datos(df):
    """
    Limpia el DataFrame inicial.
    CAMBIO: Se elimina el cálculo de 'Active Stores', ya que ahora se hace en la agregación.
    """
    df = df.copy()
    df.replace('-', 0, inplace=True)

    columnas_renombrar = {
        'is_online': 'Online Store',
        '__Online Connection Rate': 'Online Connection Rate',
        'gmv': 'GMV',
        'pay_order_cnt': 'Pay_order_cnt',
        'complete_order_cnt': 'Complete_order_cnt',
        'order_price': 'Real pay price', 
    }
    df.rename(columns=columnas_renombrar, inplace=True)

    columnas_numericas = [
        'GMV', 'p2c_total', 'r_burn', 'Pay_order_cnt', 'Complete_order_cnt',
        'b_duty_cancel_order_cnt', 'b2c_total', 'Real pay price', 'cancel_order_cnt',
        'Online Store'
    ]
    
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).replace(',', '', regex=True), errors='coerce').fillna(0)

    columnas_porcentaje = ['Online Connection Rate', 'D Cancel Rate', 'P Cancel Rate', 'C Cancel Rate']
    for col in columnas_porcentaje:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace('%', '', regex=True), errors='coerce'
            ).fillna(0) / 100
    
    df['stat_date'] = pd.to_datetime(df['stat_date'], errors='coerce')
    df['week_number'] = df['stat_date'].dt.isocalendar().week
    
    return df


def generar_scorecard(df_limpio, metricas_ordenadas, grouping_level='brand_name'):
    """
    Genera el scorecard. 
    ACTUALIZADO: 'Online Stores' y 'Active Stores' ahora se calculan como conteos de tiendas únicas.
    ACTUALIZADO 2: 'p2c_total' se calcula como % del GMV.
    """
    if grouping_level not in ['brand_name', 'shop_name']:
        raise ValueError("grouping_level must be 'brand_name' or 'shop_name'")

    grouping_cols = [grouping_level, 'week_number']
    if grouping_level == 'shop_name':
        grouping_cols.insert(1, 'brand_name')

    # --- INICIO DE LA NUEVA LÓGICA DE AGREGACIÓN ---
    agregaciones_principales = {
        'shop_name': ('shop_name', 'nunique'), 
        'GMV': ('GMV', 'sum'),
        'Real pay price': ('Real pay price', 'sum'),
        'Complete_order_cnt': ('Complete_order_cnt', 'sum'),
        'Pay_order_cnt': ('Pay_order_cnt', 'sum'),
        'b_duty_cancel_order_cnt': ('b_duty_cancel_order_cnt', 'sum'),
        'cancel_order_cnt': ('cancel_order_cnt', 'sum'),
        'r_burn': ('r_burn', 'sum'),
        'b2c_total': ('b2c_total', 'sum'),
        'p2c_total': ('p2c_total', 'sum'),
        'Online Connection Rate': ('Online Connection Rate', 'mean'),
        'D Cancel Rate': ('D Cancel Rate', 'mean'),
        'P Cancel Rate': ('P Cancel Rate', 'mean'),
        'C Cancel Rate': ('C Cancel Rate', 'mean')
    }
    base_semanal = df_limpio.groupby(grouping_cols).agg(**agregaciones_principales).reset_index()
    base_semanal.rename(columns={'shop_name': 'Signed stores'}, inplace=True)

    online_stores_df = df_limpio[df_limpio['Online Store'] == 1].groupby(grouping_cols).agg(
        Online_Stores_Unicas=('shop_name', 'nunique')
    ).reset_index()

    active_stores_df = df_limpio[df_limpio['Pay_order_cnt'] > 0].groupby(grouping_cols).agg(
        Active_Stores_Unicas=('shop_name', 'nunique')
    ).reset_index()

    base_semanal = pd.merge(base_semanal, online_stores_df, on=grouping_cols, how='left')
    base_semanal = pd.merge(base_semanal, active_stores_df, on=grouping_cols, how='left')

    base_semanal.rename(columns={
        'Online_Stores_Unicas': 'Online Store',
        'Active_Stores_Unicas': 'Active Stores'
    }, inplace=True)
    base_semanal['Online Store'] = base_semanal['Online Store'].fillna(0).astype(int)
    base_semanal['Active Stores'] = base_semanal['Active Stores'].fillna(0).astype(int)

    # --- FIN DE LA NUEVA LÓGICA DE AGREGACIÓN ---

    # Se calcula después de la agregación para obtener sum(r_burn) / sum(GMV)
    # Se usa .replace(0, np.nan) para evitar errores de división por cero.
    base_semanal['r_burn'] = base_semanal['r_burn'] / base_semanal['GMV'].replace(0, np.nan)
    
    # <<< NUEVO: CALCULAR P2C COMO % DEL GMV >>>
    # Lógica idéntica a r_burn: se calcula post-agregación dividiendo la suma de p2c_total por la suma de GMV.
    base_semanal['p2c_total'] = base_semanal['p2c_total'] / base_semanal['GMV'].replace(0, np.nan)
    
    # El resto del código continúa igual, trabajando sobre el 'base_semanal' correctamente calculado.
    base_semanal['Completion rate'] = base_semanal['Complete_order_cnt'] / base_semanal['Pay_order_cnt'].replace(0, np.nan)
    base_semanal['Ticket_promedio'] = base_semanal['GMV'] / base_semanal['Complete_order_cnt'].replace(0, np.nan)
    base_semanal['B-cancel rate'] = base_semanal['b_duty_cancel_order_cnt'] / base_semanal['cancel_order_cnt'].replace(0, np.nan)
    
    id_vars = [grouping_level, 'week_number']
    if grouping_level == 'shop_name':
        id_vars.insert(1, 'brand_name')

    melted = base_semanal.melt(id_vars=id_vars, value_vars=metricas_ordenadas, var_name='Metric', value_name='Value')
    
    index_cols = [grouping_level, 'Metric']
    if grouping_level == 'shop_name':
        index_cols.insert(1, 'brand_name')
        
    scorecard = melted.pivot_table(index=index_cols, columns='week_number', values='Value').reset_index()

    # Cálculos de WoW, L4 y Alertas (sin cambios)
    semana_cols = sorted([col for col in scorecard.columns if isinstance(col, int)])
    if len(semana_cols) >= 2:
        ultima, penultima = semana_cols[-1], semana_cols[-2]
        scorecard['WoW'] = (scorecard[ultima] - scorecard[penultima]) / scorecard[penultima].replace(0, np.nan)
    else:
        scorecard['WoW'] = np.nan

    if len(semana_cols) >= 4:
        avg_l4 = scorecard[semana_cols[-4:]].mean(axis=1)
        scorecard['LW_vs_Avg_L4'] = (scorecard[semana_cols[-1]] - avg_l4) / avg_l4.replace(0, np.nan)
    else:
        scorecard['LW_vs_Avg_L4'] = np.nan
    
    marcas_con_alerta = scorecard[(scorecard['Metric'] == 'GMV') & (scorecard['WoW'] < 0)][grouping_level].unique()
    scorecard['Attention'] = scorecard[grouping_level].apply(lambda x: '🔴 Attention!' if x in marcas_con_alerta else '')

    scorecard['Metric'] = pd.Categorical(scorecard['Metric'], categories=metricas_ordenadas, ordered=True)
    scorecard = scorecard.sort_values(by=index_cols)
    
    final_cols = index_cols + semana_cols + ['WoW', 'LW_vs_Avg_L4', 'Attention']
    scorecard = scorecard[final_cols]
    
    return scorecard


def formatear_reporte(df):
    df_formateado = df.copy()
    
    # <<< MODIFICADO: Se quita 'p2c_total' de las métricas de moneda >>>
    metricas_pesos = ['GMV', 'Real pay price', 'Ticket_promedio', 'b2c_total']
    
    # <<< MODIFICADO: Se añade 'p2c_total' a las métricas de porcentaje >>>
    metricas_porcentaje = [
        'Completion rate', 'B-cancel rate', 'Online Connection Rate', 
        'D Cancel Rate', 'P Cancel Rate', 'C Cancel Rate', 'r_burn', 'p2c_total'
    ]
    
    semana_cols = [col for col in df.columns if isinstance(col, int)]
    for idx, row in df_formateado.iterrows():
        metric = row['Metric']
        for col in semana_cols:
            val = df_formateado.at[idx, col]
            if pd.notnull(val):
                if metric in metricas_pesos:
                    df_formateado.at[idx, col] = f"${val:,.0f}"
                elif metric in metricas_porcentaje:
                    df_formateado.at[idx, col] = f"{val * 100:.1f}%"
                elif isinstance(val, (int, float)):
                     df_formateado.at[idx, col] = f"{val:,.0f}"

    for col in ['WoW', 'LW_vs_Avg_L4']:
        if col in df_formateado.columns:
            df_formateado[col] = df_formateado[col].apply(lambda x: f"{x * 100:.1f}%" if pd.notnull(x) else "")
            
    return df_formateado