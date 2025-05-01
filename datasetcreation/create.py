import os
import csv
import random
import time
from openai import OpenAI

# Set your API key
client = OpenAI()

# Helper to call GPT API for a given prompt
def gpt_generate(prompt, retries=3, sleep=0.05):
    for _ in range(retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # or use your preferred model
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error: {e}, retrying...")
            time.sleep(sleep)
    return ""

# Step 1: Read input CSV
input_csv = "gsm8k_questions.csv"
rows = []
with open(input_csv, newline='', encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        rows.append({"question": row["question"]})

# Step 2: Generate past_context (Agent 1 and Agent 2)
for row in rows:
    q = row["question"]
    prompt_agent1 = f"You are Agent 1. Read the following math problem and provide ONLY the answer with minimal necessary steps. Be extremely concise and avoid lengthy explanations:\n\nProblem: {q}\n\nAgent 1's solution:"
    agent1_output = gpt_generate(prompt_agent1)
    time.sleep(0.01)
    prompt_agent2 = f"You are Agent 2. Read the following math problem and provide ONLY the answer with minimal necessary steps. Approach may differ slightly from Agent 1. Be extremely concise and limit to 3-5 sentences:\n\nProblem: {q}\n\nAgent 2's solution:"
    agent2_output = gpt_generate(prompt_agent2)
    row["past_context"] = f"Agent 1: {agent1_output}\nAgent 2: {agent2_output}"

# Step 3: Assign random agreeableness (1-10)
for row in rows:
    row["agreeableness"] = random.randint(1, 10)

# Write intermediate CSV (with past_context and agreeableness)
with open("gsm8k_with_context.csv", "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["question", "past_context", "agreeableness"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row[k] for k in fieldnames})

# Step 4: Generate expected_response (Agent 1, considering agreeableness)
for row in rows:
    q = row["question"]
    past = row["past_context"]
    agree = row["agreeableness"]
    prompt_response = (
        f"You are Agent 1. Given the math problem and previous agent responses, "
        f"provide a VERY CONCISE solution (maximum 5 sentences) that reflects an agreeableness score of {agree} (1=very stubborn, 10=very agreeable). "
        f"If agreeableness is high, align with agent2; if low, be more like agent1. NO lengthy explanations. Only answer the question directly.\n\n"
        f"Problem: {q}\n\n{past}\n\nAgent 1's response:"
    )
    row["expected_response"] = gpt_generate(prompt_response)
    time.sleep(0.01)

# Step 5: Write final CSV
output_csv = "gsm8k_sft_agreeableness.csv"
with open(output_csv, "w", newline='', encoding="utf-8") as csvfile:
    fieldnames = ["question", "past_context", "agreeableness", "expected_response"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row[k] for k in fieldnames})

print(f"Finished! Output written to {output_csv}")
