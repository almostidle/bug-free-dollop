"""create initial tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(500), nullable=False, server_default="Untitled"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("plagiarism_score", sa.Float(), nullable=True),
        sa.Column("ai_score", sa.Float(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_documents_id", "documents", ["id"])

    op.create_table(
        "detector_config",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(100), nullable=False, unique=True),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_detector_config_id", "detector_config", ["id"])
    op.create_index("ix_detector_config_key", "detector_config", ["key"], unique=True)


def downgrade() -> None:
    op.drop_table("detector_config")
    op.drop_table("documents")
