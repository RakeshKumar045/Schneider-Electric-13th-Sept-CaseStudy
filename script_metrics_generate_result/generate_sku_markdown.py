import pandas as pd

r = pd.read_csv('sku_divergence_report.csv')

top_inc = r.sort_values('delta_inventory_value', ascending=False).head(20)
top_dec = r.sort_values('delta_inventory_value', ascending=True).head(20)

with open('SKU_drivers.md','w',encoding='utf-8') as f:
    f.write('# SKU Drivers — Top Contributors to Inventory Change\n\n')
    f.write('## Top 20 Increases (recommended - current)\n\n')
    f.write('| SKU | Current Inventory ($) | Recommended Inventory ($) | Delta ($) | Delta (%) |\n')
    f.write('|---:|---:|---:|---:|---:|\n')
    for _,row in top_inc.iterrows():
        f.write(f"| {row['sku_id']} | {row['current_inventory_value']:,.0f} | {row['recommended_inventory_value']:,.0f} | {row['delta_inventory_value']:,.0f} | {row['delta_inventory_pct']:,.1f}% |\n")

    f.write('\n## Top 20 Decreases (recommended - current)\n\n')
    f.write('| SKU | Current Inventory ($) | Recommended Inventory ($) | Delta ($) | Delta (%) |\n')
    f.write('|---:|---:|---:|---:|---:|\n')
    for _,row in top_dec.iterrows():
        f.write(f"| {row['sku_id']} | {row['current_inventory_value']:,.0f} | {row['recommended_inventory_value']:,.0f} | {row['delta_inventory_value']:,.0f} | {row['delta_inventory_pct']:,.1f}% |\n")

print('SKU_drivers.md created....')
