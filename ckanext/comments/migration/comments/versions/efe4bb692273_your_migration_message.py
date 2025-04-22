"""Your migration message

Revision ID: efe4bb692273
Revises: acd1862c2e17
Create Date: 2024-09-02 15:33:16.559279

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'efe4bb692273'
down_revision = 'acd1862c2e17'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comments_comments",
        sa.Column("pinned", sa.Boolean, nullable=True, default=False),
    )
    op.add_column(
        "comments_comments",
        sa.Column("hidden", sa.Boolean, nullable=True, default=False),
    )


def downgrade():
    op.drop_column("comments_comments", "pinned")
    op.drop_column("comments_comments", "hidden")
