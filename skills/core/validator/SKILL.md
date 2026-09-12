---
name: validator
description: "Verifies task results meet quality criteria before returning to user"
version: "1.0.0"
author: "hakimagent"
license: "MIT"
tools: ["validate", "check_syntax", "run_tests", "check_security"]
triggers:
  - "validate"
  - "verify"
  - "check"
  - "test"
  - "lint"
examples:
  - input: "Validate the Python code in main.py"
    output: "syntax: valid, tests: passing, security: clean"
---
# Validator Skill

## Overview
Verifies task results meet quality criteria before returning to user.

## Tools

### validate(result: any, criteria: dict) -> ValidationResult
Validate a result against criteria.

### check_syntax(code: string, language: string) -> SyntaxResult
Check code syntax for errors.

### run_tests(test_path: string) -> TestResult
Run tests and return results.

### check_security(code: string) -> SecurityResult
Check code for security vulnerabilities.
