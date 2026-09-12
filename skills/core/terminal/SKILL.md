---
name: terminal
description: "Command execution, shell operations, and background processes"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["execute", "background"]
triggers:
  - "run"
  - "execute"
  - "command"
  - "shell"
  - "terminal"
examples:
  - input: "Run ls -la"
    output: "directory listing"
---
# Terminal Skill

## Overview
Command execution, shell operations, and background processes.

## Tools

### execute(command: string, timeout: int) -> Result
Execute a shell command.

### background(command: string) -> ProcessInfo
Run a command in background.
