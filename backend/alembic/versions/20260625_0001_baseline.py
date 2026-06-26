"""baseline — establish migration chain and required extensions

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-25

Phase 1 baseline. Enables the pgcrypto extension (used for gen_random_uuid and
future column defaults) and establishes the migration head. Domain tables are
introduced from Phase 2 onward.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')
