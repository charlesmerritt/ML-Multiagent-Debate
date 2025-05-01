import argparse, duckdb, os, sys

def parquet_to_sample_csv(src, dst, n_rows=5_000):
    if not os.path.isfile(src):
        raise FileNotFoundError(src)

    p_src = src.replace("'", "''")
    p_dst = dst.replace("'", "''")

    con = duckdb.connect()
    con.execute(f"""
        COPY (
          SELECT *
          FROM read_parquet('{p_src}')
          WHERE question IS NOT NULL         -- keep if you have that column
          ORDER BY random()
          LIMIT {n_rows}
        )
        TO '{p_dst}'
        (FORMAT CSV, HEADER TRUE);
    """)
    con.close()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("parquet")
    ap.add_argument("csv")
    ap.add_argument("-n", "--rows", type=int, default=5000)
    args = ap.parse_args()

    try:
        parquet_to_sample_csv(args.parquet, args.csv, args.rows)
        print(f"✔ wrote {args.rows} sampled rows → {args.csv}")
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)
