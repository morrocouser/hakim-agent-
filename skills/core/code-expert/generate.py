def generate(specification: str, language: str = "python") -> dict:
    """Generate code based on specification"""
    templates = {
        "python": {
            "function": '''def {name}({params}):
    """{docstring}"""
    {body}
''',
            "class": '''class {name}:
    """{docstring}"""

    def __init__(self{params}):
        {body}
''',
        },
        "javascript": {
            "function": '''function {name}({params}) {{
    // {docstring}
    {body}
}}''',
        },
    }

    # Simple pattern matching for generation
    spec_lower = specification.lower()
    lang_templates = templates.get(language, templates.get("python", {}))

    if "class" in spec_lower:
        template = lang_templates.get("class", lang_templates.get("function", ""))
        return {
            "code": template.format(
                name="GeneratedClass",
                params="",
                docstring=specification,
                body="pass",
            ),
            "language": language,
            "type": "class",
        }
    else:
        template = lang_templates.get("function", "")
        return {
            "code": template.format(
                name="generated_function",
                params="",
                docstring=specification,
                body="pass",
            ),
            "language": language,
            "type": "function",
        }
