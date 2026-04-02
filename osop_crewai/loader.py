"""Load OSOP workflows as CrewAI Crew instances."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

try:
    from crewai import Agent, Task, Crew, Process
except ImportError:
    raise ImportError("crewai is required: pip install crewai")


class OsopCrewLoader:
    """Load an OSOP workflow and instantiate a CrewAI Crew from it.

    Maps OSOP agent nodes to CrewAI Agents, and the edge sequence to Tasks.

    Example:
        loader = OsopCrewLoader("workflow.osop.yaml")
        crew = loader.build_crew()
        result = crew.kickoff()
    """

    def __init__(self, file_path: str | Path | None = None, content: str | None = None):
        if content:
            self._raw = content
        elif file_path:
            self._raw = Path(file_path).read_text(encoding="utf-8")
        else:
            raise ValueError("Either file_path or content must be provided")
        self._data = yaml.safe_load(self._raw)
        if not isinstance(self._data, dict):
            raise ValueError("OSOP content must be a YAML mapping")

    def _build_agents(self) -> dict[str, Agent]:
        """Create CrewAI Agent instances from OSOP agent nodes."""
        agents: dict[str, Agent] = {}
        for node in self._data.get("nodes", []):
            if not isinstance(node, dict):
                continue
            if node.get("type") != "agent":
                continue

            nid = node.get("id", "")
            runtime = node.get("runtime", {})
            config = runtime.get("config", {}) if isinstance(runtime, dict) else {}

            agent = Agent(
                role=node.get("name", nid),
                goal=node.get("purpose", node.get("description", f"Agent: {nid}")),
                backstory=config.get("system_prompt", f"You are {node.get('name', nid)}."),
                verbose=True,
                allow_delegation=node.get("subtype") == "coordinator",
            )
            agents[nid] = agent

        return agents

    def _build_task_sequence(self) -> list[str]:
        """Topological sort of agent node IDs based on edges."""
        nodes = self._data.get("nodes", [])
        edges = self._data.get("edges", [])
        agent_ids = {n["id"] for n in nodes if isinstance(n, dict) and n.get("type") == "agent"}

        in_deg: dict[str, int] = {nid: 0 for nid in agent_ids}
        adj: dict[str, list[str]] = {nid: [] for nid in agent_ids}

        for e in edges:
            if not isinstance(e, dict):
                continue
            f, t = e.get("from", ""), e.get("to", "")
            if f in agent_ids and t in agent_ids:
                adj[f].append(t)
                in_deg[t] = in_deg.get(t, 0) + 1

        queue = [nid for nid, deg in in_deg.items() if deg == 0]
        order: list[str] = []
        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for child in adj.get(nid, []):
                in_deg[child] -= 1
                if in_deg[child] == 0:
                    queue.append(child)

        # Add any remaining
        for nid in agent_ids:
            if nid not in order:
                order.append(nid)
        return order

    def build_crew(
        self,
        process: Process | None = None,
        verbose: bool = True,
        **crew_kwargs: Any,
    ) -> Crew:
        """Build a CrewAI Crew from the OSOP workflow.

        Args:
            process: CrewAI Process type (sequential or hierarchical).
                     Auto-detected from edges if not specified.
            verbose: Enable verbose output.
            **crew_kwargs: Additional kwargs passed to Crew().
        """
        agents = self._build_agents()
        if not agents:
            raise ValueError("No agent nodes found in the OSOP workflow")

        task_order = self._build_task_sequence()

        # Auto-detect process type from edges
        if process is None:
            edges = self._data.get("edges", [])
            has_spawn = any(e.get("mode") == "spawn" for e in edges if isinstance(e, dict))
            process = Process.hierarchical if has_spawn else Process.sequential

        # Create tasks
        tasks: list[Task] = []
        node_map = {n["id"]: n for n in self._data.get("nodes", []) if isinstance(n, dict)}
        for nid in task_order:
            if nid not in agents:
                continue
            node = node_map.get(nid, {})
            task = Task(
                description=node.get("purpose", node.get("description", f"Task for {nid}")),
                expected_output=f"Output from {node.get('name', nid)}",
                agent=agents[nid],
            )
            tasks.append(task)

        return Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=process,
            verbose=verbose,
            **crew_kwargs,
        )

    def get_workflow_info(self) -> dict[str, Any]:
        """Get workflow metadata without building the crew."""
        nodes = self._data.get("nodes", [])
        edges = self._data.get("edges", [])
        return {
            "id": self._data.get("id", ""),
            "name": self._data.get("name", ""),
            "description": self._data.get("description", ""),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "agent_nodes": [n["id"] for n in nodes if isinstance(n, dict) and n.get("type") == "agent"],
        }
