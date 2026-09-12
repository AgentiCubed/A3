"""Register a live-provider agent squad in an existing organization.

Companion to ``app.seed.demo``: the demo proves the governed loop offline
with the deterministic ``mock`` adapter; this seed registers a planner,
two executors, and an independent evaluator that call a real model
provider (default: ``gemini`` on Google AI Studio's free tier)
so new projects produce genuine model output.

The provider credential is resolved by reference at call time (e.g. the
``GEMINI_API_KEY`` environment variable); no secret value is stored.
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


async def verify_provider(provider: str, model: str) -> int:
    """Non-destructive credential/endpoint check; return process exit code."""
    from app.services.provider_preflight import preflight_provider

    result = await preflight_provider(provider, model=model)
    status = "PASS" if result.ok else "FAIL"
    print(f"[{status}] provider={result.provider} model={result.model or model}")  # noqa: T201
    print(result.message)  # noqa: T201
    if result.diagnostic:
        print(f"diagnostic: {result.diagnostic}")  # noqa: T201
    return 0 if result.ok else 1


async def _main(email: str, provider: str, model: str) -> None:  # pragma: no cover
    from app.db.session import SessionFactory

    async with SessionFactory() as session:
        lines = await seed_live_agents(session, email=email, provider=provider, model=model)
    print(f"Live agent squad for {email}:")  # noqa: T201
    for line in lines:
        print(line)  # noqa: T201
    print(  # noqa: T201
        "\nCredential is resolved by reference at call time; ensure the "
        "provider token (e.g. GEMINI_API_KEY) is present in the "
        "runtime environment. Re-run with --verify to preflight without seeding."
    )


if __name__ == "__main__":  # pragma: no cover
    import argparse
    import asyncio
    import sys

    parser = argparse.ArgumentParser(description="Register live-provider agents")
    parser.add_argument(
        "--email",
        help="Owner account email (required unless --verify)",
    )
    parser.add_argument(
        "--provider",
        default="gemini",
        help="Provider adapter name (default: gemini)",
    )
    parser.add_argument(
        "--model",
        default="gemini-flash-latest",
        help="Model ID (default: gemini-flash-latest; the models/ prefix is optional)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Non-destructive provider preflight only (no agent registration)",
    )
    args = parser.parse_args()
    if args.verify:
        sys.exit(asyncio.run(verify_provider(args.provider, args.model)))
    if not args.email:
        parser.error("--email is required unless --verify is set")
    asyncio.run(_main(args.email, args.provider, args.model))
