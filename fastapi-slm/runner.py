#!/usr/bin/env python
# Eval harness for task-specialised code models.
#
#   python runner.py list
#   python runner.py selftest                       # reference solutions must pass their own tests
#   python runner.py run --label base --model <name> --base-url <url> --api-key-env <ENV_VAR>
#   python runner.py export-prompts --out prompts.jsonl      # for models you run elsewhere (e.g. Kaggle)
#   python runner.py score --completions completions.jsonl --label finetuned
#   python runner.py report results/base.jsonl results/finetuned.jsonl

import argparse
import json
import os
import sys
from pathlib import Path

from lab.config import SYSTEM_PROMPT
from lab.models import ChatClient
from lab.prompts import build_user_prompt
from lab.scoring import print_summary, read_jsonl, run_items, summarize, write_jsonl
from lab.tasks import load_tasks

ROOT = Path(__file__).parent


def _tasks(args):
    only = [t.strip() for t in args.tasks.split(",")] if args.tasks else None
    tasks = load_tasks(args.tasks_dir, only)
    if not tasks:
        sys.exit(f"no tasks found in {args.tasks_dir}")
    return tasks


def cmd_list(args):
    for t in _tasks(args):
        print(f"{t.id:<28} {t.meta.get('difficulty', '?'):<8} {', '.join(t.meta.get('tags', []))}")


def cmd_selftest(args):
    tasks = _tasks(args)
    items, refs = [], {}
    for t in tasks:
        if t.reference is None:
            print(f"skip {t.id}: no reference.py")
            continue
        refs[t.id] = "```python\n" + t.reference.read_text(encoding="utf-8") + "\n```"
        items.append({"task_id": t.id, "sample": 0})
    recs = run_items(items, {t.id: t for t in tasks}, lambda it: refs[it["task_id"]],
                     args.sandbox, args.workers, "selftest")
    bad = [r for r in recs if not r["passed"]]
    for r in recs:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['task_id']}")
    for r in bad:
        print(f"\n--- {r['task_id']} ({r['reason']}) ---\n{r['output']}")
    sys.exit(1 if bad else 0)


def cmd_run(args):
    tasks = _tasks(args)
    api_key = os.environ.get(args.api_key_env, "") if args.api_key_env else ""
    if args.api_key_env and not api_key:
        sys.exit(f"environment variable {args.api_key_env} is empty")
    client = ChatClient(args.model, args.base_url, api_key,
                        extra_body=json.loads(args.extra_body) if args.extra_body else None)
    items = [{"task_id": t.id, "sample": i} for t in tasks for i in range(args.n)]
    by_id = {t.id: t for t in tasks}

    def gen(item):
        return client.generate(SYSTEM_PROMPT, build_user_prompt(by_id[item["task_id"]].prompt),
                               temperature=args.temperature, max_tokens=args.max_tokens)

    recs = run_items(items, by_id, gen, args.sandbox, args.workers, args.label)
    _finish(args.label, recs, args.out)


def cmd_export(args):
    tasks = _tasks(args)
    rows = [{"task_id": t.id, "sample": i, "system": SYSTEM_PROMPT, "user": build_user_prompt(t.prompt)}
            for t in tasks for i in range(args.n)]
    write_jsonl(args.out, rows)
    print(f"wrote {len(rows)} prompts to {args.out}")


def cmd_score(args):
    tasks = _tasks(args)
    by_id = {t.id: t for t in tasks}
    rows = [r for r in read_jsonl(args.completions) if r["task_id"] in by_id]
    items = [{"task_id": r["task_id"], "sample": r.get("sample", 0)} for r in rows]
    lookup = {(r["task_id"], r.get("sample", 0)): r["completion"] for r in rows}
    recs = run_items(items, by_id, lambda it: lookup[(it["task_id"], it["sample"])],
                     args.sandbox, args.workers, args.label)
    _finish(args.label, recs, args.out)


def _finish(label, recs, out):
    out = out or str(ROOT / "results" / f"{label}.jsonl")
    write_jsonl(out, recs)
    print_summary(label, summarize(recs))
    print(f"\nsaved {len(recs)} records to {out}")


def cmd_report(args):
    sums = {}
    for p in args.files:
        recs = read_jsonl(p)
        sums[recs[0].get("label", Path(p).stem) if recs else Path(p).stem] = summarize(recs)
    labels = list(sums)
    task_ids = sorted({t for s in sums.values() for t in s["per_task"]})
    print(f"{'task':<28}" + "".join(f"{l[:18]:>20}" for l in labels))
    for tid in task_ids:
        row = f"{tid:<28}"
        for l in labels:
            v = sums[l]["per_task"].get(tid)
            row += f"{(str(v['passed']) + '/' + str(v['samples'])) if v else '-':>20}"
        print(row)
    print(f"{'pass@1':<28}" + "".join(f"{sums[l]['pass_at_1']:>20.1%}" for l in labels))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, sandbox=True):
        sp.add_argument("--tasks-dir", default=str(ROOT / "eval" / "tasks"))
        sp.add_argument("--tasks", default="", help="comma-separated task ids or prefixes, e.g. 001,003")
        if sandbox:
            sp.add_argument("--sandbox", default="auto", choices=["auto", "docker", "subprocess"])
            sp.add_argument("--workers", type=int, default=4)

    sp = sub.add_parser("list"); common(sp, False); sp.set_defaults(fn=cmd_list)
    sp = sub.add_parser("selftest"); common(sp); sp.set_defaults(fn=cmd_selftest)

    sp = sub.add_parser("run"); common(sp)
    sp.add_argument("--label", required=True)
    sp.add_argument("--model", required=True)
    sp.add_argument("--base-url", required=True)
    sp.add_argument("--api-key-env", default="")
    sp.add_argument("--extra-body", default="", help='JSON merged into the request, e.g. \'{"chat_template_kwargs": {"enable_thinking": false}}\'')
    sp.add_argument("-n", type=int, default=1, help="samples per task")
    sp.add_argument("--temperature", type=float, default=0.2)
    sp.add_argument("--max-tokens", type=int, default=2048)
    sp.add_argument("--out", default="")
    sp.set_defaults(fn=cmd_run)

    sp = sub.add_parser("export-prompts"); common(sp, False)
    sp.add_argument("--out", default="prompts.jsonl")
    sp.add_argument("-n", type=int, default=1)
    sp.set_defaults(fn=cmd_export)

    sp = sub.add_parser("score"); common(sp)
    sp.add_argument("--completions", required=True)
    sp.add_argument("--label", required=True)
    sp.add_argument("--out", default="")
    sp.set_defaults(fn=cmd_score)

    sp = sub.add_parser("report")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(fn=cmd_report)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
