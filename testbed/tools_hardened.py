"""
tools_hardened.py

The hardened, validated version of the user-lookup tool. Same purpose
as the naive tool (let the LLM look up a user) but with two independent
protections layered on top:

1. Restricted rows (restricted=True) are refused entirely -- nothing
   about them is returned, not even non-sensitive fields.
2. `password` is NEVER included in a successful response, regardless
   of whether the user is restricted -- this protects ordinary users'
   passwords too, not just the flagged restricted row.

These two checks are independent on purpose. Relying on `restricted`
alone would still leak alice's password, since she isn't restricted --
see the project notes / conversation for why that gap matters.
"""

from testbed.fake_data import find_user_by_username

PURPOSE_FIELDS: dict[str, set[str]] = {
    "basic_lookup": {"id", "username", "role"},
    "audit_export": {
        "id",
        "username",
        "restricted",
        "department",
        "role",
        "two_factor_enabled",
        "password_was_leaked",
    },
}


def hardened_get_user(username: str, purpose: str = "basic_lookup") -> dict:
    if purpose not in PURPOSE_FIELDS:
        return {
            "error": (
                f"Invalid purpose '{purpose}'. Allowed: "
                f"{sorted(list(PURPOSE_FIELDS.keys()))}"
            )
        }

    user = find_user_by_username(username)
    if user is None:
        return {"error": f"No user found with username '{username}'"}

    if user.restricted:
        return {"error": f"Access denied for user '{username}'"}

    allowed_keys = PURPOSE_FIELDS[purpose]
    user_dict = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        'restricted':user.restricted,
        "department": user.department,
        "two_factor_enabled": user.two_factor_enabled,
        "password_was_leaked": user.password_was_leaked,
    }

    return {k: v for k, v in user_dict.items() if k in allowed_keys}