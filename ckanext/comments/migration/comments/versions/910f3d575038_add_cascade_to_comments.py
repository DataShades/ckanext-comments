"""add cascade to comments

Revision ID: 910f3d575038
Revises: 275515c51af1
Create Date: 2023-10-06 22:54:18.933232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "910f3d575038"
down_revision = "275515c51af1"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("comments_comments_thread_id_fkey", "comments_comments")
    op.drop_constraint("comments_comments_reply_to_id_fkey", "comments_comments")

    op.create_foreign_key(
        "comments_comments_thread_id_fkey",
        "comments_comments",
        "comments_threads",
        ["thread_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "comments_comments_reply_to_id_fkey",
        "comments_comments",
        "comments_comments",
        ["reply_to_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    pass
