# FuturAI Labs vault: what rules make this book, and can they be improved?

Vault `0xb65dd7c56afbf3b272ab5fc49be44b47dca18003` on Hyperliquid ("High Sharpe, Low Volatility":
long-only, buys dips, sells rebounds, max leverage 1.5x). Study started 2026-11-11.

## Questions

1. What is the vault's record, honestly? **answered** (REPORT.md, "Record")
2. Skill or luck: does its book beat its nulls? **answered** (mirror gauntlet)
3. What rules produce the book? **partly answered** (ladder and exits exact; entry level rough; deep-trip
   handling not found; the replica misses the 0.5 return-correlation bar)
4. Does a changed rule set do better than the replica on the same data? **answered: one of nineteen does**
   (`pick=5`, the five most volatile markets; holds out of sample, deflated Sharpe not passed)
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

## Round 6, declared before running (2026-11-11): which markets, and a plateau check

**Selection.** The vault's best markets per dollar held were its most volatile (HYPE, LINK, ADA) and its
worst was BTC. As a point-in-time rule: new trips only in the `pick` markets with the highest 7-day
volatility of hourly returns. The numbers are fixed here, not tuned:
- R6a: the vault's ten, `pick=7` (the slot count).
- R6b: the vault's ten, `pick=5`.
- R6c: the 17 markets the vault has ever traded (its ten plus AVAX, BCH, HBAR, LTC, NEAR, SUI, XLM), `pick=10`.
  TON is left out because it delisted in June 2026 and the hourly candles stop; that is a small survivorship
  bias in this variant's favour. R6c's own baseline is the same 17 with no pick.
No design window (nothing is fitted), so both halves and the full hourly run count; same kill condition.

**Plateau check.** One setting moved at a time around the vault's own: `exit_scale` 0.5, 0.75, 1.5, 2;
`step_scale` 0.75, 1.5; `entry` -0.005, -0.012, -0.016; `ema_hours` 6, 24, 48. This describes the surface
(a plateau or a peak); a neighbour that scores higher is a thing to test on new data, not a setting to adopt.

### Round 6, selection result, and two controls declared before running them

R6b (`pick=5`) is the first variant to pass: smaller drawdown and higher return over drawdown than the
replica in both halves, the full run and the minute window. R6a (`pick=7`) passes except the second half
(1.96 against 1.99). R6c fails: the 17-market book is far worse than the ten with or without the pick.
Sixteen tries before this one, so a pass can be luck. Two controls to see whether volatility ranking is doing
the work or just holding fewer coins:
- C1: `max_open=5`, no pick (five slots, any market).
- C2: `pick=-5`, the five calmest markets (if ranking matters this should be clearly worse than R6b).

### Round 6, controls and plateau result

C1 (five unranked slots) keeps most of the return and loses the second-half drawdown cut; C2 (five calmest)
makes +9.79% against R6b's +24.40% at a larger drawdown. The ranking does the work. Plateau check: exits
are a plateau; add distances are a peak with a cliff on the tight side; shallow entries and long EMAs are
worse (REPORT.md). 106 trials. `pick=5` gauntlet: holds out of sample, deflated Sharpe 0.00 over 106 trials.

## Round 7, declared before running (2026-11-11): charge funding, then trade on it

**Fix.** The hourly runs so far charged no funding: the engine needs a price on the settlement row and the
hourly dataset had none there. `build_hourly.py` now puts the hour's close on each settlement row as the mark
price. Every hourly result is rerun with funding charged; the old hashes are superseded and the new ones are
the baseline from here.

**Idea.** Longs pay funding when it is positive and are paid when it is negative. As entry filters, fixed
before running:
- R7a: new trips only in markets whose last settled funding rate is below zero (`fr_max=0`).
- R7b: only where the 24-hour mean funding rate is below zero (`fr_max=0 fr_hours=24`).
- R7c: softer: skip a market only while its funding is above the venue's base rate of 0.00125% an hour
  (`fr_max=0.0000126`), where longs are crowded and paying extra.
