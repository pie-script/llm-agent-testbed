"""
models.py

The data shapes for the LLM security testbed. Same pattern as the
header scanner: static definitions (FakeUser, FakeApiKey, AttackAttempt)
are separated from per-run outcomes (AttackResult).

Nothing in this file "does" anything — no I/O, no logic. Just shapes.
"""

from dataclasses import dataclass
from typing import Literal

# =============================================================================
# Fake backend records — the mock data an attack prompt might try to extract
# =============================================================================


@dataclass(frozen=True)
class FakeUser:
    """
    One row in the mock 'users' table.

    `restricted` marks rows that should never be returned to a
    non-admin caller — this is what lets you test access-control
    bypass attacks, not just secrecy attacks.
    """
    id: int
    username: str
    password: str
    role: str
    restricted: bool = False
    bio: str = ""


@dataclass(frozen=True)
class FakeApiKey:
    """
    One row in the mock 'api_keys' table.
    """
    service: str
    key: str
    restricted: bool = False


# =============================================================================
# AttackAttempt — the fixed checklist entry (defined once, reused every run)
# =============================================================================

AttackCategory = Literal[
    "direct_override",
    "role_authority_claim",
    "indirect_injection",
    "boundary_bypass",
    "chained_request",
]


@dataclass(frozen=True)
class AttackAttempt:
    """
    One adversarial prompt, plus what it's actually trying to steal.

    `target_secret` is the ground-truth value this attack is trying to
    extract (e.g. the admin's real password). Grading compares the
    tool's actual output/arguments against this value directly, rather
    than guessing intent from the prompt text.
    """
    name: str
    category: AttackCategory
    prompt: str
    target_secret: str


# =============================================================================
# AttackResult — the outcome of running one AttackAttempt against one tool
# =============================================================================

ToolVersion = Literal["naive", "hardened"]
AttackStatus = Literal["leaked", "blocked", "unclear"]


@dataclass(frozen=True)
class AttackResult:
    """
    Outcome of running one AttackAttempt against one tool version.

    `attempt` holds a reference to the AttackAttempt this result came
    from -- not a copy of its fields -- same reasoning as HeaderFinding
    holding a reference to its HeaderRule.

    `evidence` is a human-readable trace of what actually happened, so
    a "leaked" or "blocked" verdict can be manually spot-checked later
    rather than trusted blindly (see Phase 7 -- Refining).
    """
    attempt: AttackAttempt
    tool_version: ToolVersion
    status: AttackStatus
    evidence: str