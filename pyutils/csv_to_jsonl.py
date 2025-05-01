#!/usr/bin/env python3
"""
csv_to_batch_jsonl.py
=====================

Convert a CSV (must contain a 'question' column) into a JSONL file that
OpenAI's /v1/batches endpoint can consume.  Each JSONL line is a *single*
chat-completion request that internally simulates a 1-round debate:

• high-agreeableness variant  → polite collaborative synthesis
• low-agreeableness variant   → critical, independent synthesis

CLI
---
$ python csv_to_batch_jsonl.py questions.csv requests.jsonl
$ python csv_to_batch_jsonl.py questions.csv hi.jsonl --agree hi
$ python csv_to_batch_jsonl.py questions.csv mid.jsonl --agree 0.3
"""

import csv, json, argparse, pathlib, sys

# ---------- system prompt templates ------------------------------
SIM_HI = (
    "You are to imagine two internal agents debating. "
    "Agent-1 and Agent-2 each produce a detailed answer, then you—"
    "as a highly *agreeable* moderator—synthesize them. "
    "Integrate their viewpoints explicitly and present a unified, constructive answer."
)

SIM_LO = (
    "You are to imagine two internal agents debating. "
    "Agent-1 and Agent-2 each produce a detailed answer. "
    "You are a *critical* moderator: review their ideas, highlight flaws, "
    "and present your own concise, self-contained conclusion without overt collaboration."
)

# ---------- variant selector -------------------------------------
def make_records(prompt: str,
                 model: str,
                 agree_flag: str,
                 prefix: str,
                 idx: int):
    """
    Yield 1–2 JSONL request records depending on agree_flag.
    """
    if agree_flag == "both":
        variants = [("hi", 1.0, SIM_HI), ("lo", 0.0, SIM_LO)]
    elif agree_flag in ("hi", "lo"):
        variants = [("hi", 1.0, SIM_HI)] if agree_flag == "hi" \
                 else [("lo", 0.0, SIM_LO)]
    else:                               # numeric 0-1
        agree_val = float(agree_flag)
        tmpl = SIM_HI if agree_val >= 0.5 else SIM_LO
        variants = [("c", agree_val, tmpl)]               # 'c' = custom

    for tag, val, sys_prompt in variants:
        yield {
            "custom_id": f"{prefix}{idx:06d}_{tag}",
            "method":   "POST",
            "url":      "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [
                    {"role": "system",
                     "content": f"{sys_prompt} (Agreeableness={val})"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 256
            }
        }

# ---------- main converter ---------------------------------------
def csv_to_jsonl(csv_path, jsonl_path, agree, model, prefix):
    csv_path   = pathlib.Path(csv_path).expanduser().resolve()
    jsonl_path = pathlib.Path(jsonl_path).expanduser()
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open(newline='') as cf, jsonl_path.open('w') as jf:
        rdr = csv.DictReader(cf)
        if 'question' not in rdr.fieldnames:
            raise KeyError("CSV missing 'question' column")

        for i, row in enumerate(rdr, 1):
            prompt = row['question'].strip()
            for rec in make_records(prompt, model, agree, prefix, i):
                jf.write(json.dumps(rec, ensure_ascii=False) + '\n')

# ---------- CLI ---------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Create Batch-API JSONL with high/low agreeableness debate prompts."
    )
    ap.add_argument("csv",   help="input CSV with a 'question' column")
    ap.add_argument("jsonl", help="output JSONL path")
    ap.add_argument("-a", "--agree", default="both",
                    help="'both' (default), 'hi', 'lo', or a float 0-1")
    ap.add_argument("-m", "--model", default="gpt-4.1-nano-2025-04-14",
                    help="OpenAI model name (default gpt-4.1-nano)")
    ap.add_argument("-n", "--name",  default="",
                    help="prefix for custom_id values")
    args = ap.parse_args()

    try:
        csv_to_jsonl(args.csv, args.jsonl, args.agree, args.model, args.name)
        print(f"✓ wrote {args.jsonl}")
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)
