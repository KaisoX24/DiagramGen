import re
from models.data_models import DiagramSpec,Node
from pathlib import Path

SHAPE_DELIMITERS = {
    "rect": ("[", "]"),
    "cylinder": ("[(", ")]"),
    "diamond": ("{", "}"),
    "stadium": ("([", "])"),
}

def clean_label(label:str) -> str:
    "Strip characters that would break Mermaid Parser inside a node label"
    return(
        label.replace('"', "'")
        .replace("[", "(")
        .replace("]", ")")
        .replace("{", "(")
        .replace("}", ")")
    )

def clean_id(name:str) -> str:
    "Turn any string into safe Mermaid Identifier"
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe or "sg"

def compile_diagram_spec(spec:DiagramSpec) ->str:
    "Compiles a validated DiagramSPec into Meramid FLowchar syntax"
    lines = [f"flowchart {spec.direction}"]
 
    # group nodes by subgraph, keep top-level nodes separate
    grouped = {name: [] for name in spec.subgraphs}
    top_level = []
    for node in spec.nodes:
        if node.subgraph and node.subgraph in grouped:
            grouped[node.subgraph].append(node)
        else:
            top_level.append(node)
 
    def node_line(node: Node) -> str:
        open_d, close_d = SHAPE_DELIMITERS[node.shape]
        label = clean_label(node.label)
        return f'{node.id}{open_d}"{label}"{close_d}'
 
    for node in top_level:
        lines.append(node_line(node))
 
    for subgraph_name, nodes in grouped.items():
        if not nodes:
            continue
        lines.append(f'subgraph {clean_id(subgraph_name)} ["{subgraph_name}"]')
        for node in nodes:
            lines.append(" " + node_line(node).strip())
        lines.append("end")
 
    for edge in spec.edges:
        if edge.label:
            label = clean_label(edge.label)
            lines.append(f'{edge.source} -->|"{label}"| {edge.target}')
        else:
            lines.append(f"{edge.source} --> {edge.target}")
 
    return "\n".join(lines)