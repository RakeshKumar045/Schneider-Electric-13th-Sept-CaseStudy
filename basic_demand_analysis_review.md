# Review: `basic_demand_analysis.ipynb`

## Summary
- Notebook purpose: build ML demand-forecast models (LR, RF, XGB, LGB) to predict `future_4wk_avg_demand` using engineered time features and lags.
- Overall: well-structured pipeline and sensible feature engineering. Good use of category handling for LightGBM and a simple ensemble.

## What I ran /  verified
- I inspected the notebook source (did not execute model-training here). The code flow is: load CSV → datetime conversion → sort → impute → feature engineering (lags, rolling) → drop NA → time-based train/val split → preprocessing → train multiple models → print leaderboard.

## Issues & Bugs (action required)
1. Invalid metric import: the notebook imports `root_mean_squared_error` from `sklearn.metrics`, but sklearn exposes `mean_squared_error`. Replace usages with:

```python
from sklearn.metrics import mean_squared_error
def rmse(y_true, y_pred):
    return mean_squared_error(y_true, y_pred, squared=False)
```

Then use `rmse(y_val, preds)` when building the `results` dict.

2. Target leakage risk: the notebook uses `future_4wk_avg_demand` as the target. That column appears to be forward-looking (pre-computed future average) and may leak future data into training. Verify whether `future_4wk_avg_demand` was computed from historical rows available at prediction time. If not, replace with a target computed from historical data (e.g., aggregate trailing 4-week demand shifted appropriately) or confirm the intended workflow:

- If this is an offline model for forecasting next-4-weeks, create the target like:

```python
df = df.sort_values(['sku_id','week_start_date'])
df['target_4w'] = df.groupby('sku_id')['demand_qty'].shift(-1).rolling(window=4, min_periods=1).sum()
```

3. `dropna()` after generating lags will remove all rows with initial lags — this is expected but reduces training data for short histories. Consider dropping only rows where the target is NA rather than all NA across the dataframe.

4. Preprocessing compatibility: `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` uses the `sparse_output` argument which requires a recent sklearn version; older versions use `sparse=False`. If the environment is older, change to `sparse=False` for compatibility.

5. Metric naming in final print: the code sorts `results.items()` and prints RMSE values; after fixing the metric import, ensure consistent formatting (e.g., 3 decimals) and handle any missing predictions gracefully.

6. Resource/time cautions: RandomForest training with `n_estimators=100` and XGBoost/LightGBM could be slow on large datasets. Consider a smaller sample for experimentation, or use `n_estimators=50` and early-stopping for XGBoost/LGB.

## Recommendations (next steps)
- Confirm target definition: either keep `future_4wk_avg_demand` only if it is computed from data available at prediction time, or re-generate a target from `demand_qty` using a shifted window.
- Replace `root_mean_squared_error` with `mean_squared_error(..., squared=False)` and add the `rmse` helper.
- Log-transform demand where appropriate: `y = np.log1p(y)` during training and invert predictions with `np.expm1()` to reduce RMSE sensitivity to large outliers.
- Add longer rolling features (4/8/12-week means), ratio features (on_hand / avg_demand), and supplier-level aggregates to help models explain supplier-driven stockouts.
- Use `TimeSeriesSplit` or rolling-origin evaluation for more robust validation rather than a single 4-week holdout.
- Persist models and store per-SKU metrics (RMSE, bias) to find SKUs where the model underperforms.

## Suggested quick patch (copy into a new final cell to fix metric + leaderboard)

```python
from sklearn.metrics import mean_squared_error
import numpy as np

def rmse(y_true, y_pred):
    return mean_squared_error(y_true, y_pred, squared=False)

# compute RMSEs safely
results = {}
for name, preds in val_predictions.items():
    try:
        results[name] = rmse(y_val, preds)
    except Exception as e:
        results[name] = float('nan')

print('\nMODEL results')
print('-'*45)
for model_name, rmse_val in sorted(results.items(), key=lambda item: (item[1] if not np.isnan(item[1]) else 1e9)):
    print(f"{model_name:<30} | Validation RMSE: {rmse_val:.4f}")
print('-'*45)
```

## Deliverables I created
- `basic_demand_analysis_review.md` (this file)

If you want, I can :
- run this notebook end-to-end (I will execute the cells and produce real RMSEs) and write computed results into a new markdown with numbers, or
- patch the notebook to replace `future_4wk_avg_demand` with a computed target from `demand_qty` and re-run models.

Which would you like me to do next? (run end-to-end, patch target, or both)
