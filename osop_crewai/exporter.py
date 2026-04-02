"""Export CrewAI Crew definitions to OSOP YAML."""

from __future__ import annotations

from typing import Any

import yaml

try:
    from crewai import Crew
except ImportError:
    raise ImportError("crewai is required: pip install crewai")


class OsopCrewExporter:
    """Export a CrewAI Crew instance to OSOP YAML format.

    Example:
        from crewai import Agent, Task, Crew
        crew = Crew(agents=[...], tasks=[...])
        exporter = OsopCrewExporter(crew)
        yaml_str = exporter.to_yaml()
    """

    def __init__(self, crew: Crew):
        self.crew = crew

    def _slugify(self, text: str) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")

    def to_dict(self) -> dict[str, Any]:
        """Convert crew to OSOP workflow dict."""
        nodes: list[dict[str, Any]] = []
        for agent in self.crew.agents:
            nid = self._slugify(agent.role)
            node: dict[str, Any] = {
                "id": nid,
                "type": "agent",
                "subtype": "coordinator" if agent.allow_delegation else "worker",
                "name": agent.role,
                "purpose": agent.goal,
            }
            runtime_config: dict[str, Any] = {}
            if agent.backstory:
                runtime_config["system_prompt"] = agent.backstory
            if runtime_config:
                node["runtime"] = {"config": runtime_config}
            nodes.append(node)

        # Build edges from task order (tasks reference agents in sequence)
        edges: list[dict[str, Any]] = []
        agent_sequence: list[str] = []
        for task in self.crew.tasks:
            if task.agent:
                agent_id = self._slugify(task.agent.role)
                agent_sequence.append(agent_id)

        seen: set[tuple[str, str]] = set()
        for i in range(len(agent_sequence) - 1):
            pair = (agent_sequence[i], agent_sequence[i + 1])
            if pair not in seen and pair[0] != pair[1]:
                edges.append({"from": pair[0], "to": pair[1], "mode": "sequential"})
                seen.add(pair)

        process_name = "sequential"
        if hasattr(self.crew, "process") and self.crew.process:
            process_name = str(self.crew.process.value) if hasattr(self.crew.process, "value") else str(self.crew.process)

        workflow: dict[str, Any] = {
            "osop_version": "1.0",
            "id": self._slugify(f"crewai-{len(nodes)}-agents"),
            "name": f"CrewAI Crew ({len(nodes)} agents)",
            "description": f"Exported from CrewAI — {process_name} process with {len(nodes)} agents.",
            "nodes": nodes,
            "edges": edges,
        }
        return workflow

    def to_yaml(self) -> str:
        """Convert crew to OSOP YAML string."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False, allow_unicode=True)

    def to_file(self, path: str) -> None:
        """Write OSOP YAML to file."""
        from pathlib import Path
        Path(path).write_text(self.to_yaml(), encoding="utf-8")
