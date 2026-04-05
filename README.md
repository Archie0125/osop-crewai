# osop-crewai

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/osop-crewai)](https://pypi.org/project/osop-crewai/)

Define CrewAI crews in [OSOP](https://osop.ai) YAML and run them anywhere. Export existing crews to portable OSOP format.

## Installation

```bash
pip install osop-crewai
```

## Usage

### Load OSOP → CrewAI

```python
from osop_crewai import OsopCrewLoader

# Load from file
loader = OsopCrewLoader("research-crew.osop.yaml")
crew = loader.build_crew()
result = crew.kickoff()

# Load from string
loader = OsopCrewLoader(content=yaml_string)
crew = loader.build_crew(verbose=True)
```

### Export CrewAI → OSOP

```python
from crewai import Agent, Task, Crew
from osop_crewai import OsopCrewExporter

crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])
exporter = OsopCrewExporter(crew)

# Get YAML string
yaml_str = exporter.to_yaml()

# Save to file
exporter.to_file("my-crew.osop.yaml")
```

## OSOP Workflow Format

```yaml
osop_version: "1.0"
id: research-crew
name: Research Crew
nodes:
  - id: researcher
    type: agent
    subtype: worker
    name: Research Analyst
    purpose: Conduct thorough research
    runtime:
      config:
        system_prompt: You are an experienced researcher.
        tools: [web_search, arxiv_search]

  - id: writer
    type: agent
    subtype: worker
    name: Content Writer
    purpose: Write compelling articles

edges:
  - from: researcher
    to: writer
    mode: sequential
```

## Mapping

| OSOP | CrewAI |
|------|--------|
| Node `type: "agent"` | `Agent()` |
| Node `purpose` | `Agent(goal=...)` |
| Node `runtime.config.system_prompt` | `Agent(backstory=...)` |
| Node `subtype: "coordinator"` | `Agent(allow_delegation=True)` |
| Edge `mode: "sequential"` | `Process.sequential` |
| Edge `mode: "spawn"` | `Process.hierarchical` |

## Why?

- **Portability**: Same workflow runs in CrewAI, LangGraph, n8n, Airflow
- **Visualization**: Render crews as Mermaid diagrams or in the [OSOP Editor](https://osop-editor.vercel.app)
- **Analysis**: Risk assessment, optimization, and execution reports via [OSOP MCP Server](https://github.com/Archie0125/osop-mcp)

## Links

- [OSOP Spec](https://github.com/Archie0125/osop-spec) — Protocol specification
- [OSOP Interop](https://github.com/Archie0125/osop-interop) — Format converters
- [OSOP MCP Server](https://github.com/Archie0125/osop-mcp) — 5 MCP tools (validate, render, report, diff, risk_assess)
- [Visual Editor](https://osop-editor.vercel.app)

## License

Apache License 2.0
