"""Credential resolution by reference.

Agent/Tool configs store the *env-var key* of a credential, never the value
(see security-model §7). This module resolves a key to its value at call time
and never logs it. The resolved value must never be persisted or put in a prompt.

Resolution is restricted to an allowlist (``ALLOWED_CREDENTIAL_REFS``): agent
config is user-supplied data, and without the allowlist any registered user
could name an arbitrary server env var (``SECRET_KEY``, ``DATABASE_URL``, ...)
as an ``api_key_ref`` and have its value sent to a model provider as a Bearer
header. A reference outside the allowlist is refused here even if some caller
forgot to validate it earlier — this is the enforcement point of last resort.
"""

from __future__ import annotations

import os

from app.core.config import get_settings


class CredentialNotConfigured(RuntimeError):
    """Raised when a referenced credential key is not present in the environment."""


class CredentialNotAllowed(RuntimeError):
    """Raised when a referenced credential key is outside the allowlist."""


def allowed_credential_refs() -> frozenset[str]:
    """The env-var keys agent/tool configs may reference."""
    return get_settings().allowed_credential_ref_set


def resolve_credential(ref_key: str) -> str:
    """Resolve an allowlisted env-var *key* to its secret value.

    Raises CredentialNotAllowed for keys outside ``ALLOWED_CREDENTIAL_REFS``
    and CredentialNotConfigured if the key is unset or empty. Error messages
    contain only the key name, never any value.
    """
    if not ref_key:
        raise CredentialNotConfigured("empty credential reference")
    if not isinstance(ref_key, str):
        # Malformed input, not a policy refusal; the message never carries the
        # value. Adapters map this to invalid_request.
        raise TypeError("credential reference must be a string")
    if ref_key not in allowed_credential_refs():
        raise CredentialNotAllowed(f"credential reference not permitted: {ref_key}")
    value = os.environ.get(ref_key)
    if not value:
        raise CredentialNotConfigured(f"credential not configured for key: {ref_key}")
    return value
