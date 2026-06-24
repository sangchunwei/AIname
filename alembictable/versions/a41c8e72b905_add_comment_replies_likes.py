"""add comment replies and likes

Revision ID: a41c8e72b905
Revises: f2b6c9a1d034
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a41c8e72b905"
down_revision: Union[str, None] = "f2b6c9a1d034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("community_comment", sa.Column("parent_comment_id", sa.Integer(), nullable=True))
    op.add_column("community_comment", sa.Column("like_count", sa.Integer(), server_default="0", nullable=False))
    op.create_foreign_key(
        "fk_community_comment_parent_comment_id_community_comment",
        "community_comment",
        "community_comment",
        ["parent_comment_id"],
        ["id"],
    )
    op.create_index("ix_community_comment_parent_comment_id", "community_comment", ["parent_comment_id"])

    op.create_table(
        "community_comment_like",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["comment_id"], ["community_comment.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("comment_id", "user_id", name="uq_community_comment_like_comment_user"),
    )
    op.create_index("ix_community_comment_like_comment_id", "community_comment_like", ["comment_id"])
    op.create_index("ix_community_comment_like_user_id", "community_comment_like", ["user_id"])


def downgrade() -> None:
    op.drop_table("community_comment_like")
    op.drop_index("ix_community_comment_parent_comment_id", table_name="community_comment")
    op.drop_constraint(
        "fk_community_comment_parent_comment_id_community_comment",
        "community_comment",
        type_="foreignkey",
    )
    op.drop_column("community_comment", "like_count")
    op.drop_column("community_comment", "parent_comment_id")
