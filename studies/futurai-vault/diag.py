"""Replica trips beside the vault's, one market: python3 diag.py XRP [-p name=value ...]"""
import json, datetime, importlib.util, sys, oxarchive_backtest as oxb
spec = importlib.util.spec_from_file_location('f', 'futurai.py'); f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
coin = sys.argv[1]
kw = {}
for a in sys.argv[2:]:
    k, v = a.split('='); kw[k] = float(v) if v.replace('.', '').replace('-', '').isdigit() else v
rep = oxb.backtest(f.strategy(**kw), "2026-10-03", "2026-11-11", source="data/hyperliquid")
U = lambda ms: datetime.datetime.fromtimestamp(ms / 1000, datetime.UTC).strftime('%m-%d %H:%M')
x = rep.fills[0]; attrs = [a for a in dir(x) if not a.startswith('_')]
pos = 0; cur = None; out = []
for x in rep.fills:
    if x.market != coin: continue
    if pos <= 1e-12 and x.size > 0: cur = dict(t0=x.ts, first=x.price, buys=0, ids=set())
    if x.size > 0 and x.order_id not in cur['ids']: cur['ids'].add(x.order_id); cur['buys'] += 1
    pos += x.size
    if pos <= 1e-9 and cur: out.append(('rep', cur['t0'], x.ts, cur['first'], cur['buys'], x.price)); cur = None; pos = 0
if cur: out.append(('rep', cur['t0'], None, cur['first'], cur['buys'], None))
for t in json.load(open('trips.json')):
    if t['coin'] == coin and t['t0'] >= 1790985600000:
        out.append(('VLT', t['t0'], t['t1'], t['buys'][0]['px'], len(t['buys']), t['sells'][-1]['px']))
for o in sorted(out, key=lambda o: o[1]):
    print(o[0], U(o[1]), '->', U(o[2]) if o[2] else 'open ', 'first', round(o[3], 5), 'buys', o[4], 'exit', o[5] and round(o[5], 5))
