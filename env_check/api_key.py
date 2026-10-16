import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".diagramgen"
CONFIG_FILE = CONFIG_DIR / "config.env"


PROVIDER_ENV_KEYS:dict = {
    "google_genai": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

def get_env_key(provider:str)->str|None:
    "Return an API key already available in the environment."
    env_name=PROVIDER_ENV_KEYS.get(provider)
    if env_name is None: return None
    return os.environ.get(env_name)

def get_saved_key(provider:str) ->str|None:
    "Return a provider API key saved in DiagramGen's config."
    env_name=PROVIDER_ENV_KEYS.get(provider)
    if env_name is None or not CONFIG_FILE.exists(): return None

    for line in CONFIG_FILE.read_text(encoding='utf-8').splitlines():
        if line.startswith(f'{env_name}='):
            return line.split("=",1)[-1].strip()

    return None


def get_api_key(provider: str) -> str | None:
    "Return the API key for a provider from environment or saved config."
    key = get_env_key(provider)

    if key:
        return key

    return get_saved_key(provider)


def save_api_key(provider: str, key: str) -> None:
    "Save or update an API key for a provider."

    env_name = PROVIDER_ENV_KEYS.get(provider)

    if env_name is None:
        raise ValueError(f"Unsupported provider: {provider}")

    CONFIG_DIR.mkdir(exist_ok=True)

    lines = []

    if CONFIG_FILE.exists():
        lines = CONFIG_FILE.read_text(encoding="utf-8").splitlines()

    updated = False

    for i, line in enumerate(lines):
        if line.startswith(f"{env_name}="):
            lines[i] = f"{env_name}={key}"
            updated = True
            break

    if not updated:
        lines.append(f"{env_name}={key}")

    CONFIG_FILE.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    try:
        CONFIG_FILE.chmod(0o600)
    except (NotImplementedError, PermissionError):
        pass

def remove_api_key(provider:str) ->None:
    "Remove a saved API key for a provider."

    env_name = PROVIDER_ENV_KEYS.get(provider)

    if env_name is None:
        raise ValueError(f"Unsupported provider: {provider}")

    if not CONFIG_FILE.exists():
        return
    
    lines = CONFIG_FILE.read_text(encoding="utf-8").splitlines()

    lines=[line for line in lines if not line.startswith(f'{env_name}=')]

    CONFIG_FILE.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

def ensure_api_key(provider:str) -> None:
    """
    Ensure the selected provider has an API key available.
    Providers such as Ollama do not require an API key.
    """
    if provider=='ollama':
        return
    env_name=PROVIDER_ENV_KEYS.get(provider)
    if env_name is None: raise ValueError(f"Unsupported provider: {provider}")
    key=get_api_key(provider)
    if key:
        os.environ[env_name]=key
        return
    print(f"No API key found for {provider}.")
    key = input(f"Paste your {env_name}: ").strip()
    if not key:
        print(f"No key entered. {provider} requires an API key to run.")
        raise SystemExit(1)

    os.environ[env_name]=key
    save_api_key(provider,key)

    print(
        f"Saved. Future runs won't ask again "
        f"(stored in {CONFIG_FILE})."
    )

def reset_api_key(provider: str) -> None:
    "Remove the saved API key for a provider."

    remove_api_key(provider)

    print(f"Saved {provider} API key removed.")