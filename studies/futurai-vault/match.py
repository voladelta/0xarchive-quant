"""Trip-level match: share of the vault's trip opens with a replica open within 30 minutes, and the reverse."""
import json, importlib.util, sys, bisect, oxarchive_backtest as oxb
spec = importlib.util.spec_from_file_location('f', 'futurai.py'); f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
kw = {}
for a in sys.argv[1:]:
    k, v = a.split('='); kw[k] = float(v)
END = 1794355200000 if not kw.get('until') else kw.pop('until')
rep = oxb.backtest(f.strategy(**kw), "2026-10-03", "2026-11-11", source="data/hyperliquid")
pos = {}; ro = {}
for x in rep.fills:
    if pos.get(x.market, 0) <= 1e-12 and x.size > 0: ro.setdefault(x.market, []).append(x.ts)
    pos[x.market] = pos.get(x.market, 0) + x.size
    if pos[x.market] < 1e-9: pos[x.market] = 0
vo = {}
for t in json.load(open('trips.json')):
    if t['t0'] >= 1790985600000: vo.setdefault(t['coin'], []).append(t['t0'])
def near(a, b, w=1800000):
    b = sorted(b); n = 0
    for t in a:
        i = bisect.bisect_left(b, t)
        if any(0 <= j < len(b) and abs(b[j] - t) <= w for j in (i - 1, i)): n += 1
    return n
for lo, hi, name in ((1790985600000, 1793836800000, '3 Oct to 5 Nov'), (1793836800000, 1794355200000, '5 Nov to 11 Nov')):
    V = {m: [t for t in v if lo <= t < hi] for m, v in vo.items()}; R = {m: [t for t in v if lo <= t < hi] for m, v in ro.items()}
    nv = sum(map(len, V.values())); nr = sum(map(len, R.values()))
    print(name, 'vault opens', nv, 'replica opens', nr, 'vault opens matched %.2f' % (sum(near(V[m], R.get(m, [])) for m in V) / nv),
          'replica opens matched %.2f' % (sum(near(R[m], V.get(m, [])) for m in R) / max(nr, 1)))