Each is run alone and on top of `pick=5`. Kill condition as before, against the funding-charged replica (and
against funding-charged `pick=5` for the stacked runs), both halves and the full run. Round 3's event study
found no link between funding at entry and trip depth, so the prior is that these cut income without cutting risk.

### Round 7 hourly result, and one follow-up declared before running

Funding charged costs the replica 0.43% of equity over 17 months (+31.49% against +31.98%). Alone, none of the
three funding filters passes. On top of `pick=5`, R7a (`fr_max=0`) passes on all three hourly windows with a
third of the return (+7.61%, max drawdown 1.46%). A filter that only trades less can look good on a ratio, so
one follow-up: the same rules at three times the first order (`base=0.0108`), to compare drawdown at about the
return of plain `pick=5`. It counts as a pass only if, at a full-run return of at least `pick=5`'s, its
drawdown is smaller in both halves and the full run.

### Round 7 result

At three times the first order `pick=5 fr_max=0` makes +24.57% with a 4.39% drawdown on the full run (Sharpe
4.25) against `pick=5`'s +24.01% and 6.59%, but its second-half drawdown is 3.01% against 2.87% and it is behind
on the minute window: not a pass by the rule above. A near-miss worth a forward test at the normal size.
142 trials.

## Round 8, declared before running (2026-11-11): more income from the funding state at the vault's worst case

Round 7's near-miss made `pick=5`'s return at a smaller drawdown only by tripling the first order, which lifts
the worst case (every ladder full) from the vault's 1.5x equity to 4.7x. Three ways to take more income without
that, fixed here before any run. This is the eighth look at the same 17 months.

**A. Size by funding state, worst case held at the vault's.** A full ladder is 61.55 first orders, so the
vault's seven are 1.53x equity.
- R8a: `pick=5 fr_max=0 base=0.0083 max_open=3`: negative funding only, 2.3x the first order, three slots (1.53x).
- R8b: `pick=5 fr_max=0 base=0.0124 max_open=2`: the same at 3.45x and two slots (1.53x).
- R8c: `pick=5 fr_max=0 fr_boost=3 fr_else=1 cap=1.55`: a tilt, not a filter. Markets with negative funding
  open at 3x the first order, the rest at 1x. `cap` is new: each open trip reserves its full ladder, and no new
  trip opens if the reserved notional would pass 1.55x equity.
