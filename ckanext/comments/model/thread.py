from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Text

import ckan.model as model
import ckan.lib.dictization as d
from ckan.model.types import make_uuid


from .base import Base


if TYPE_CHECKING:
    from .comment import Comment


class Thread(Base):
    __tablename__ = "comments_threads"

    id: str = Column(Text, primary_key=True, default=make_uuid)
    subject_type: str = Column(Text, nullable=False)

    created_at: datetime = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    def __repr__(self):
        return (
            "Thread("
            f"id={self.id!r}, "
            f"subject_type={self.subject_type!r}, "
            ")"
        )

    def comments(self):
        from .comment import Comment

        return model.Session.query(Comment).filter(
            Comment.thread_id == self.id
        )

    def dictize(self, context):
        from .comment import Comment

        comments_dictized = None
        if context.get("include_comments"):
            comments = self.comments()

            approved_filter = Comment.state == Comment.State.approved
            if not context["user"]:
                comments = comments.filter(approved_filter)
            elif (
                not context.get("ignore_auth")
                and not context["auth_user_obj"].sysadmin
            ):
                comments = comments.filter(
                    approved_filter
                    | (
                        (Comment.author_type == "user")
                        & (Comment.author_id == context["auth_user_obj"].id)
                    )
                )
            dictize_context = dict(**context, active=False)
            comments_dictized = d.obj_list_dictize(
                comments, dictize_context, sort_key=lambda c: c["created_at"]
            )

        return d.table_dictize(self, context, comments=comments_dictized)
