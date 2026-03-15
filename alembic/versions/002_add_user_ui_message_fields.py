"""002_add_user_ui_message_fields: chat_id, ui_message_id, updated_at в users

Revision ID: 002_ui_fields
Revises: 001_initial
Create Date: 2026-03-15

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_ui_fields"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("chat_id", sa.BigInteger(), nullable=True))
    op.add_column("users", sa.Column("ui_message_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "updated_at")
    op.drop_column("users", "ui_message_id")
    op.drop_column("users", "chat_id")
