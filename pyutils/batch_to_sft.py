#!/usr/bin/env python3
"""
batch_to_sft.py  --req requests.jsonl --res results.jsonl --csv out.csv --sft out.jsonl
i.e. batch_to_sft.py --req batch_requests/gsm8k_lo.jsonl --res batch_responses/low_batch_68132d3745808190a446a21dc14edb6c_output.jsonl --csv low_gsm8k.csv --sft low_gsm8k.jsonl
"""

import argparse, json, pathlib, re, sys
import pandas as pd

TAG_RE = re.compile(r"_(hi|lo|c)$")

def load_requests(req_path):
    """Return dict custom_id → question prompt."""
    mapping = {}
    with open(req_path) as f:
        for ln in f:
            rec = json.loads(ln)
            cid = rec["custom_id"]
            prompt = rec["body"]["messages"][1]["content"].strip()
            mapping[cid] = prompt
    return mapping

def parse_batch(res_path, req_map):
    for ln in open(res_path):
        rec = json.loads(ln)
        cid = rec["custom_id"]
        answer = rec["response"]["body"]["choices"][0]["message"]["content"].strip()
        prompt = req_map.get(cid, "<MISSING_PROMPT>")
        tag = TAG_RE.search(cid)
        yield {"question": prompt, "answer": answer,
               "agree_tag": tag.group(1) if tag else "na"}

def write_sft(df, out_path):
    with open(out_path, "w") as f:
        for _, r in df.iterrows():
            token = "<AGREE=hi>" if r.agree_tag == "hi" else "<AGREE=lo>"
            obj = {"messages":[
                     {"role":"system",    "content": token},
                     {"role":"user",      "content": r.question},
                     {"role":"assistant", "content": r.answer}
                   ]}
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--req", required=True,  help="original request JSONL")
    p.add_argument("--res", required=True,  help="batch result JSONL")
    p.add_argument("--csv", default="answers.csv")
    p.add_argument("--sft", default="sft_dataset.jsonl")
    a = p.parse_args()

    req_map = load_requests(a.req)
    df = pd.DataFrame(parse_batch(a.res, req_map))
    if df.empty:
        sys.exit("No records parsed.")

    df.to_csv(a.csv, index=False)
    print(f"✓ wrote {a.csv} ({len(df)})")

    write_sft(df, a.sft)
    print(f"✓ wrote {a.sft} ({len(df)})")

if __name__ == "__main__":
    main()
