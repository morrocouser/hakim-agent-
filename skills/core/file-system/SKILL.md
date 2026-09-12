---
name: file-system
description: "File operations, directory management, and file search"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["read", "write", "list", "search"]
triggers:
  - "file"
  - "directory"
  - "folder"
  - "read file"
  - "write file"
examples:
  - input: "Read the contents of config.json"
    output: "file contents returned"
---
# File System Skill

## Overview
File operations, directory management, and file search.

## Tools

### read(path: string) -> string
Read file contents.

### write(path: string, content: string) -> bool
Write content to file.

### list(path: string, pattern: string) -> list[string]
List files in directory.

### search(path: string, query: string) -> list[string]
Search for files containing query.
