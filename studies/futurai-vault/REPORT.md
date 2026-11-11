# FuturAI Labs vault, reverse engineered

Vault `0xb65dd7c56afbf3b272ab5fc49be44b47dca18003` on Hyperliquid. Studied 2026-11-11.

**It is a seven-step martingale ladder, sized small.** The ladder and exits are read exactly from 11,374
fills; the entry trigger is found only roughly; the handling of deep trips is not mechanical and not copied.
Thirteen changes to the rules were tested in four rounds and none beat the vault's own settings by the rule
set beforehand; a fifth round on 2023 to 2025 mark prices gave no verdict (the data misprices the strategy). Verdicts: the vault's book **holds out of sample** (deflated Sharpe not passed, 0.89 over 3
trials, 39 days); the replica **holds out of sample** (deflated Sharpe not passed, 0.00 over 30 trials, the
count when its gauntlet ran). 60 trials in the ledger now.

Labels: **measured** = from fills, an engine result hash or the venue's API; **inferred** = reasoning from
measured numbers; **untested** = not run.

## Record

| | Value | Label |
|---|---|---|
| Lifetime PnL, 2026-03-04 to 2026-11-11 | $14,558 on equity that grew from $18k to $441k by deposits | measured (Hyperliquid `vaultDetails`) |
| From fills: closed PnL, fees | $16,129, $1,292 on $6.73M volume (1.9 bps) | measured |
| Round trips | 2,776 closed, 15 at a loss; median hold 1.2 hours | measured |
| Position now | $2.9k notional on $441k equity (BTC and XRP, one buy each) | measured |
| Engine, vault's own book, 2026-10-03 to 2026-11-11 | +4.71% on its peak exposure ($123.7k) = $5,824; Sharpe 6.19, max drawdown 3.73% | measured, hash `a83c1281e778a553` |
| Same window, its fills | $5,991 closed PnL less $409 fees = $5,582 | measured |

The mirror is within 4% of the vault's realized number, so the engine's fills and fees fit this book.

The return on equity is modest because most of the equity sits idle: about 7% in eight months
(Hyperliquid shows 13.7% APR). The Sharpe of 6 is a 39-day number from a strategy that sells small
gains and holds its losers; it says little about the tail.

## Skill or luck

Mirror gauntlet, 1-minute clock, 2026-10-03 to 2026-11-11 (`mirror-card.md`): **holds out of sample**,
deflated Sharpe not passed (0.89 over 3 trials, under 0.95). Fading the book: Sharpe -7.76. No random run
and no stale run (its own positions at random earlier times) matched it, so the timing of its buys, not
just being long these markets, made the money in this window. 35 days in sample: every test here is weak.

## Rules

### The ladder (measured, stable from May 2026)

| Buy | Price, from the first fill | Size, x first order | Position after, x first | Exit, over average entry |
|---|---|---|---|---|
| 1 | entry | 1.00 | 1.00 | +0.560% |
| 2 | -2.25% | 1.00 | 2.00 | +0.567% |
| 3 | -3.54% | 1.93 | 3.93 | +0.580% |
| 4 | -5.04% | 3.80 | 7.73 | +0.603% |
| 5 | -7.00% | 7.47 | 15.20 | +0.652% |
| 6 | -9.85% | 14.68 | 29.88 | managed (below) |
| 7 | -14.9% | about 31.7 | about 61.6 | managed |

- Each add from the third on is 0.966x what is held. Price steps and sizes land within a few basis points
  trip after trip (10th to 90th percentile of the first add: -2.26% to -2.25%).
- One reduce-only limit sell for the whole position rests at the exit; it is re-placed after every add.
  The live order book on 2026-11-11 shows exactly this: for each held coin one sell at +0.56% and one buy
  at -2.25% of equal size.
- First order: about 0.36% of vault equity ($1,450 on $441k; $600 on $165k in September).
- At most 7 coins at once (time share at 7: 17%; never 8). Seven full ladders are 7 x 61.6 x 0.36% = 1.55x
  equity, which is the "max leverage 1.5x" in the vault's description. (inferred)
- Long only: 100% of held time. 85% of fills are maker; 32% of first buys are taker.
- March and April used -2.90% for the first step and +0.51% exits; the table is the setting since May.

### The entry (inferred, partly found)

Opening buys sit 0.9% under a 14-hour EMA of hourly closes (median -0.88%, interquartile range 0.27%, 90%
of entries at least 0.64% under; `trader.py entries` ranks 12 to 16 hours together, lift 3.3 over ordinary
minutes). Re-entry is quick when price is still under the level: 15% of trips reopen within 5 minutes of the
last exit. The replica rests a buy 0.88% under the live EMA; a looser level (0.68%) scored worse and was dropped.

