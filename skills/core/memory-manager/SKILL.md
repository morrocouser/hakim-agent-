---
name: memory-manager
description: "Manages agent context, conversation history, and knowledge persistence"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["store", "retrieve", "search", "summarize", "clear"]
triggers:
  - "remember"
  - "recall"
  - "context"
  - "history"
  - "memory"
examples:
  - input: "Remember that the user prefers Python"
    output: "Stored preference: language=python"
---
# Memory Manager Skill

## Overview
Manages agent context, conversation history, and knowledge persistence.

## Tools

### store(key: string, value: any, metadata: dict) -> bool
Store a key-value pair with metadata.

### retrieve(key: string) -> any
Retrieve a stored value by key.

### search(query: string) -> list[Entry]
Search memory for entries matching query.

### summarize(context: dict) -> string
Generate a summary of relevant context.

### clear(pattern: string) -> bool
Clear memory entries matching pattern.
