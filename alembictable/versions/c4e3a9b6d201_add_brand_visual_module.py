"""add brand visual module

Revision ID: c4e3a9b6d201
Revises: 8b312c54e9a1
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e3a9b6d201"
down_revision: Union[str, None] = "8b312c54e9a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brand_project",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("selected_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("name_reference", sa.Text(), nullable=True),
        sa.Column("name_moral", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=False),
        sa.Column("audience", sa.String(length=200), nullable=True),
        sa.Column("style", sa.String(length=100), nullable=False),
        sa.Column("color_preference", sa.String(length=100), nullable=True),
        sa.Column("brand_brief", sa.Text(), nullable=True),
        sa.Column("visual_keywords", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_brand_project_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brand_project")),
    )
    op.create_index(op.f("ix_brand_project_user_id"), "brand_project", ["user_id"], unique=False)

    op.create_table(
        "brand_slogan",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(length=200), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("is_selected", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["brand_project.id"], name=op.f("fk_brand_slogan_project_id_brand_project")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brand_slogan")),
    )
    op.create_index(op.f("ix_brand_slogan_project_id"), "brand_slogan", ["project_id"], unique=False)

    op.create_table(
        "visual_generation_job",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requested_count", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["brand_project.id"], name=op.f("fk_visual_generation_job_project_id_brand_project")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visual_generation_job")),
    )
    op.create_index(op.f("ix_visual_generation_job_project_id"), "visual_generation_job", ["project_id"], unique=False)
    op.create_index(op.f("ix_visual_generation_job_status"), "visual_generation_job", ["status"], unique=False)

    op.create_table(
        "visual_asset",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(length=30), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["brand_project.id"], name=op.f("fk_visual_asset_project_id_brand_project")),
        sa.ForeignKeyConstraint(["job_id"], ["visual_generation_job.id"], name=op.f("fk_visual_asset_job_id_visual_generation_job")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visual_asset")),
    )
    op.create_index(op.f("ix_visual_asset_project_id"), "visual_asset", ["project_id"], unique=False)
    op.create_index(op.f("ix_visual_asset_job_id"), "visual_asset", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_visual_asset_job_id"), table_name="visual_asset")
    op.drop_index(op.f("ix_visual_asset_project_id"), table_name="visual_asset")
    op.drop_table("visual_asset")
    op.drop_index(op.f("ix_visual_generation_job_status"), table_name="visual_generation_job")
    op.drop_index(op.f("ix_visual_generation_job_project_id"), table_name="visual_generation_job")
    op.drop_table("visual_generation_job")
    op.drop_index(op.f("ix_brand_slogan_project_id"), table_name="brand_slogan")
    op.drop_table("brand_slogan")
    op.drop_index(op.f("ix_brand_project_user_id"), table_name="brand_project")
    op.drop_table("brand_project")
