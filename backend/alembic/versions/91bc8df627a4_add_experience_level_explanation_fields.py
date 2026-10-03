"""Add Hindi and Hinglish explanation tiers.

Revision ID: 91bc8df627a4
Revises: f23ac0781d9e
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "91bc8df627a4"
down_revision: Union[str, None] = "f23ac0781d9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("explanation_hindi_intermediate", sa.Text(), nullable=True))
    op.add_column("analyses", sa.Column("explanation_hindi_advanced", sa.Text(), nullable=True))
    op.add_column("analyses", sa.Column("explanation_hinglish_intermediate", sa.Text(), nullable=True))
    op.add_column("analyses", sa.Column("explanation_hinglish_advanced", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "explanation_hinglish_advanced")
    op.drop_column("analyses", "explanation_hinglish_intermediate")
    op.drop_column("analyses", "explanation_hindi_advanced")
    op.drop_column("analyses", "explanation_hindi_intermediate")
