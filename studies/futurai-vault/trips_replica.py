"""The replica's trips on the hourly run, one row each: market, open time, close time, buys, PnL in units of
the first order's notional. Written to ext/replica_trips.json."""
import json, importlib.util, sys, oxarchive_backtest as oxb
spec = importlib.util.spec_from_file_location('f', 'futurai.py'); f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
rep = oxb.backtest(f.strategy(), "2025-06-05", "2026-11-01", source="data1h/hyperliquid")
cur, out = {}, []
for x in rep.fills:
    t = cur.get(x.market)
    if t is None:
        if x.size <= 0: continue
        t = cur[x.market] = dict(coin=x.market, t0=x.ts, first=x.price, base=x.size * x.price, ids=set(), pos=0.0, cash=0.0)
    if x.size > 0: t['ids'].add(x.order_id)
    t['pos'] += x.size; t['cash'] -= x.size * x.price + x.fee
    if t['pos'] <= 1e-9:
        out.append(dict(coin=t['coin'], t0=t['t0'], t1=x.ts, buys=len(t['ids']), pnl=t['cash'] / t['base'], first=t['first'])); del cur[x.market]
for t in cur.values():
    out.append(dict(coin=t['coin'], t0=t['t0'], t1=None, buys=len(t['ids']), pnl=None, first=t['first']))
json.dump(out, open('ext/replica_trips.json', 'w'))
import collections
print(len(out), sorted(collections.Counter(t['buys'] for t in out).items()))
