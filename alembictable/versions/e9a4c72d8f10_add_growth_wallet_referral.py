"""add growth wallet referral and partner distribution

Revision ID: e9a4c72d8f10
Revises: d7f2b19a4c31
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "e9a4c72d8f10"
down_revision: Union[str, None] = "d7f2b19a4c31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("wallet_account",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("available_cents", sa.Integer(), server_default="0", nullable=False), sa.Column("frozen_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("pending_cents", sa.Integer(), server_default="0", nullable=False), sa.Column("total_earned_cents", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_withdrawn_cents", sa.Integer(), server_default="0", nullable=False), sa.Column("bonus_ai_credits", sa.Integer(), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"],["user.id"]),
        sa.UniqueConstraint("user_id", name="uq_wallet_account_user_id"))
    op.create_index("ix_wallet_account_user_id", "wallet_account", ["user_id"], unique=True)

    op.create_table("wallet_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("entry_type", sa.String(50), nullable=False), sa.Column("available_delta", sa.Integer(), nullable=False),
        sa.Column("frozen_delta", sa.Integer(), nullable=False), sa.Column("pending_delta", sa.Integer(), nullable=False), sa.Column("bonus_delta", sa.Integer(), nullable=False),
        sa.Column("available_after", sa.Integer(), nullable=False), sa.Column("frozen_after", sa.Integer(), nullable=False),
        sa.Column("pending_after", sa.Integer(), nullable=False), sa.Column("bonus_after", sa.Integer(), nullable=False),
        sa.Column("reference_type", sa.String(50)), sa.Column("reference_id", sa.Integer()),
        sa.Column("idempotency_key", sa.String(120), nullable=False), sa.Column("description", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"],["user.id"]),
        sa.UniqueConstraint("idempotency_key", name="uq_wallet_ledger_idempotency_key"))
    op.create_index("ix_wallet_ledger_user_id", "wallet_ledger", ["user_id"]); op.create_index("ix_wallet_ledger_entry_type", "wallet_ledger", ["entry_type"])
    op.create_index("ix_wallet_ledger_idempotency_key", "wallet_ledger", ["idempotency_key"], unique=True); op.create_index("ix_wallet_ledger_created_at", "wallet_ledger", ["created_at"])

    op.create_table("recharge_order",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("order_no", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("paid_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"],["user.id"]), sa.UniqueConstraint("order_no", name="uq_recharge_order_order_no"))
    op.create_index("ix_recharge_order_order_no", "recharge_order", ["order_no"], unique=True); op.create_index("ix_recharge_order_user_id", "recharge_order", ["user_id"]); op.create_index("ix_recharge_order_status", "recharge_order", ["status"])

    op.create_table("withdrawal_request",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("request_no", sa.String(64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(30), nullable=False), sa.Column("destination", sa.String(300), nullable=False),
        sa.Column("account_name", sa.String(100), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("review_note", sa.String(500)), sa.Column("reviewed_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"],["user.id"]),
        sa.UniqueConstraint("request_no", name="uq_withdrawal_request_request_no"))
    op.create_index("ix_withdrawal_request_request_no", "withdrawal_request", ["request_no"], unique=True); op.create_index("ix_withdrawal_request_user_id", "withdrawal_request", ["user_id"]); op.create_index("ix_withdrawal_request_status", "withdrawal_request", ["status"])

    op.create_table("referral_code",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(32), nullable=False), sa.Column("qr_file_url", sa.String(500)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"],["user.id"]),
        sa.UniqueConstraint("user_id", name="uq_referral_code_user_id"), sa.UniqueConstraint("code", name="uq_referral_code_code"))
    op.create_index("ix_referral_code_user_id", "referral_code", ["user_id"], unique=True); op.create_index("ix_referral_code_code", "referral_code", ["code"], unique=True)

    op.create_table("referral_relation",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("inviter_user_id", sa.Integer(), nullable=False),
        sa.Column("invitee_user_id", sa.Integer(), nullable=False), sa.Column("referral_code_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["inviter_user_id"],["user.id"]), sa.ForeignKeyConstraint(["invitee_user_id"],["user.id"]),
        sa.ForeignKeyConstraint(["referral_code_id"],["referral_code.id"]), sa.UniqueConstraint("invitee_user_id", name="uq_referral_relation_invitee_user_id"))
    op.create_index("ix_referral_relation_inviter_user_id", "referral_relation", ["inviter_user_id"]); op.create_index("ix_referral_relation_invitee_user_id", "referral_relation", ["invitee_user_id"], unique=True)

    op.create_table("partner_profile",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("business_type", sa.String(100), nullable=False), sa.Column("business_name", sa.String(200), nullable=False),
        sa.Column("contact_info", sa.String(200), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("commission_bps", sa.Integer(), nullable=False), sa.Column("review_note", sa.String(500)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"],["user.id"]),
        sa.UniqueConstraint("user_id", name="uq_partner_profile_user_id"))
    op.create_index("ix_partner_profile_user_id", "partner_profile", ["user_id"], unique=True); op.create_index("ix_partner_profile_status", "partner_profile", ["status"])

    op.create_table("commission_record",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("beneficiary_user_id", sa.Integer(), nullable=False),
        sa.Column("source_user_id", sa.Integer()), sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("source_order_id", sa.Integer(), nullable=False), sa.Column("commission_type", sa.String(30), nullable=False),
        sa.Column("gross_amount_cents", sa.Integer(), nullable=False), sa.Column("platform_fee_cents", sa.Integer(), nullable=False),
        sa.Column("commission_cents", sa.Integer(), nullable=False), sa.Column("status", sa.String(30), nullable=False),
        sa.Column("settled_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["beneficiary_user_id"],["user.id"]), sa.ForeignKeyConstraint(["source_user_id"],["user.id"]),
        sa.UniqueConstraint("beneficiary_user_id","source_type","source_order_id","commission_type",name="uq_commission_source"))
    op.create_index("ix_commission_record_beneficiary_user_id", "commission_record", ["beneficiary_user_id"]); op.create_index("ix_commission_record_status", "commission_record", ["status"])


def downgrade() -> None:
    for table in ["commission_record","partner_profile","referral_relation","referral_code","withdrawal_request","recharge_order","wallet_ledger","wallet_account"]:
        op.drop_table(table)
