import re
import ast
from pathlib import Path


IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", "dist",
    "build", ".next", "env", ".egg-info", ".mypy_cache", ".pytest_cache",
}

IGNORE_EXT_PATTERNS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip",
    ".lock", ".pyc", ".woff", ".ttf", ".mp4", ".mp3", ".exe", ".bin",
)

ENTRY_POINT_NAMES = [
    "main.py", "app.py", "__main__.py", "cli.py",
    "index.js", "index.ts", "server.js", "app.js", "main.js",
]

MAX_FILE_CHARS=4000
MAX_TOTAL_CHARS=40000

def build_directory_tree(root:Path,max_depth:int=4) -> str:
    "Renders a Filtered directory tree as text"
    lines=[root.name + "/"]

    def walk(dir_path:Path,prefix:str,depth:int):
        if depth>max_depth:
            return
        entries=sorted(
            [p for p in dir_path.iterdir() if p.name not in IGNORE_DIRS and not p.name.startswith(".")],
            key=lambda p:(p.is_file(),p.name.lower())
        )
        for i,entry in enumerate(entries):
            is_last=True if i==len(entries)-1 else False
            connector = "└── " if is_last else "├── "
            lines.append(prefix+connector+entry.name+("/" if entry.is_dir() else ""))
            if entry.is_dir():
                extension="    " if is_last else"│   "
                walk(entry,prefix+extension,depth+1)

    walk(root,"",1)
    return "\n".join(lines)

def find_readme(root:Path) -> Path |None:
    "Find a README file at the repo root"
    for entry in root.iterdir():
        if entry.is_file() and entry.stem.lower()=='readme': return entry
    return None

def find_entry_points(root:Path) ->list[Path]:
    "Search the root and subdirectories for known entry-point filenames"
    found=[]
    search_dirs=[root]+[p for p in root.iterdir() if p.is_dir() and p.name not in IGNORE_DIRS]
    for dir in search_dirs:
        for name in ENTRY_POINT_NAMES:
            file=dir/name
            if file.is_file():
                found.append(file)
    return found

def read_file_safe(path: Path, max_chars: int = MAX_FILE_CHARS) -> str:
    "Reads a text file, truncating with a note if it exceeds max_chars"
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    if len(content) > max_chars:
        return content[:max_chars] + f"\n... [truncated, {len(content) - max_chars} more chars]"
    return content

def extract_python_imports(file_path:Path,root:Path) ->list[Path]:
    try:
        tree=ast.parse(file_path.read_text(encoding='utf-8',errors='ignore'))
    except SyntaxError:
        return []

    module_names=[]
    from_import_submodules=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            module_names.extend(alias.name for alias in node.names)
        elif isinstance(node,ast.ImportFrom) and node.module:
            module_names.append(node.module)
            from_import_submodules.append(
                (node.module,[alias.name for alias in node.names])
            )

    def resolve(module_name:str) -> Path | None:
        parts=module_name.split('.')
        file=root.joinpath(*parts).with_suffix(".py")
        file_pkg=root.joinpath(*parts,"__init__.py")

        if file.is_file(): return file
        if file_pkg.is_file(): return file_pkg
        return None

    resolved=[]
    for module_name in module_names:
        hit=resolve(module_name)
        if hit:
            resolved.append(hit)

    for module_name, names in from_import_submodules:
        for name in names:
            hit = resolve(f"{module_name}.{name}")
            if hit:
                resolved.append(hit)

    seen=set()
    deduped=[]
    for path in resolved:
        if path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped

def extract_js_imports(file_path: Path, root: Path) -> list[Path]:
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r"""(?:require\(|from\s+)['"](\.[^'"]+)['"]""")
    resolved = []
    for rel_import in pattern.findall(text):
        base = (file_path.parent / rel_import).resolve()
        for candidate in (base, base.with_suffix(".js"), base.with_suffix(".ts"), base / "index.js"):
            if candidate.is_file():
                resolved.append(candidate)
                break
    return resolved


def extract_local_imports(file_path:Path,root:Path) -> list[Path]:
    "Finds files within the rep that the given file imports"
    if file_path.suffix=='.py':
        return extract_python_imports(file_path,root)
    if file_path.suffix in(".js", ".ts", ".jsx", ".tsx"):
        return extract_js_imports(file_path,root)
    return []

def ingest_repo(root:Path) ->str:
    "Combines README,directory tree,entry points and their local import into one string"
    sections=[]
    sections.append("## Directory tree\n" + build_directory_tree(root))

    readme_path=find_readme(root)
    if readme_path:
        sections.append(f"## README ({readme_path.name})\n"+ read_file_safe(readme_path))

    entry_points=find_entry_points(root)
    referenced=[]
    for entry in entry_points:
        referenced.extend(extract_local_imports(entry,root))

    referenced=[p for p in referenced if p not in entry_points]

    for ep in entry_points:
        sections.append(f"## Entry point ({ep.relative_to(root)})\n" + read_file_safe(ep))
 
    for ref in referenced:
        sections.append(f"## Referenced file ({ref.relative_to(root)})\n" + read_file_safe(ref))

    content="\n\n".join(sections)
    if len(content)>MAX_TOTAL_CHARS:
        content=content[:MAX_TOTAL_CHARS]+"\n... [content truncated to fit budget]"
    return content