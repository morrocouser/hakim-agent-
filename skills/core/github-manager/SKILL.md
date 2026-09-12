---
name: github-manager
description: "Repository management, PR creation, and issue tracking"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["repo", "pr", "issue"]
triggers:
  - "github"
  - "repository"
  - "pull request"
  - "issue"
  - "commit"
examples:
  - input: "Create a new repository for my project"
    output: "repository created with README"
---
# GitHub Manager Skill

## Overview
Repository management, PR creation, and issue tracking.

## Tools

### repo(action: string, params: dict) -> Result
Manage repositories (create, clone, list).

### pr(action: string, params: dict) -> Result
Manage pull requests (create, list, merge).

### issue(action: string, params: dict) -> Result
Manage issues (create, list, close).
