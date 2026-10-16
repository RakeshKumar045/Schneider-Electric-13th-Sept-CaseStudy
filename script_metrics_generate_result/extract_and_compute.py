import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
from scipy.stats import norm

# 1) Extract Candidate_Brief.docx using stdlib (no external dependencies)
def extract_docx_text(path):
    texts = []
    with zipfile.ZipFile(path) as z:
        if 'word/document.xml' in z.namelist():
            xml = z.read('word/document.xml')
            root = ET.fromstring(xml)
            # namespace handling
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            for para in root.findall('.//w:p', ns):
                texts_run = []
                for node in para.findall('.//w:t', ns):
                    if node.text:
                        texts_run.append(node.text)
                if texts_run:
                    texts.append(''.join(texts_run))
    return '\n'.join(texts)

text = extract_docx_text('Candidate_Brief.docx')
with open('Candidate_Brief_text.txt','w',encoding='utf-8') as f:
    f.write(text)

# Simple summary: first 1200 chars
summary = text[:1200]
print('---CANDIDATE_BRIEF SUMMARY START----')
print(summary)
print('---CANDIDATE_BRIEF SUMMARY END---')

# 2) Load CSV and compute metrics (reproducing notebook logic)
df = pd.read_csv('component_demand_history.csv', parse_dates=['week_start_date'])
# cleaning
df_clean = df.copy()
df_clean = df_clean.dropna(subset=['demand_qty','sku_id','week_start_date'])
# fill lead time median by supplier
df_clean['lead_time_days'] = df_clean.groupby('supplier_id')['lead_time_days'].transform(lambda x: x.fillna(x.median()))
# drop duplicates
df_clean = df_clean.drop_duplicates()

# Current inventory value (same as notebook)
current_inventory_value = (df_clean.groupby('sku_id')['on_hand_qty'].mean() * df_clean.groupby('sku_id')['unit_cost'].first()).sum()
current_stockout_weeks = int(df_clean['stockout_flag'].sum())
current_stockout_rate = df_clean['stockout_flag'].sum() / len(df_clean) if len(df_clean)>0 else 0

# Policy calculations
from math import sqrt
policy = {}
service_level = 0.95
z_score = norm.ppf(service_level)
ordering_cost = 50.0
holding_rate = 0.25  # matches notebook

for sku in df_clean['sku_id'].unique():
    sku_data = df_clean[df_clean['sku_id'] == sku]
    demand = sku_data['demand_qty'].values
    avg_demand = np.mean(demand)
    lead_time_weeks = sku_data['lead_time_days'].mean() / 7 if not np.isnan(sku_data['lead_time_days'].mean()) else 0
    demand_std = np.std(demand)
    safety_stock = z_score * demand_std * np.sqrt(max(lead_time_weeks, 0))
    reorder_point = avg_demand * lead_time_weeks + safety_stock
    unit_cost = sku_data['unit_cost'].iloc[0] if len(sku_data)>0 else 0
    holding_cost = unit_cost * holding_rate
    eoq = sqrt((2 * avg_demand * 52 * ordering_cost) / holding_cost) if holding_cost>0 else 0
    policy[sku] = {'reorder_point': reorder_point, 'safety_stock': safety_stock, 'eoq': eoq, 'avg_demand': avg_demand, 'unit_cost': unit_cost}

recommended_inventory = {sku: policy[sku]['reorder_point'] * policy[sku]['unit_cost'] for sku in policy}
recommended_inventory_value = sum(recommended_inventory.values())

projected_stockout_rate = 0.05
projected_stockout_weeks = int(len(df_clean) * projected_stockout_rate)

inventory_reduction = current_inventory_value - recommended_inventory_value
inventory_reduction_pct = (inventory_reduction / current_inventory_value * 100) if current_inventory_value>0 else 0
stockout_improvement = current_stockout_weeks - projected_stockout_weeks
stockout_improvement_pct = (stockout_improvement / current_stockout_weeks * 100) if current_stockout_weeks>0 else None

# Print computed metrics
print('\n---COMPUTED METRICS---')
print(f"total_inventory_value: {current_inventory_value}")
print(f"current_stockout_weeks: {current_stockout_weeks}")
print(f"current_stockout_rate: {current_stockout_rate:.4f}")
print(f"recommended_inventory_value: {recommended_inventory_value}")
print(f"projected_stockout_weeks: {projected_stockout_weeks}")
print(f"inventory_reduction: {inventory_reduction}")
print(f"inventory_reduction_pct: {inventory_reduction_pct}")
print(f"total_annual_benefit (approx carrying savings only): {current_inventory_value*0.25 - recommended_inventory_value*0.25}")

# 3) Update EXECUTIVE_SUMMARY.md placeholders
import re

def fmt_currency(v):
    return f"${v:,.0f}"

def fmt_pct(v):
    return f"{v:.1f}%"

with open('EXECUTIVE_SUMMARY.md','r',encoding='utf-8') as f:
    text = f.read()

replacements = {
    '[TOTAL_INVENTORY_VALUE]': fmt_currency(current_inventory_value),
    '[STOCKOUT_WEEKS]': str(current_stockout_weeks),
    '[INVENTORY_REDUCTION]': fmt_currency(inventory_reduction),
    '[INVENTORY_REDUCTION_PCT]': fmt_pct(inventory_reduction_pct),
    '[ANNUAL_BENEFIT]': fmt_currency((current_inventory_value*0.25 - recommended_inventory_value*0.25)),
    '[RECOMMENDED_INVENTORY_VALUE]': fmt_currency(recommended_inventory_value),
    '[CURRENT_SERVICE_LEVEL]': f"{current_stockout_rate*100:.1f}%",
    '[STOCKOUT_REDUCTION_WEEKS]': str(stockout_improvement),
    '[STOCKOUT_REDUCTION_PCT]': fmt_pct(stockout_improvement_pct) if stockout_improvement_pct is not None else 'N/A',
    '[CURRENT_STOCKOUT_RATE]': f"{current_stockout_rate:.2%}",
    '[PROJECTED_STOCKOUT_WEEKS]': str(projected_stockout_weeks),
    '[CARRYING_COST_SAVINGS]': fmt_currency(current_inventory_value*0.25 - recommended_inventory_value*0.25),
    '[LOST_SALES_REDUCTION]': 'TBD'
}

for k,v in replacements.items():
    text = text.replace(k, v)

with open('EXECUTIVE_SUMMARY.md','w',encoding='utf-8') as f:
    f.write(text)

print('\nEXECUTIVE_SUMMARY.md updated with computed metrics.')

# Save computed metrics to file
import json
metrics = {
    'total_inventory_value': current_inventory_value,
    'current_stockout_weeks': current_stockout_weeks,
    'current_stockout_rate': current_stockout_rate,
    'recommended_inventory_value': recommended_inventory_value,
    'projected_stockout_weeks': projected_stockout_weeks,
    'inventory_reduction': inventory_reduction,
    'inventory_reduction_pct': inventory_reduction_pct,
    'annual_benefit_estimate': (current_inventory_value*0.25 - recommended_inventory_value*0.25)
}
with open('computed_metrics.json','w',encoding='utf-8') as f:
    json.dump(metrics,f,indent=2)

print('\nSaved computed_metrics.json and Candidate_Brief_text.txt.')