### Deep trips (measured, not a rule I could write)

The 39 trips that reached six or more buys were closed with several sells, often taker, in pieces of 10%,
20%, 25% and 50%, some at a loss, with re-buys in between. Twice every open position was closed in the same
minute at a loss (2026-06-08 14:04, three coins, -$911; 2026-06-24 18:32, seven coins, about -$1,000). That
is a risk overlay or a person; the fills don't show a fixed trigger.

### Where the money comes from (measured, net of fees)

| Buys in the trip | Trips | Net PnL | Share of PnL | Share of capital-hours |
|---|---|---|---|---|
| 1 | 2,123 | $6,416 | 43.2% | 4.3% |
| 2 | 311 | $1,739 | 11.7% | 5.1% |
| 3 | 151 | $1,819 | 12.3% | 7.0% |
| 4 | 102 | $2,213 | 14.9% | 11.4% |
| 5 | 50 | $2,276 | 15.3% | 20.5% |
| 6 or more | 39 | $374 | 2.5% | 51.7% |

Best per dollar held: HYPE, LINK, ADA (about $7 to $8 a day per $1,000 held). Worst: XLM (a loss), BTC ($1.0),
AVAX ($1.8), XRP ($2.6). Descriptive, eight months, not a tested rule.

## The replica (`futurai.py`)

| Check | Result | Label |
|---|---|---|
| Vault trip opens with a replica open within 30 minutes, 3 Oct to 5 Nov | 68% (chance is about 5%) | measured |
| Same, 5 to 11 Nov (market-wide fall) | 38% | measured |
| Same side as the vault, of the market hours it held, full window | 55% (other side 0%, flat 45%) | measured |
| Daily return correlation with the vault's book | 0.08 full window; 0.34 to 5 Nov | measured |
| Replica return, 39 days, minute data | -0.17%, max drawdown 2.79% | measured, hash `94d028e7e6d6b656` |
| Replica, vault's lifetime on hourly bars (2026-03-04 to 2026-11-01) | +9.22%, max drawdown 4.78% | measured (coarse data) |
| Replica, 2025-06-05 to 2026-11-01 on hourly bars | +31.98%, Sharpe 1.42, max drawdown 10.38% | measured, hash `ae0653fe02fee8f4` |

By the kill condition written before the first run (daily return correlation under 0.5), **the book-level
rules are not fully found**. What is found: the ladder and exits (exact) and roughly where it enters. What
is missing shows on 5 to 10 November: the replica opened XRP into the fall and rode it to the seventh buy
(-$150 on $10k, its whole loss for the window), while the vault was full with other coins, trimmed its deep
trips on bounces and finished the week up. Which coin gets caught is path dependent, and the vault's handling
of caught coins is the part not copied.

Replica gauntlet on hourly bars (`replica-card.md`): **holds out of sample**, deflated Sharpe not passed
(0.00 over 30 trials). Walk-forward Sharpe 1.62 over 6 folds; alpha against BTC +23% a year, beta 0.18.
Nulls not run (a strategy written as one step has no signal to flip). Do not read it as an edge: it is a
description of what the vault does, on coarse data, with no funding charged.

## Can it be improved? Rounds 1 and 2: seven tries, none passed

Kill condition (STUDY.md): smaller max drawdown and higher return over drawdown than the replica on the
hourly run, and not worse on the minute window. Round 1 was four changes fixed in advance; round 2 was three
more after seeing round 1 and is weaker evidence for it.

