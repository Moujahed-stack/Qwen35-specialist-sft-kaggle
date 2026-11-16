# Shared prompt constants. Training data must be built with the SAME system prompt and
# build_user_prompt() as evaluation, otherwise train/eval formats drift apart.

SYSTEM_PROMPT = (
    "You are an expert FastAPI backend engineer. Use FastAPI, Pydantic v2 and SQLModel. "
    "Return complete, runnable code."
)

OUTPUT_CONTRACT = (
    "Return the complete solution as a single Python file named main.py, in one ```python code block. "
    "The file must define a FastAPI instance called `app`."
)

DEFAULT_TIMEOUT_S = 30
