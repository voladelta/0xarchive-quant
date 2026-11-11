# FuturAI Labs vault, reverse engineered

Vault `0xb65dd7c56afbf3b272ab5fc49be44b47dca18003` on Hyperliquid. Studied 2026-11-11.

**It is a seven-step martingale ladder, sized small.** The ladder and exits are read exactly from 11,374
fills; the entry trigger is found only roughly; the handling of deep trips is not mechanical and not copied.
Thirty-two changes to the rules were tested in nine rounds. Two passed the rule set beforehand. **Trade only
the five most volatile of the ten markets** (`pick=5`) had a smaller drawdown and a higher return over
drawdown than the replica in both halves of the hourly run, the full run and the 39-day minute window. Its
gauntlet rung is **holds out of sample**, deflated Sharpe not passed (0.00 over 106 trials). On top of it, **a
size tilt by funding state under a worst-case cap** (round 8) made more than `pick=5` at a smaller drawdown
in every window, +27.42% / 5.20% against +24.01% / 6.59% on the full run; it also **holds out of sample**
(deflated Sharpe 0.01 over 198 trials), its second-half margin is one point wide, and it failed on seven
coins outside the vault's list. The other thirty failed; a round on 2023 to 2025 mark prices gave no verdict
(the data misprices the strategy).
Verdicts on the rest: the vault's book **holds out of sample** (deflated Sharpe not passed, 0.89 over 3
trials, 39 days); the replica **holds out of sample** (deflated Sharpe not passed, 0.00 over 30 trials, the
count when its gauntlet ran). 220 distinct results in the ledger now.

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

## Round 6: which markets, and how fragile the vault's numbers are

### Selection by volatility (measured, hourly bars; nothing fitted, so every window counts)

New trips only in the `pick` markets with the highest 7-day volatility of hourly returns, re-ranked each hour.

| Run | 2025-06 to 2026-03: return / max DD | 2026-03 to 2026-11: return / max DD | Full: return / max DD / Sharpe | 39 days, minute | Passed |
|---|---|---|---|---|---|
| Replica (ten markets) | +20.62% / 10.38% | +9.49% / 4.78% | +31.98% / 10.38% / 1.42 | -0.17% | |
| Seven most volatile (`pick=7`) | +19.99% / 8.81% | +9.11% / 4.64% | +30.85% / 8.81% / 1.65 | +1.45% | no: second half 1.96 against 1.99 |
| **Five most volatile (`pick=5`)** | +15.83% / 6.53% | +7.44% / 2.87% | +24.40% / 6.53% / 1.84 | +1.81% | **yes** |
| Control: five slots, any market (`max_open=5`) | +19.01% / 7.95% | +8.00% / 5.21% | +28.45% / 7.95% / 1.46 | +1.18% | |
| Control: five calmest (`pick=-5`) | +2.28% / 8.30% | +3.14% / 4.52% | +9.79% / 8.68% / 0.66 | -1.41% | |
| 17 markets the vault ever traded, no pick | +5.65% / 17.23% | +8.82% / 11.68% | +9.11% / 23.98% / 0.36 | | |
| 17 markets, ten most volatile | +2.30% / 12.47% | +7.80% / 9.60% | +5.41% / 22.53% / 0.28 | | no |

- **The ranking does the work, not just holding fewer coins.** The five most volatile make +24.4% and the five
  calmest +9.8% at a larger drawdown. Five unranked slots keep most of the return but not the drawdown cut in
  the second half. The vault's own fills say the same thing independently: its best markets per dollar held
  were HYPE, LINK and ADA and its worst BTC.
- **Why it works (inferred):** the exit is a fixed +0.56%. A volatile coin crosses that many times a day; a
  calm one ties up a slot and a ladder for the same exit.
- **What it costs:** about a quarter of the return (24.4% against 32.0%) for a drawdown 37% smaller. It is a
  better ratio, not more money. Size the first order up by a quarter and the drawdown comes back.
- **How much to believe it:** it is the one pass in nineteen tries, on hourly bars, with no funding and no
  holdout; deflated Sharpe 0.00 over 106 trials. HYPE made 28% of its gains. The minute-window gain is mostly
  one avoided stuck trip. Treat it as the best-supported change here, not as proven.
- **The vault's ten are a good list.** The wider 17-market book is far worse (24% drawdown), with or without
  the pick. Part of the vault's result is which markets it chose, and that choice can't be tested here.

