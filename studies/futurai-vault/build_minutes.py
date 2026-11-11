"""Minute bars for the vault's markets from ironflow/hyperliquid-trades (Hugging Face), via duckdb.
Reads only the columns it needs; one remote file per UTC day."""
import duckdb, sys, datetime, pathlib
COINS = "'ADA','LINK','HYPE','SOL','DOGE','XRP','ETH','TRX','BNB','BTC'"
BASE = "https://huggingface.co/datasets/ironflow/hyperliquid-trades/resolve/main/data/"
out = pathlib.Path("ext/minutes"); out.mkdir(parents=True, exist_ok=True)
c = duckdb.connect(); c.execute("INSTALL httpfs; LOAD httpfs;")
d = datetime.date.fromisoformat(sys.argv[1]); end = datetime.date.fromisoformat(sys.argv[2])
while d <= end:
    f = out / f"{d}.parquet"
    if not f.exists():
        c.execute(f"""COPY (
          SELECT coin, epoch_ms(date_trunc('minute', timestamp)) AS ts,
                 arg_min(price, (timestamp, block, tid)) AS open, max(price) AS high, min(price) AS low,
                 arg_max(price, (timestamp, block, tid)) AS close,
                 sum(size) AS volume, sum(notional) AS quote_volume, sum(notional)/sum(size) AS vwap,
                 coalesce(sum(notional) FILTER (WHERE taker_side='buy'),0) AS taker_buy_quote,
                 coalesce(sum(notional) FILTER (WHERE taker_side='sell'),0) AS taker_sell_quote,
                 count(*)::INTEGER AS trade_count
          FROM '{BASE}{d}.parquet'
          WHERE dex='' AND market_class='perp' AND coin IN ({COINS})
          GROUP BY 1,2 ORDER BY 1,2) TO '{f}' (FORMAT parquet)""")
        print(d, c.execute(f"SELECT count(*) FROM '{f}'").fetchone()[0], flush=True)
    d += datetime.timedelta(days=1)
