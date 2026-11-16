# fastapi-slm

Evaluation harness and training pipeline for a small language model specialised in **FastAPI + Pydantic v2 + SQLModel**
backend code. The core idea: a task is only "solved" if generated code passes real tests, so the same harness
measures models, filters training data and tracks progress.

## Layout

```
runner.py                 CLI: list / selftest / run / export-prompts / score / report
lab/                      harness code (prompts, code extraction, sandbox, scoring, API client)
eval/tasks/<id>/          prompt.md, test_task.py (pytest), reference.py, meta.json
scripts/kaggle_generate_cell.py   generate completions on Kaggle for models you can't call by API
tests/                    unit tests for the harness itself
Dockerfile.sandbox        isolated image used to run untrusted generated code
```

## Task contract

The model receives the task prompt plus a fixed output contract (see `lab/config.py`): one Python file `main.py` in a
single code block defining a FastAPI instance named `app`. The runner extracts the code, writes it as `main.py` next
to `test_task.py` in a temp directory, and runs `pytest`. A sample passes only if all tests pass.

**Training data must use the same system prompt and `build_user_prompt()` as evaluation**, so train and eval formats match.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-sandbox.txt
python runner.py selftest --sandbox subprocess            # all reference solutions should PASS
python -m pytest tests -q                                 # harness unit tests
```

### Sandbox (recommended)

Generated code is untrusted. Subprocess mode only applies a timeout and basic limits; it is **not isolated**.
For anything beyond your own quick checks, use Docker mode (no network, memory/CPU/pid limits):

```bash
docker build -f Dockerfile.sandbox -t lab-sandbox .
python runner.py selftest --sandbox docker
```

With `--sandbox auto` (default) the runner uses Docker when the `lab-sandbox` image exists, otherwise subprocess mode.
Docker mode is implemented but was not exercised in development; run `selftest --sandbox docker` once to confirm.

## Commands

```bash
python runner.py list

# Any OpenAI-compatible endpoint (OpenRouter, Together, Fireworks, vLLM, Ollama, ...)
export API_KEY=...
python runner.py run --label ref-model --model <model-name> \
    --base-url https://<provider>/v1 --api-key-env API_KEY -n 1

# Models you run elsewhere (e.g. Kaggle GPU): export prompts, generate there, score here
python runner.py export-prompts --out prompts.jsonl -n 1
#   ... run scripts/kaggle_generate_cell.py on Kaggle, download completions.jsonl ...
python runner.py score --completions completions.jsonl --label qwen35-4b-base

# Compare runs side by side
python runner.py report results/qwen35-4b-base.jsonl results/qwen35-4b-ft.jsonl
```

Useful flags: `--tasks 001,003` to run a subset, `-n 8 --temperature 0.8` for several samples per task,
`--extra-body '{"chat_template_kwargs": {"enable_thinking": false}}'` for servers that support it.
Results are saved to `results/<label>.jsonl` (raw completion, pass/fail, reason, test output tail).

## Workflow

1. **Baselines.** Run the untouched base models (Qwen3.5 4B and 9B) and one strong reference model. The gap is the project.
2. **Verified data.** Generate solutions with a teacher model, keep only those whose tests pass, and build `train.jsonl`
   (`{"prompt", "completion"}`, with `prompt` built by `build_user_prompt`). Check the teacher's license terms first.
3. **Train** with the Kaggle notebook (QLoRA via Unsloth).
4. **Re-evaluate** the adapter with `export-prompts` / Kaggle / `score`, then `report` against the baselines.
5. **Round 2.** Sample from your own model, keep passes, retrain.

## Keeping the eval honest

- Never train on `eval/tasks`. Synthetic training tasks should live in a separate folder and be deduplicated against these prompts.
- `reference.py` files are answer keys. Before publishing this repo, consider moving them out (or keeping the eval tasks in a
  private repo) so future models are not trained on the solutions.
- Six tasks are a smoke test, not a benchmark. Grow to 150-300 tasks before drawing conclusions; with few tasks a single
  flaky sample moves the score a lot, so use `-n` samples and report pass@1 over all of them.

## Known limits

- Tests are black-box HTTP checks against `main.py`; they do not judge code style or efficiency.
- Pinned versions in `requirements-sandbox.txt` are what the reference solutions were verified with. Models trained on older
  FastAPI/Pydantic idioms may fail on purpose: that is part of what this eval measures.
