"""Add normalized input metadata and evidence items.

Revision ID: e81c7a2f5b60
Revises: d4a82fb193c1
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e81c7a2f5b60"
down_revision: Union[str, None] = "d4a82fb193c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_inputs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("input_type", sa.String(), nullable=False),
        sa.Column("media_type", sa.String(), nullable=True),
        sa.Column("byte_length", sa.Integer(), nullable=True),
        sa.Column("extraction_status", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_inputs_id"), "analysis_inputs", ["id"], unique=False)
    op.create_table(
        "evidence_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("verification_result_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("source_code", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("retrieval_status", sa.String(), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(), nullable=True),
        sa.Column("source_published_at", sa.DateTime(), nullable=True),
        sa.Column("source_version", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verification_result_id"], ["verification_results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("verification_result_id"),
    )
    op.create_index(op.f("ix_evidence_items_id"), "evidence_items", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_items_id"), table_name="evidence_items")
    op.drop_table("evidence_items")
    op.drop_index(op.f("ix_analysis_inputs_id"), table_name="analysis_inputs")
    op.drop_table("analysis_inputs")
