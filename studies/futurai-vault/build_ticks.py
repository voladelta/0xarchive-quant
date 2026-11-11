"""Every trade in the vault's ten markets from ironflow/hyperliquid-trades, one local file per UTC day:
time, coin, price, size, taker side. usage: build_ticks.py 2026-10-03 2026-11-08"""
import duckdb, sys, datetime, pathlib
BASE = "https://huggingface.co/datasets/ironflow/hyperliquid-trades/resolve/main/data/"
out = pathlib.Path("ext/ticks"); out.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(); c.execute("INSTALL httpfs; LOAD httpfs;")
d = datetime.date.fromisoformat(sys.argv[1]); end = datetime.date.fromisoformat(sys.argv[2])
while d <= end:
    f = out / f"{d}.parquet"
    if not f.exists():
        c.execute(f"""COPY (SELECT epoch_ms(timestamp) AS ts, coin, price, size, taker_side = 'buy' AS taker_buy
          FROM '{BASE}{d}.parquet' WHERE dex='' AND market_class='perp'
            AND coin IN ('ADA','LINK','HYPE','SOL','DOGE','XRP','ETH','TRX','BNB','BTC')
          ORDER BY coin, ts) TO '{f}' (FORMAT parquet, COMPRESSION zstd)""")
        print(d, flush=True)
    d += datetime.timedelta(days=1)
