"""Shared service-layer exceptions.

Several services need to signal "the requested entity does not exist within the
caller's scope". Defining a single ``NotFound`` here (instead of one per service)
means routers can translate it once and callers can catch a single type.
"""

from __future__ import annotations


class NotFound(Exception):
    """A requested entity does not exist within the caller's scope."""
