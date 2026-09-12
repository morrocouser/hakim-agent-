---
name: reasoning
description: "Strategy selection, problem analysis, and error recovery"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["strategy_select", "analyze", "recover"]
triggers:
  - "reason"
  - "strategy"
  - "analyze"
  - "recover"
  - "error"
examples:
  - input: "The API is returning 500 errors"
    output: "strategy: analyze_logs, check_dependencies, retry_with_backoff"
---
# Reasoning Skill

## Overview
Strategy selection, problem analysis, and error recovery for agent operations.

## Tools

### strategy_select(problem: string, context: dict) -> Strategy
Select the best strategy for a given problem.

### analyze(data: any, criteria: dict) -> Analysis
Analyze data against criteria to identify issues.

### recover(failed_results: list, objective: string) -> Result
Recover from failed execution by retrying with adjusted approach.
