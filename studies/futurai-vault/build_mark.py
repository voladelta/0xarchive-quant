"""A coarse dataset from ironflow/hyperliquid-open-interest alone, 2023-06 to 2026-10: each hour's bar closes
at the hour's last mark price and opens at the previous hour's; high and low are the larger and smaller of
the two (no intrahour range). Open interest is the hour's last reading; funding from ironflow/hyperliquid-funding."""
import duckdb, pathlib
c = duckdb.connect(); c.execute("INSTALL httpfs; LOAD httpfs;")
B = "https://huggingface.co/datasets/ironflow/"
MONTHS = [f"{y}-{m:02d}" for y in (2023, 2024, 2025, 2026) for m in range(1, 13) if (2023, 6) <= (y, m) <= (2026, 10)]
COINS = "ADA LINK HYPE SOL DOGE XRP ETH TRX BNB BTC".split()
IN = "(" + ",".join(repr(x) for x in COINS) + ")"
c.execute(f"""CREATE TABLE k AS SELECT coin, epoch_ms(date_trunc('hour', timestamp)) ts, any_value(mark_price) px, any_value(open_interest) oi
  FROM read_parquet({[B + f'hyperliquid-open-interest/resolve/main/data/{m}.parquet' for m in ['2023-05'] + MONTHS]}) WHERE dex='' AND coin IN {IN} GROUP BY 1, 2""")
c.execute("CREATE TABLE b AS SELECT coin, ts, px AS close, lag(px) OVER (PARTITION BY coin ORDER BY ts) AS open, oi, lag(ts) OVER (PARTITION BY coin ORDER BY ts) AS pts FROM k WHERE px IS NOT NULL")
c.execute(f"""CREATE TABLE fund AS SELECT coin, epoch_ms(date_trunc('hour', timestamp)) ts, any_value(funding_rate) funding_rate
  FROM read_parquet({[B + f'hyperliquid-funding/resolve/main/data/{m}.parquet' for m in MONTHS]}) WHERE dex='' AND coin IN {IN} GROUP BY 1, 2""")
desc = c.execute("DESCRIBE SELECT * FROM 'data/hyperliquid/BTC/2026-11.parquet'").fetchall()
for coin in COINS:
    first = c.execute(f"SELECT min(ts) FROM b WHERE coin='{coin}' AND open IS NOT NULL").fetchone()[0]
    for mon in MONTHS:
        t0 = c.execute(f"SELECT epoch_ms(TIMESTAMP '{mon}-01 00:00:00')").fetchone()[0]
        t1 = c.execute(f"SELECT epoch_ms(TIMESTAMP '{mon}-01 00:00:00' + INTERVAL 1 MONTH)").fetchone()[0]
        if first is None or t1 <= first: continue
        sel = []
        for name, typ, *_ in desc:
            if name == "ts": e = "g.ts"
            elif name in ("open", "close"): e = f"k.{name}"
            elif name == "high": e = "greatest(k.open, k.close)"
            elif name == "low": e = "least(k.open, k.close)"
            elif name in ("volume", "quote_volume"): e = "CASE WHEN k.close IS NOT NULL THEN 1e9 END"   # no volume in the source
            elif name == "vwap": e = "(k.open + k.close) / 2"
            elif name == "trade_count": e = "CASE WHEN k.close IS NOT NULL THEN 1000 END"
            elif name == "open_interest": e = "o.oi"
            elif name == "funding_rate": e = "f2.funding_rate"
            elif name == "funding_settled": e = "f.funding_rate"
            else: e = "NULL"
            sel.append(f"CAST({e} AS {typ}) AS {name}")
        out = pathlib.Path(f"datamark/hyperliquid/{coin}"); out.mkdir(parents=True, exist_ok=True)
        # the bar of clock hour H (its last mark) sits on H:59; a bar after a gap is dropped (its open would be stale)
        c.execute(f"""COPY (SELECT {', '.join(sel)}
          FROM (SELECT unnest(range({t0}, {t1}, 60000)) AS ts) g
          LEFT JOIN b k ON k.ts + 3540000 = g.ts AND k.coin = '{coin}' AND k.open IS NOT NULL AND k.ts - k.pts = 3600000
          LEFT JOIN fund f ON f.ts = g.ts AND f.coin = '{coin}'
          LEFT JOIN fund f2 ON f2.ts = (g.ts // 3600000 + 1) * 3600000 AND f2.coin = '{coin}'
          LEFT JOIN b o ON o.ts = (g.ts // 3600000) * 3600000 AND o.coin = '{coin}'
          ORDER BY g.ts) TO '{out}/{mon}.parquet' (FORMAT parquet, COMPRESSION zstd, KV_METADATA {{"oxs.schema_version": '1m-v0', "oxs.dataset_version": 'ironflow-mark-1h-v0', "oxs.market": 'hyperliquid:{coin}', "oxs.month": '{mon}', "oxs.start.fills": '2023-05-20', "oxs.start.orders": '2026-03-10', "oxs.start.book": '2023-04-15', "oxs.start.context": '2023-05-20', "oxs.start.liquidations": '2025-12-22', "oxs.start.liqlevels": '2026-07-27'}})""")
    print(coin, first and c.execute(f"SELECT to_timestamp({first}/1000)").fetchone()[0], flush=True)
