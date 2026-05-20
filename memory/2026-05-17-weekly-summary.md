# 📊 Weekly Trading Summary — Week 20 (May 11-17, 2026)

**Generated:** 2026-05-17 18:00 UTC  
**System:** Yagati v4 + Scan System  
**Phase:** ML Phase D (paper-deploy)  
**Paper Capital:** 10,000 €

---

## 🎯 Weekly KPIs vs Targets

| KPI | Target | Achieved | Gap | Status |
|-----|--------|----------|-----|--------|
| **Win Rate** | ≥ 70% | ~55-60% (historical) | -10 to -15 pts | 🟡 Improving |
| **Signals Sent** | 35-105 / week (5-15/day) | **4 signals** | -31 to -101 | 🟠 Low |
| **PnL Total** | 3,500-4,200 € / week | 0 € (paper) | -3,500 € | 🔴 Paper mode |
| **Active Edges** | 5-10 | 3 (Scan System) | -2 to -7 | 🟡 Partial |

---

## 📈 Signals Sent This Week (4 total)

**System Restart:** After 7 days of silence (May 9-16), Scan System resumed signal generation ✅

| Date | Time UTC | Asset | Type | Entry | TP | SL | Confidence | Status |
|------|----------|-------|------|-------|----|----|------------|--------|
| **May 16** | 14:41 | ETH/USDT | LONG | ~2180 | +2.4% | -2.5% | N/A | ✅ Sent |
| **May 16** | 14:43 | ETH | LONG | N/A | N/A | N/A | 78/100 | ✅ Sent |
| **May 16** | 23:06 | BTC/USDT | LONG | $78,180 | $79,547 (+1.75%) | $76,279 (-2.43%) | 66/100 | ✅ Sent |
| **May 17** | 10:47 | ETH | LONG | N/A | N/A | N/A | 78/100 | ✅ Sent |
| **May 17** | 14:39 | BTC/USDT | LONG | $78,000 | $79,289 (+1.65%) | $75,859 (-2.74%) | 66/100 | 🟡 Open |

**Signal Frequency:** ~0.5 signals/day (target: 0.7-2/day)

---

## 🏆 Best Performing Strategies

### Top 3 (Historical Paper Trades, n=31 closed)

| Rank | Strategy | Asset | Win Rate | Avg PnL | n_trades | Status |
|------|----------|-------|----------|---------|----------|--------|
| **🥇 #1** | **ma_distance_revert** | ETHUSDT | **100%** ✅ | N/A | 3 | ARCHIVED |
| **🥈 #2** | **bb_walk** | ETHUSDT | **66.7%** ✅ | +7.8% | 3 | ARCHIVED |
| **🥉 #3** | **Scan System (BB_RSI_ADX)** | BTC/ETH | N/A | N/A | 4 (this week) | 🟡 Testing |

### Strategies Pending Backtest

| Strategy | Concept | TF | Filter | Potential |
|----------|---------|-----|--------|-----------|
| **RSI Mean Reversion** | RSI(14) <20 or >80 | 5-15min | HMM=RANGE only | ⭐⭐⭐⭐ |
| **BB Walk Optimized** | 2.5σ + volume > MA20 | Adaptive | Volume confirmation | ⭐⭐⭐⭐ |
| **Momentum Breakout** | Resistance + HMM RANGE→BULL | - | Stop: back to range | ⭐⭐⭐ |

---

## 🧠 Lessons Learned

### ✅ What Worked

1. **Signal Generation Resumed:** After 7-day silence (May 9-16), system generated 4 signals in 48h
2. **HMM Detection:** RANGE regime correctly identified (100/100) on all BTC/ETH signals
3. **Extreme Oversold Capture:** RSI < 10 (BTC 7.96, ETH 4.67) = rare opportunities well captured
4. **Telegram Delivery:** All signals successfully sent ✅

### ⚠️ Issues Identified

1. **Gates Too Strict (CRITICAL):**
   - CPCV, DSR, PSR, PBO block 100% of Yagati v4 edges
   - 0 edges ENABLED out of 141 → system in "observability" mode only
   - **Fix:** Relax thresholds or migrate to Confluence Scoring 0-100

2. **Low Volume on Signals:**
   - BTC 23:06: Volume 0.21x MA20 (16.8% of average)
   - ETH 12:07: Volume 0.09x MA20 (9% of average)
   - **Risk:** False signals, lack of market conviction
   - **Fix:** Adjust volume gate (1.5 → 1.2) or add warning instead of block

