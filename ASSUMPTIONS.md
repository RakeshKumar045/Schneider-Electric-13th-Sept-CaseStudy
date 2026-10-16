# ASSUMPTIONS & NEXT STEPS

## Key Assumptions Made

### 1. Demand Assumptions
- **Stationarity**: Demand patterns are stable over time (no long-term trend)
- **No Seasonality**: No seasonal patterns beyond what's captured in 2-year history
- **Independence**: Demand for one SKU doesn't affect demand for others
- **Normality**: Demand follows approximately normal distribution (for safety stock calculation)

### 2. Supply Chain Assumptions
- **Constant Lead Time**: Supplier lead times are fixed (no variability)
- **Reliable Suppliers**: Suppliers deliver on promised lead times
- **No Batch Constraints**: Can order any quantity (no minimum order quantities)
- **Immediate Fulfillment**: Orders are fulfilled immediately upon receipt

### 3. Cost Assumptions
- **Holding Cost**: 25% of unit cost annually (used in calculations). Note: finance may use 15% — confirm and align.
 - **Holding Cost**: 25% of unit cost annually (used in `assignment_forecast_2.ipynb` EOQ calculation).\
    NOTE: finance often reports different carrying rate (e.g. 15%). Confirm with finance and align notebook or assumptions accordingly.
- **Ordering Cost**: $50 per order (fixed, includes processing, shipping, receiving)
- **No Stockout Cost**: Stockouts result in lost sales (no backorders)
- **No Quantity Discounts**: Unit cost is constant regardless of order quantity

### 4. Service Level Assumption
- **Target Service Level**: 95% (acceptable to miss demand 5% of the time)
- **Metric**: Cycle service level (probability of not stocking out during lead time)

### 5. Data Assumptions
- **Data Quality**: Cleaned data is representative of true demand
- **No Structural Breaks**: No major changes in product mix or customer base
- **Complete History**: 2 years of data is sufficient for forecasting
- **Accurate Recording**: Demand and inventory records are accurate

-----

## What We Would Do With More Time

### 1. Lead Time Variability
**Current**: Assume constant lead time  
**Better**: Model lead time as random variable
- Collect supplier performance data
- Estimate lead time distribution
- Adjust safety stock formula: SS = Z × σ_d × √(L + σ_L²)

### 2. Demand Forecasting Improvements
**Current**: Segment-based methods (MA, ES, Croston)  
**Better**: Machine learning models
- ARIMA/SARIMA for time series
- Prophet for trend + seasonality
- LSTM neural networks for complex patterns
- Ensemble methods combining multiple models

### 3. Supplier Performance Analysis
**Current**: Assume all suppliers are equal  
**Better**: Differentiate by supplier
- Analyze on-time delivery rates
- Identify unreliable suppliers
- Adjust safety stock by supplier risk
- Negotiate lead time improvements

### 4. Demand Sensing
**Current**: Historical data only  
**Better**: Incorporate forward-looking signals
- Customer order pipeline
- Sales forecasts
- Market trends
- Seasonal indicators

### 5. Multi-Echelon Optimization
**Current**: Single plant optimization  
**Better**: Network-wide optimization
- Coordinate inventory across multiple plants
- Optimize central warehouse vs. plant stock
- Reduce total system inventory

### 6. Dynamic Safety Stock
**Current**: Static safety stock based on historical data  
**Better**: Adjust dynamically
- Increase safety stock when demand forecast uncertainty rises
- Decrease when demand becomes more predictable
- Respond to supplier performance changes

### 7. Simulation & Validation
**Current**: Analytical calculations  
**Better**: Monte Carlo simulation
- Simulate demand and lead time variability
- Test policy under different scenarios
- Validate service level assumptions
- Identify edge cases

### 8. Integration with ERP
**Current**: Standalone analysis  
**Better**: Real-time system integration
- Automated reorder point updates
- Real-time inventory monitoring
- Automatic order generation
- Performance dashboards

---

## Data Limitations & Workarounds

### Limitation 1: No Demand Forecast Column
**Issue**: `future_4wk_avg_demand` column not used  
**Reason**: Appears to be forward-looking data (data leakage risk)  
**Workaround**: Generated our own forecasts using historical data only

### Limitation 2: No Stockout Quantity
**Issue**: `stockout_flag` is binary, doesn't show magnitude  
**Reason**: Can't calculate exact lost sales  
**Workaround**: Estimated lost sales as average demand × stockout weeks

### Limitation 3: No Supplier Reliability Data
**Issue**: Lead times vary but no explanation  
**Reason**: Can't distinguish between supplier variability and data errors  
**Workaround**: Used median lead time per supplier; flagged for investigation

### Limitation 4: No Product Demand Drivers
**Issue**: No information on why demand varies  
**Reason**: Can't predict future demand changes  
**Workaround**: Assumed demand patterns are stable; recommend demand sensing

### Limitation 5: No Carrying Cost Breakdown
**Issue**: Assumed 15% annual holding cost  
**Reason**: Not provided in data  
**Workaround**: Used industry standard; recommend validation with finance

---

## Validation & Testing

### How to Validate This Recommendation

1. **Pilot Test** (4 weeks)
   - Select 20 high-value SKUs
   - Implement recommended policy
   - Compare actual vs. projected stockouts
   - Measure inventory reduction

2. **Performance Metrics**
   - Stockout rate (target: <5%)
   - Inventory turnover (target: increase by X%)
   - Order frequency (target: Y orders/year)
   - Cash freed up (target: $X)

3. **Sensitivity Analysis**
   - What if service level is 90%? (lower inventory)
   - What if service level is 98%? (higher inventory)
   - What if lead time increases by 50%?
   - What if demand variability doubles?

---

## Scalability Considerations

### Current Solution
- 200 SKUs
- Weekly updates
- Manual analysis

### Scaling to 20,000 SKUs

**Changes Needed**:
1. **Automation**: Batch processing instead of manual
2. **Efficiency**: Vectorized calculations (pandas/numpy)
3. **Frequency**: Daily or real-time updates
4. **Monitoring**: Automated alerts for policy violations
5. **Governance**: Version control, audit trails

**Implementation**:
```python
# Pseudocode for scalable solution
def update_inventory_policy_batch(df, batch_size=1000):
    for batch in chunks(df, batch_size):
        forecasts = forecast_batch(batch)
        policies = calculate_policy_batch(batch, forecasts)
        update_erp_batch(policies)
        log_changes(policies)
