"""add open platform api paas demo

Revision ID: f2b6c9a1d034
Revises: e9a4c72d8f10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2b6c9a1d034"
down_revision: Union[str, None] = "e9a4c72d8f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "developer_app",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("total_quota", sa.Integer(), nullable=False),
        sa.Column("remaining_quota", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index("ix_developer_app_user_id", "developer_app", ["user_id"])
    op.create_index("ix_developer_app_status", "developer_app", ["status"])

    op.create_table(
        "developer_api_key",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("app_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(32), nullable=False),
        sa.Column("key_tail", sa.String(8), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["app_id"], ["developer_app.id"]),
        sa.UniqueConstraint("key_hash", name="uq_developer_api_key_key_hash"),
    )
    op.create_index("ix_developer_api_key_app_id", "developer_api_key", ["app_id"])
    op.create_index("ix_developer_api_key_key_prefix", "developer_api_key", ["key_prefix"])
    op.create_index("ix_developer_api_key_status", "developer_api_key", ["status"])

    op.create_table(
        "developer_usage_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("app_id", sa.Integer(), nullable=False),
        sa.Column("api_key_id", sa.Integer(), nullable=True),
        sa.Column("endpoint", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("charged_calls", sa.Integer(), nullable=False),
        sa.Column("response_count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("request_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["app_id"], ["developer_app.id"]),
        sa.ForeignKeyConstraint(["api_key_id"], ["developer_api_key.id"]),
    )
    op.create_index("ix_developer_usage_log_request_id", "developer_usage_log", ["request_id"], unique=True)
    op.create_index("ix_developer_usage_log_app_id", "developer_usage_log", ["app_id"])
    op.create_index("ix_developer_usage_log_api_key_id", "developer_usage_log", ["api_key_id"])
    op.create_index("ix_developer_usage_log_endpoint", "developer_usage_log", ["endpoint"])
    op.create_index("ix_developer_usage_log_status", "developer_usage_log", ["status"])
    op.create_index("ix_developer_usage_log_created_at", "developer_usage_log", ["created_at"])


def downgrade() -> None:
    op.drop_table("developer_usage_log")
    op.drop_table("developer_api_key")
    op.drop_table("developer_app")
