"""Where does the replica's profit come from and where does its drawdown come from, by what was true at entry?

Every trip closes in profit, so "does it go deep" is the wrong question. A trip costs the book by being under
water, and most of all by being under water when the others are. For each closed replica trip on the hourly run:
  profit   realised PnL, in first orders
  mae      its worst mark-to-market loss at an hourly close, in first orders
  ulcer    its open loss summed over every hour it was open (first orders x hours under water)
  crash    its loss summed over the book's worst hours (the 10% of hours with the largest total open loss)
Trips are sorted into fifths of each entry feature (read at the last hour closed before the entry bar). A feature
is useful if its fifths differ in profit share over risk share: size should go where that ratio is high.
On the design half the worst 2% of hours are carried by 63 of 3,513 trips, so the crash column is a handful of
events however it is cut; mae and ulcer have more trips behind them.

usage: observe.py design|test|all [feature ...]      design = trips opened before 2026-03-01
"""
import sys, datetime, importlib.util, duckdb, numpy as np, oxarchive_backtest as oxb

H = 3600000
which = sys.argv[1] if len(sys.argv) > 1 else 'design'
only = sys.argv[2:]
SPLIT = 1772323200000 // H                       # 2026-03-01
COINS = "ADA BNB BTC DOGE ETH HYPE LINK SOL TRX XRP".split()
T0 = 1748736000000 // H; N = 1793491200000 // H - T0    # 2025-06-01 .. 2026-11-01

def ffill(x):
    idx = np.where(~np.isnan(x), np.arange(len(x)), 0); np.maximum.accumulate(idx, out=idx); return x[idx]
def ema(x, n):
    a = 2 / (n + 1); o = np.empty_like(x); o[0] = x[0]
    for i in range(1, len(x)): o[i] = a * x[i] + (1 - a) * o[i - 1]
    return o
def roll(x, n, fn):
    from numpy.lib.stride_tricks import sliding_window_view as sw
    o = np.full(len(x), np.nan); o[n - 1:] = fn(sw(x, n), 1); return o
def ret(c, n):
    o = np.full(len(c), np.nan); o[n:] = c[n:] / c[:-n] - 1; return o

X = {}
for m in COINS:
    g = {k: np.full(N, np.nan) for k in ('close', 'low', 'volume', 'fr', 'oi')}
    for ts, c, lo, v, fr, oi in duckdb.sql(f"SELECT ts, close, low, volume, funding_rate, open_interest FROM "
                                           f"'data1h/hyperliquid/{m}/*.parquet' WHERE close IS NOT NULL").fetchall():
        i = ts // H - T0
        if 0 <= i < N:
            for k, x in zip(g, (c, lo, v, fr, oi)): g[k][i] = np.nan if x is None else x
    c = ffill(g['close']); r1 = ret(c, 1); r1[np.isnan(r1)] = 0
    vol = np.nan_to_num(g['volume']); oi = ffill(g['oi']); fr = ffill(g['fr'])
    path = roll(np.abs(r1), 168, np.sum)
    hi7, lo7 = roll(c, 168, np.max), roll(c, 168, np.min)
    X[m] = dict(c=c, r1=r1, funding=fr, funding8=roll(fr, 8, np.mean), funding24=roll(fr, 24, np.mean),
                ret1=ret(c, 1), ret4=ret(c, 4), ret24=ret(c, 24), ret168=ret(c, 168),
                vs_ema14=c / ema(c, 14) - 1, vs_ema72=c / ema(c, 72) - 1, vs_ema168=c / ema(c, 168) - 1,
                ema_slope24=ret(ema(c, 14), 24),
                vol24=roll(r1, 24, np.std), vol168=roll(r1, 168, np.std),
                path168=path, eff168=np.abs(ret(c, 168)) / path,          # displacement over path length
                off_high7=c / hi7 - 1, range_pos7=(c - lo7) / (hi7 - lo7),
                vol_spike=vol / roll(vol, 24, np.mean), oi4=ret(oi, 4), oi24=ret(oi, 24))
    X[m]['volx'] = X[m]['vol24'] / X[m]['vol168']
vols = np.array([X[m]['vol168'] for m in COINS])
rank = (-vols).argsort(0).argsort(0) + 1.0                                 # 1 = the most volatile of the ten
dips = np.sum([X[m]['vs_ema14'] < -0.005 for m in COINS], 0)
mret4 = np.nanmean([X[m]['ret4'] for m in COINS], 0)

