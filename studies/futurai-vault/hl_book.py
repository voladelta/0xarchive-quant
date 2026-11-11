"""The vault's whole fill history from Hyperliquid's public API (no key), written three ways:
hl_fills.json (raw), trips.json (round trips, fills joined into orders), and trader_oct.json (the fills
from 3 Oct 2026 in trader.py's book format, for the mirror and `replicate`)."""
import collections, datetime, json, time, urllib.request
A = "0xb65dd7c56afbf3b272ab5fc49be44b47dca18003"
FROM_BOOK = 1790985600000   # 2026-10-03, where the minute data starts

def post(body):
    r = urllib.request.Request("https://api.hyperliquid.xyz/info", data=json.dumps(body).encode(),
                               headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=60))

out, t = {}, int(datetime.datetime(2026, 3, 1, tzinfo=datetime.timezone.utc).timestamp() * 1000)
while True:
    page = post({"type": "userFillsByTime", "user": A, "startTime": t, "aggregateByTime": False})
    new = [x for x in page if x["tid"] not in out]
    for x in page: out[x["tid"]] = x
    if len(page) < 2000 or not new: break
    t = page[-1]["time"]; time.sleep(0.3)
fills = sorted(out.values(), key=lambda x: (x["time"], x["tid"]))
json.dump(fills, open("hl_fills.json", "w"))

orders = {}
for f in fills:
    o = orders.setdefault(f["oid"], dict(coin=f["coin"], side=f["side"], t0=f["time"], t1=f["time"], sz=0, ntl=0, pnl=0, fee=0, crossed=f["crossed"]))
    sz = float(f["sz"]); o["sz"] += sz; o["ntl"] += sz * float(f["px"]); o["pnl"] += float(f["closedPnl"]); o["fee"] += float(f["fee"]); o["t1"] = f["time"]
trips, cur, pos = [], {}, collections.defaultdict(float)
for o in sorted(orders.values(), key=lambda o: o["t0"]):
    o["px"] = o["ntl"] / o["sz"]; c = o["coin"]
    if o["side"] == "B":
        if abs(pos[c]) < 1e-9: cur[c] = dict(coin=c, buys=[], sells=[], t0=o["t0"])
        cur[c]["buys"].append(o); pos[c] += o["sz"]
    elif c in cur:
        cur[c]["sells"].append(o); pos[c] -= o["sz"]
        if pos[c] < o["sz"] * 1e-6:
            pos[c] = 0; tr = cur.pop(c); tr["t1"] = o["t1"]; trips.append(tr)
json.dump(trips, open("trips.json", "w"))

ch, held, gross = [], {}, 0.0
for f in fills:
    if f["time"] < FROM_BOOK: continue
    sz, sp, px = float(f["sz"]), float(f["startPosition"]), float(f["px"])
    ep = sp + (sz if f["side"] == "B" else -sz)
    if abs(ep) < 1e-9: ep = 0.0
    ch.append({"ts": f["time"], "symbol": f["coin"], "end_position": ep, "start_position": sp, "price": px, "size": sz, "side": f["side"],
               "direction": f["dir"], "closed_pnl": float(f["closedPnl"]), "fee": float(f["fee"]), "maker": not f["crossed"]})
    held[f["coin"]] = abs(ep) * px; gross = max(gross, sum(held.values()))
ch.sort(key=lambda c: (c["ts"], c["symbol"]))
json.dump({"address": A, "venue": "hyperliquid", "start": FROM_BOOK, "end": fills[-1]["time"] + 1, "max_gross_usd": gross, "changes": ch,
           "notices": ["built from Hyperliquid userFillsByTime, not the 0xArchive route"],
           "in_dataset": sorted({c["symbol"] for c in ch})}, open("trader_oct.json", "w"))
print(len(fills), "fills,", len(trips), "closed trips,", len(ch), "changes from 3 Oct")
