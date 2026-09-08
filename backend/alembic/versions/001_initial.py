"""initial migration

Revision ID: 001
Revises: None
Create Date: 2025-08-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), default="patient", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("disease", sa.String(50), nullable=False),
        sa.Column("input_type", sa.String(20), nullable=False, default="image"),
        sa.Column("input_text", sa.JSON(), nullable=True),
        sa.Column("input_image_path", sa.String(512), nullable=True),
        sa.Column("heatmap_path", sa.String(512), nullable=True),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("probabilities", sa.JSON(), nullable=True),
        sa.Column("explanation", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(100), nullable=False, default="demo"),
        sa.Column("is_demo", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("prediction_id", sa.Integer(), ForeignKey("predictions.id"), nullable=False, index=True),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("disease", sa.String(50), nullable=False, index=True),
        sa.Column("version", sa.String(100), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("model_versions")
    op.drop_table("reports")
    op.drop_table("predictions")
    op.drop_table("users")