spec = importlib.util.spec_from_file_location('f', 'futurai.py'); f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
rep = oxb.backtest(f.strategy(), "2025-06-05", "2026-11-01", source="data1h/hyperliquid")
cur, trips = {}, []
for x in rep.fills:
    t = cur.get(x.market)
    if t is None:
        if x.size <= 0: continue
        t = cur[x.market] = dict(coin=x.market, t0=x.ts // H - T0, first=x.price, base=x.size * x.price, ids=set(), pos=0.0, cash=0.0, steps=[])
    if x.size > 0: t['ids'].add(x.order_id)
    t['pos'] += x.size; t['cash'] -= x.size * x.price + x.fee
    t['steps'].append((x.ts // H - T0, t['pos'], t['cash']))
    if t['pos'] <= 1e-9:
        t['t1'] = x.ts // H - T0; t['pnl'] = t['cash'] / t['base']; t['buys'] = len(t['ids']); trips.append(cur.pop(x.market))
trips.sort(key=lambda t: t['t0'])

book = np.zeros(N)                               # the book's open loss at each hourly close, in first orders
for t in trips:
    u = np.zeros(max(0, t['t1'] - t['t0'])); j = 0; pos = cash = 0.0
    c = X[t['coin']]['c']
    for k in range(len(u)):
        h = t['t0'] + k
        while j < len(t['steps']) and t['steps'][j][0] <= h: _, pos, cash = t['steps'][j]; j += 1
        u[k] = min(0.0, (pos * c[h] + cash) / t['base'])
    t['u'] = u; t['mae'] = -u.min() if len(u) else 0.0
    book[t['t0']:t['t0'] + len(u)] += u
lo, hi = (0, SPLIT - T0) if which == 'design' else (SPLIT - T0, N) if which == 'test' else (0, N)
worst = np.zeros(N, bool); cut = np.quantile(book[lo:hi], 0.10); worst[lo:hi] = book[lo:hi] <= cut
last = {}
rows = []
open_now = []
for t in trips:
    open_now = [o for o in open_now if o['t1'] > t['t0']]
    i = t['t0'] - 1
    prev = last.get(t['coin']); last[t['coin']] = t
    keep = lo <= t['t0'] < hi and i >= 200
    if keep:
        x = X[t['coin']]; b = X['BTC']; ci = COINS.index(t['coin'])
        fr = x['funding'][i]
        ft = {k: x[k][i] for k in ('funding', 'funding8', 'funding24', 'ret1', 'ret4', 'ret24', 'ret168', 'vs_ema14', 'vs_ema72', 'vs_ema168',
                                   'ema_slope24', 'vol168', 'volx', 'path168', 'eff168', 'off_high7', 'range_pos7', 'vol_spike', 'oi4', 'oi24')}
        ft.update(gap=x['c'][i] / t['first'] - 1,                       # how far it had to fall inside the entry hour
                  fund_state=0.0 if fr < 0 else 2.0 if fr >= 1.26e-5 else 1.0,
                  btc_vs_ema14=b['vs_ema14'][i], rel_dip=x['vs_ema14'][i] - b['vs_ema14'][i], btc_ret4=b['ret4'][i], btc_ret24=b['ret24'][i],
                  btc_vs_ema168=b['vs_ema168'][i], btc_oi24=b['oi24'][i], mkt_ret4=mret4[i], dips=float(dips[i]),
                  vol_rank=rank[ci][i], open_trips=float(len(open_now)), open_deep=float(sum(1 for o in open_now if o['buys'] >= 3 and o['t0'] + 6 < t['t0'])),
                  book_loss=book[i], since_prev=float(t['t0'] - prev['t1']) if prev else np.nan, prev_buys=float(prev['buys']) if prev else np.nan,
                  hour=float((t['t0'] + T0) % 24), weekday=float(((t['t0'] + T0) // 24 + 3) % 7))
        w = worst[t['t0']:t['t0'] + len(t['u'])]
        rows.append((ft, t['pnl'], t['mae'], -t['u'][w].sum(), t['buys'], len(t['u']), -t['u'].sum()))
    open_now.append(t)

pnl, mae, crash = (np.array([r[k] for r in rows]) for k in (1, 2, 3))
hours = np.array([r[5] for r in rows], float); ulcer = np.array([r[6] for r in rows])
print(f"{which}: {len(rows)} trips; profit {pnl.sum():.1f} first orders; worst book loss {-book[lo:hi].min():.1f}; "
      f"worst-hours cut {-cut:.1f}; trips touching a worst hour {int((crash > 0).sum())}")
print("per fifth of the feature, low to high: profit share over risk share (1.00 = average, high = cheap income), for three risk measures")
res = []
for k in rows[0][0]:
    if only and k not in only: continue
    v = np.array([r[0][k] for r in rows], float); ok = ~np.isnan(v)
    uniq = np.unique(v[ok])
    q = (uniq[:-1] + uniq[1:]) / 2 if len(uniq) <= 8 else np.unique(np.quantile(v[ok], [.2, .4, .6, .8]))
    b = np.digitize(v, q)
    out = []
    for j in range(len(q) + 1):
        s = ok & (b == j)
        ps = pnl[s].sum() / pnl[ok].sum()
        out.append((int(s.sum()), ps) + tuple(ps / max(r[s].sum() / r[ok].sum(), 1e-9) for r in (ulcer, mae, crash)))
    e = [o[3] for o in out if o[0] >= 50]
    res.append((max(e) / min(e) if e else 0, k, q, out))
res.sort(reverse=True)
for _, k, q, out in res:
    print('%-13s ulcer ' % k + ' '.join('%5.2f' % o[2] for o in out) + ' | mae ' + ' '.join('%5.2f' % o[3] for o in out)
          + ' | crash ' + ' '.join('%5.2f' % min(o[4], 99) for o in out) + ' | n ' + ' '.join(str(o[0]) for o in out) + ' | cuts ' + ' '.join('%.3g' % x for x in q))
    if only:
        v = np.array([r[0][k] for r in rows], float); b = np.digitize(v, q)
        for j, o in enumerate(out):
            m = b == j
            print('   part %d: %4d trips, %4.1f%% of profit, %4.1f%% of ulcer, %4.1f%% of mae, %4.1f%% of crash loss, %4.1f%% of trips with 5+ buys' % (
                j + 1, o[0], 100 * o[1], 100 * ulcer[m].sum() / ulcer.sum(), 100 * mae[m].sum() / mae.sum(), 100 * crash[m].sum() / crash.sum(),
                100 * np.mean(np.array([r[4] for r in rows])[m] >= 5)))
