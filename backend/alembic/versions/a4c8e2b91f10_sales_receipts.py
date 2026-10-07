"""sales receipts and conversation context

Revision ID: a4c8e2b91f10
Revises: 71e92f13169f
Create Date: 2026-10-07 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a4c8e2b91f10"
down_revision: Union[str, None] = "71e92f13169f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE conversation_state ADD VALUE IF NOT EXISTS 'RECORDING_SALE'")
        op.execute(
            "ALTER TYPE conversation_state ADD VALUE IF NOT EXISTS 'WAITING_RECEIPT_NAME'"
        )
        op.execute("ALTER TYPE message_type ADD VALUE IF NOT EXISTS 'DOCUMENT'")

    op.add_column(
        "conversations",
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "sales",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("store_id", sa.UUID(), nullable=False),
        sa.Column("public_code", sa.String(length=16), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("RECORDED", "CANCELLED", name="sale_status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sales_public_code"), "sales", ["public_code"], unique=False)
    op.create_index(op.f("ix_sales_store_id"), "sales", ["store_id"], unique=False)

    op.create_table(
        "sale_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sale_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sale_items_sale_id"), "sale_items", ["sale_id"], unique=False)

    op.create_table(
        "receipts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("store_id", sa.UUID(), nullable=False),
        sa.Column("sale_id", sa.UUID(), nullable=False),
        sa.Column("number", sa.String(length=32), nullable=False),
        sa.Column("verification_key", sa.String(length=64), nullable=False),
        sa.Column("customer_name", sa.String(length=120), nullable=True),
        sa.Column("pdf_path", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sale_id"),
    )
    op.create_index(op.f("ix_receipts_number"), "receipts", ["number"], unique=True)
    op.create_index(op.f("ix_receipts_store_id"), "receipts", ["store_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_receipts_store_id"), table_name="receipts")
    op.drop_index(op.f("ix_receipts_number"), table_name="receipts")
    op.drop_table("receipts")
    op.drop_index(op.f("ix_sale_items_sale_id"), table_name="sale_items")
    op.drop_table("sale_items")
    op.drop_index(op.f("ix_sales_store_id"), table_name="sales")
    op.drop_index(op.f("ix_sales_public_code"), table_name="sales")
    op.drop_table("sales")
    op.drop_column("conversations", "context")
    op.execute("DROP TYPE IF EXISTS sale_status")
