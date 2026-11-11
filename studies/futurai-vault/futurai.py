# The FuturAI Labs vault's rules as read from its fills (REPORT.md "Rules"), and the changes tested on them.
#
#     0xbt backtest futurai.py --start 2026-10-03 --end 2026-11-11
#     python3 trader.py replicate trader_oct.json futurai.py --clock 1m --start 2026-10-03 --end 2026-11-11
#
# Flat market, fewer than `max_open` trips running: rest a buy where price would sit `entry` under a live
# hourly EMA. The first fill opens a trip. Then one add rests at each of `steps` from the first fill, sized
# `mult` x what is held, and one reduce-only sell for the whole position rests at the average entry plus
# the `exits` value for the number of buys so far.
#
# The vault's numbers are the defaults. The changes, each off by default:
#   gate_market/gate_hours  open new trips only while gate_market closes above its own hourly EMA
#   max_level               stop adding after this many buys (the vault's ladder runs to 7)
#   stop                    close a trip at its average entry less this fraction
#   vol_scale               scale steps and exits by the market's 24h volatility over vol_ref
#   budget                  no new trip while the cost held across all trips is above this share of equity
import oxarchive_backtest as oxb

STEPS = "-0.0225,-0.0354,-0.0504,-0.0700,-0.0985,-0.1495"
MULT = "1.0,0.966,0.966,0.966,0.966,1.06"
EXITS = "0.0056,0.00567,0.0058,0.00603,0.00652,0.0035,0.0035"


def strategy(markets="ADA,BNB,BTC,DOGE,ETH,HYPE,LINK,SOL,TRX,XRP", ema_hours=14, entry=-0.0088,
             steps=STEPS, mult=MULT, exits=EXITS, base=0.0036, max_open=7,
             gate_market="", gate_hours=0, max_level=7, stop=0.0, vol_scale=0, vol_ref=0.006, budget=0.0):
    universe = [m.strip() for m in markets.split(",")] if isinstance(markets, str) else list(markets)
    steps = [float(v) for v in steps.split(",")] if isinstance(steps, str) else list(steps)
    mult = [float(v) for v in mult.split(",")] if isinstance(mult, str) else list(mult)
    exits = [float(v) for v in exits.split(",")] if isinstance(exits, str) else list(exits)
    a = 2 / (ema_hours + 1)
    ga = 2 / (gate_hours + 1) if gate_hours else 0.0

    def cancel(ctx, oid):
        if oid is not None and any(o.id == oid for o in ctx.open_orders):
            ctx.cancel(oid)

    def entry_px(e, k):
        # p / (e (1 - a) + p a) = k, solved for p: where price sits `entry` under the live EMA
        return k * e * (1 - a) / (1 - k * a)

    def rest(ctx, m, t):
        for key in ("next", "out", "stop"):
            cancel(ctx, t.get(key))
            t[key] = None
        held = t["qty"]
        if held <= 0:
            return
        avg = t["cost"] / t["qty"]
        i = t["level"]                       # buys so far, 1 = the entry
        s = t["scale"]
        t["out"] = ctx.limit(m, -held, avg * (1 + s * exits[min(i, len(exits)) - 1]), reduce_only=True)
        if stop > 0 and i >= max_level:      # the stop only arms once the ladder is spent
            t["stop"] = ctx.stop(m, -held, avg * (1 - stop), reduce_only=True)
        if i <= len(steps) and i < max_level:
            t["next"] = ctx.limit(m, mult[i - 1] * held, t["first"] * (1 + s * steps[i - 1]))

    def step(ctx, h):
        st = ctx.state
        ema, trips, ent = st.setdefault("ema", {}), st.setdefault("trips", {}), st.setdefault("entry", {})
        hour = ctx.time // 3_600_000
        new_hour = st.get("hour") != hour
        if new_hour:
            st["hour"] = hour
            closes = h.close.last()
            vols = h.close.vol(24) if vol_scale else None
            for m in universe:
                c = closes[m]
                if c is not None:
                    ema[m] = c if m not in ema else ema[m] * (1 - a) + c * a
                if vols is not None and vols[m] is not None:
                    st.setdefault("vol", {})[m] = vols[m]
            if gate_hours:
                g = closes[gate_market]
                if g is not None:
                    st["gema"] = g if "gema" not in st else st["gema"] * (1 - ga) + g * ga
                    st["gate"] = g >= st["gema"]
        gate = st.get("gate", True) if gate_hours else True
        spent = sum(t["cost"] for t in trips.values())
        room = gate and len(trips) < max_open and (budget <= 0 or spent <= budget * ctx.equity)
        for m in universe:
            if m in trips or m not in ema or ctx.price(m) is None:
                continue
            if not room:
                cancel(ctx, ent.pop(m, None))
                continue
            if new_hour or m not in ent:     # the level only moves when an hour closes
                cancel(ctx, ent.get(m))
                s = max(0.5, min(3.0, st.get("vol", {}).get(m, vol_ref) / vol_ref)) if vol_scale else 1.0
                px = entry_px(ema[m], 1 + s * entry)
                ent[m] = ctx.limit(m, base * ctx.equity / px, px)
                st.setdefault("scale", {})[m] = s

    def on_fill(ctx, f):
        st = ctx.state
        m, trips, ent = f.market, st.setdefault("trips", {}), st.setdefault("entry", {})
        t = trips.get(m)
        if f.size > 0:                       # a buy
            if t is None:
                t = trips[m] = {"first": f.price, "qty": 0.0, "cost": 0.0, "level": 0,
                                "scale": st.get("scale", {}).get(m, 1.0)}
                ent.pop(m, None)
                if len(trips) >= max_open:   # the book is full: pull the other entries
                    for o in list(ent):
                        cancel(ctx, ent.pop(o))
            if f.order_id != t.get("last_add"):
                t["level"] += 1
                t["last_add"] = f.order_id
            t["qty"] += f.size
            t["cost"] += f.size * f.price
            rest(ctx, m, t)
        elif t is not None:                  # a sell
            t["cost"] *= (t["qty"] + f.size) / t["qty"]
            t["qty"] += f.size
            if abs(ctx.positions[m]) <= 1e-12:
                for key in ("next", "out", "stop"):
                    cancel(ctx, t.get(key))
                del trips[m]

    return oxb.Strategy(universe=universe, clock="1m", step=step, on_fill=on_fill)
