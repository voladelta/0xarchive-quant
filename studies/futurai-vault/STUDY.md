# FuturAI Labs vault: what rules make this book, and can they be improved?

Vault `0xb65dd7c56afbf3b272ab5fc49be44b47dca18003` on Hyperliquid ("High Sharpe, Low Volatility":
long-only, buys dips, sells rebounds, max leverage 1.5x). Study started 2026-11-11.

## Questions

1. What is the vault's record, honestly? **answered** (REPORT.md, "Record")
2. Skill or luck: does its book beat its nulls? **answered** (mirror gauntlet)
3. What rules produce the book? **partly answered** (ladder and exits exact; entry level rough; deep-trip
   handling not found; the replica misses the 0.5 return-correlation bar)
4. Does a changed rule set do better than the replica on the same data? **answered: no**, thirteen tries
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

## Round 3, declared before running (2026-11-11): entry filters from market state

Question: does anything known at entry tell a trip that will go deep (5 or more buys) from one that closes
clean? Candidates: regime (BTC and the coin against slow EMAs, BTC volatility, breadth), Bollinger stretch,
funding and premium, long liquidations, open interest change. Data: ironflow hourly funding, open interest
and liquidation events, with the hourly candles.

Method, to keep an honest test:
1. Event study on the replica's trips, **design window 2025-06-05 to 2026-03-01 only** (before the vault
   existed). Rank features by how they sort trips into deep and clean.
2. Pick at most four filters and their thresholds from the design window alone.
3. Run each once on the **test window 2026-03-01 to 2026-11-01** (hourly) and on the 39-day minute window.
   Same kill condition as before, judged on the test window: smaller max drawdown and higher return over
   drawdown than the replica, and not worse on the minute window.

### Round 3, step 1 result and the filters picked (design window only, before any test run)

3,513 replica trips, 4.6% deep. Regime (BTC or the coin against a 7-day EMA, 24h and 72h returns, volatility,
breadth), Bollinger stretch (20h and 80h), funding, premium and long liquidations do not sort deep trips from
clean ones (rank AUC 0.46 to 0.54). Open interest does: with BTC open interest up over 24 hours, deep share
rises from 2.1% in the lowest fifth to 7.8% in the highest (AUC 0.63); the ten markets' mean OI change
says the same (0.60). Mean PnL per trip is positive in every fifth of every feature, so a filter can cut
depth but will also cut income.

Filters, thresholds from the design window's quintile cuts:
- R3a: no new trips while BTC OI is up more than 5% over 24h (`oi_max=0.05`).
- R3b: no new trips while BTC OI is up more than 1.6% over 24h (`oi_max=0.016`).
- R3c: half-size first order while BTC OI is up more than 1.6% (`oi_max=0.016 oi_size=0.5`).
- R3d (the fourth and last slot, added after R3a to R3c ran): no new trips while the ten markets' mean OI
  is up more than 3.5% over 24h (`oi_market=ALL oi_max=0.035`), the design window's top-fifth cut.

### Round 3 result: no filter passed

On the test window (2026-03 to 2026-11) none of the four OI filters had both a smaller drawdown and a higher
return over drawdown than the replica (REPORT.md). The BTC OI filter cut all three large design-window
drawdowns and none on the test window.

## Round 4, declared before running: trim deep trips the way the vault does

The vault's deep trips sell a piece on a bounce and buy it back lower (REPORT.md "Deep trips"); its partial
sells sit 0.7% to 2.8% over the last buy. As a rule: from `trim_level` buys on, offer the last add `trim`
above its own fill; when it sells, step back one level and rest that add again. Numbers from the vault's
fills, not from returns: `trim=0.02`, and two levels: R4a `trim_level=6` (where the vault starts), R4b
`trim_level=5`. No design window is used, so both halves and the full hourly run count; same kill condition.

### Round 4 result: neither trim passed

Both lower drawdown in every window and both lose return over drawdown on the first half and the full run
(REPORT.md). Thirteen changes in four rounds, none passed. Stopping here: more tries on this sample would be
fitting it.

`ext/oi_1h.parquet`, `ext/funding_1h.parquet` and `ext/liq_1h.parquet` are hourly reads of
ironflow/hyperliquid-open-interest, -funding and -liquidations (`data/events`), months 2025-05 to 2026-10,
the vault's 18 markets: one row per coin and hour (OI snapshot; funding rate and premium; long and short
liquidation notional summed).

## Round 5, declared before running (2026-11-11): the OI filter on two years it has not seen

ironflow/hyperliquid-open-interest also has an hourly mark price from 2023-05-20, two years before the
hourly candles start. `build_mark.py` makes a third dataset from it: one bar per hour whose close is the
hour's last mark and whose open is the previous hour's, so high and low are just the larger and smaller of
the two. No intrahour range: fills are understated, more than on the candle bars. To size that bias the same
build also covers 2025-06 to 2026-10, where the candle-bar result is known.

Test, fixed in advance: the replica against R3a (`oi_max=0.05`) and R3d (`oi_market=ALL oi_max=0.035`),
unchanged, on 2023-07-01 to 2025-06-01. HYPE lists in late 2024 and joins when its data starts. Same kill
condition: smaller max drawdown and higher return over drawdown than the replica on that window.
Known gap: 301 hours without rows on 85 evenings, August to December 2024.

### Round 5 result: the instrument failed its calibration, so no verdict

On 2025-06-05 to 2026-11-01 the mark bars give the replica -16.20% with a 44.91% drawdown where the candle
bars give +31.98% and 10.38%. Mark bars have about half the real hourly range (BTC 0.30% against 0.63%), the
+0.56% exits mostly fill inside the hour, and without them trips stay open and ladders run deep. So this
dataset cannot price the strategy, and a pass or fail on it is not a verdict. What it does show is in
REPORT.md. (`0xbt data check` also flags these files: price rows before the engine's 2025-03-22 fills era.)
