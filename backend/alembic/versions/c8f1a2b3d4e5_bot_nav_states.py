"""bot navigation states for language and delete flows

Revision ID: c8f1a2b3d4e5
Revises: a4c8e2b91f10
Create Date: 2026-10-08
"""

from alembic import op

revision = "c8f1a2b3d4e5"
down_revision = "a4c8e2b91f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE conversation_state ADD VALUE IF NOT EXISTS 'CHOOSING_LANGUAGE'"
    )
    op.execute(
        "ALTER TYPE conversation_state ADD VALUE IF NOT EXISTS 'DELETING_PRODUCT'"
    )
    op.execute(
        "ALTER TYPE conversation_state ADD VALUE IF NOT EXISTS 'CONFIRMING_DELETE'"
    )


def downgrade() -> None:
    # Postgres cannot easily remove enum values; leave them in place.
    pass
