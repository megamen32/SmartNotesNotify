"""Add is_done column to notes.

Revision ID: d3cf938a6938
Revises: 
Create Date: 2025-12-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "d3cf938a6938"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notes",
        sa.Column(
            "is_done",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("notes", "is_done")
