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


def hardened_get_user(username: str) -> dict:
    user = find_user_by_username(username)
    if user is None:
        return {"error": f"No user found with username '{username}'"}

    # Protection 1: refuse restricted rows entirely, before anything
    # else is considered.
    if user.restricted:
        return {"error": f"Access denied for user '{username}'"}

    # Protection 2: build the response by hand, listing only the
    # fields we want to expose. `password` is simply never mentioned --
    # not fetched, not deleted, just never included in the first place.
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "restricted": user.restricted,
        "bio": user.bio,
    }