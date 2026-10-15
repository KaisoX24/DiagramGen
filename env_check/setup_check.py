import shutil
import subprocess
from pathlib import Path
import sys

CONFIG_DIR=Path.home()/".diagramgen"
MARKER_FILE=CONFIG_DIR/"setup_complete"
IS_WINDOWS=sys.platform=="win32"

def ensure_render_environment() -> None:
    """
    Call once at CLI startup. Verifies Node.js and the Mermaid CLI are
    available.Auto install MMDC if not available .
    Write a marker file so future runs skip all checks.
    """
    if MARKER_FILE.exists(): return

    # NODE JS CHECK
    if not shutil.which("node"):
        print(
            "Node.js is required to render diagrams but wasn't found.\n"
            "Install it from https://nodejs.org, then re-run this command again."
        )
        raise SystemExit(1)

    if not shutil.which("mmdc"):
        ans=input("Mermaid CLI not Found. Install now? [Y/n]: ").strip().lower()
        if ans in ("","yes",'y',"1"): _install_mmdc()
        else:
            print("Skipping install. Diagram rendering won't work until mmdc is installed.\n"
                  "Manually install Mermaid CLI if you dont want auto install")
            raise SystemExit(1)

    _sanity_check()

    CONFIG_DIR.mkdir(exist_ok=True)
    MARKER_FILE.write_text("ok")


def _install_mmdc() -> None:
    "Installs the Mermaid CLI globally via npm"
    print("Installing @mermaid-js/mermaid-cli...")
    result=subprocess.run(["npm","install","-g","@mermaid-js/mermaid-cli"],shell=IS_WINDOWS)
    if result.returncode!=0:
        print("NPM INSTALL FAILED. Try running it manually and re-run this command")
        raise SystemExit(1)

def _sanity_check() -> None:
    "Confirm mmdc actually runs, not just that it exists in PATH"
    result=subprocess.run(["mmdc","--version"],capture_output=True,text=True,shell=IS_WINDOWS)
    if result.returncode!=0:
        print(f"mmdc found but failed to run:\n{result.stderr}")
        raise SystemExit(1)
    