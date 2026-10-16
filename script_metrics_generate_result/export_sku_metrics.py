import pandas as pd
import numpy as np
from scipy.stats import norm
import json

# Load and clean
print('Running final export....')
df = pd.read_csv('component_demand_history.csv', parse_dates=['week_start_date'])
df_clean = df.dropna(subset=['demand_qty','sku_id','week_start_date']).copy()
df_clean['lead_time_days'] = df_clean.groupby('supplier_id')['lead_time_days'].transform(lambda x: x.fillna(x.median()))
df_clean = df_clean.drop_duplicates()

# Per-SKU current inventory value
sku_current = df_clean.groupby('sku_id').agg({
    'on_hand_qty': 'mean',
    'unit_cost': 'first'
}).rename(columns={'on_hand_qty':'avg_on_hand'})
sku_current['current_inventory_value'] = sku_current['avg_on_hand'] * sku_current['unit_cost']

# Compute recommended reorder_point per SKU using 95% service level (same logic as notebook)
service_level = 0.95
z = norm.ppf(service_level)
rec_rows = []
for sku, g in df_clean.groupby('sku_id'):
    demand = g['demand_qty'].values
    avg_demand = float(np.mean(demand)) if len(demand)>0 else 0.0
    demand_std = float(np.std(demand)) if len(demand)>0 else 0.0
    lead_time_weeks = float(np.mean(g['lead_time_days']))/7.0 if not np.isnan(np.mean(g['lead_time_days'])) else 0.0
    safety_stock = z * demand_std * np.sqrt(max(lead_time_weeks, 0.0))
    reorder_point = avg_demand * lead_time_weeks + safety_stock
    unit_cost = float(g['unit_cost'].iloc[0]) if len(g)>0 else 0.0
    rec_value = reorder_point * unit_cost
    rec_rows.append((sku, reorder_point, safety_stock, rec_value, avg_demand, demand_std, lead_time_weeks))

sku_rec = pd.DataFrame(rec_rows, columns=['sku_id','reorder_point','safety_stock','recommended_inventory_value','avg_demand','demand_std','lead_time_weeks']).set_index('sku_id')

# Combine
sku_report = sku_current.join(sku_rec, how='outer').fillna(0.0)
sku_report['delta_inventory_value'] = sku_report['recommended_inventory_value'] - sku_report['current_inventory_value']
sku_report['delta_pct'] = np.where(sku_report['current_inventory_value']>0, sku_report['delta_inventory_value']/sku_report['current_inventory_value']*100, np.nan)

# Totals
current_inventory_value = sku_report['current_inventory_value'].sum()
recommended_inventory_value = sku_report['recommended_inventory_value'].sum()
inventory_reduction = current_inventory_value - recommended_inventory_value
holding_rate = 0.25
annual_benefit_estimate = (current_inventory_value * holding_rate) - (recommended_inventory_value * holding_rate)

# Output files
sku_report.reset_index().to_csv('sku_divergence_report.csv', index=False)
computed = {
    'current_inventory_value': float(current_inventory_value),
    'recommended_inventory_value': float(recommended_inventory_value),
    'inventory_reduction': float(inventory_reduction),
    'holding_rate': holding_rate,
    'annual_benefit_estimate': float(annual_benefit_estimate)
}
with open('computed_metrics.json','w',encoding='utf-8') as f:
    json.dump(computed, f, indent=2)

print('Wrote sku_divergence_report.csv and computed_metrics.json')
print(f"Current inventory value: ${current_inventory_value:,.0f}")
print(f"Recommended inventory value: ${recommended_inventory_value:,.0f}")
print(f"Inventory delta: ${inventory_reduction:,.0f}")
