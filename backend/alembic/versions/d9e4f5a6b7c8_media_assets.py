"""persist product media bytes in postgres

Revision ID: d9e4f5a6b7c8
Revises: c8f1a2b3d4e5
Create Date: 2026-10-09
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "d9e4f5a6b7c8"
down_revision = "c8f1a2b3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("kind", "filename", name="uq_media_assets_kind_filename"),
    )
    op.create_index("ix_media_assets_filename", "media_assets", ["filename"])


def downgrade() -> None:
    op.drop_index("ix_media_assets_filename", table_name="media_assets")
    op.drop_table("media_assets")
