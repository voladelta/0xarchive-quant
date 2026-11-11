# futurai.py: holds out of sample

**Verdict: holds out of sample** (rung 4 of 6: loses after costs / fails nulls / in-sample only / holds out of sample / passes deflated Sharpe / passes sealed holdout).
- deflated Sharpe 0.00 over 30 trial(s), under 0.95

2025-06-05 to 2026-11-01, params {}.

| Check | Result |
|---|---|
| After costs | Sharpe 1.42, return +31.98%, max drawdown 10.38%, fees 213.57, funding paid 0.00 |
| Against BTC | alpha +23.03% a year, beta 0.18, information ratio 0.93 |
| Split at 2026-05-13 | picked {}: Sharpe 1.38 before, 1.98 after |
| Walk-forward | 6 folds, Sharpe 1.62, return +16.40% |
| Deflated Sharpe | 0.00 over 30 trial(s) (the study ledger); luck's best: Sharpe 5.69 |
| Robustness | +100.00% of 1 grid points positive; weakest neighbour n/ax the best; top market HYPE made +17.34% of gains |
| Holdout | sealed from 2026-11-12 |

Notes:

- nulls not run: flipped() needs a strategy with a signal (a strategy written as one `step` has no signal to flip or randomise)
- clock phases not run: a 1-minute clock has no 6 phases a minute apart

Result hash `ae0653fe02fee8f4`, receipt `b49b0809c0cde378538e09987ff38ec0fb2734bf4cbec253492b5a990b4b7d60`.