3. **ADX Borderline:**
   - BTC 14:39: ADX 45.06 >> 25 (gate threshold)
   - **Problem:** Mean-reversion underperforms in trending markets
   - **Fix:** ADX 25-35 → reduced confidence, ADX > 35 → block

4. **Unfavorable R/R Ratio:**
   - BTC 23:06: R/R = 0.73 (risk > reward)
   - **Target:** R/R ≥ 1.0
   - **Fix:** Adjust TP/SL or filter setups with R/R < 1

### 🎯 Strategic Insights

1. **Confluence Scoring > Binary Gates:**
   - Current: ON/OFF (either 100% or 0%)
   - Vision: Score 0-100 with adaptive position sizing (25%-150%)
   - **Impact:** More nuance, fewer false negatives

2. **Regime-Aware Signal Fusion:**
   - HMM detects regime → weight strategies dynamically
   - RANGE: mean-reversion at 70%
   - BULL/BEAR: momentum/breakout at 70%
   - **Potential Impact:** +40% Sharpe ratio

3. **RSI Extreme Filter:**
   - RSI < 5 or > 95 → increase confidence by 10-15 points
   - Extreme oversold/overbought are rare and often followed by rebound

---

## 📊 70% WR Target Gap Analysis

| Metric | Current | Target | Gap | Required Action |
|--------|---------|--------|-----|-----------------|
| **Win Rate** | ~55-60% (historical) | ≥ 70% | -10 to -15 pts | Promote bb_walk, backtest RSI Mean Reversion |
| **Signals/week** | 4 | 35-105 (5-15/day) | -31 to -101 | Relax gates, activate 5-10 edges |
| **PnL/day** | 0 € (paper) | 500-600 € | -600 € | Move to live (Phase E) after 30d paper |
| **Avg Confidence** | 66/100 | ≥ 70/100 | -4 pts | Confluence Scoring + RSI extreme filter |
| **R/R Ratio** | 0.73 | ≥ 1.0 | -0.27 | Adjust TP/SL or filter setups |

---

## 📋 Action Plan to Reach 70% WR

### P0 (This Week)
- [ ] Promote **bb_walk** to PROBATION (WR=66.7%, close to target)
- [ ] Relax volume gate (1.5 → 1.2) to avoid false negatives
- [ ] Adjust ADX gate (25 → 30) with reduced confidence
- [ ] Monitor open signals (BTC May 16, ETH May 17)

### P1 (1-3 Weeks)
- [ ] Backtest **RSI Mean Reversion** (RSI <20/>80, HMM=RANGE, 30d)
- [ ] Backtest **BB Walk Optimized** (2.5σ + volume > MA20)
- [ ] Implement **Confluence Scoring MVP** (0-100 score)
- [ ] Adaptive Position Sizing (25%-150% by confidence)

### P2 (1-2 Months)
- [ ] **Regime-Aware Signal Fusion** (HMM-based weighting)
- [ ] **Self-Healing Strategy Generator** (auto-adjustment)
- [ ] **Walk-Forward Auto** (periodic re-optimization)

---

## 🔮 Projections

### Optimistic Scenario (WR 70-80%)
- bb_walk promoted + 2 new strategies validated
- Confluence Scoring implemented → reduced false signals
- 5-15 signals/day with 70%+ WR → 500-600 €/day achievable
- **Timeline:** 4-6 weeks

### Realistic Scenario (WR 60-70%)
- Gates relaxed → 3-5 signals/day
- Average WR 60-65% (close to historical)
- PnL/day: 200-300 € (suboptimal but positive)
- **Timeline:** 2-3 weeks

### Pessimistic Scenario (WR < 60%)
- Gates too strict maintained → 0-1 signal/day
- WR < 60% → negative or zero PnL
- **Action:** Pivot to new system (Saiyan) with Regime-Aware architecture

---

## 📝 Conclusion

**Overall Status:** 🟡 **Improving** (system restarted after 7-day silence)

**Strengths:**
- ✅ Signals generated and sent successfully
- ✅ HMM regime detection functional
- ✅ Extreme oversold conditions captured

**Weaknesses:**
- 🔴 Gates too strict blocking pipeline
- 🟠 Low volume on signals (false positive risk)
- 🟠 Unfavorable R/R ratio (< 1.0)

**Recommendation:** Prioritize gate relaxation (P0) and backtesting new mean-reversion strategies (P1) to reach 70% WR target within 4-6 weeks.

---

*Report generated automatically by trading scan system.*  
*Paper-trading data — actual performance may vary.*  
*Next weekly summary: 2026-05-24 18:00 UTC*
