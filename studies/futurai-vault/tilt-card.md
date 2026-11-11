# futurai.py: holds out of sample

**Verdict: holds out of sample** (rung 4 of 6: loses after costs / fails nulls / in-sample only / holds out of sample / passes deflated Sharpe / passes sealed holdout).
- deflated Sharpe 0.01 over 198 trial(s), under 0.95

2025-06-05 to 2026-11-01, params {}.

| Check | Result |
|---|---|
| After costs | Sharpe 2.44, return +27.42%, max drawdown 5.20%, fees 189.38, funding paid 0.33 |
| Against BTC | alpha +18.90% a year, beta 0.07, information ratio 0.98 |
| Split at 2026-05-13 | picked {}: Sharpe 2.42 before, 2.83 after |
| Walk-forward | 6 folds, Sharpe 2.80, return +16.32% |
| Deflated Sharpe | 0.01 over 198 trial(s) (the study ledger); luck's best: Sharpe 4.91 |
| Robustness | +100.00% of 1 grid points positive; weakest neighbour n/ax the best; top market ADA made +23.89% of gains |
| Holdout | sealed from 2026-11-12 |

Notes:

- nulls not run: flipped() needs a strategy with a signal (a strategy written as one `step` has no signal to flip or randomise)
- clock phases not run: a 1-minute clock has no 6 phases a minute apart

Result hash `cc00955cbe8f1b26`, receipt `b762244733538b5f2404b0c67fc3826e0ebf3269e921b47c764956f3ec5afbd1`.
