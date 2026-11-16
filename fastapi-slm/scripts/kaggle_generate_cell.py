# Paste this into a Kaggle notebook cell, AFTER `model`, `tok`, `Loader` and `CFG` exist
# (i.e. after the training notebook's model-loading cell, with or without training).
#
#   Baseline of the untouched model: run the load cell, skip LoRA/training, run this cell.
#   Fine-tuned model in a fresh session: load the adapter instead of the base model:
#       model, tokenizer = FastLanguageModel.from_pretrained(
#           model_name="<your-hf-user>/<adapter-repo>", max_seq_length=2048, load_in_4bit=True)
#       tok = getattr(tokenizer, "tokenizer", tokenizer)
#
# Workflow:
#   1. locally:   python runner.py export-prompts --out prompts.jsonl -n 1
#   2. upload prompts.jsonl to Kaggle as a dataset and attach it to the notebook
#   3. run this cell, download /kaggle/working/completions.jsonl
#   4. locally:   python runner.py score --completions completions.jsonl --label <name>

import json
import torch

PROMPTS = "/kaggle/input/lab-prompts/prompts.jsonl"     # <-- your dataset path
OUT = "/kaggle/working/completions.jsonl"
TEMPERATURE = 0.2          # 0 = greedy
MAX_NEW_TOKENS = 1024

Loader.for_inference(model)

with open(PROMPTS, encoding="utf-8") as f:
    items = [json.loads(line) for line in f if line.strip()]

with open(OUT, "w", encoding="utf-8") as fo:
    for it in items:
        msgs = [{"role": "system", "content": it["system"]},
                {"role": "user", "content": it["user"]}]
        try:
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                           enable_thinking=False)
        except TypeError:
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = tok(text, return_tensors="pt", add_special_tokens=False).to("cuda")
        gen_kwargs = dict(max_new_tokens=MAX_NEW_TOKENS)
        if TEMPERATURE > 0:
            gen_kwargs.update(do_sample=True, temperature=TEMPERATURE, top_p=0.9)
        else:
            gen_kwargs.update(do_sample=False)
        with torch.no_grad():
            out = model.generate(**inputs, **gen_kwargs)
        completion = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        fo.write(json.dumps({"task_id": it["task_id"], "sample": it["sample"],
                             "completion": completion}, ensure_ascii=False) + "\n")
        fo.flush()
        print(it["task_id"], it["sample"], "done")

print("wrote", OUT)
