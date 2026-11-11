# futurai.py: holds out of sample

**Verdict: holds out of sample** (rung 4 of 6: loses after costs / fails nulls / in-sample only / holds out of sample / passes deflated Sharpe / passes sealed holdout).
- deflated Sharpe 0.00 over 106 trial(s), under 0.95

2025-06-05 to 2026-11-01, params {}.

| Check | Result |
|---|---|
| After costs | Sharpe 1.84, return +24.40%, max drawdown 6.53%, fees 163.81, funding paid 0.00 |
| Against BTC | alpha +16.79% a year, beta 0.07, information ratio 0.73 |
| Split at 2026-05-13 | picked {}: Sharpe 1.78 before, 2.60 after |
| Walk-forward | 6 folds, Sharpe 2.55, return +12.46% |
| Deflated Sharpe | 0.00 over 106 trial(s) (the study ledger); luck's best: Sharpe 4.53 |
| Robustness | +100.00% of 1 grid points positive; weakest neighbour n/ax the best; top market HYPE made +28.17% of gains |
| Holdout | sealed from 2026-11-12 |

Notes:

- nulls not run: flipped() needs a strategy with a signal (a strategy written as one `step` has no signal to flip or randomise)
- clock phases not run: a 1-minute clock has no 6 phases a minute apart

Result hash `51694e022f0e2210`, receipt `e15349f89e22dfee34167b23b110b74e0cc255e2e3e76d04556ae1be15728f12`.
