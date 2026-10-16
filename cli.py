import typer
from pathlib import Path
from env_check.setup_check import ensure_render_environment
from env_check.api_key import reset_api_key,ensure_api_key,save_api_key
from ingestion.parser import ingest_repo
from ingestion.source import resolve_repo_source
from models.data_models import DiagramSpec
from reasoning.llm import generate_diagram_spec,edit_diagram_spec
from rendering.compiler import compile_diagram_spec
from rendering.renderer import render_diagram
from interactive.interactive import UserOptChoice
from typing import Optional

app=typer.Typer(help="Generate and edit Github project architecture workflow diagrams.")

@app.command()
def generate(
    source:str=typer.Argument(...,help="Github Repo url or local repo path"),
    provider:Optional[str]=typer.Option(
        None,'--provider','-p',
        help="openai/google_genai/anthropic/ollama. Uses the selected model Provider for the llm"
    ),
    model:Optional[str]=typer.Option(
            None,'--model','-m',
            help="gpt-5.6-luna/gemini-4-argon/claude-sonnet-5-5/gemma4. Uses the selected model from the Provider"
    ),
    out:Path=typer.Option(Path("diagram.svg"),"--out","-o",help="Output Image Path")):

    "Analyze a repo and generate an architecture diagram."
    try:
        ensure_render_environment()
        if provider is None:
            provider=UserOptChoice._select_provider()
        if model is None:
            model=UserOptChoice._select_model(provider)   
        ensure_api_key(provider=provider)
        repo_path=resolve_repo_source(source)
        repo_content=ingest_repo(repo_path)
        spec=generate_diagram_spec(provider=provider,model=model,repo_content=repo_content)
        if spec is None:
            typer.secho("Falied to generate Diagram Spec", fg=typer.colors.BRIGHT_RED,bold=True)
            raise typer.Exit(1)

        meramid_text=compile_diagram_spec(spec)
        result=render_diagram(meramid_text,out)

        spec_path=out.with_suffix(".spec.json")
        spec_path.write_text(spec.model_dump_json(indent=2),encoding='utf-8')

        typer.secho(f"Diagram: {result['img_path']}",fg=typer.colors.BRIGHT_GREEN,bold=True)
        typer.secho(f"Mermaid Source: {result['mmd_path']}",fg=typer.colors.BRIGHT_CYAN,bold=True)
        typer.secho(f"Spec: {spec_path}",fg=typer.colors.BRIGHT_YELLOW,bold=True)

    except (ValueError,RuntimeError) as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.BRIGHT_RED,bold=True)
        raise typer.Exit(1)

@app.command()
def edit(
    spec_path: Path = typer.Argument(..., help="Path to the .spec.json from a previous generate"),
    request: str = typer.Argument(..., help="Plain-language description of the change"),
    provider:Optional[str]=typer.Option(
        None,'--provider','-p',
        help="openai/google_genai/anthropic/ollama. Uses the selected model Provider for the llm"
    ),
    model:Optional[str]=typer.Option(
        None,'--model','-m',
        help="gpt-5.6-luna/gemini-4-argon/claude-sonnet-5-5/gemma4. Uses the selected model from the Provider"
    ),
    out: Path = typer.Option(None, "--out", "-o", help="Output path (defaults to overwriting original)")):

    "Apply an edit to an existing diagram."
    try:
        ensure_render_environment()

        if provider is None:
            provider=UserOptChoice._select_provider()
        if model is None:
            model=UserOptChoice._select_model(provider)
        if provider!='ollama':    
            ensure_api_key(provider=provider)

        if not spec_path.exists():
            typer.echo(f"Spec file not found: {spec_path}")
            raise typer.Exit(1)
 
        current_spec = DiagramSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))
        updated_spec = edit_diagram_spec(provider=provider,model=model,current_spec=current_spec, edit_request=request)
        if updated_spec is None:
            typer.echo("Failed to apply edit.")
            raise typer.Exit(1)
 
        mermaid_text = compile_diagram_spec(updated_spec)
 
        target = out or spec_path.with_suffix("").with_suffix(".svg")
        result = render_diagram(mermaid_text, target)
        spec_path.write_text(updated_spec.model_dump_json(indent=2), encoding="utf-8")
 
        typer.echo(f"Updated diagram: {result['img_path']}")
        typer.echo(f"Updated spec: {spec_path}")
 
    except (ValueError, RuntimeError) as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

@app.command()
def configure(
    reset: bool = typer.Option(False, "--reset", help="Remove the saved API key"),
):
    "View or update the saved OpenAI API key."
    if reset:
        reset_api_key()
        return
    provider=UserOptChoice._select_provider()
    if provider=='ollama':
        typer.secho("Ollama Doesnt Require API Key. Nothing changed.", fg=typer.colors.BRIGHT_BLUE)
        return

    key = input(f"Paste your {provider} API key: ").strip()
    if not key:
        typer.secho("No key entered. Nothing changed.", fg=typer.colors.BRIGHT_RED)
        raise typer.Exit(1)

    save_api_key(provider,key)


if __name__=="__main__":
    app()