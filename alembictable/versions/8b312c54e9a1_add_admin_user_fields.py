"""add admin and account status fields

Revision ID: 8b312c54e9a1
Revises: 36736599c2da
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8b312c54e9a1"
down_revision: Union[str, None] = "36736599c2da"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("is_admin", sa.Boolean(), server_default=sa.text("0"), nullable=False))
    op.add_column("user", sa.Column("is_frozen", sa.Boolean(), server_default=sa.text("0"), nullable=False))
    op.add_column("user", sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("0"), nullable=False))
    op.add_column("user", sa.Column("token_version", sa.Integer(), server_default=sa.text("0"), nullable=False))
    op.add_column("user", sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False))
    op.add_column("user", sa.Column("deleted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("user", "deleted_at")
    op.drop_column("user", "created_at")
    op.drop_column("user", "token_version")
    op.drop_column("user", "is_deleted")
    op.drop_column("user", "is_frozen")
    op.drop_column("user", "is_admin")
