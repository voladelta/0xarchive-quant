# FuturAI Labs vault: what rules make this book, and can they be improved?

Vault `0xb65dd7c56afbf3b272ab5fc49be44b47dca18003` on Hyperliquid ("High Sharpe, Low Volatility":
long-only, buys dips, sells rebounds, max leverage 1.5x). Study started 2026-11-11.

## Questions

1. What is the vault's record, honestly? **answered** (REPORT.md, "Record")
2. Skill or luck: does its book beat its nulls? **answered** (mirror gauntlet)
3. What rules produce the book? **partly answered** (ladder and exits exact; entry level rough; deep-trip
   handling not found; the replica misses the 0.5 return-correlation bar)
4. Does a changed rule set do better than the replica on the same data? **answered: no**, seven tries
   (REPORT.md; the minute window is 39 days and the 17-month run is on hourly bars)

## Hypothesis

The book is a fixed long-only martingale ladder run on about ten large perps: a base buy when price is
under a slow moving average, adds at fixed drops from the first fill with sizes near 1x what is held, and
one reduce-only exit a fixed distance over the average entry. Its income is the sum of small take-profits;
its risk is every ladder filling at once in a market-wide fall.

## Spec

- **Universe:** the ten markets the vault traded from 2026-10-03: ADA, BNB, BTC, DOGE, ETH, HYPE, LINK,
  SOL, TRX, XRP. This is the vault's own list, not a point-in-time rule: it is used to copy the book, and
  it is survivorship-free only in the sense that the vault picked it before the window.
- **Clock:** 1 minute, resting limit orders.
- **Signal, sizing, exits:** read from the fills (REPORT.md "Rules"), not tuned on returns.
- **Costs:** engine defaults (fees, funding, 2 bps fallback slippage).
- **Windows:**
  - minute data, 2026-10-03 to 2026-11-11 (39 days). November is `0xbt data pull`; October is built by
    `build_october.py` from ironflow/hyperliquid-trades and -funding (the free 0xArchive key reads 30 days
    and `data pull` works in whole months). Its bars match ironflow's hourly candles exactly.
  - hourly bars, 2025-06-01 to 2026-10-31, built by `build_hourly.py` from ironflow/hyperliquid-candles-1h,
    one row per hour. Coarse: a take-profit can't fill in the hour its buy filled, so income is understated;
    used for drawdowns and for comparing variants, not for a headline return.
- **Holdout:** none worth the name. The seal is set past the end of the data (2026-11-12); 39 days leaves
  nothing to hold back. No verdict here can pass rung 5.

## Kill conditions (written before the first backtest)

- Rules: the replica is on the same side as the vault for under half of the market hours the vault held,
  or its daily return correlation with the vault's book is under 0.5. Then the rules are not found.
- Improvement: a variant counts only if, on the 18-month hourly run, its maximum drawdown is smaller than
  the replica's **and** its return over drawdown is higher, and it does not lose to the replica on the
  39-day minute window. Otherwise it is not an improvement, whatever its return.
- Variants are fixed before running: at most four, each one change justified by something in the fills.

## Round 1 result (2026-11-11): no variant passed

BTC trend gate, a 5-buy cap with a 4% stop, volatility-scaled steps, and a 35% cost budget each did worse
than the replica on return over drawdown (REPORT.md has the table). The stop was the worst: it turns the
ladder's paper losses into real ones.

## Round 2, declared before running

Round 1 was four tries and all failed, so this is a second look at the same data and counts as such: seven
variants in total. One idea, from the vault's own profit split: trips that end after one buy made 43% of
its net profit on 4% of its capital-hours, and trips of six or more buys made 2.5% on 52%. So spend the
same worst-case notional on a shallower ladder with a bigger first order.

- R2a: `max_level=5`, base unchanged (what the cut alone does).
- R2b: `max_level=5 base=0.0144`: 4x the base, the same full-ladder notional as the vault (7 x 15.2 x 1.44% = 1.53x).
- R2c: `max_level=6 base=0.0072`: 2x the base, the same full-ladder notional (7 x 29.9 x 0.72% = 1.51x).

Same kill condition, plus: the variant must beat the replica on return over drawdown in both halves of the
hourly run (2025-06-05 to 2026-03-01, before the vault existed, and 2026-03-01 to 2026-11-01).

## Round 2 result: no variant passed

All three lost money on the hourly run with drawdowns of 22% to 86% (REPORT.md). The deep buys are what
closes stuck trips; a bigger first order at the same full-ladder notional multiplies the drawdown.

## Data notes

`ext/candles_1h.parquet` (ignored by git) is this query over ironflow/hyperliquid-candles-1h, months 2025-05
to 2026-10: `SELECT coin, epoch_ms(timestamp) ts, open, high, low, close, volume, trades WHERE dex='' AND
market_class='perp' AND coin IN (the vault's 18 markets) ORDER BY coin, ts`. The October minute bars built
from ironflow trades sum to the same highs, lows and volume as those hourly candles (checked on BTC, 31 Oct).
