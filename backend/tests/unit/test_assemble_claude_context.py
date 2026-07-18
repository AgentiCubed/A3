from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.assemble_claude_context import (
    ContextAssemblyError,
    DraftPullRequest,
    GitHubClient,
    read_sources,
    render_context,
)


def test_render_context_contains_canonical_sources_and_complete_draft_diff():
    context = render_context(
        repository="AgentiCubed/agenticubed",
        commit_sha="abc123",
        generated_at=datetime(2026, 7, 18, tzinfo=UTC),
        sources=[
            ("Architecture v2", Path("docs/agentic3/ARCHITECTURE-v2.md"), "# Architecture"),
            (
                "Constitution v1.0",
                Path("docs/governance/constitution/Constitution-v1.0.md"),
                "# Constitution",
            ),
        ],
        draft_pulls=[
            DraftPullRequest(
                number=42,
                title="Harden acceptance",
                url="https://github.com/AgentiCubed/agenticubed/pull/42",
                head_sha="def456",
                diff="diff --git a/a.py b/a.py\n+accepted",
            )
        ],
    )

    assert "# Architecture" in context
    assert "# Constitution" in context
    assert "### PR #42: Harden acceptance" in context
    assert "diff --git a/a.py b/a.py\n+accepted" in context


def test_read_sources_fails_closed_when_a_canonical_document_is_missing(tmp_path):
    with pytest.raises(ContextAssemblyError, match="unable to read canonical source"):
        read_sources(tmp_path)


def test_github_client_includes_only_open_drafts_and_fetches_each_diff(monkeypatch):
    client = GitHubClient("token", "AgentiCubed/agenticubed")
    pulls = [
        {
            "number": 42,
            "draft": True,
            "title": "Draft",
            "html_url": "https://example.test/42",
            "head": {"sha": "abc"},
        },
        {
            "number": 43,
            "draft": False,
            "title": "Ready",
            "html_url": "https://example.test/43",
            "head": {"sha": "def"},
        },
    ]
    monkeypatch.setattr(client, "_get_json", lambda _path: pulls)
    monkeypatch.setattr(client, "_get_text", lambda path, _accept: f"complete diff for {path}")

    drafts = client.list_draft_pull_requests()

    assert [draft.number for draft in drafts] == [42]
    assert drafts[0].diff.endswith("/pulls/42")


def test_github_client_rejects_invalid_repository_or_missing_token():
    with pytest.raises(ContextAssemblyError, match="owner/repository"):
        GitHubClient("token", "invalid")
    with pytest.raises(ContextAssemblyError, match="GITHUB_TOKEN"):
        GitHubClient("", "AgentiCubed/agenticubed")
