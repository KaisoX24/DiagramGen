from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage,SystemMessage
from models.data_models import DiagramSpec
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# System Prompts

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SYS_MSG_DIR=PROJECT_ROOT/"sys_msg"

sys_msg=(SYS_MSG_DIR/"sys_msg.txt").read_text(encoding='utf-8')
edit_msg=(SYS_MSG_DIR/"edit_msg.txt").read_text(encoding='utf-8')

# Initalized LLM
llm=init_chat_model(model='google_genai:gemini-3.5-flash',temperature=0.66)
structured_llm=llm.with_structured_output(DiagramSpec)

def generate_diagram_spec(repo_content:str)->DiagramSpec:
    "Takes the Repo Content,directory tree etc and return the validated DiagramSpec"
    try:
        messages=[
            SystemMessage(content=sys_msg),
            HumanMessage(content=repo_content)
        ]
        return structured_llm.invoke(messages)
    except Exception as e:
        print(f"CANT GENERATE WORKFLOW diagragm: {e}")
        return None

def edit_diagram_spec(current_spec:DiagramSpec,edit_request:str) -> DiagramSpec:
    """Edit loop call. Takes the existing spec plus the user's plain-language
    change request, and returns an updated, validated DiagramSpec."""
    try:
        current_spec_json=current_spec.model_dump_json(indent=2)

        user_message=(
            f"Current Diagram Spec:\n{current_spec_json}\n\n"
            f"Requested Change:\n{edit_request}"
        )
        messages=[
            SystemMessage(content=edit_msg),
            HumanMessage(content=user_message)
        ]
        return structured_llm.invoke(messages)
    except Exception as e:
        print(f"CANT Edit WORKFLOW diagragm: {e}")
        return None