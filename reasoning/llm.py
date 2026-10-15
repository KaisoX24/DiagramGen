from pathlib import Path
from diagramgen.models.data_models import DiagramSpec
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYS_MSG_DIR = PROJECT_ROOT / "sys_msg"


_structured_llm = None
_sys_msg = None
_edit_msg = None


def _get_structured_llm():
    "Creates the LLM client on first use only, and caches it for reuse"
    global _structured_llm
    if _structured_llm is None:
        llm = init_chat_model(model="google_genai:gemini-3.8-flash",temperature=0.66)
        _structured_llm = llm.with_structured_output(DiagramSpec)
    return _structured_llm


def _get_sys_msg() -> str:
    global _sys_msg
    if _sys_msg is None:
        _sys_msg = (SYS_MSG_DIR / "sys_msg.txt").read_text(encoding="utf-8")
    return _sys_msg


def _get_edit_msg() -> str:
    global _edit_msg
    if _edit_msg is None:
        _edit_msg = (SYS_MSG_DIR / "edit_msg.txt").read_text(encoding="utf-8")
    return _edit_msg


def generate_diagram_spec(repo_content: str) -> DiagramSpec | None:
    "Takes the repo content, directory tree, etc. and returns the validated DiagramSpec"
    try:
        structured_llm = _get_structured_llm()
        messages = [
            SystemMessage(content=_get_sys_msg()),
            HumanMessage(content=repo_content),
        ]
        return structured_llm.invoke(messages)
    except Exception as e:
        print(f"Can't generate workflow diagram: {e}")
        return None


def edit_diagram_spec(current_spec: DiagramSpec, edit_request: str) -> DiagramSpec | None:
    """Edit loop call. Takes the existing spec plus the user's plain-language
    change request, and returns an updated, validated DiagramSpec."""
    try:
        structured_llm = _get_structured_llm()
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
