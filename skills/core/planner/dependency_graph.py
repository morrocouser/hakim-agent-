from dataclasses import dataclass
from typing import Optional


@dataclass
class Graph:
    nodes: list[str]
    edges: list[tuple[str, str]]
    parallel_groups: list[list[str]]
    execution_order: list[str]


def dependency_graph(tasks: list[dict]) -> dict:
    """Compute execution order and parallelization opportunities"""
    nodes = [task["name"] for task in tasks]
    edges = []

    # Build dependency edges
    for task in tasks:
        for dep in task.get("dependencies", []):
            edges.append((dep, task["name"]))

    # Topological sort for execution order
    in_degree = {node: 0 for node in nodes}
    for src, dst in edges:
        in_degree[dst] += 1

    execution_order = []
    queue = [node for node in nodes if in_degree[node] == 0]

    while queue:
        queue.sort()  # Deterministic order
        node = queue.pop(0)
        execution_order.append(node)

        for src, dst in edges:
            if src == node:
                in_degree[dst] -= 1
                if in_degree[dst] == 0:
                    queue.append(dst)

    # Group tasks that can run in parallel
    parallel_groups = []
    visited = set()
    for node in execution_order:
        if node not in visited:
            group = [node]
            visited.add(node)
            # Find tasks that can run in parallel (same dependencies satisfied)
            for other in execution_order:
                if other not in visited:
                    other_deps = set()
                    for src, dst in edges:
                        if dst == other:
                            other_deps.add(src)
                    node_deps = set()
                    for src, dst in edges:
                        if dst == node:
                            node_deps.add(src)
                    if other_deps == node_deps:
                        group.append(other)
                        visited.add(other)
            parallel_groups.append(group)

    return {
        "nodes": nodes,
        "edges": edges,
        "parallel_groups": parallel_groups,
        "execution_order": execution_order,
    }
