import ast
import json
from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from .extract import extract_code
from .sandbox import run_tests
from .tasks import Task


def score_one(task: Task, completion: str, sandbox_mode: str) -> dict:
    code = extract_code(completion)
    if code is None:
        return {"passed": False, "reason": "no_code", "seconds": 0.0, "output": ""}
    try:
        ast.parse(code)
    except SyntaxError as e:
        return {"passed": False, "reason": "syntax_error", "seconds": 0.0, "output": str(e)}
    r = run_tests(code, task.test_file, timeout=task.timeout, mode=sandbox_mode)
    return {"passed": r.passed, "reason": r.reason, "seconds": round(r.seconds, 2), "output": r.output[-1500:]}


def run_items(items: List[dict], tasks: Dict[str, Task], get_completion: Callable[[dict], str],
              sandbox_mode: str, workers: int, label: str) -> List[dict]:
    # items: [{"task_id", "sample"}, ...]; get_completion(item) returns the raw model text.
    def work(item):
        task = tasks[item["task_id"]]
        try:
            completion = get_completion(item)
        except Exception as e:           # generation failure counts as a failed sample, not a crash
            return {**item, "label": label, "completion": "", "passed": False,
                    "reason": "generation_error", "seconds": 0.0, "output": repr(e)[:500]}
        res = score_one(task, completion, sandbox_mode)
        return {**item, "label": label, "completion": completion, **res}

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        return list(ex.map(work, items))


def write_jsonl(path, records: Iterable[dict]):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def read_jsonl(path) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def summarize(records: List[dict]) -> dict:
    by_task = defaultdict(list)
    for r in records:
        by_task[r["task_id"]].append(r)
    per_task = OrderedDict()
    for tid in sorted(by_task):
        rs = by_task[tid]
        reasons = defaultdict(int)
        for r in rs:
            if not r["passed"]:
                reasons[r["reason"]] += 1
        per_task[tid] = {"passed": sum(r["passed"] for r in rs), "samples": len(rs), "fail_reasons": dict(reasons)}
    n_samples = sum(v["samples"] for v in per_task.values())
    n_pass = sum(v["passed"] for v in per_task.values())
    return {
        "tasks": len(per_task),
        "samples": n_samples,
        "pass_at_1": (n_pass / n_samples) if n_samples else 0.0,
        "any_pass_rate": (sum(1 for v in per_task.values() if v["passed"] > 0) / len(per_task)) if per_task else 0.0,
        "per_task": per_task,
    }


def print_summary(label: str, s: dict):
    print(f"\n== {label} ==")
    for tid, v in s["per_task"].items():
        extra = f"  fails: {v['fail_reasons']}" if v["fail_reasons"] else ""
        print(f"  {tid:<28} {v['passed']}/{v['samples']}{extra}")
    print(f"  pass@1 (mean over samples): {s['pass_at_1']:.1%}   ({s['tasks']} tasks, {s['samples']} samples)")
    if s["samples"] > s["tasks"]:
        print(f"  any-sample pass rate:       {s['any_pass_rate']:.1%}")
