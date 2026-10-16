import pandas as pd
import numpy as np

from scipy.stats import norm

from math import sqrt

# Load cleaned data
df = pd.read_csv('component_demand_history.csv', parse_dates=['week_start_date'])
df = df.dropna(subset=['demand_qty','sku_id','week_start_date']).drop_duplicates()
df['lead_time_days'] = df.groupby('supplier_id')['lead_time_days'].transform(lambda x: x.fillna(x.median()))

# Current totals
current_inventory_value = (df.groupby('sku_id')['on_hand_qty'].mean() * df.groupby('sku_id')['unit_cost'].first()).sum()
current_stockout_weeks = int(df['stockout_flag'].sum())

holding_rates = [0.15, 0.25]
service_levels = [0.90, 0.95, 0.98]
ordering_cost = 50.0

results = []
for h in holding_rates:
    for s in service_levels:
        z = norm.ppf(s)
        policy_totals = {'recommended_inventory_value': 0.0}
        for sku, g in df.groupby('sku_id'):
            demand = g['demand_qty'].values
            avg_demand = np.mean(demand)
            demand_std = np.std(demand)
            lead_time_weeks = g['lead_time_days'].mean() / 7 if not np.isnan(g['lead_time_days'].mean()) else 0
            safety_stock = z * demand_std * np.sqrt(max(lead_time_weeks, 0))
            reorder_point = avg_demand * lead_time_weeks + safety_stock
            unit_cost = g['unit_cost'].iloc[0]
            policy_totals['recommended_inventory_value'] += reorder_point * unit_cost
        recommended = policy_totals['recommended_inventory_value']
        inventory_delta = recommended - current_inventory_value
        inventory_delta_pct = inventory_delta / current_inventory_value * 100 if current_inventory_value>0 else np.nan
        current_carrying = current_inventory_value * h
        recommended_carrying = recommended * h
        carrying_delta = recommended_carrying - current_carrying
        results.append({
            'holding_rate': h,
            'service_level': s,
            'current_inventory_value': current_inventory_value,
            'recommended_inventory_value': recommended,
            'inventory_delta': inventory_delta,
            'inventory_delta_pct': inventory_delta_pct,
            'current_carrying_cost': current_carrying,
            'recommended_carrying_cost': recommended_carrying,
            'carrying_cost_delta': carrying_delta
        })

res_df = pd.DataFrame(results)
res_df.to_csv('sensitivity_results.csv', index=False)
print(res_df.to_string(index=False))
