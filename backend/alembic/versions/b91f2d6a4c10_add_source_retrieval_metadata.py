"""Add source retrieval metadata for evidence and health reporting.

Revision ID: b91f2d6a4c10
Revises: a748d2310f2c
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b91f2d6a4c10"
down_revision: Union[str, None] = "a748d2310f2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("last_successful_retrieval_at", sa.DateTime(), nullable=True))
    op.add_column("sources", sa.Column("last_retrieval_status", sa.String(), nullable=True))
    op.add_column("sources", sa.Column("last_error", sa.String(), nullable=True))
    op.add_column("verification_results", sa.Column("source_type", sa.String(), nullable=True))
    op.add_column("verification_results", sa.Column("retrieval_status", sa.String(), nullable=True))
    op.add_column("verification_results", sa.Column("source_published_at", sa.DateTime(), nullable=True))
    op.add_column("verification_results", sa.Column("source_version", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("verification_results", "source_version")
    op.drop_column("verification_results", "source_published_at")
    op.drop_column("verification_results", "retrieval_status")
    op.drop_column("verification_results", "source_type")
    op.drop_column("sources", "last_error")
    op.drop_column("sources", "last_retrieval_status")
    op.drop_column("sources", "last_successful_retrieval_at")