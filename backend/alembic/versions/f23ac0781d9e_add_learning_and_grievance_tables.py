"""Add learning-content and grievance-guidance storage.

Revision ID: f23ac0781d9e
Revises: e81c7a2f5b60
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f23ac0781d9e"
down_revision: Union[str, None] = "e81c7a2f5b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def _create_content_table(table_name: str, code_column: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(code_column, sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        *(
            [sa.Column("knowledge_level", sa.String(), nullable=True)]
            if table_name == "learning_content"
            else []
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("source_published_at", sa.DateTime(), nullable=True),
        sa.Column("source_version", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(code_column),
    )


def upgrade() -> None:
    _create_content_table("learning_content", "content_code")
    op.create_index(op.f("ix_learning_content_id"), "learning_content", ["id"], unique=False)
    _create_content_table("grievance_guidance", "guidance_code")
    op.create_index(op.f("ix_grievance_guidance_id"), "grievance_guidance", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_grievance_guidance_id"), table_name="grievance_guidance")
    op.drop_table("grievance_guidance")
    op.drop_index(op.f("ix_learning_content_id"), table_name="learning_content")
    op.drop_table("learning_content")
