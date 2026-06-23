"""add membership community and expert modules

Revision ID: d7f2b19a4c31
Revises: c4e3a9b6d201
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7f2b19a4c31"
down_revision: Union[str, None] = "c4e3a9b6d201"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("is_expert", sa.Boolean(), server_default=sa.text("0"), nullable=False))

    op.create_table("user_profile",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("avatar_url", sa.String(500)), sa.Column("bio", sa.String(500)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("user_id", name="uq_user_profile_user_id"))
    op.create_index("ix_user_profile_user_id", "user_profile", ["user_id"], unique=True)

    op.create_table("vip_plan",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(50), nullable=False), sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("daily_name_limit", sa.Integer(), nullable=False),
        sa.Column("daily_visual_limit", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.UniqueConstraint("code", name="uq_vip_plan_code"))
    plans = sa.table("vip_plan", sa.column("code"), sa.column("name"), sa.column("description"),
                     sa.column("price_cents"), sa.column("duration_days"),
                     sa.column("daily_name_limit"), sa.column("daily_visual_limit"), sa.column("is_active"))
    op.bulk_insert(plans, [
        {"code": "vip_monthly", "name": "月度 VIP", "description": "更多起名与品牌视觉额度，专家服务九折",
         "price_cents": 1990, "duration_days": 30, "daily_name_limit": 100, "daily_visual_limit": 20, "is_active": True},
        {"code": "vip_yearly", "name": "年度 VIP", "description": "全年高额度服务与专家服务九折",
         "price_cents": 19900, "duration_days": 365, "daily_name_limit": 300, "daily_visual_limit": 50, "is_active": True},
    ])

    op.create_table("user_subscription",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]), sa.ForeignKeyConstraint(["plan_id"], ["vip_plan.id"]))
    op.create_index("ix_user_subscription_user_id", "user_subscription", ["user_id"])
    op.create_index("ix_user_subscription_status", "user_subscription", ["status"])
    op.create_index("ix_user_subscription_expires_at", "user_subscription", ["expires_at"])

    op.create_table("vip_order",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_no", sa.String(64), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False), sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("payment_provider", sa.String(30), nullable=False),
        sa.Column("paid_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]), sa.ForeignKeyConstraint(["plan_id"], ["vip_plan.id"]),
        sa.UniqueConstraint("order_no", name="uq_vip_order_order_no"))
    op.create_index("ix_vip_order_order_no", "vip_order", ["order_no"], unique=True)
    op.create_index("ix_vip_order_user_id", "vip_order", ["user_id"])
    op.create_index("ix_vip_order_status", "vip_order", ["status"])

    op.create_table("usage_counter",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False), sa.Column("used_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("user_id", "usage_date", "action", name="uq_usage_user_date_action"))
    op.create_index("ix_usage_counter_user_id", "usage_counter", ["user_id"])

    op.create_table("community_post",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("post_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False), sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("like_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("comment_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("vote_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]))
    for name, columns in [("ix_community_post_user_id", ["user_id"]), ("ix_community_post_post_type", ["post_type"]),
                          ("ix_community_post_status", ["status"]), ("ix_community_post_created_at", ["created_at"])]:
        op.create_index(name, "community_post", columns)

    op.create_table("community_comment",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["community_post.id"]), sa.ForeignKeyConstraint(["user_id"], ["user.id"]))
    op.create_index("ix_community_comment_post_id", "community_comment", ["post_id"])
    op.create_index("ix_community_comment_user_id", "community_comment", ["user_id"])

    op.create_table("community_like",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["community_post.id"]), sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("post_id", "user_id", name="uq_community_like_post_user"))
    op.create_index("ix_community_like_post_id", "community_like", ["post_id"])
    op.create_index("ix_community_like_user_id", "community_like", ["user_id"])

    op.create_table("name_poll_option",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), nullable=False), sa.Column("name", sa.String(100), nullable=False),
        sa.Column("moral", sa.Text()), sa.Column("vote_count", sa.Integer(), server_default="0", nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["community_post.id"]))
    op.create_index("ix_name_poll_option_post_id", "name_poll_option", ["post_id"])

    op.create_table("name_poll_vote",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("post_id", sa.Integer(), nullable=False), sa.Column("option_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["community_post.id"]), sa.ForeignKeyConstraint(["option_id"], ["name_poll_option.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("post_id", "user_id", name="uq_name_poll_vote_post_user"))
    op.create_index("ix_name_poll_vote_post_id", "name_poll_vote", ["post_id"])
    op.create_index("ix_name_poll_vote_option_id", "name_poll_vote", ["option_id"])
    op.create_index("ix_name_poll_vote_user_id", "name_poll_vote", ["user_id"])

    op.create_table("expert_profile",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False), sa.Column("title", sa.String(100), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False), sa.Column("avatar_url", sa.String(500)),
        sa.Column("is_verified", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("accepting_orders", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]), sa.UniqueConstraint("user_id", name="uq_expert_profile_user_id"))
    op.create_index("ix_expert_profile_user_id", "expert_profile", ["user_id"], unique=True)
    op.create_index("ix_expert_profile_category", "expert_profile", ["category"])

    op.create_table("expert_service",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("expert_id", sa.Integer(), nullable=False), sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("delivery_days", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["expert_id"], ["expert_profile.id"]))
    op.create_index("ix_expert_service_expert_id", "expert_service", ["expert_id"])

    op.create_table("expert_order",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_no", sa.String(64), nullable=False), sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=False), sa.Column("expert_id", sa.Integer(), nullable=False),
        sa.Column("selected_name", sa.String(100), nullable=False), sa.Column("requirements", sa.Text(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("ai_draft", sa.Text()), sa.Column("final_report", sa.Text()),
        sa.Column("paid_at", sa.DateTime()), sa.Column("delivered_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]), sa.ForeignKeyConstraint(["service_id"], ["expert_service.id"]),
        sa.ForeignKeyConstraint(["expert_id"], ["expert_profile.id"]),
        sa.UniqueConstraint("order_no", name="uq_expert_order_order_no"))
    for name, columns in [("ix_expert_order_order_no", ["order_no"]), ("ix_expert_order_user_id", ["user_id"]),
                          ("ix_expert_order_service_id", ["service_id"]), ("ix_expert_order_expert_id", ["expert_id"]),
                          ("ix_expert_order_status", ["status"])]:
        op.create_index(name, "expert_order", columns, unique=name.endswith("order_no"))


def downgrade() -> None:
    for table in ["expert_order", "expert_service", "expert_profile", "name_poll_vote", "name_poll_option",
                  "community_like", "community_comment", "community_post", "usage_counter", "vip_order",
                  "user_subscription", "vip_plan", "user_profile"]:
        op.drop_table(table)
    op.drop_column("user", "is_expert")
