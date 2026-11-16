from .config import OUTPUT_CONTRACT


def build_user_prompt(task_prompt: str) -> str:
    return f"{task_prompt.strip()}\n\n{OUTPUT_CONTRACT}"
