"""
display.py

A small pretty-printer for AttackResult, so results are readable in
the terminal instead of relying on the raw dataclass repr() -- which
escapes every quote inside nested strings and becomes unreadable the
moment tool output contains an apostrophe (e.g. "Alice's bio").

This is Phase 8 (reporting) pulled slightly earlier, because readable
output is genuinely needed NOW while manually spot-checking results
during Phase 6/7, not just at the very end.
"""

from testbed.models import AttackResult


def print_result(result: AttackResult) -> None:
    """
    Print one AttackResult in a clean, readable block instead of the
    raw dataclass repr().
    """
    status_labels = {
        "leaked": "LEAKED",
        "blocked": "BLOCKED",
        "unclear": "UNCLEAR",
    }
    label = status_labels[result.status]

    print("=" * 60)
    print(f"Attack:   {result.attempt.name}  [{result.attempt.category}]")
    print(f"Tool:     {result.tool_version}")
    print(f"Status:   {label}")
    print("-" * 60)
    print("Prompt:")
    print(f"  {result.attempt.prompt}")
    print("-" * 60)
    print("Evidence:")
    print(f"  {result.evidence}")
    print("=" * 60)