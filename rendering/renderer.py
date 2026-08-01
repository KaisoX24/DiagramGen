import subprocess
import sys
from pathlib import Path

IS_WINDOWS=sys.platform=="win32"
THEME="neutral"

def _run_mmdc(mmd_path:Path,output_path:Path) ->None:
    "Runs the Mermaid CLI for creating diagram to output path"
    command=[
        "mmdc",
        "-i", str(mmd_path),
        "-o", str(output_path),
        "--theme",THEME
    ]
    result=subprocess.run(command,capture_output=True,text=True,shell=IS_WINDOWS)
    if result.returncode!=0:
        raise RuntimeError(f"mmdc failed to render diagram:\n{result.stderr}")

def render_diagram(mermaid_text:str,output_path:Path) ->dict:
    "Writes the .mmd file next to output path ,with the image"
    output_path=Path(output_path)
    output_path.parent.mkdir(parents=True,exist_ok=True)
    mmd_path=output_path.with_suffix(".mmd")

    mmd_path.write_text(mermaid_text,encoding='utf-8')
    _run_mmdc(mmd_path,output_path)

    return {"mmd_path":mmd_path,"img_path":output_path}