`pick5-card.md` is its gauntlet card (the card prints `params {}`; the numbers are the `pick=5` run, hash `51694e022f0e2210`).

### Plateau check on the vault's own settings (measured; first half / second half of the hourly run)

| Setting moved | Return / max DD, 2025-06 to 2026-03 | Return / max DD, 2026-03 to 2026-11 |
|---|---|---|
| Vault's settings | +20.62% / 10.38% | +9.49% / 4.78% |
| Exits x0.5 | +14.10% / 6.49% | +6.08% / 3.35% |
| Exits x0.75 | +17.87% / 6.49% | +7.79% / 3.55% |
| Exits x1.5 | +25.90% / 10.52% | +12.45% / 7.84% |
| Exits x2 | +26.66% / 13.52% | +16.26% / 7.52% |
| Add distances x0.75 | -28.63% / 41.88% | +12.91% / 6.73% |
| Add distances x1.5 | +2.87% / 13.37% | +5.95% / 4.34% |
| Entry 0.5% under the EMA | -3.70% / 19.79% | +10.88% / 7.72% |
| Entry 1.2% under | +11.59% / 10.92% | +7.98% / 1.83% |
| Entry 1.6% under | +14.55% / 5.65% | +5.91% / 3.52% |
| EMA 6 hours | +19.13% / 6.67% | +8.22% / 5.50% |
| EMA 24 hours | +12.39% / 10.55% | +8.89% / 9.19% |
| EMA 48 hours | +4.64% / 10.84% | +9.27% / 8.34% |

- **Exits are a plateau.** Wider exits earn more and draw down more, in step; no setting is clearly better.
- **Add distances are a peak with a cliff.** A quarter tighter and the first half loses 29% with a 42% drawdown;
  half wider and the return is gone. The vault's spacing is the fragile part: it fits how far these markets
  fell in this sample, and a sample with deeper falls would want wider steps.
- **Entry depth has a cliff on the shallow side** (0.5% under loses money in the first half) and trades return
  for drawdown on the deep side. **A longer EMA is worse**; 6 to 14 hours is flat.
- None of these is adopted. They are twelve more tries on the same data.

## Round 7: funding charged, and trading on it (measured, hourly bars unless said)

**Funding is now charged on the hourly runs** (`build_hourly.py` puts a mark price on each settlement row).
Hourly numbers in the sections above were run without it. The difference is small because the book is
mostly flat: the replica pays $43 on $10,000 over 17 months, +31.49% against +31.98%; `pick=5` pays $32,
+24.01% against +24.40%. Drawdowns move by under 0.2 points. Hashes with funding: replica `f0e81c38e8aba68c`,
`pick=5` `97a2ad7458718e91`. No conclusion above changes.

**There is no carry to capture.** Holding only when funding is negative earns the book $12 to $38 on
$10,000 over 17 months. Whatever the filter does, it is not the funding payment.

| Run | 2025-06 to 2026-03: return / max DD | 2026-03 to 2026-11: return / max DD | Full: return / max DD / Sharpe | 39 days, minute: return / max DD |
|---|---|---|---|---|
| Replica | +20.42% / 10.21% | +9.26% / 4.76% | +31.49% / 10.21% / 1.40 | -0.17% / 2.79% |
| Only markets with funding under zero | +6.80% / 4.26% | +4.59% / 3.50% | +11.70% / 4.26% / 1.49 | +0.81% / 1.36% |
| Only where 24h mean funding is under zero | +4.57% / 1.42% | +2.60% / 3.03% | +7.27% / 3.03% / 1.88 | |
| Skip markets paying over the base rate | +19.30% / 6.67% | +8.96% / 4.79% | +29.92% / 6.67% / 1.65 | -0.19% / 2.79% |
| `pick=5` | +15.46% / 6.59% | +7.45% / 2.87% | +24.01% / 6.59% / 1.82 | +1.81% / 1.94% |
| `pick=5`, funding under zero | +4.50% / 1.46% | +2.99% / 1.00% | +7.61% / 1.46% / 4.25 | +0.88% / 1.31% |
| `pick=5`, 24h mean funding under zero | +3.29% / 1.01% | +1.78% / 1.00% | +5.11% / 1.01% / 3.65 | |
| `pick=5`, skip over the base rate | +14.55% / 5.05% | +7.03% / 3.04% | +22.55% / 5.05% / 2.18 | +1.79% / 1.94% |
| `pick=5`, funding under zero, 3x first order | +14.10% / 4.39% | +9.22% / 3.01% | +24.57% / 4.39% / 4.25 | +2.66% / 3.93% |

