import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .config import DEFAULT_TIMEOUT_S


@dataclass
class Task:
    id: str
    path: Path
    prompt: str
    test_file: Path
    reference: Optional[Path]
    meta: dict = field(default_factory=dict)

    @property
    def timeout(self) -> int:
        return int(self.meta.get("timeout", DEFAULT_TIMEOUT_S))


def load_tasks(root, only: Optional[List[str]] = None) -> List[Task]:
    root = Path(root)
    tasks = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        prompt_f, test_f = d / "prompt.md", d / "test_task.py"
        if not (prompt_f.exists() and test_f.exists()):
            continue
        if only and not any(d.name == o or d.name.startswith(o) for o in only):
            continue
        meta_f = d / "meta.json"
        meta = json.loads(meta_f.read_text(encoding="utf-8")) if meta_f.exists() else {}
        ref = d / "reference.py"
        tasks.append(Task(
            id=d.name,
            path=d,
            prompt=prompt_f.read_text(encoding="utf-8").strip(),
            test_file=test_f,
            reference=ref if ref.exists() else None,
            meta=meta,
        ))
    return tasks
