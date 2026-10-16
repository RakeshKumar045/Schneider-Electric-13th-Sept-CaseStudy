import pandas as pd
import numpy as np
from math import sqrt
from scipy.stats import norm

# Load data
df = pd.read_csv('component_demand_history.csv', parse_dates=['week_start_date'])
# Clean
df_clean = df.copy()
df_clean = df_clean.dropna(subset=['demand_qty','sku_id','week_start_date'])
df_clean['lead_time_days'] = df_clean.groupby('supplier_id')['lead_time_days'].transform(lambda x: x.fillna(x.median()))
df_clean = df_clean.drop_duplicates()

service_level = 0.95
z = norm.ppf(service_level)
holding_rate = 0.25
ordering_cost = 50.0

records = []
for sku, g in df_clean.groupby('sku_id'):
    avg_onhand = g['on_hand_qty'].mean()
    unit_cost = g['unit_cost'].iloc[0]
    current_inventory_value = avg_onhand * unit_cost

    demand = g['demand_qty'].values
    avg_demand = np.mean(demand)
    demand_std = np.std(demand)
    lead_time_weeks = g['lead_time_days'].mean() / 7 if not np.isnan(g['lead_time_days'].mean()) else 0
    safety_stock = z * demand_std * np.sqrt(max(lead_time_weeks,0))
    reorder_point = avg_demand * lead_time_weeks + safety_stock
    recommended_inventory_value = reorder_point * unit_cost
    holding_cost = unit_cost * holding_rate
    eoq = sqrt((2 * avg_demand * 52 * ordering_cost) / holding_cost) if holding_cost>0 else 0

    records.append({
        'sku_id': sku,
        'avg_on_hand': avg_onhand,
        'unit_cost': unit_cost,
        'current_inventory_value': current_inventory_value,
        'avg_demand': avg_demand,
        'demand_std': demand_std,
        'lead_time_weeks': lead_time_weeks,
        'safety_stock': safety_stock,
        'reorder_point': reorder_point,
        'recommended_inventory_value': recommended_inventory_value,
        'eoq': eoq,
        'delta_inventory_value': recommended_inventory_value - current_inventory_value,
        'delta_inventory_pct': (recommended_inventory_value - current_inventory_value)/current_inventory_value*100 if current_inventory_value>0 else np.nan
    })

report = pd.DataFrame.from_records(records)
report.to_csv('sku_divergence_report.csv', index=False)

# Top 20 largest increases
top_increases = report.sort_values('delta_inventory_value', ascending=False).head(20)
# Top 20 largest decreases
top_decreases = report.sort_values('delta_inventory_value', ascending=True).head(20)

print('Top 20 SKU increases (recommended - current)')
print(top_increases[['sku_id','current_inventory_value','recommended_inventory_value','delta_inventory_value','delta_inventory_pct']].to_string(index=False))

print('\n Top 20 SKU decreases (recommended - current)')
print(top_decreases[['sku_id','current_inventory_value','recommended_inventory_value','delta_inventory_value','delta_inventory_pct']].to_string(index=False))

print('\n Saved sku_divergence_report.csv')
