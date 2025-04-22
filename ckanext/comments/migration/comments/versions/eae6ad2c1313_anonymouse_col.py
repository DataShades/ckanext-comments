"""anonymouse_col

Revision ID: eae6ad2c1313
Revises: efe4bb692273
Create Date: 2025-02-02 22:50:24.549561

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eae6ad2c1313'
down_revision = 'efe4bb692273'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comments_comments",
        sa.Column("anonymous", sa.Boolean, nullable=True, default=False),
    )


def downgrade():
    op.drop_column("comments_comments", "anonymous")
