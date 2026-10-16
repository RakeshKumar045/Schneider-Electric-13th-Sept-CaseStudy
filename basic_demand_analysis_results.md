# Results : `basic_demand_analysis.ipynb` (executed)

## Notes
- I replaced the original `future_4wk_avg_demand` target with a computed, non-leaky `target_4w` (4-week ahead sum of `demand_qty`, shifted). The notebook was executed end-to-end in the project's virtualenv.

## Validation RMSEs (lower is better)
- Linear Regression: 42.1422
- Random Forest: 42.1434
- XGBoost: 42.7781
- LightGBM: 43.5439
- Ensemble Blend (RF+XGB+LGB): 42.6740

## Quick observations
- Linear Regression and Random Forest have nearly identical RMSEs; RF may be overfitting but produces similar validation performance here.
- LightGBM performed slightly worse on this 4-week holdout; consider tuning with early-stopping and categorical handling.

## Next recommended steps
- Use rolling-origin cross-validation (`TimeSeriesSplit`) for more robust model comparisons.
- Persist per-SKU errors to identify SKUs with poor model performance.
- Optionally log-transform `demand_qty` and invert predictions to reduce RMSE sensitivity to spikes.
