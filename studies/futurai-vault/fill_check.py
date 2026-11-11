"""The engine's limit rule (fill only when price trades through, from the next minute) against the vault's
real maker fills, using every trade in ext/ticks. For each real maker fill at price P and time t:
did the tape trade through P (below for a buy, above for a sell), and how soon?"""
import json, duckdb, numpy as np
c = duckdb.connect()
c.execute("CREATE TABLE t AS SELECT * FROM 'ext/ticks/*.parquet'")
lo, hi = c.execute("SELECT min(ts), max(ts) FROM t").fetchone()
book = json.load(open('trader_oct.json'))
# one row per real maker order: first fill time, price, side, total size
orders = {}
for x in book['changes']:
    if not x['maker'] or not (lo <= x['ts'] <= hi - 3600000): continue
    k = (x['symbol'], x['side'], x['price'], x['ts'] // 60000)
    o = orders.setdefault(k, dict(coin=x['symbol'], side=x['side'], px=x['price'], ts=x['ts'], sz=0.0)); o['sz'] += x['size']
rows = list(orders.values())
c.execute("CREATE TABLE o (id INTEGER, coin VARCHAR, buy BOOLEAN, px DOUBLE, ts BIGINT, sz DOUBLE)")
c.executemany("INSERT INTO o VALUES (?,?,?,?,?,?)", [(i, r['coin'], r['side'] == 'B', r['px'], r['ts'], r['sz']) for i, r in enumerate(rows)])
res = c.execute("""
SELECT o.id, o.buy,
  min(t.ts) FILTER (WHERE CASE WHEN o.buy THEN t.price < o.px ELSE t.price > o.px END) - any_value(o.ts) AS wait_through,
  sum(t.size) FILTER (WHERE t.ts < o.ts + 60000 AND CASE WHEN o.buy THEN t.price < o.px ELSE t.price > o.px END) AS vol_through_1m,
  sum(t.size) FILTER (WHERE t.ts < o.ts + 60000 AND t.price = o.px) AS vol_at_1m, any_value(o.sz) sz
FROM o LEFT JOIN t ON t.coin = o.coin AND t.ts >= o.ts AND t.ts < o.ts + 3600000
GROUP BY 1, 2""").fetchall()
for name, sel in (('buys', True), ('sells', False), ('all', None)):
    r = [x for x in res if sel is None or x[1] == sel]; n = len(r)
    w = np.array([x[2] if x[2] is not None else np.inf for x in r], float)
    print(f"{name}: {n} real maker orders | traded through within 1s {np.mean(w<1000):.3f}, 10s {np.mean(w<10000):.3f}, 60s {np.mean(w<60000):.3f}, 5m {np.mean(w<300000):.3f}, 1h {np.mean(w<3600000):.3f}, never in 1h {np.mean(np.isinf(w)):.3f}")
    ok = [x for x in r if x[3]]
    print(f"   where it traded through inside a minute: volume through / order size, median {np.median([x[3]/x[5] for x in ok]):.0f}x, share under 1x {np.mean([x[3]/x[5] < 1 for x in ok]):.3f}")
# 0xArchive's November minute bars against the tape
print(c.execute("""SELECT count(*), avg(CASE WHEN abs(b.low - k.lo) / k.lo < 1e-9 THEN 1 ELSE 0 END) low_same, avg(CASE WHEN abs(b.high - k.hi) / k.hi < 1e-9 THEN 1 ELSE 0 END) high_same,
  max(abs(b.low - k.lo) / k.lo) worst_low, median(abs(b.volume / k.v - 1)) vol_diff
  FROM (SELECT (ts // 60000) * 60000 m, min(price) lo, max(price) hi, sum(size) v FROM t WHERE coin = 'SOL' AND ts >= 1793491200000 GROUP BY 1) k
  JOIN read_parquet('data/hyperliquid/SOL/2026-11.parquet') b ON b.ts = k.m WHERE b.low IS NOT NULL""").fetchall())
