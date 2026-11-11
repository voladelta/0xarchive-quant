"""An 18-month coarse dataset in the engine's format, from ironflow/hyperliquid-candles-1h and -funding:
each hour's bar sits on the hour's last minute row (known at its close), every other minute is empty.
Coarse on purpose: for drawdowns and for comparing variants, not for a headline return."""
import duckdb, pathlib
c = duckdb.connect(); c.execute("INSTALL httpfs; LOAD httpfs;")
MONTHS = [f"{y}-{m:02d}" for y in (2025, 2026) for m in range(1, 13) if (2025, 6) <= (y, m) <= (2026, 10)]
import sys
COINS = sys.argv[1].split(",") if len(sys.argv) > 1 else "ADA LINK HYPE SOL DOGE XRP ETH TRX BNB BTC".split()
furls = [f"https://huggingface.co/datasets/ironflow/hyperliquid-funding/resolve/main/data/{m}.parquet" for m in MONTHS]
c.execute(f"""CREATE TABLE fund AS SELECT coin, epoch_ms(date_trunc('hour', timestamp)) ts, any_value(funding_rate) funding_rate, any_value(premium) premium
              FROM read_parquet({furls}) WHERE dex='' AND coin IN ({','.join(repr(x) for x in COINS)}) GROUP BY 1, 2""")
c.execute("CREATE TABLE k AS SELECT * FROM 'ext/candles_1h.parquet'")
c.execute("CREATE TABLE oi AS SELECT * FROM 'ext/oi_1h.parquet'")   # ironflow/hyperliquid-open-interest, hourly snapshots
ref = "data/hyperliquid/BTC/2026-11.parquet"
desc = c.execute(f"DESCRIBE SELECT * FROM '{ref}'").fetchall()
for coin in COINS:
    for mon in MONTHS:
        y, m = map(int, mon.split("-"))
        t0 = c.execute(f"SELECT epoch_ms(TIMESTAMP '{mon}-01 00:00:00')").fetchone()[0]
        t1 = c.execute(f"SELECT epoch_ms(TIMESTAMP '{mon}-01 00:00:00' + INTERVAL 1 MONTH)").fetchone()[0]
        sel = []
        for name, typ, *_ in desc:
            if name == "ts": e = "g.ts"
            elif name in ("open", "high", "low", "close", "volume"): e = f"k.{name}"
            elif name == "quote_volume": e = "k.volume * (k.open + k.close) / 2"
            elif name == "vwap": e = "(k.open + k.close) / 2"
            elif name == "trade_count": e = "k.trades"
            elif name == "open_interest": e = "o.oi"   # the last reading of the clock hour, on its rows; strategies see it only once the hour's bar has closed
            elif name == "funding_rate": e = "f2.funding_rate"
            elif name == "funding_settled": e = "f.funding_rate"
            else: e = "NULL"
            sel.append(f"CAST({e} AS {typ}) AS {name}")
        out = pathlib.Path(f"data1h/hyperliquid/{coin}"); out.mkdir(parents=True, exist_ok=True)
        c.execute(f"""COPY (SELECT {', '.join(sel)}
          FROM (SELECT unnest(range({t0}, {t1}, 60000)) AS ts) g
          LEFT JOIN k ON k.ts + 3540000 = g.ts AND k.coin = '{coin}'
          LEFT JOIN fund f ON f.ts = g.ts AND f.coin = '{coin}'
          LEFT JOIN fund f2 ON f2.ts = (g.ts // 3600000 + 1) * 3600000 AND f2.coin = '{coin}'
          LEFT JOIN oi o ON o.ts = (g.ts // 3600000) * 3600000 AND o.coin = '{coin}'
          ORDER BY g.ts) TO '{out}/{mon}.parquet' (FORMAT parquet, COMPRESSION zstd, KV_METADATA {{"oxs.schema_version": '1m-v0', "oxs.dataset_version": 'ironflow-1h-v0', "oxs.market": 'hyperliquid:{coin}', "oxs.month": '{mon}', "oxs.start.fills": '2025-03-22', "oxs.start.orders": '2026-03-10', "oxs.start.book": '2023-04-15', "oxs.start.context": '2023-05-20', "oxs.start.liquidations": '2025-12-22', "oxs.start.liqlevels": '2026-07-27'}})""")
    print(coin, flush=True)
