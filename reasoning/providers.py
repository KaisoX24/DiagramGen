from dotenv import load_dotenv
from functools import lru_cache
load_dotenv()

@lru_cache
def get_llm(provider:str,model:str):
    if provider=='ollama':
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model,temperature=0.66)
    else:
        from langchain.chat_models import init_chat_model
        return init_chat_model(model=f'{provider}:{model}',temperature=0.66)

