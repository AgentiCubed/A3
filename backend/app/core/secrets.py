"""Credential resolution by reference.

Agent/Tool configs store the *env-var key* of a credential, never the value
(see security-model §7). This module resolves a key to its value at call time
and never logs it. The resolved value must never be persisted or put in a prompt.
"""

from __future__ import annotations

import os


class CredentialNotConfigured(RuntimeError):
    """Raised when a referenced credential key is not present in the environment."""


def resolve_credential(ref_key: str) -> str:
    """Resolve an env-var *key* to its secret value.

    Raises CredentialNotConfigured if unset or empty. The error message contains
    only the key name, never the value.
    """
    if not ref_key:
        raise CredentialNotConfigured("empty credential reference")
    value = os.environ.get(ref_key)
    if not value:
        raise CredentialNotConfigured(f"credential not configured for key: {ref_key}")
    return value
