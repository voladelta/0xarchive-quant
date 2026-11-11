# mirror.py: holds out of sample

**Verdict: holds out of sample** (rung 4 of 6: loses after costs / fails nulls / in-sample only / holds out of sample / passes deflated Sharpe / passes sealed holdout).
- deflated Sharpe 0.89 over 3 trial(s), under 0.95

2026-10-03 to 2026-11-11, params {}.

| Check | Result |
|---|---|
| After costs | Sharpe 6.19, return +4.71%, max drawdown 3.73%, fees 48.75, funding paid 1.99 |
| Against BTC | alpha +56.96% a year, beta 0.10, information ratio 5.71 |
| Nulls | flipped Sharpe -7.76; random mean -5.00, +0.00% at or above; stale mean -4.88, +0.00% at or above; redrawn every 8 h |
| Split at 2026-10-29 | picked {}: Sharpe 6.70 before, 5.41 after |
| Deflated Sharpe | 0.89 over 3 trial(s) (the study ledger); luck's best: Sharpe 2.77 |
| Robustness | +100.00% of 1 grid points positive; weakest neighbour n/ax the best; top market ADA made +24.42% of gains |
| Holdout | sealed from 2026-11-12 |

Notes:

- clock phases not run: a 1-minute clock has no 6 phases a minute apart
- walk-forward not run: the window is shorter than 180d plus two 60d tests
- 35 days in sample: under a year, so every test here is weak

Result hash `a83c1281e778a553`, receipt `4976eb9976a6e5c5b3e8e1f6e4da0da2902c6aa7f55de73bca597793a75d78a7`.
