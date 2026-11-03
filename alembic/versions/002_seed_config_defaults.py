"""seed detector config defaults

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:01.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

config_table = sa.table(
    "detector_config",
    sa.column("key", sa.String),
    sa.column("value", sa.String),
    sa.column("description", sa.Text),
)

DEFAULTS = [
    ("shingle_size", "5", "Number of words per shingle for plagiarism detection"),
    ("plagiarism_threshold", "0.3", "Minimum combined score to flag as plagiarized"),
    ("ai_threshold", "0.5", "Minimum AI score to flag as AI-generated"),
    ("min_text_length", "50", "Minimum character count required for analysis"),
    ("jaccard_weight", "0.5", "Weight of Jaccard similarity in combined plagiarism score"),
    ("tfidf_weight", "0.5", "Weight of TF-IDF cosine similarity in combined plagiarism score"),
    ("weight_burstiness", "0.25", "Weight for sentence length variance metric in AI detection"),
    ("weight_lexical_diversity", "0.25", "Weight for type-token ratio metric in AI detection"),
    ("weight_repeated_ngrams", "0.25", "Weight for repeated n-gram ratio metric in AI detection"),
    ("weight_avg_sentence_length", "0.15", "Weight for average sentence length metric in AI detection"),
    ("weight_punctuation_patterns", "0.10", "Weight for punctuation diversity metric in AI detection"),
    ("ngram_size", "3", "N-gram size for the repeated n-gram analysis"),
]


def upgrade() -> None:
    op.bulk_insert(
        config_table,
        [{"key": k, "value": v, "description": d} for k, v, d in DEFAULTS],
    )


def downgrade() -> None:
    for key, _, _ in DEFAULTS:
        op.execute(config_table.delete().where(config_table.c.key == key))
