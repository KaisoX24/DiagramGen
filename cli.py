import typer
from pathlib import Path

from setup_check import ensure_render_environment
from ingestion.parser import ingest_repo
from ingestion.source import resolve_repo_source
from reasoning.llm import generate_diagram_spec,edit_diagram_spec,DiagramSpec
from rendering.compiler import compile_diagram_spec
from rendering.renderer import render_diagram

app=typer.Typer(help="Generate and edit Github project architecture workflow diagrams.")

@app.command()
def generate(
    source:str=typer.Argument(...,help="Github Repo url or local repo paht"),
    out:Path=typer.Option(Path("diagram.svg"),"--out","-o",help="Output Image Path")):

    "Analyze a repo and generate an architecture diagram."
    try:
        ensure_render_environment()
        repo_path=resolve_repo_source(source)
        repo_content=ingest_repo(repo_path)
        spec=generate_diagram_spec(repo_content)
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
    out: Path = typer.Option(None, "--out", "-o", help="Output path (defaults to overwriting original)"),
):
    "Apply an edit to an existing diagram."
    try:
        ensure_render_environment()
 
        if not spec_path.exists():
            typer.echo(f"Spec file not found: {spec_path}")
            raise typer.Exit(1)
 
        current_spec = DiagramSpec.model_validate_json(spec_path.read_text(encoding="utf-8"))
        updated_spec = edit_diagram_spec(current_spec, request)
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

if __name__=="__main__":
    app()