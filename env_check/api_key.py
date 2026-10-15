import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".diagramgen"
CONFIG_FILE = CONFIG_DIR / "config.env"

def ensure_api_key() -> None:
    """
    Call once at CLI startup, before any module that talks to the LLM is
    imported. Checks for an API key in the environment or saved config;
    if neither exists, prompts once and saves it for future runs.
    """
    if os.environ.get("GEMINI_API_KEY"):
        return

    if CONFIG_FILE.exists():
        key = _read_saved_key()
        if key:
            os.environ["GEMINI_API_KEY"] = key
            return

    print("No Gemini API key found.")
    key = input("Paste your GEMINI API key: ").strip()
    if not key:
        print("No key entered. Diagram generation requires an API key to run. Get a valid Gemini API key and rerun the command")
        raise SystemExit(1)

    os.environ["GEMINI_API_KEY"] = key
    _save_key(key)
    print(f"Saved. Future runs won't ask again (stored in {CONFIG_FILE}).")

def _read_saved_key() -> str | None:
    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None

def _save_key(key: str) -> None:
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(f"GEMINI_API_KEY={key}\n", encoding="utf-8")
    try:
        CONFIG_FILE.chmod(0o600)
    except (NotImplementedError, PermissionError):
        pass

def reset_api_key() -> None:
    "Deletes the saved key, e.g. for `diagramgen configure --reset`"
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        print("Saved API key removed.")
    else:
        print("No saved API key to remove.")