- R8d: R8c plus `fr_skip=0.0000126`: no new trips in markets paying over the base rate (round 7's R7c).

**B. More trips in the good state, same size.**
- R8e: `pick=5 fr_max=0 entry=-0.005`: the shallower entry the plateau check found worse in general, taken only
  where funding is negative. Its baseline is `pick=5 fr_max=0`; it counts only if return rises and return over
  drawdown does not fall, in both halves and the full run.

**C. Front-load the first order.** One-buy trips made 43% of the vault's net profit on 4% of its capital-hours
(REPORT.md). Round 2 scaled the whole ladder and blew up; this scales only the first order.
- R8f: `pick=5 front=2`: first order 2x, every add the vault's absolute size. Worst case 7 x 62.55 x 0.36% =
  1.58x. The cost: the average entry sits higher after each add, so the exit needs a bigger bounce.

**Rule.** Against funding-charged `pick=5` (+24.01% / 6.59% full, +15.46% / 6.59% and +7.45% / 2.87% the halves,
+1.81% / 1.94% on the minute window). "More profit, less drawdown" means: full-run return at least `pick=5`'s,
max drawdown smaller in both halves and the full run, and on the minute window return and return over drawdown
both at least `pick=5`'s. A better ratio on less return is a near-miss, as in round 7. If a lever from A and
R8f both pass, one stacked run is allowed. Defaults must reproduce `f0e81c38e8aba68c` and `97a2ad7458718e91`.

### Round 8 result, and controls declared before running them

Correction to the declaration: seven vault ladders are 7 x 61.55 x 0.36% = 1.55x equity, not 1.53x. So
`cap=1.55` sits on the edge: it admits six 1x trips, or two 3x trips and nothing else, until equity grows.

| Variant | First half | Second half | Full: return / max DD / Sharpe | Minute window | Verdict |
|---|---|---|---|---|---|
| `pick=5` (baseline) | +15.46% / 6.59% | +7.45% / 2.87% | +24.01% / 6.59% / 1.82 | +1.81% / 1.94% | |
| R8a negative only, 2.3x, 3 slots | +10.20% / 2.49% | +6.48% / 2.31% | +17.31% / 2.49% / 4.05 | +1.86% / 3.00% | near-miss: less return, minute ratio worse |
| R8b negative only, 3.45x, 2 slots | +13.45% / 2.82% | +8.38% / 3.46% | +22.90% / 3.46% / 3.73 | +2.18% / 4.19% | fail |
| R8c tilt 3x/1x, cap | +17.94% / 6.71% | +9.07% / 2.73% | +28.56% / 6.71% / 2.06 | +2.25% / 1.82% | fail: first-half drawdown 0.12 points over |
| R8d tilt 3x/1x, skip over base rate, cap | +17.19% / 5.20% | +8.81% / 2.76% | +27.42% / 5.20% / 2.44 | +2.23% / 1.82% | **pass** |
| R8e negative only, entry -0.5% | +4.93% / 1.67% | +3.52% / 1.05% | +8.60% / 1.67% / 4.28 | +1.02% / 1.67% | fail against its baseline (ratio falls in the first half) |
| R8f first order 2x | +20.67% / 7.63% | +11.05% / 5.79% | +33.89% / 7.63% / 1.78 | +2.39% / 2.21% | fail: more return, more drawdown |

R8d is the second pass in the study: nineteen changes through round 6, six in round 7, six here. R8f did not pass, so no stacked run. The margins in
the second half (2.76% against 2.87%) and on the minute window are thin. Before believing it:

- C3, is it the funding state or just more size? `pick=5 fr_skip=0.0000126 base=0.0044 cap=1.55`: the same
  skip and cap, every first order 1.22x, which should land near R8d's return. If the tilt matters, C3's
  drawdown is clearly larger than R8d's at that return.
- C4, the tilt upside down: `pick=5 fr_max=0 fr_boost=1 fr_else=3 fr_skip=0.0000126 cap=1.55`: 3x where
  funding is not negative. Should be clearly worse than R8d.
- Plateau, one setting at a time around R8d: `fr_boost` 2 and 4; `cap` 1.25, 1.6 and 2.0; `fr_hours=8`.
  The pass should not hang on `cap=1.55` being on the edge above.
- `0xbt gauntlet` on R8d.

### Round 8, controls and plateau result, and one check on other coins declared before running

- C3 (every first order 1.22x, same skip and cap) lands on R8d's return, +27.63%, with a larger drawdown:
  6.09% against 5.20% full, 3.75% against 2.76% in the second half, 2.22% against 1.82% on the minute window.
- C4 (3x where funding is not negative) makes +45.63% with a 13.49% drawdown: return over drawdown 3.4 against
  R8d's 5.3. The drawdown lives in the trips opened while funding is not negative.
- Plateau: every neighbour beats `pick=5` on return and on drawdown in the first half, the full run and the
  minute window. The second half does not hold: R8d's 2.76% against 2.87% becomes 2.90% (`cap=1.6`), 2.94%
  (`fr_boost=2`), 3.89% (`cap=2.0`), 3.97% (`cap=1.25`), 4.91% (`fr_boost=4`). So "more profit" is a plateau and
  "less drawdown in the second half" is one point. `fr_hours=8` scored higher than R8d (+25.74% / 2.76% full).
- Gauntlet on R8d (`tilt-card.md`): holds out of sample, deflated Sharpe 0.01 over 198 trials.

One check on coins R8d was not found on: the seven other markets the vault has traded (AVAX, BCH, HBAR, LTC,
NEAR, SUI, XLM), hourly bars only. R6c ran them once inside the 17-market book, never with funding.
- U0: those seven, `pick=4` (the more volatile half, as `pick=5` is of ten).
- U1: U0 with R8d's tilt, skip and cap.
- U2: U1 with `fr_hours=8`.
The tilt carries over if U1 beats U0 on full-run return and max drawdown and on return over drawdown in both
halves. `fr_hours=8` replaces `fr_hours=1` in the recommendation only if U2 beats U1 on return over drawdown
in the full run and both halves here, as it did on the ten.

### Round 8, other-coins result, and two normal-size runs declared before running

U0 (the seven, `pick=4`): -6.86% / 26.66% full. U1 (with the tilt): +10.75% / 31.50% full; first half +5.48% /
8.69% against -10.37% / 16.68%, second half +8.59% / 22.95% against +7.98% / 8.56%. The tilt does not carry
over: more return, more drawdown, and the second half is far worse. U2 (`fr_hours=8`) does not beat U1, so
`fr_hours` stays 1. To tell "the funding state means nothing on these coins" from "3x size is what hurts":
- U3: the seven, `pick=4 fr_max=0` (negative funding only, normal size).
- U4: the seven, `pick=4 fr_skip=0.0000126` (skip over the base rate only, normal size).
Read against U0 on return over drawdown; no pass or fail, this is a diagnosis.

### Round 8, diagnosis on the other coins

U3 (negative funding only, normal size): +6.29% / 7.98% full against U0's -6.86% / 26.66%; first half +3.75% /
0.59%, second half +2.44% / 7.98% against U0's +7.98% / 8.56%. U4 (skip only): +8.00% / 16.94% full. So the
funding state helps on these coins in the first half and not in the second, and the second half is one trip:
BCH, opened 2026-05-27 under negative funding, took all seven buys and sat 12 weeks before its exit filled. At
3x that one ladder was 58% of equity and is U1's 22.95% drawdown.

The same thing on the ten: R8d took three 3x trips to all seven buys (ADA and DOGE together on 2026-01-31, SOL
on 2026-02-05), each just under 60% of equity, and each bounced out inside a day. R8d's pass rests on those
bounces. `cap` bounds the book's notional, not how much of it sits in one coin.

## Round 9, declared before running (2026-11-11): tilt the shallow buys only

Round 8's tail is the deep end of a 3x ladder. In R8d's run, trips that end within four buys are 96% of trips
and about 64% of gross income; buys five to seven are where the size is. So: in a market with negative funding,
buys one to four are 3x the vault's, and buys five to seven are the vault's own size (`boost_buys=4`). A full
ladder is then 77 first orders, 1.25x the vault's, not 3x. The known cost, from R8f: the average entry sits
higher going into the deep buys, so a deep trip needs a bigger bounce (6.4% from the last add, against 4.6%).

- R9a: `pick=5 fr_max=0 fr_boost=3 fr_else=1 fr_skip=0.0000126 cap=1.55 boost_buys=4` on the ten. Round 8's
  rule against `pick=5`, all four windows.
- R9b: the same on the other seven with `pick=4`, against U0: full-run return and max drawdown both better,
  return over drawdown better in both halves.
One variant, no tuning of the 4. It replaces R8d as the candidate only if R9a passes; R9b says whether it
travels.

### Round 9 result: fails on both coin sets

R9a on the ten: +29.77% / 7.24% full against `pick=5`'s +24.01% / 6.59%; first half +18.98% / 5.60%, second
half +9.13% / 7.24% against +7.45% / 2.87%; minute window +2.49% / 1.82%. More return, and the second-half
drawdown is two and a half times the baseline's: an ADA trip opened 2026-06-04 took all seven buys and sat ten
days, because its average entry was too high for the bounce it got. R9b on the seven: +9.06% / 29.45% against
U0's -6.86% / 26.66%. Trading the concentration tail for a slow-exit tail is worse. R8d stays as round 8 left
it: a pass on the vault's ten that does not travel. 32 changes in nine rounds, two passes; 220 distinct results
in the ledger.

Measured exposure on the full hourly run (`ctx.positions` x price over equity, each step): the replica peaks at
1.21x gross and 0.21x in one coin; `pick=5` at 0.84x and 0.20x; R8d at 1.18x and 0.59x (DOGE, 2026-01-31);
round 7's 3x filter at 2.38x and 0.60x.
