# DiagramGen

**Automated architecture diagram generation for software repositories.**

DiagramGen analyzes a codebase — local or remote — and produces a structured, editable workflow diagram describing how the system actually operates: its components, execution boundaries, and control flow. It is designed to close a common gap in open-source documentation, where a project's README describes *what* a system does but rarely *how* its parts interact at runtime.

---

## Motivation

Well-documented repositories often include an architecture diagram: a visual account of initialization, request handling, background processing, and data persistence. These diagrams communicate system design far more efficiently than prose, but producing one is manual, time-consuming, and typically skipped by individual developers and small teams.

DiagramGen automates this process. Given a repository, it infers the system's architecture using a language model, encodes that understanding as a structured, machine-readable specification, and deterministically compiles it into a diagram. The result is intended to be accurate, visually consistent, and iteratively editable — not a one-shot illustration.

---

## Design Overview

A central design decision shapes this project: **diagram generation is treated as a text-to-structure problem, not a text-to-image problem.**

An earlier version of this project considered using an image generation model to render diagrams directly from a natural-language description. This approach was rejected for two reasons:

1. **Reliability.** Diffusion-based image models are not consistently accurate at rendering precise text, maintaining node-to-arrow correspondence, or preserving layout structure — all of which are non-negotiable for a technical diagram to be usable.
2. **Editability.** Iterative editing of a rendered image (regenerating from a modified prompt) tends to alter the entire composition, rather than applying a targeted change. This makes an "edit this diagram" workflow impractical.

Instead, DiagramGen separates *reasoning* from *rendering*:

- A language model analyzes the repository and produces a **structured diagram specification** (nodes, edges, groupings), validated against a fixed schema.
- A deterministic, non-AI compiler transforms that specification into Mermaid flowchart syntax.
- The Mermaid CLI renders the final image.

This separation means the language model is never responsible for producing syntactically correct diagram code — a task at which models are prone to subtle errors (mismatched brackets, invalid identifiers, inconsistent references). It is only responsible for the analytical step it is well suited to: understanding what a system does.

Edits are applied to the structured specification, not to the rendered image or the raw diagram text, keeping changes minimal, predictable, and independent of how the diagram happens to be laid out visually.

The reasoning layer is provider-agnostic. DiagramGen can use different language model providers and allows the user to select the provider and model at runtime. Local models can also be used through Ollama, allowing diagram generation without an external API.

---

## Architecture

```text
Repository (URL or local path)
        │
        ▼
  ┌─────────────────┐
  │    Ingestion     │   README, directory tree, entry points,
  │                  │   and their local imports
  └────────┬─────────┘
           ▼
  ┌─────────────────┐
  │ Provider / Model │   User-selected language model provider
  │    Selection     │   and model
  └────────┬─────────┘
           ▼
  ┌─────────────────┐
  │   Reasoning LLM  │   Infers architecture and control flow,
  │                  │   returns a validated DiagramSpec
  └────────┬─────────┘
           ▼
  ┌─────────────────┐
  │     Compiler     │   Deterministically converts DiagramSpec
  │  (non-AI, rules) │   into Mermaid flowchart syntax
  └────────┬─────────┘
           ▼
  ┌─────────────────┐
  │     Renderer     │   Mermaid CLI produces the final SVG/PNG
  └────────┬─────────┘
           ▼
    Diagram + editable specification
           │
           ▼ (on edit request)
  ┌─────────────────┐
  │    Edit Loop     │   LLM modifies the existing DiagramSpec
  │                  │   in place; recompiled and re-rendered
  └─────────────────┘
```

### Pipeline stages

| Stage | Responsibility | AI involved |
|---|---|---|
| Ingestion | Resolve repo source, extract README, directory structure, entry points, and their local dependencies | No |
| Provider / Model Selection | Select the language model provider and model used for reasoning | No |
| Reasoning | Infer system architecture and produce a structured specification | Yes |
| Compilation | Convert the specification into valid Mermaid syntax | No |
| Rendering | Convert Mermaid syntax into a final image via the Mermaid CLI | No |
| Editing | Apply a natural-language change request to the existing specification | Yes |

---

## Repository Ingestion

Ingestion accepts either a public GitHub URL or a local directory. GitHub repositories are retrieved directly as a zip archive via the GitHub REST and codeload APIs, without requiring a local Git installation.