- **Alone, no funding filter passes.** Negative-only cuts the return by two thirds and return over drawdown
  falls in both halves.
- **On top of `pick=5`, negative-only is the strongest near-miss in the study.** At the same size it has a
  higher return over drawdown in all three hourly windows, on a third of the return. Scaled to match
  `pick=5`'s return (three times the first order) it makes +24.57% with a 4.39% drawdown against 6.59%, Sharpe
  4.25 against 1.82. It fails the rule set beforehand on two counts: its second-half drawdown is 3.01% against
  2.87%, and on the 39-day minute window it is behind `pick=5` at either size.
- **Why it might be real (inferred):** negative funding means the perp trades under spot and shorts are
  paying to stay short; a dip bought then has squeeze fuel behind it. Round 3 found no link between funding and
  trip depth among all entries, so this is a different cut of the data, found after 142 trials.
- **Do not run the 3x size.** Seven full ladders at that size are 4.7x equity. Round 2 showed what a bigger
  first order does when ladders fill together; the filter makes that rarer, not impossible. The honest form of
  this idea is the same size and a third of the income.
- "Skip markets paying over the base rate" trims the first-half drawdown and does nothing in the second:
  the same shape as the open-interest filter.

## Round 8: more income from the funding state, worst case held at the vault's (measured, hourly bars unless said)

Round 7's near-miss needed three times the first order, which lifts the worst case (every ladder full) from
the vault's 1.55x equity to 4.7x. Six ways to take more income without that, fixed in STUDY.md before running.
Baseline is `pick=5` with funding charged.

| Run | 2025-06 to 2026-03: return / max DD | 2026-03 to 2026-11: return / max DD | Full: return / max DD / Sharpe | 39 days, minute: return / max DD | Passed |
|---|---|---|---|---|---|
| `pick=5` | +15.46% / 6.59% | +7.45% / 2.87% | +24.01% / 6.59% / 1.82 | +1.81% / 1.94% | |
| Negative funding only, 2.3x first order, 3 slots | +10.20% / 2.49% | +6.48% / 2.31% | +17.31% / 2.49% / 4.05 | +1.86% / 3.00% | no: less return, minute ratio worse |
| Negative funding only, 3.45x, 2 slots | +13.45% / 2.82% | +8.38% / 3.46% | +22.90% / 3.46% / 3.73 | +2.18% / 4.19% | no |
| Tilt: 3x where funding is negative, 1x elsewhere, cap 1.55x | +17.94% / 6.71% | +9.07% / 2.73% | +28.56% / 6.71% / 2.06 | +2.25% / 1.82% | no: first-half drawdown 0.12 points over |
| **The same, no new trips where funding is over the base rate** | +17.19% / 5.20% | +8.81% / 2.76% | +27.42% / 5.20% / 2.44 | +2.23% / 1.82% | **yes** |
| Negative funding only, entry 0.5% under the EMA | +4.93% / 1.67% | +3.52% / 1.05% | +8.60% / 1.67% / 4.28 | +1.02% / 1.67% | no (against `pick=5 fr_max=0`) |
| First order 2x, adds unchanged (`front=2`) | +20.67% / 7.63% | +11.05% / 5.79% | +33.89% / 7.63% / 1.78 | +2.39% / 2.21% | no: more return, more drawdown |

**The pass, in words.** Among the five most volatile markets: where the last settled funding rate is negative,
the first order is 3x the vault's (1.08% of equity) and the ladder scales with it; where funding sits at the
base rate, the vault's size; where funding is above the base rate (longs crowded), no new trip. Each open
trip reserves its full ladder, and a new trip opens only if the reserved notional stays under 1.55x equity,
the vault's own worst case. Settings: `pick=5 fr_max=0 fr_boost=3 fr_else=1 fr_skip=0.0000126 cap=1.55`, hash
`cc00955cbe8f1b26` (hourly, full run), `28f3d6a5d5fdb323` (minute window). `tilt-card.md` is its gauntlet card
(the card prints `params {}`): holds out of sample, deflated Sharpe 0.01 over 198 trials.

**Controls (declared after the pass, before running).**

