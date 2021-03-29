from __future__ import annotations

import logging

from datetime import datetime
from typing import Callable, Optional, TYPE_CHECKING, Union, cast

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.orm import Query

import ckan.model as model

from ckan.model.types import make_uuid

from .base import Base
from ckanext.comments.exceptions import UnsupportedSubjectType

if TYPE_CHECKING:
    from .comment import Comment

log = logging.getLogger(__name__)

Subject = Union[model.Package, model.Resource, model.User, model.Group]
SubjectGetter = Callable[[str], Optional[Subject]]


class Thread(Base):
    __tablename__ = "comments_threads"
    _subject_getters: dict[str, SubjectGetter] = {
        "package": model.Package.get,
        "resource": model.Resource.get,
        "user": model.User.get,
        "group": model.Group.get,
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

    def comments(self) -> Query:
        from .comment import Comment

        return Comment.by_thread(self.id)

    def get_subject(self) -> Optional[Subject]:
        try:
            getter = self._subject_getters[self.subject_type]
        except KeyError:
            log.error("Unknown subject type: %s", self.subject_type)
            raise UnsupportedSubjectType(self.subject_type)
        return getter(self.subject_id)

    @classmethod
    def for_subject(
        cls, type_: str, id_: str, init_missing: bool = False
    ) -> Optional[Thread]:
        thread = cast(
            Optional[Thread],
            model.Session.query(cls)
            .filter(cls.subject_type == type_, cls.subject_id == id_)
            .one_or_none(),
        )
        if thread is None and init_missing:
            thread = cls(subject_type=type_, subject_id=id_)
        return thread
