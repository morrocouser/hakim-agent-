from typing import Any


def summarize(context: dict) -> str:
    """Generate a summary of relevant context"""
    if not context:
        return "No context available"

    summary_parts = []

    # Summarize different context types
    if "conversation" in context:
        conv = context["conversation"]
        summary_parts.append(f"Conversation has {len(conv)} messages")

    if "tasks" in context:
        tasks = context["tasks"]
        summary_parts.append(f"{len(tasks)} tasks in progress")

    if "memory" in context:
        memory = context["memory"]
        summary_parts.append(f"{len(memory)} memory entries")

    if "current_task" in context:
        summary_parts.append(f"Current task: {context['current_task']}")

    return ". ".join(summary_parts) if summary_parts else "Context summary unavailable"
