#!/usr/bin/env python3
# debate_csv.py  --input questions.csv --out answers.csv --model gpt-3.5-turbo
import csv, json, argparse, os, openai, time, sys

openai.api_key = os.getenv("OPENAI_API_KEY")

def one_debate(question, model):
    # Agent 1
    a1 = openai.ChatCompletion.create(
        model=model,
        messages=[{"role":"user","content":f"Question: {question}\nProvide a detailed answer."}],
        max_tokens=200, temperature=0.7
    ).choices[0].message.content.strip()

    # Agent 2
    a2 = openai.ChatCompletion.create(
        model=model,
        messages=[{"role":"user","content":f"Question: {question}\nProvide a detailed answer."}],
        max_tokens=200, temperature=0.7
    ).choices[0].message.content.strip()

    # Moderator
    mod = openai.ChatCompletion.create(
        model=model,
        messages=[
          {"role":"system","content":"You are an AI debate moderator. Correct errors and merge answers."},
          {"role":"user",
           "content":f"Agent 1: {a1}\nAgent 2: {a2}\n\nProvide a consensus answer to: {question}"}
        ],
        max_tokens=200, temperature=0.7
    ).choices[0].message.content.strip()

    return a1, a2, mod

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_in",  help="CSV with 'question' column")
    ap.add_argument("csv_out", help="CSV to write question,agent1,agent2,moderator")
    ap.add_argument("--model", default="gpt-4.1-nano-2025-04-14")
    args = ap.parse_args()

    rows=[]
    with open(args.csv_in) as f:
        for row in csv.DictReader(f):
            q=row['question'].strip()
            try:
                a1,a2,mod=one_debate(q,args.model)
            except Exception as e:
                print("API error on:",q[:60], file=sys.stderr); raise
            rows.append({"question":q,"agent1":a1,"agent2":a2,"moderator":mod})
            print(f"✓ {len(rows)}", end='\r', flush=True)

    csv.DictWriter(open(args.csv_out,'w'), fieldnames=rows[0].keys()).writeheader()
    csv.DictWriter(open(args.csv_out,'a'), fieldnames=rows[0].keys()).writerows(rows)
    print(f"\nDone → {args.csv_out}")

if __name__=="__main__":
    main()