| Run | First half | Second half | Full: return / max DD | Minute |
|---|---|---|---|---|
| The pass | +17.19% / 5.20% | +8.81% / 2.76% | +27.42% / 5.20% | +2.23% / 1.82% |
| Same skip and cap, every first order 1.22x | +17.73% / 6.09% | +8.46% / 3.75% | +27.63% / 6.09% | +2.09% / 2.22% |
| Tilt upside down: 3x where funding is not negative | +29.05% / 13.49% | +12.98% / 4.02% | +45.63% / 13.49% | +2.36% / 3.02% |

- **The tilt beats plain size.** Sizing every trip up 22% lands on the same return with a drawdown about a
  point larger on each hourly window and 0.4 points larger on the minute window.
- **The drawdown lives in trips opened while funding is not negative.** The upside-down tilt has a return over
  drawdown of 3.4 against the pass's 5.3.

**Plateau around the pass** (one setting moved; `pick=5`'s second-half drawdown is 2.87%).

| Setting | Full: return / max DD | Second half: return / max DD | Minute |
|---|---|---|---|
| The pass (`fr_boost=3 cap=1.55`) | +27.42% / 5.20% | +8.81% / 2.76% | +2.23% / 1.82% |
| `fr_boost=2` | +25.69% / 5.07% | +8.08% / 2.94% | +2.04% / 1.82% |
| `fr_boost=4` | +28.75% / 4.91% | +8.97% / 4.91% | +2.15% / 1.82% |
| `cap=1.25` | +25.36% / 4.58% | +7.91% / 3.97% | +1.91% / 1.82% |
| `cap=1.6` | +29.02% / 5.16% | +9.07% / 2.90% | +2.41% / 1.94% |
| `cap=2.0` | +30.73% / 5.23% | +9.50% / 3.89% | +2.59% / 1.94% |
| `fr_hours=8` (8-hour mean funding) | +25.74% / 2.76% | +8.49% / 2.76% | +2.10% / 1.82% |

- **More profit is a plateau.** Every neighbour beats `pick=5` on return and on drawdown over the full run
  and the first half; on the minute window each has a higher return and the same or a smaller drawdown.
- **Less drawdown in the second half is one point.** The pass has 2.76% against 2.87%; two neighbours tie
  (2.90%, 2.94%) and three are clearly worse (3.89% to 4.91%). The full-run drawdown cut comes from the first
  half.

**It does not travel** (declared before running; the seven other markets the vault has traded, `pick=4`).

| Run on AVAX, BCH, HBAR, LTC, NEAR, SUI, XLM | First half | Second half | Full: return / max DD |
|---|---|---|---|
| Ladder, four most volatile | -10.37% / 16.68% | +7.98% / 8.56% | -6.86% / 26.66% |
| With the pass's tilt, skip and cap | +5.48% / 8.69% | +8.59% / 22.95% | +10.75% / 31.50% |
| Negative funding only, normal size | +3.75% / 0.59% | +2.44% / 7.98% | +6.29% / 7.98% |

- On these coins the tilt adds return and adds drawdown. The second half is one trip: BCH, opened 2026-05-27
  under negative funding, took all seven buys and sat 12 weeks before its exit filled. At 3x that ladder was
  58% of equity.
- The same thing happened on the ten and ended well: three 3x trips took all seven buys (ADA and DOGE together
  on 2026-01-31, SOL on 2026-02-05), each just under 60% of equity, and each bounced out inside a day. **The pass
  rests on those bounces.**
- **Exposure, measured on the full hourly run:** the replica peaks at 1.21x equity gross and 0.21x in one coin;
  `pick=5` at 0.84x and 0.20x; the pass at 1.18x and 0.59x. The cap holds the book under the vault's worst
  case. It does not limit how much sits in one coin, and that tripled.

**How much to believe it.** It passes the rule set beforehand, on the vault's ten, with a control that says
the funding state is doing the work. Against that: it is the second pass in 31 tries; the second-half margin
is 0.11 points; it failed on other coins; a full 3x ladder is three fifths of equity in one coin and the test
window contains no case of one failing to bounce on the ten. The gain over `pick=5` is 3.4 points of return in
17 months and 1.4 points of drawdown. Do not raise `fr_boost` or `cap`: 4x and 2.0 both lost the second-half
drawdown.

## Round 9: tilt the shallow buys only (measured; fails)

The fix that suggests itself for round 8's tail: 3x on buys one to four only, the vault's own size on buys
five to seven (`boost_buys=4`), so a full ladder is 1.25x the vault's, not 3x. One variant, declared before
running.

| Run | First half | Second half | Full: return / max DD | Minute |
|---|---|---|---|---|
| `pick=5` | +15.46% / 6.59% | +7.45% / 2.87% | +24.01% / 6.59% | +1.81% / 1.94% |
| Round 8's pass | +17.19% / 5.20% | +8.81% / 2.76% | +27.42% / 5.20% | +2.23% / 1.82% |
| Shallow buys 3x, deep buys 1x | +18.98% / 5.60% | +9.13% / 7.24% | +29.77% / 7.24% | +2.49% / 1.82% |
| The same on the seven other coins | +0.45% / 13.90% | +8.95% / 10.13% | +9.06% / 29.45% | |

It fails on both coin sets. With the shallow buys large and the deep buys small, the average entry stays high
and a deep trip needs a 6.4% bounce from its last add, against 4.6%. An ADA trip opened 2026-06-04 sat ten
days for that reason and made the second-half drawdown 7.24%. It swaps a concentration tail for a slow-exit
tail, and the second is worse. Same lesson as `front=2` above and the add-spacing cliff in round 6: the
ladder's geometry is the fragile part.

## Fill model check against the tape (measured)

Every trade in the ten markets, 2026-10-03 to 2026-11-08, from ironflow/hyperliquid-trades (`build_ticks.py`,
`fill_check.py`). The engine fills a resting limit only when price trades through it, never on a touch, from
the minute after the order is placed.

| Check | Result |
|---|---|
| The vault's 922 real maker orders: tape traded through their price within 1 s / 10 s / 60 s / 5 min | 62% / 87% / 94% / 97% |
| Never traded through within an hour (filled on a touch; the engine would not fill these) | 1.1% |
| Volume traded through inside the minute, against the vault's order size | median 55x; under 1x for 10% |
| 0xArchive's November minute lows and highs against the tape (SOL, 11,517 minutes) | lows 100% identical, highs 99.99% |
| Vault trips that close inside 60 s / 120 s (faster than the engine's one-minute step) | 0.9% / 2.5%, 1.7% of its profit |
| Replica, October, minute bars against hourly bars | +1.37% against +1.09%, max drawdown 1.94% against 1.91% |
| `pick=5`, October, minute bars against hourly bars | +1.07% against +0.79%, max drawdown 1.94% against 1.84% |

- The engine's rule grants 94% of the vault's real maker fills within a minute and misses about 1%. It is
  slightly conservative, and replaying raw trades instead of minute bars would change little: the minute bars
  are made from the same trades and the rule is already trade-through.
- Size is not a constraint at the vault's scale in nine fills out of ten; the tenth would fill in part.
- **Hourly bars understate return by about a quarter and leave drawdown unchanged** (one month, two runs).
  The 17-month hourly returns in this report are more likely low than high on that account; they still charge
  no funding. (inferred from one month)

## Not tested, and why

- **The vault's real deep-trip handling** (its partial sells and the two "close everything" minutes). The trim
  rule in round 4 is a guess at it; 39 deep trips are too few to read a trigger from.
- **Order-book and cross-venue features** (spread, depth, CEX lead-lag): not in any dataset used here.
- **Anything on minute data before 2026-10-03.** The 0xArchive key is on the free plan (30 days) and `0xbt
  data pull` works in whole months, so October was built from ironflow's free trades and the long run from
  ironflow's hourly candles. On hourly bars a take-profit can't fill in the hour its buy filled, the order of
  a buy and a sell inside one hour is unknown (funding is charged from round 7 on). A paid key would let the
  same variants run on minute data, which matters most for the trim rule and for round 8's tilt.
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
0xbt backtest futurai.py --data data1h/hyperliquid --start 2025-06-05 --end 2026-11-01            # f0e81c38e8aba68c
0xbt backtest futurai.py --data data1h/hyperliquid --start 2025-06-05 --end 2026-11-01 -p pick=5  # 97a2ad7458718e91
0xbt backtest futurai.py --data data1h/hyperliquid --start 2025-06-05 --end 2026-11-01 -p pick=5 \
  -p fr_max=0 -p fr_boost=3 -p fr_else=1 -p fr_skip=0.0000126 -p cap=1.55                         # cc00955cbe8f1b26
python3 trader.py replicate trader_oct.json futurai.py --clock 1m --start 2026-10-03 --end 2026-11-11
python3 match.py
```

The vault trades on, so `hl_book.py` run later returns more fills than the 11,374 used here; the hashes
above need the `trader_oct.json` in this directory. Paper trading the replica: `oxb.Session`
(strategy-api.md, "Paper trading"). No live orders from this study.