For each entry point identified (e.g. `main.py`, `app.py`, `index.js`), the ingestion layer resolves the local files it imports — one level deep — and includes their content alongside the README and a filtered directory tree. This keeps the context provided to the reasoning model focused and bounded, rather than including an entire codebase.

Python import resolution is implemented via `ast` parsing (not regular expressions) to reliably identify both `import x.y` and `from x import y` forms, including submodule imports. JavaScript and TypeScript imports are resolved via relative-path matching.

---

## Diagram Specification Schema

The structured output produced by the reasoning stage is validated against a fixed schema:

```python
class Node(BaseModel):
    id: str
    label: str
    shape: Literal["rect", "cylinder", "diamond", "stadium"]
    subgraph: str | None = None

class Edge(BaseModel):
    source: str
    target: str
    label: str | None = None

class DiagramSpec(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    subgraphs: list[str]
    direction: Literal["TD", "LR"] = "TD"
```

Node shape carries semantic meaning rather than being decorative: rectangles represent processing steps, cylinders represent persistent storage, diamonds represent decision points, and stadium shapes mark start and end points. Subgraphs represent distinct execution contexts (e.g. main thread, background worker, external service).

---

## Language Model Providers

DiagramGen supports multiple language model providers rather than being tied to a single model.

The provider and model can be selected interactively when generating or editing a diagram, or supplied directly through CLI options.

Currently supported providers include:

- **OpenAI**
- **Google Gemini**
- **Anthropic**
- **Ollama**

Ollama provides support for local models, allowing DiagramGen to operate without an external API key.

The reasoning layer uses a common chat model interface, while provider-specific initialization is handled separately. This allows the rest of the diagram generation pipeline to remain independent of the selected provider.

---

## API Key Configuration

API keys are stored per provider in DiagramGen's configuration rather than being tied to a single model.

Provider credentials can be configured through:

```bash
python cli.py configure
```

Configuration is stored in DiagramGen's user configuration directory and can contain keys for multiple providers.

Ollama does not require an API key.

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js (required by the Mermaid CLI renderer)
- An API key for the configured language model provider, unless using Ollama

DiagramGen checks for Node.js and the Mermaid CLI (`mmdc`) automatically on first run, and will offer to install `mmdc` if it is missing.

### Setup

```bash
git clone <this-repository>
cd diagramgen
uv sync
```

Configure the API key for the provider you intend to use:

```bash
python cli.py configure
```

---

## Usage

### Generate a diagram

```bash
python cli.py generate <repo-url-or-path> --out diagram.svg
```

When no provider or model is specified, DiagramGen interactively asks which provider and model to use.

A provider and model can also be specified directly:

```bash
python cli.py generate <repo-url-or-path> --provider google_genai --model gemini-4-argon --out diagram.svg
```

For a local Ollama model:

```bash
python cli.py generate <repo-url-or-path> --provider ollama --model <local-model> --out diagram.svg
```

This produces three files:

- `diagram.svg` — the rendered diagram
- `diagram.mmd` — the underlying Mermaid source
- `diagram.spec.json` — the structured specification, used for subsequent edits

### Edit an existing diagram

```bash
python cli.py edit diagram.spec.json "add a caching layer between the API and the database" --out diagram.svg
```

The edit command also supports selecting a provider and model:

```bash
python cli.py edit diagram.spec.json "add a caching layer" --provider openai --model <model> --out diagram.svg
```

The edit is applied to the specification, not the rendered image, and the diagram is recompiled and re-rendered from the updated structure.

### Configure providers

```bash
python cli.py configure
```

The configuration command allows API credentials to be stored for supported providers. Multiple provider credentials can be kept simultaneously, allowing the user to switch between models without modifying the project source code.

---

## Technology Stack

- **Language model orchestration:** LangChain, with provider-specific chat model integrations and structured output validated via Pydantic
- **LLM providers:** OpenAI, Google Gemini, Anthropic, and Ollama
- **CLI:** Typer
- **Diagram compilation:** custom deterministic compiler targeting Mermaid syntax
- **Rendering:** Mermaid CLI (`@mermaid-js/mermaid-cli`)
- **Repository access:** GitHub REST API and codeload zip archives (no Git dependency)
- **Configuration:** environment-based provider API key configuration

---
## Author
Pramit Acharjya
---

## License

MIT
