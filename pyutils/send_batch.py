#!/usr/bin/env python3
"""
send_batch.py
=============

Submit an OpenAI Batch JSONL, poll until it finishes, then download the
result file and convert it to CSV.

• Dry-run    :  --test 5     (sends only the first 5 records)
• Window     :  --window 1h  (default 24h)
• Output     :  --out myrun  (produces myrun.jsonl + myrun.csv)
"""

import argparse, csv, itertools, json, os, sys, time, tempfile, pandas as pd
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def head_jsonl(src, dst, n):
    """Copy first n lines of src JSONL → dst."""
    with open(src) as fin, open(dst, "w") as fout:
        for line in itertools.islice(fin, n):
            fout.write(line)


def submit_batch(jsonl_path, window):
    """Upload JSONL & create a batch job."""
    file_obj = openai.files.create(
        file=open(jsonl_path, "rb"),
        purpose="batch"
    )
    batch = openai.batches.create(
        input_file_id=file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window=window
    )
    return batch


def poll(batch_id, interval=20):
    """Poll until batch status is completed|failed → return batch object."""
    start = time.time()
    while True:
        b = openai.batches.retrieve(batch_id)
        if b.status in ("completed", "failed"):
            return b
        elapsed = int(time.time() - start)
        print(f"…{b.status} (elapsed {elapsed}s)")
        time.sleep(interval)


def download_file(file_id, out_path):
    """Fetch File content → write to out_path (binary)."""
    data = openai.files.content(file_id)          # returns HttpxBinaryResponseContent
    with open(out_path, "wb") as f:
        # .content or .read() depending on SDK version
        if hasattr(data, "read"):
            f.write(data.read())                  # SDK ≥1.10
        else:
            f.write(data)                         # older helper returned bytes


def save_csv(jsonl_path, csv_path):
    rows = []
    with open(jsonl_path) as f:
        for line in f:
            rec = json.loads(line)
            q   = rec["request"]["body"]["messages"][1]["content"]
            ans = rec["response"]["body"]["choices"][0]["message"]["content"].strip()
            rows.append({"question": q, "answer": ans})
    pd.DataFrame(rows).to_csv(csv_path, index=False)


# ----------------------------------------------------------------------
# main
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Submit OpenAI Batch JSONL")
    ap.add_argument("jsonl", help="request JSONL created by csv_to_batch_jsonl.py")
    ap.add_argument("--window", default="24h", choices=("1h", "24h"),
                    help="completion window (default 24h)")
    ap.add_argument("--test", type=int, metavar="N",
                    help="dry-run first N records instead of full JSONL")
    ap.add_argument("--out", default="answers",
                    help="output prefix (default 'answers')")
    args = ap.parse_args()

    job_jsonl = args.jsonl
    cleanup_tmp = False

    # optional dry-run
    if args.test:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        tmp.close()
        head_jsonl(args.jsonl, tmp.name, args.test)
        job_jsonl = tmp.name
        cleanup_tmp = True
        print(f"Submitting DRY-RUN with first {args.test} records → {tmp.name}")

    # 1. upload & create batch
    batch = submit_batch(job_jsonl, args.window)
    print("⇢ Batch id:", batch.id)

    # 2. poll
    batch = poll(batch.id)
    if batch.status == "failed":
        print("Batch failed:", batch.error, file=sys.stderr)
        sys.exit(1)

    # 3. download result JSONL
    result_jsonl = f"{args.out}.jsonl"
    download_file(batch.output_file_id, result_jsonl)
    print("✓ downloaded results →", result_jsonl)

    # 4. convert to CSV
    save_csv(result_jsonl, f"{args.out}.csv")
    print("✓ wrote", f"{args.out}.csv")

    if cleanup_tmp:
        os.unlink(job_jsonl)


if __name__ == "__main__":
    main()
