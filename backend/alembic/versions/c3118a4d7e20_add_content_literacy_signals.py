"""Persist transparent content literacy cues.

Revision ID: c3118a4d7e20
Revises: b91f2d6a4c10
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3118a4d7e20"
down_revision: Union[str, None] = "b91f2d6a4c10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("content_classification", sa.String(), nullable=True))
    op.add_column("analyses", sa.Column("content_signals", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "content_signals")
    op.drop_column("analyses", "content_classification")