| Change | 17 months, hourly: return | Max drawdown | 39 days, minute: return | Passed |
|---|---|---|---|---|
| Replica (the vault's settings) | +31.98% | 10.38% | -0.17% | |
| New trips only while BTC is over its 7-day EMA | +13.08% | 6.88% | -1.51% | no: return fell more than drawdown |
| Stop at 5 buys, 4% stop under average entry | -1.77% | 5.76% | -0.05% | no |
| Steps and exits scaled by 24-hour volatility | +17.01% | 15.56% | -3.86% | no |
| No new trip while cost held is over 35% of equity | +29.52% | 10.39% | -0.22% | no |
| Stop at 5 buys, no stop | -13.42% | 22.45% | -2.41% | no |
| Stop at 5 buys, 4x first order (same full-ladder notional) | -61.55% | 85.92% | -9.65% | no |
| Stop at 6 buys, 2x first order (same full-ladder notional) | -27.31% | 54.86% | +0.31% | no |

What the failures say (inferred):

- **The deep buys are what keeps the book alive.** They earn 2.5% of the profit, but they pull the average
  entry down far enough for a small bounce to close the trip. Cut them and trips never close, the seven slots
  fill with stuck coins, and the book stops trading while it falls. In the first half of the hourly run
  (2025-06 to 2026-03, before the vault existed) the 5-buy version lost 16% where the replica made 21%.
- **A stop turns the ladder into a loss machine.** The exit is +0.56%; one 4% stop on a 15x position costs
  more than a hundred clean trips make.
- **The small first order is the risk control.** Doubling or quadrupling it at the same full-ladder notional
  took the drawdown from 10% to 55% and 86%. The vault's idle equity is the margin of safety, not waste.
- The vault's settings are near the best of what was tried on these 17 months. That is a statement about
  this sample. The same ladder at seven buys has the 5-buy problem one step further down: a fall of more
  than about 15% from first entry in seven coins at once leaves it 1.5x long with nothing left to add.

## Rounds 3 and 4: market state at entry, and trimming deep trips

### Does anything known at entry warn of a deep trip? (event study, measured)

5,651 closed replica trips on the hourly run; "deep" is five or more buys. Features are from the last hour
closed before entry. Filters and thresholds were picked on 2025-06-05 to 2026-03-01 only (3,513 trips, 4.6%
deep) and tested on 2026-03-01 to 2026-11-01 (2,138 trips, 3.0% deep). Rank AUC of 0.5 is no information.

| Idea | Design-window AUC for "deep" | Reading |
|---|---|---|
| Regime: BTC or the coin against a 7-day EMA, 24h/72h/7d returns, breadth | 0.47 to 0.53 | nothing |
| Volatility: 24h, and 24h over 7d (BTC and the coin) | 0.46 to 0.50 | nothing |
| Bollinger stretch, 20h and 80h z-score; depth under the 14h EMA | 0.51 to 0.54 | nothing |
| Funding rate, 24h mean funding, premium (coin, BTC, market) | 0.50 to 0.54 | nothing on the design window |
| Long liquidations over 1h, 4h, 24h, against open interest (coin and market) | 0.46 to 0.49 | nothing |
| Open interest change, 24h: BTC / the ten markets' mean / the coin | 0.63 / 0.60 / 0.55 | deep share 2.1% in the lowest fifth of BTC OI change, 7.8% in the highest |

Mean PnL per trip is positive in every fifth of every feature: deep trips still close in profit, so a filter
can only buy a smaller drawdown with income. On the test window the ten-market OI change still sorted
(AUC 0.59) and BTC's did not.

The entry is already a dip buy under a moving average, which is why Bollinger stretch and "how far has it
fallen" add nothing: every entry is already stretched. A liquidation flush before entry does not make the dip
safer or worse in this sample.

### Filters and the trim rule against the replica (measured, hourly bars)

| Change | Design 2025-06 to 2026-03: return / max DD | Test 2026-03 to 2026-11: return / max DD | 39 days, minute | Passed |
|---|---|---|---|---|
| Replica | +20.62% / 10.38% | +9.49% / 4.78% | -0.17% | |
| No new trips while BTC OI is up over 5% in 24h | +18.49% / 4.18% | +8.63% / 4.99% | -0.22% | no: test drawdown not smaller |
| Same, over 1.6% | +15.35% / 4.18% | +7.04% / 4.03% | -0.35% | no: return fell more than drawdown |
| Half-size first order while BTC OI is up over 1.6% | +15.54% / 6.94% | +7.53% / 4.17% | -0.41% | no |
| No new trips while the ten markets' mean OI is up over 3.5% | +18.66% / 6.81% | +8.85% / 4.98% | -0.37% | no |
| Trim from the 6th buy: sell the last add 2% over its fill, re-rest it | +13.36% / 9.56% | +7.90% / 3.71% | +0.04% | no: fails the first half and the full run |
| Trim from the 5th buy | +14.11% / 7.76% | +7.62% / 3.75% | -0.22% | no |

- **The BTC OI filter is the nearest miss.** On the design window it removed or halved all three large
  drawdowns (June 2025 6.8% to under 2.5%, 10 October 2025 10.4% to 4.2%, February 2026 6.4% to 3.2%) for a
  tenth of the return. On the test window it cut neither of the two drawdowns (June 2026) and still cost a
  tenth. That is insurance that paid three times and then not at all, on five events. Not proven, and by the
  rule not an improvement. (inferred)
- **The trim rule** has no design window (its numbers come from the vault's fills), so all windows count. It
  lowers drawdown everywhere (8% to 25%) and costs about 30% of the return on the full run; return over
  drawdown is better only on the second half. Hourly bars are unkind to it: a trim can't sell in the hour its
  add filled. Worth a rerun on minute data, not a claim.

## Round 5: two more years from the open-interest set's mark price (no verdict)

ironflow/hyperliquid-open-interest carries an hourly mark price from May 2023, two years before the candles.
`build_mark.py` turns it into close-to-close hourly bars with OI and funding. The filters were run unchanged.

| Run (mark bars) | 2023-07 to 2025-06, never used before: return / max DD | 2025-06 to 2026-11: return / max DD |
|---|---|---|
| Replica | +14.30% / 37.40% | -16.20% / 44.91% |
| No new trips while BTC OI is up over 5% in 24h | +24.25% / 21.25% | -7.70% / 37.05% |
| No new trips while the ten markets' mean OI is up over 3.5% | +2.29% / 36.68% | -7.74% / 36.57% |

- **The dataset fails its calibration.** On 2025-06 to 2026-11 the same replica makes +31.98% with a 10.38%
  drawdown on candle bars and -16.20% with 44.91% on mark bars. Mark bars have half the real hourly range,
  so the +0.56% exits rarely fill, trips stay open and ladders run deep. None of the returns in this table is
  a number to quote. (measured)
- **What it is good for:** a world where exits fill badly and ladders go deep far more often. In that world
  the BTC OI filter beat the replica on both return and drawdown in both periods, including the two years it
  had never seen. The ten-market version did not. (measured on a mispriced dataset)
- **Reading:** together with round 3, the BTC OI filter helps when ladders go deep and costs about a tenth of
  the income when they don't. It is still not a tested improvement: its only clean test (2026-03 to 2026-11,
  candle bars) failed. It is the one idea here worth a paid month of minute data. (inferred)
- **The same run is a warning about the strategy itself:** it earns its return inside the hour. Anything that
  stops the small exits from filling (thin books, a slower bot, wider spreads) moves it from a 10% drawdown
  toward a 40% one. (inferred)

## Not tested, and why

- **A sweep of the vault's own numbers** (exit distance, step sizes, entry depth). It would show whether its
  settings sit on a plateau or a peak, at the price of more trials on a sample that has already had thirteen.
- **Dropping the weak markets** (BTC, AVAX, XRP, XLM). The per-market table is eight months in sample; testing
  it on the same months would be fitting.
- **Anything on minute data before 2026-10-03.** The 0xArchive key is on the free plan (30 days) and `0xbt
  data pull` works in whole months, so October was built from ironflow's free trades and the long run from
  ironflow's hourly candles. On hourly bars a take-profit can't fill in the hour its buy filled, the order of
  a buy and a sell inside one hour is unknown, and the run charged no funding (longs usually pay; about 11% a
  year on notional held at the base rate). A paid key would let the same variants run on minute data,
  which matters most for the trim rule.
- **The universe is the vault's own list** of ten markets, not a point-in-time rule. HYPE, the top earner,
  is in it because the vault chose it.
- **Holdout:** none. Nothing here can pass rung 5.

## Rerun

```bash
python3 hl_book.py                                   # fills, trips.json, trader_oct.json (no key)
export OXARCHIVE_API_KEY=...                         # November minute data
0xbt data pull --markets ADA,LINK,HYPE,SOL,DOGE,XRP,ETH,TRX,BNB,BTC --from 2026-11 --to 2026-11
python3 build_minutes.py 2026-10-03 2026-10-31 && python3 build_october.py   # October from ironflow trades
python3 build_hourly.py                              # needs ext/candles_1h.parquet and ext/oi_1h.parquet (STUDY.md)
python3 trips_replica.py && python3 event_study.py design          # then: event_study.py test

0xbt backtest mirror.py -p path=trader_oct.json -p clock=1m --start 2026-10-03 --end 2026-11-11   # a83c1281e778a553
0xbt backtest futurai.py --start 2026-10-03 --end 2026-11-11                                      # 94d028e7e6d6b656
0xbt backtest futurai.py --data data1h/hyperliquid --start 2025-06-05 --end 2026-11-01            # ae0653fe02fee8f4
python3 trader.py replicate trader_oct.json futurai.py --clock 1m --start 2026-10-03 --end 2026-11-11
python3 match.py
```

The vault trades on, so `hl_book.py` run later returns more fills than the 11,374 used here; the hashes
above need the `trader_oct.json` in this directory. Paper trading the replica: `oxb.Session`
(strategy-api.md, "Paper trading"). No live orders from this study.
