"""Which reference level do the vault's opening buys track? Offsets of each opening fill from EMA/SMA/rolling
high on 1m-4h bars; tightest interquartile range first."""
import json, duckdb, numpy as np, sys
from numpy.lib.stride_tricks import sliding_window_view as sw
book = json.load(open(sys.argv[1]))
opens = [c for c in book['changes'] if c['start_position'] == 0 and c['side'] == 'B']
if len(sys.argv) > 2: opens = [c for c in opens if c['maker'] == (sys.argv[2] == 'maker')]
M = {}
for coin in book['in_dataset']:
    r = duckdb.sql(f"SELECT ts, close FROM read_parquet('data/hyperliquid/{coin}/*.parquet') WHERE close IS NOT NULL ORDER BY ts").fetchnumpy()
    ts = np.arange(r['ts'][0], r['ts'][-1] + 60000, 60000); cl = np.full(len(ts), np.nan)
    cl[((r['ts'] - ts[0]) // 60000).astype(int)] = np.asarray(r['close'], float)
    idx = np.where(~np.isnan(cl), np.arange(len(cl)), 0); np.maximum.accumulate(idx, out=idx)
    M[coin] = (ts, cl[idx])
def ema(x, n):
    a = 2 / (n + 1); o = np.empty_like(x); o[0] = x[0]
    for i in range(1, len(x)): o[i] = a * x[i] + (1 - a) * o[i - 1]
    o[:3 * n] = np.nan; return o
def sma(x, n):
    o = np.full_like(x, np.nan); o[n - 1:] = sw(x, n).mean(1); return o
def high(x, n):
    o = np.full_like(x, np.nan); o[n - 1:] = sw(x, n).max(1); return o
out = []
for tf in (1, 5, 15, 60, 240):
    for kind, fn in (('ema', ema), ('sma', sma), ('high', high)):
        for n in (5, 10, 14, 20, 30, 50, 100, 200):
            offs = []
            for coin, (ts, cl) in M.items():
                off0 = (-ts[0] // 60000) % tf   # align bars to UTC
                x = cl[off0:]; k = len(x) // tf
                if k < 4 * n: continue
                bc = x[:k * tf].reshape(k, tf)[:, -1]; bt = ts[off0:][:k * tf].reshape(k, tf)[:, -1] + 60000
                ref = fn(bc, n)
                for c in opens:
                    if c['symbol'] != coin: continue
                    i = np.searchsorted(bt, c['ts'], side='right') - 1
                    if i >= 0: offs.append(c['price'] / ref[i] - 1)
            offs = np.array(offs); offs = offs[~np.isnan(offs)]
            if len(offs) < 0.6 * len(opens): continue
            p = np.percentile(offs, [10, 25, 50, 75, 90])
            out.append((p[3] - p[1], tf, kind, n, len(offs), p))
out.sort(key=lambda x: x[0])
print('opens', len(opens))
for iqr, tf, kind, n, cnt, p in out[:14]:
    print(f'{kind}{n}@{tf}m n={cnt} iqr={100*iqr:.3f}%  p10/25/50/75/90 = ' + ' '.join('%.2f' % (100 * v) for v in p))
