"""add payment transaction table

Revision ID: b8f4c2d91a7e
Revises: f2b6c9a1d034
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8f4c2d91a7e"
down_revision: Union[str, None] = "f2b6c9a1d034"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_transaction",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("out_trade_no", sa.String(64), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("business_type", sa.String(30), nullable=False),
        sa.Column("business_order_id", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(256), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("alipay_trade_no", sa.String(128), nullable=True),
        sa.Column("raw_notify", sa.Text(), nullable=True),
        sa.Column("notified_at", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("business_type", "business_order_id", name="uq_payment_business_order"),
        sa.UniqueConstraint("out_trade_no", name="uq_payment_transaction_out_trade_no"),
    )
    op.create_index("ix_payment_transaction_out_trade_no", "payment_transaction", ["out_trade_no"])
    op.create_index("ix_payment_transaction_provider", "payment_transaction", ["provider"])
    op.create_index("ix_payment_transaction_business_type", "payment_transaction", ["business_type"])
    op.create_index("ix_payment_transaction_business_order_id", "payment_transaction", ["business_order_id"])
    op.create_index("ix_payment_transaction_status", "payment_transaction", ["status"])
    op.create_index("ix_payment_transaction_alipay_trade_no", "payment_transaction", ["alipay_trade_no"])


def downgrade() -> None:
    op.drop_index("ix_payment_transaction_alipay_trade_no", table_name="payment_transaction")
    op.drop_index("ix_payment_transaction_status", table_name="payment_transaction")
    op.drop_index("ix_payment_transaction_business_order_id", table_name="payment_transaction")
    op.drop_index("ix_payment_transaction_business_type", table_name="payment_transaction")
    op.drop_index("ix_payment_transaction_provider", table_name="payment_transaction")
    op.drop_index("ix_payment_transaction_out_trade_no", table_name="payment_transaction")
    op.drop_table("payment_transaction")
