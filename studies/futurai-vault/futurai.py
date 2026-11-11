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
#   pick/pick_hours         new trips only in the `pick` markets with the highest volatility over pick_hours
#   exit_scale/step_scale   multiply every exit distance / every add distance (for the plateau check)
#   trim_level/trim         from trim_level buys on, the last add is also offered `trim` above its own fill;
#                           when that sells, the trip steps back one level and the add rests again
#   oi_max/oi_hours/oi_size while oi_market's open interest is up more than oi_max over oi_hours, new trips
#                           open at oi_size x the first order (0 = no new trips)
import oxarchive_backtest as oxb

STEPS = "-0.0225,-0.0354,-0.0504,-0.0700,-0.0985,-0.1495"
MULT = "1.0,0.966,0.966,0.966,0.966,1.06"
EXITS = "0.0056,0.00567,0.0058,0.00603,0.00652,0.0035,0.0035"


def strategy(markets="ADA,BNB,BTC,DOGE,ETH,HYPE,LINK,SOL,TRX,XRP", ema_hours=14, entry=-0.0088,
             steps=STEPS, mult=MULT, exits=EXITS, base=0.0036, max_open=7,
             gate_market="", gate_hours=0, max_level=7, stop=0.0, vol_scale=0, vol_ref=0.006, budget=0.0,
             oi_market="BTC", oi_hours=24, oi_max=0.0, oi_size=0.0, trim_level=0, trim=0.02,
             pick=0, pick_hours=168, exit_scale=1.0, step_scale=1.0):
    universe = [m.strip() for m in markets.split(",")] if isinstance(markets, str) else list(markets)
    steps = [float(v) * step_scale for v in (steps.split(",") if isinstance(steps, str) else steps)]
    mult = [float(v) for v in mult.split(",")] if isinstance(mult, str) else list(mult)
    exits = [float(v) * exit_scale for v in (exits.split(",") if isinstance(exits, str) else exits)]
    a = 2 / (ema_hours + 1)
    ga = 2 / (gate_hours + 1) if gate_hours else 0.0

    def cancel(ctx, oid):
        if oid is not None and any(o.id == oid for o in ctx.open_orders):
            ctx.cancel(oid)

    def entry_px(e, k):
        # p / (e (1 - a) + p a) = k, solved for p: where price sits `entry` under the live EMA
        return k * e * (1 - a) / (1 - k * a)

    def rest(ctx, m, t):
        for key in ("next", "out", "stop", "trim"):
            cancel(ctx, t.get(key))
            t[key] = None
        held = t["qty"]
        if held <= 0:
            return
        avg = t["cost"] / t["qty"]
        i = t["level"]                       # buys so far, 1 = the entry
        s = t["scale"]
        out_px = avg * (1 + s * exits[min(i, len(exits)) - 1])
        cut = 0.0
        if trim_level and i >= trim_level and i > 1:
            q, px = t["adds"][-1]
            if px * (1 + trim) < out_px and q < held:
                cut = q
                t["trim"] = ctx.limit(m, -cut, px * (1 + trim), reduce_only=True)
        t["out"] = ctx.limit(m, -(held - cut), out_px, reduce_only=True)
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
            if pick:
                v = h.close.vol(int(pick_hours))
                ranked = sorted((m for m in universe if v[m] is not None), key=lambda m: -v[m] if pick > 0 else v[m])
                st["allowed"] = set(ranked[:abs(int(pick))]) if len(ranked) >= abs(pick) else None   # pick < 0: the calmest, a control
            if oi_max > 0:
                now, then = h.open_interest.last(), h.open_interest.ago(int(oi_hours))
                over = [oi_market] if oi_market != "ALL" else universe   # ALL: the markets' mean change
                ch = [now[m] / then[m] - 1 for m in over if now[m] and then[m]]
                st["hot"] = bool(ch and sum(ch) / len(ch) > oi_max)
            if gate_hours:
                g = closes[gate_market]
                if g is not None:
                    st["gema"] = g if "gema" not in st else st["gema"] * (1 - ga) + g * ga
                    st["gate"] = g >= st["gema"]
        gate = st.get("gate", True) if gate_hours else True
        spent = sum(t["cost"] for t in trips.values())
        hot = oi_max > 0 and st.get("hot", False)
        size = base * (oi_size if hot else 1.0)
        room = gate and size > 0 and len(trips) < max_open and (budget <= 0 or spent <= budget * ctx.equity)
        allowed = st.get("allowed") if pick else None
        for m in universe:
            if m in trips or m not in ema or ctx.price(m) is None:
                continue
            if not room or (allowed is not None and m not in allowed):
                cancel(ctx, ent.pop(m, None))
                continue
            if new_hour or m not in ent:     # the level only moves when an hour closes
                cancel(ctx, ent.get(m))
                s = max(0.5, min(3.0, st.get("vol", {}).get(m, vol_ref) / vol_ref)) if vol_scale else 1.0
                px = entry_px(ema[m], 1 + s * entry)
                ent[m] = ctx.limit(m, size * ctx.equity / px, px)
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
                t.setdefault("adds", []).append([0.0, f.price])
            t["adds"][-1][0] += f.size
            t["qty"] += f.size
            t["cost"] += f.size * f.price
            rest(ctx, m, t)
        elif t is not None:                  # a sell
            trimmed = f.order_id == t.get("trim")
            t["cost"] *= (t["qty"] + f.size) / t["qty"]
            t["qty"] += f.size
            if abs(ctx.positions[m]) <= 1e-12:
                for key in ("next", "out", "stop", "trim"):
                    cancel(ctx, t.get(key))
                del trips[m]
            elif trimmed:                    # the last add is sold: back one level, rest it again
                t["adds"].pop()
                t["level"] -= 1
                t["last_add"] = None
                rest(ctx, m, t)

    return oxb.Strategy(universe=universe, clock="1m", step=step, on_fill=on_fill)
