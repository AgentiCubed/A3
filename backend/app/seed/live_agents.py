"""Register a live-provider agent squad in an existing organization.

Companion to ``app.seed.demo``: the demo proves the governed loop offline
with the deterministic ``mock`` adapter; this seed registers a planner,
two executors, and an independent evaluator that call a real model
provider (default: ``github_models``, the zero-cost GitHub Models tier)
so new projects produce genuine model output.

The provider credential is resolved by reference at call time (e.g. the
``GITHUB_MODELS_TOKEN`` environment variable); no secret value is stored.
Idempotent: an agent whose name already exists in the organization is
left untouched.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AgentKind, AgentRole
from app.models.agent import Agent
from app.models.user import User
from app.services import agent_service

SQUAD = [
    ("Live Planner", AgentRole.EXECUTOR, ["planning.decompose"]),
    (
        "Live Analyst",
        AgentRole.EXECUTOR,
        ["research.market", "analysis.data", "analysis.stats"],
    ),
    ("Live Writer", AgentRole.EXECUTOR, ["writing.brief", "writing.report"]),
    ("Live Evaluator", AgentRole.EVALUATOR, ["evaluation.rubric"]),
]


async def seed_live_agents(
    session: AsyncSession,
    *,
    email: str,
    provider: str,
    model: str,
) -> list[str]:
    """Create the live squad in ``email``'s organization; return a report."""
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        raise SystemExit(
            f"No account found for {email!r}. Run the demo seed first "
            "(python -m app.seed.demo --email ...) or use the email you "
            "registered with."
        )

    lines: list[str] = []
    for name, role, capabilities in SQUAD:
        existing = (
            await session.execute(
                select(Agent).where(
                    Agent.organization_id == user.organization_id,
                    Agent.name == name,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            lines.append(f"- {name}: already exists ({existing.provider}) — skipped")
            continue
        agent = await agent_service.register_agent(
            session,
            org_id=user.organization_id,
            actor_id=user.id,
            name=name,
            kind=AgentKind.AI,
            provider=provider,
            model=model,
            default_role=role,
            config=None,
        )
        for capability in capabilities:
            await agent_service.add_capability(
                session,
                agent=agent,
                capability=capability,
                proficiency=3,
                evidence="live-provider seed registration",
            )
        lines.append(f"- {name}: created ({provider} / {model}, {role.value})")
    await session.commit()
    return lines


async def _main(email: str, provider: str, model: str) -> None:  # pragma: no cover
    from app.db.session import SessionFactory

    async with SessionFactory() as session:
        lines = await seed_live_agents(session, email=email, provider=provider, model=model)
    print(f"Live agent squad for {email}:")  # noqa: T201
    for line in lines:
        print(line)  # noqa: T201
    print(  # noqa: T201
        "\nCredential is resolved by reference at call time; ensure the "
        "provider token (e.g. GITHUB_MODELS_TOKEN) is present in the "
        "runtime environment."
    )


if __name__ == "__main__":  # pragma: no cover
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Register live-provider agents")
    parser.add_argument("--email", required=True, help="Owner account email")
    parser.add_argument(
        "--provider",
        default="github_models",
        help="Provider adapter name (default: github_models)",
    )
    parser.add_argument(
        "--model",
        default="openai/gpt-4o-mini",
        help="Model ID (default: openai/gpt-4o-mini)",
    )
    args = parser.parse_args()
    asyncio.run(_main(args.email, args.provider, args.model))
