---
name: web-research
description: "Web search, content extraction, and fact-checking"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["search", "extract", "fact_check"]
triggers:
  - "search"
  - "web"
  - "research"
  - "find"
  - "look up"
examples:
  - input: "Search for Python best practices"
    output: "search results with links and summaries"
---
# Web Research Skill

## Overview
Web search, content extraction, and fact-checking.

## Tools

### search(query: string, num_results: int) -> list[Result]
Search the web for information.

### extract(url: string) -> Content
Extract content from a URL.

### fact_check(statement: string) -> FactCheckResult
Verify a statement against trusted sources.
