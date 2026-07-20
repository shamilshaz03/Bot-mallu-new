"""
Generates cryptographically random, unique, single-use activation keys.

Format:  <PLAN>-XXXX-XXXX     e.g.  199-K3F9-QP2M
"""
import secrets
import string

ALPHABET = string.ascii_uppercase + string.digits
# Exclude visually ambiguous characters to reduce user typo/support issues
ALPHABET = ALPHABET.translate({ord(c): None for c in "O0I1"})


def _block(length: int = 4) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def generate_key(plan: str) -> str:
    return f"{plan}-{_block()}-{_block()}"


def generate_keys(plan: str, count: int) -> list[str]:
    """Generate `count` unique keys. Uniqueness against the DB is still enforced
    by the unique index on `key` plus a retry loop in the repository layer."""
    keys = set()
    while len(keys) < count:
        keys.add(generate_key(plan))
    return list(keys)
