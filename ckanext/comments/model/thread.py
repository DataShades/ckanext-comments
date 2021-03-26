from __future__ import annotations

import logging

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Column, DateTime, Text

import ckan.model as model
import ckan.lib.dictization as d
from ckan.model.types import make_uuid


from .base import Base
from ckanext.comments.exceptions import UnsupportedSubjectType

if TYPE_CHECKING:
    from .comment import Comment

log = logging.getLogger(__name__)

class Thread(Base):
    __tablename__ = "comments_threads"
    _subject_getters = {
        'package': model.Package.get,
        'resource': model.Resource.get,
        'user': model.User.get,
        'group': model.Group.get,
    }

    id: str = Column(Text, primary_key=True, default=make_uuid)
    subject_id: str = Column(Text, nullable=False)
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

    def get_subject(self):
        try:
            getter = self._subject_getters[self.subject_type]
        except KeyError:
            log.error('Unknown subject type: %s', self.subject_type)
            raise UnsupportedSubjectType(self.subject_type)
        return getter(self.subject_id)

    @classmethod
    def for_subject(cls, type_, id_, init_missing=False) -> Optional[Thread]:
        thread = model.Session.query(cls).filter(
            cls.subject_type==type_,
            cls.subject_id==id_
        ).one_or_none()
        if thread is None and init_missing:
            thread = cls(subject_type=type_, subject_id=id_)
        return thread

    def dictize(self, context:dict)->dict:
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
