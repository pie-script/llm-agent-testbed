"""
tools_naive.py

The naive, unvalidated version of the user-lookup tool. Deliberately
does zero checking -- whatever the LLM asks for, it gets. This is the
"confused deputy" in its purest form: a privileged function that
blindly trusts the caller's request.

This is what the attack prompts run against first, to establish a
baseline of what goes wrong with no defenses at all.
"""

from testbed.fake_data import find_user_by_username


def naive_get_user(username: str) -> dict:
    """
    Look up a user and return EVERYTHING, no restrictions.

    This function is intentionally insecure. It exists to demonstrate
    what happens when application code executes an LLM's tool request
    without validating it -- the actual vulnerability described in
    Section 1 of the project notes.
    """
    user = find_user_by_username(username)
    if user is None:
        return {"error": f"No user found with username '{username}'"}

    return {
        "id": user.id,
        "username": user.username,
        "password": user.password,
        "role": user.role,
        "restricted": user.restricted,
        "bio": user.bio,
    }