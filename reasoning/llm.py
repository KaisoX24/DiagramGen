from pathlib import Path
from models.data_models import DiagramSpec
from langchain.messages import HumanMessage, SystemMessage
from reasoning.providers import get_llm
from functools import lru_cache

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYS_MSG_DIR = PROJECT_ROOT / "sys_msg"


@lru_cache
def _get_structured_llm(provider:str,model:str):
    "Creates the LLM client on first use only, and caches it for reuse"
    llm=get_llm(provider,model)
    return llm.with_structured_output(DiagramSpec)
    

@lru_cache
def _get_sys_msg() -> str:
    return (SYS_MSG_DIR / "sys_msg.txt").read_text(encoding="utf-8")

@lru_cache
def _get_edit_msg() -> str:
    return (SYS_MSG_DIR / "edit_msg.txt").read_text(encoding="utf-8")


def generate_diagram_spec(provider:str,model:str,repo_content: str) -> DiagramSpec | None:
    "Takes the repo content, directory tree, etc. and returns the validated DiagramSpec"
    try:
        structured_llm = _get_structured_llm(provider=provider,model=model)
        messages = [
            SystemMessage(content=_get_sys_msg()),
            HumanMessage(content=repo_content),
        ]
        return structured_llm.invoke(messages)
    except Exception as e:
        print(f"Can't generate workflow diagram: {e}")
        return None


def edit_diagram_spec(provider:str,model:str,current_spec: DiagramSpec, edit_request: str) -> DiagramSpec | None:
    """Edit loop call. Takes the existing spec plus the user's plain-language
    change request, and returns an updated, validated DiagramSpec."""
    try:
        structured_llm = _get_structured_llm(provider=provider,model=model)
        current_spec_json = current_spec.model_dump_json(indent=2)
        user_message = (
            f"Current Diagram Spec:\n{current_spec_json}\n\n"
            f"Requested Change:\n{edit_request}"
        )
        messages = [
            SystemMessage(content=_get_edit_msg()),
            HumanMessage(content=user_message),
        ]
        return structured_llm.invoke(messages)
    except Exception as e:
        print(f"Can't edit workflow diagram: {e}")
        return None
