"""Versioned API router. Feature routers (auth, projects, agents, …) are
mounted here as they land in later phases.
"""

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/meta", tags=["meta"])
async def meta() -> dict[str, object]:
    """Minimal metadata endpoint, proving the v1 router is mounted."""
    return {
        "api": "agenticubed",
        "version": "v1",
        "phase": 1,
        "modules": [
            "intake",
            "methodology",
            "decomposition",
            "capability",
            "agent_registry",
            "matching",
            "orchestration",
            "evaluation",
            "remediation",
            "approval",
            "governance",
            "analytics",
            "closeout",
        ],
    }
