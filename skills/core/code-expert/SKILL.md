---
name: code-expert
description: "Code generation, review, and refactoring"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["generate", "review", "refactor"]
triggers:
  - "code"
  - "generate"
  - "review"
  - "refactor"
  - "implement"
examples:
  - input: "Generate a Python function to calculate fibonacci numbers"
    output: "function implementation with docstring"
---
# Code Expert Skill

## Overview
Code generation, review, and refactoring.

## Tools

### generate(specification: string, language: string) -> string
Generate code based on specification.

### review(code: string) -> ReviewResult
Review code for issues and improvements.

### refactor(code: string, goals: list[string]) -> string
Refactor code according to goals.
