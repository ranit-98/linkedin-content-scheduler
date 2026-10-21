"""Add optional image data to scheduled posts."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20261021_0002"
down_revision: str | None = "20261020_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("scheduled_posts", sa.Column("image_data", sa.LargeBinary(), nullable=True))
    op.add_column(
        "scheduled_posts", sa.Column("image_content_type", sa.String(length=50), nullable=True)
    )
    op.add_column(
        "scheduled_posts", sa.Column("image_filename", sa.String(length=255), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("scheduled_posts", "image_filename")
    op.drop_column("scheduled_posts", "image_content_type")
    op.drop_column("scheduled_posts", "image_data")
