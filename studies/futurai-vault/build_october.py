"""October 2026 in the engine's minute format, from free sources (the 0xArchive free key stops 30 days back):
prices, volume and taker flow from ext/minutes (ironflow/hyperliquid-trades, 3-31 Oct), funding from
ironflow/hyperliquid-funding. Every other column is null. Not an `0xbt data pull` file: say so with results."""
import duckdb
c = duckdb.connect(); c.execute("INSTALL httpfs; LOAD httpfs;")
FUND = "https://huggingface.co/datasets/ironflow/hyperliquid-funding/resolve/main/data/2026-10.parquet"
c.execute(f"CREATE TABLE fund AS SELECT coin, epoch_ms(date_trunc('hour', timestamp)) ts, funding_rate, premium FROM '{FUND}' WHERE dex=''")
c.execute("CREATE TABLE m AS SELECT * FROM 'ext/minutes/*.parquet'")
c.execute("CREATE TABLE oi AS SELECT * FROM 'ext/oi_1h.parquet'")   # ironflow/hyperliquid-open-interest, hourly snapshots
for coin in "ADA LINK HYPE SOL DOGE XRP ETH TRX BNB BTC".split():
    ref = f"data/hyperliquid/{coin}/2026-11.parquet"
    # the last October hour settles in November's first row
    c.execute(f"INSERT INTO fund SELECT '{coin}', ts, funding_settled, NULL FROM '{ref}' WHERE ts = 1793491200000")
    cols = [r[0] for r in c.execute(f"DESCRIBE SELECT * FROM '{ref}'").fetchall()]
    types = {r[0]: r[1] for r in c.execute(f"DESCRIBE SELECT * FROM '{ref}'").fetchall()}
    have = {"open","high","low","close","volume","quote_volume","vwap","taker_buy_quote","taker_sell_quote","trade_count"}
    sel = []
    for k in cols:
        if k == "ts": e = "g.ts"
        elif k in have: e = f"m.{k}"
        elif k == "cvd_delta": e = "m.taker_buy_quote - m.taker_sell_quote"
        elif k == "funding_rate": e = "coalesce(f2.funding_rate, last_value(f.funding_rate IGNORE NULLS) OVER (ORDER BY g.ts))"  # the estimate is the rate the hour settles at
        elif k == "premium": e = "last_value(f.premium IGNORE NULLS) OVER (ORDER BY g.ts)"
        elif k == "funding_settled": e = "f.funding_rate"
        elif k == "open_interest": e = "o.oi"   # the last reading of the clock hour, on its rows; strategies see it only once the hour's bar has closed
        else: e = "NULL"
        sel.append(f"CAST({e} AS {types[k]}) AS {k}")
    out = f"data/hyperliquid/{coin}/2026-10.parquet"
    c.execute(f"""COPY (SELECT {', '.join(sel)}
      FROM (SELECT unnest(range(1790812800000, 1793491200000, 60000)) AS ts) g
      LEFT JOIN m ON m.ts = g.ts AND m.coin = '{coin}'
      LEFT JOIN fund f ON f.ts = g.ts AND f.coin = '{coin}'
      LEFT JOIN fund f2 ON f2.ts = (g.ts // 3600000 + 1) * 3600000 AND f2.coin = '{coin}'
      LEFT JOIN oi o ON o.ts = (g.ts // 3600000) * 3600000 AND o.coin = '{coin}'
      ORDER BY g.ts) TO '{out}' (FORMAT parquet, COMPRESSION zstd, KV_METADATA {{"oxs.schema_version": '1m-v0', "oxs.dataset_version": 'ironflow-v0', "oxs.market": 'hyperliquid:{coin}', "oxs.month": '2026-10', "oxs.start.fills": '2025-03-22', "oxs.start.orders": '2026-03-10', "oxs.start.book": '2023-04-15', "oxs.start.context": '2023-05-20', "oxs.start.liquidations": '2025-12-22', "oxs.start.liqlevels": '2026-07-27'}})""")
    print(coin, c.execute(f"SELECT count(*), count(open), count(funding_settled) FROM '{out}'").fetchone())
