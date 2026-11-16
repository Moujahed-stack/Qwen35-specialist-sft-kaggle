import re
from typing import Optional

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE = re.compile(r"```[ \t]*([A-Za-z0-9_+-]*)[ \t]*\r?\n(.*?)(?:```|\Z)", re.DOTALL)
_PY_LANGS = {"", "python", "py", "python3"}


def extract_code(text: Optional[str]) -> Optional[str]:
    # Returns the Python source from a model answer, or None if there is no usable code.
    if not text:
        return None
    text = _THINK.sub("", text)
    if "<think>" in text:            # unterminated reasoning block (truncated output)
        text = text.split("<think>", 1)[0]

    blocks = [body for lang, body in _FENCE.findall(text) if lang.lower() in _PY_LANGS]
    blocks = [b.strip("\n") for b in blocks if b.strip()]
    if blocks:
        with_app = [b for b in blocks if "FastAPI" in b]
        pool = with_app or blocks
        return max(pool, key=len) + "\n"

    stripped = text.strip()
    if stripped and ("import " in stripped or "def " in stripped or "FastAPI" in stripped):
        return stripped + "\n"
    return None
