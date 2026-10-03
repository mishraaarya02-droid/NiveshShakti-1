"""Add Hinglish explanation field.

Revision ID: d4a82fb193c1
Revises: c3118a4d7e20
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4a82fb193c1"
down_revision: Union[str, None] = "c3118a4d7e20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("explanation_hinglish", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "explanation_hinglish")
