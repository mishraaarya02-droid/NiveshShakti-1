"""Add persisted extraction and detected-language state.

Revision ID: a748d2310f2c
Revises: fecdaac525f3
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a748d2310f2c"
down_revision: Union[str, None] = "fecdaac525f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("extraction_status", sa.String(), nullable=True))
    op.add_column("analyses", sa.Column("detected_language", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "detected_language")
    op.drop_column("analyses", "extraction_status")
