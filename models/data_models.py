from pydantic import BaseModel
from typing import Literal,List

class Node(BaseModel):
    id:str
    label:str
    shape:Literal['rect','cylinder','diamond','stadium']
    subgraph:str|None = None

class Edge(BaseModel):
    source:str
    target:str
    label:str|None = None

# Response Structure
class DiagramSpec(BaseModel):
    nodes:List[Node]
    edges:List[Edge]
    subgraphs:List[str]
    direction:Literal['TD','LR']='TD'