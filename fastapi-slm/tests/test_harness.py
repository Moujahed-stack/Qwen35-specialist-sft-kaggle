import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lab.extract import extract_code
from lab.scoring import score_one, summarize
from lab.tasks import load_tasks

TASKS = {t.id: t for t in load_tasks(Path(__file__).resolve().parents[1] / "eval" / "tasks")}


def test_extract_fenced_python():
    assert extract_code("text\n```python\nimport x\n```\nbye") == "import x\n"


def test_extract_unterminated_fence():
    assert "FastAPI" in extract_code("```python\nfrom fastapi import FastAPI\napp = FastAPI()\n")


def test_extract_prefers_block_with_fastapi_and_skips_other_languages():
    text = "```bash\npip install fastapi\n```\n```python\nprint('x')\n```\n```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```"
    assert "FastAPI()" in extract_code(text)


def test_extract_strips_think_block():
    text = "<think>```python\nbad = 1\n```</think>\n```python\nfrom fastapi import FastAPI\n```"
    assert "bad" not in extract_code(text)


def test_extract_raw_code_and_none():
    assert extract_code("import os\nx = 1") is not None
    assert extract_code("I cannot help with that.") is None
    assert extract_code("") is None
    assert extract_code("<think>still thinking") is None


def test_wrong_solution_fails():
    r = score_one(TASKS["001_health"], "```python\nfrom fastapi import FastAPI\napp = FastAPI()\n```", "subprocess")
    assert not r["passed"] and r["reason"] == "tests_failed"


def test_syntax_error_and_no_code():
    assert score_one(TASKS["001_health"], "```python\ndef (:\n```", "subprocess")["reason"] == "syntax_error"
    assert score_one(TASKS["001_health"], "no code here", "subprocess")["reason"] == "no_code"


def test_missing_app_is_an_error():
    r = score_one(TASKS["001_health"], "```python\nx = 1\n```", "subprocess")
    assert not r["passed"] and r["reason"] == "error"


def test_timeout():
    t = TASKS["001_health"]
    t.meta["timeout"] = 3
    try:
        r = score_one(t, "```python\nwhile True:\n    pass\n```", "subprocess")
    finally:
        t.meta["timeout"] = 30
    assert r["reason"] in ("timeout", "error") and not r["passed"]


def test_both_formats_of_correct_answer_pass():
    ref = TASKS["001_health"].reference.read_text()
    assert score_one(TASKS["001_health"], "```python\n" + ref + "\n```", "subprocess")["passed"]
    assert score_one(TASKS["001_health"], ref, "subprocess")["passed"]


def test_sqlmodel_task_rejects_table_model_without_validation():
    # Classic mistake: using the table model for the request body skips validation, so empty title is accepted.
    code = '''
from typing import Optional
from fastapi import FastAPI, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select

engine = create_engine("sqlite:///todos.db")

class Todo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    done: bool = False

SQLModel.metadata.create_all(engine)
app = FastAPI()

@app.post("/todos", status_code=201)
def create(todo: Todo):
    with Session(engine) as s:
        s.add(todo); s.commit(); s.refresh(todo)
        return todo

@app.get("/todos")
def lst(done: Optional[bool] = None):
    with Session(engine) as s:
        q = select(Todo)
        if done is not None:
            q = q.where(Todo.done == done)
        return s.exec(q).all()

@app.get("/todos/{i}")
def get(i: int):
    with Session(engine) as s:
        t = s.get(Todo, i)
        if not t:
            raise HTTPException(404)
        return t
'''
    r = score_one(TASKS["005_sqlmodel_todos"], "```python\n" + code + "\n```", "subprocess")
    assert not r["passed"]


def test_summarize():
    recs = [
        {"task_id": "a", "sample": 0, "passed": True, "reason": "passed"},
        {"task_id": "a", "sample": 1, "passed": False, "reason": "tests_failed"},
        {"task_id": "b", "sample": 0, "passed": False, "reason": "no_code"},
    ]
    s = summarize(recs)
    assert s["samples"] == 3 and abs(s["pass_at_1"] - 1 / 3) < 1e-9 and s["any_pass_rate"] == 0.5
