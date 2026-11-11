"""One candidate as 27 copies that differ only in where the first order rests.

A ladder that misses its exit by one fill can sit for months (STUDY.md, round 10), so one backtest of this
strategy is one draw. The copies: `entry` -0.0080 to -0.0096 in steps of 0.0002, times `ema_hours` 13, 14, 15.
Prints each copy and then the median, low and high of return and max drawdown.

usage: ensemble.py hourly|minute START END [name=value ...]
  ensemble.py hourly 2025-06-05 2026-11-01 pick=5 fr_max=0
  ensemble.py minute 2026-10-03 2026-11-11 pick=5
"""
import re, statistics, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

data, start, end, params = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
base = ["0xbt", "backtest", "futurai.py", "--start", start, "--end", end]
if data == "hourly":
    base += ["--data", "data1h/hyperliquid"]
for p in params:
    base += ["-p", p]
copies = [(e, h) for h in (13, 14, 15) for e in ("0.0080", "0.0082", "0.0084", "0.0086", "0.0088", "0.0090", "0.0092", "0.0094", "0.0096")]

def run(c):
    out = subprocess.run(base + ["-p", f"entry=-{c[0]}", "-p", f"ema_hours={c[1]}"], capture_output=True, text=True).stdout
    m = re.search(r"return ([+-][0-9.]+)%, sharpe ([-0-9.]+), max drawdown \+([0-9.]+)%", out)
    h = re.search(r"result_hash=([0-9a-f]+)", out)
    return (c, float(m.group(1)), float(m.group(3)), h.group(1)) if m and h else (c, None, None, None)

with ThreadPoolExecutor(4) as pool:
    rows = list(pool.map(run, copies))
for c, r, d, h in rows:
    print(f"entry -{c[0]} ema {c[1]}: " + (f"return {r:+.2f}%, max drawdown {d:.2f}%, {h}" if r is not None else "no result"))
ok = [x for x in rows if x[1] is not None]
ret, dd = [x[1] for x in ok], [x[2] for x in ok]
mr, md = statistics.median(ret), statistics.median(dd)
print(f"{' '.join(params) or 'replica'}: {len(ok)} copies; return {mr:+.2f}% ({min(ret):+.2f} to {max(ret):+.2f}); "
      f"max drawdown {md:.2f}% ({min(dd):.2f} to {max(dd):.2f}); median over median {mr / md:.2f}; "
      f"copies with a drawdown over 1.5x the median: {sum(1 for x in dd if x > 1.5 * md)}")
