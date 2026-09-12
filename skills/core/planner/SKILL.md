---
name: planner
description: "Decomposes objectives into executable steps with dependencies"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["task_decompose", "dependency_graph", "schedule"]
triggers:
  - "plan"
  - "decompose"
  - "roadmap"
  - "break down"
  - "steps"
examples:
  - input: "Build a REST API with authentication"
    output: "tasks: [design_schema, implement_auth, create_endpoints, write_tests]"
---
# Planner Skill

## Overview
Strategic planning and goal decomposition for agent operations.

## Tools

### task_decompose(objective: string) -> Task[]
Breaks down high-level objectives into ordered, dependency-aware tasks.

### dependency_graph(tasks: Task[]) -> Graph
Computes execution order and parallelization opportunities.

### schedule(tasks: Task[], constraints: Constraints) -> Timeline
Generates execution timeline respecting resource constraints.
