"""What was true at entry for trips that went deep? Features from the last closed hour before each replica
trip opened, sorted into quintiles. usage: event_study.py design|test|all"""
import json, sys, duckdb, numpy as np, collections
H = 3600000
which = sys.argv[1] if len(sys.argv) > 1 else 'design'
SPLIT = 1772323200000  # 2026-03-01
COINS = "ADA LINK HYPE SOL DOGE XRP ETH TRX BNB BTC".split()
T0 = 1748736000000; N = (1793491200000 - T0) // H   # 2025-06-01 .. 2026-11-01
def grid(sql, cols):
    out = {c: {k: np.full(N, np.nan) for k in cols} for c in COINS}
    for r in duckdb.sql(sql).fetchall():
        i = (r[1] - T0) // H
        if r[0] in out and 0 <= i < N:
            for k, v in zip(cols, r[2:]): out[r[0]][k][i] = v if v is not None else np.nan
    return out
K = grid("SELECT coin, ts, close FROM 'ext/candles_1h.parquet'", ['close'])
F = grid("SELECT coin, ts, funding, premium FROM 'ext/funding_1h.parquet'", ['funding', 'premium'])
O = grid("SELECT coin, ts, oi, oi_usd FROM 'ext/oi_1h.parquet'", ['oi', 'oi_usd'])
L = grid("SELECT coin, ts, liq_long, liq_short FROM 'ext/liq_1h.parquet'", ['liq_long', 'liq_short'])
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
    c = ffill(K[m]['close']); r1 = ret(c, 1); r1[np.isnan(r1)] = 0
    liq = np.nan_to_num(L[m]['liq_long']); oiu = ffill(O[m]['oi_usd']); oi = ffill(O[m]['oi'])
    X[m] = dict(c=c, ret24=ret(c, 24), ret72=ret(c, 72), ret168=ret(c, 168), vs_ema168=c / ema(c, 168) - 1, vs_ema14=c / ema(c, 14) - 1,
                vol24=roll(r1, 24, np.std), vol168=roll(r1, 168, np.std),
                bbz20=(c - roll(c, 20, np.mean)) / roll(c, 20, np.std), bbz80=(c - roll(c, 80, np.mean)) / roll(c, 80, np.std),
                funding=ffill(F[m]['funding']), funding24=roll(ffill(F[m]['funding']), 24, np.mean), premium=ffill(F[m]['premium']),
                liq1=liq / oiu, liq4=roll(liq, 4, np.sum) / oiu, liq24=roll(liq, 24, np.sum) / oiu,
                oi4=ret(oi, 4), oi24=ret(oi, 24), oi72=ret(oi, 72), liq_usd=liq, oi_usd=oiu)
    X[m]['volx'] = X[m]['vol24'] / X[m]['vol168']
breadth = np.mean([X[m]['ret24'] < 0 for m in COINS], 0); mret24 = np.nanmean([X[m]['ret24'] for m in COINS], 0)
mliq4 = roll(sum(X[m]['liq_usd'] for m in COINS), 4, np.sum) / sum(X[m]['oi_usd'] for m in COINS)
mliq24 = roll(sum(X[m]['liq_usd'] for m in COINS), 24, np.sum) / sum(X[m]['oi_usd'] for m in COINS)
moi24 = np.nanmean([X[m]['oi24'] for m in COINS], 0); mfund = np.nanmean([X[m]['funding24'] for m in COINS], 0)
names = ['ret24', 'ret72', 'ret168', 'vs_ema168', 'vs_ema14', 'vol24', 'volx', 'bbz20', 'bbz80', 'funding', 'funding24', 'premium', 'liq1', 'liq4', 'liq24', 'oi4', 'oi24', 'oi72']
rows = []
for t in json.load(open('ext/replica_trips.json')):
    if t['pnl'] is None: continue
    if which == 'design' and t['t0'] >= SPLIT: continue
    if which == 'test' and t['t0'] < SPLIT: continue
    i = (t['t0'] - T0) // H - 1          # the last hour closed before the entry bar
    if i < 200: continue
    f = {k: X[t['coin']][k][i] for k in names}
    b = X['BTC']
    f.update(btc_ret24=b['ret24'][i], btc_ret72=b['ret72'][i], btc_vs_ema168=b['vs_ema168'][i], btc_vol24=b['vol24'][i], btc_volx=b['volx'][i],
             btc_oi24=b['oi24'][i], btc_funding24=b['funding24'][i], breadth=breadth[i], mkt_ret24=mret24[i], mkt_liq4=mliq4[i], mkt_liq24=mliq24[i],
             mkt_oi24=moi24[i], mkt_funding24=mfund[i], hour=((t['t0'] // H) % 24), )
    rows.append((f, t['buys'] >= 5, t['pnl'], t['buys']))
deep = np.array([r[1] for r in rows]); pnl = np.array([r[2] for r in rows])
print(f"{which}: {len(rows)} trips, deep share {deep.mean():.3f}, mean pnl {pnl.mean():.4f} (x first order), total {pnl.sum():.1f}")
res = []
for k in rows[0][0]:
    v = np.array([r[0][k] for r in rows], float); ok = ~np.isnan(v)
    if ok.sum() < 200: continue
    q = np.quantile(v[ok], [.2, .4, .6, .8]); b = np.digitize(v, q)
    d = [deep[ok & (b == j)].mean() for j in range(5)]; p = [pnl[ok & (b == j)].mean() for j in range(5)]
    # rank AUC of the feature for "deep"
    order = np.argsort(v[ok]); rk = np.empty(ok.sum()); rk[order] = np.arange(ok.sum()); dd = deep[ok]
    auc = (rk[dd].mean() - (dd.sum() - 1) / 2) / (len(dd) - dd.sum())
    res.append((abs(auc - .5), k, auc, q, d, p))
res.sort(reverse=True)
print('%-14s %5s | deep share by quintile (low..high)      | mean pnl by quintile              | cuts' % ('feature', 'auc'))
for _, k, auc, q, d, p in res:
    print('%-14s %5.2f | ' % (k, auc) + ' '.join('%.3f' % x for x in d) + ' | ' + ' '.join('%+.4f' % x for x in p) + ' | ' + ' '.join('%.4g' % x for x in q))
