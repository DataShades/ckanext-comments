from __future__ import annotations

import logging
from datetime import datetime
from typing import (
    Any,
    Callable,
    Literal,
    Optional,
    Union,
    cast,
    overload,
)
from werkzeug.utils import import_string

from sqlalchemy import Column, DateTime, Text
from sqlalchemy.orm import Query

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.model.types import make_uuid

from ckanext.comments.exceptions import UnsupportedSubjectType

from .base import Base

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

    id = Column(Text, primary_key=True, default=make_uuid)
    subject_id = Column(Text, nullable=False)
    subject_type = Column(Text, nullable=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return "Thread(" f"id={self.id!r}, " f"subject_type={self.subject_type!r}, " ")"

    def comments(self):
        from .comment import Comment

        return Comment.by_thread(cast(str, self.id))

    def get_subject(self) -> Optional[Subject]:
        return self.locate_subject(cast(str, self.subject_type), self.subject_id)

    @classmethod
    def locate_subject(cls, subject_type: str, subject_id: Any):
        option = tk.config.get(f"ckanext.comments.subject.{subject_type}_getter")
        getter = import_string(option, True) if option else None
        if not getter and subject_type in cls._subject_getters:
            getter = cls._subject_getters[subject_type]

        if not getter:
            raise UnsupportedSubjectType(subject_type)

        return getter(subject_id)

    @overload
    @classmethod
    def for_subject(
        cls, type_: str, id_: str, init_missing: Literal[False]
    ) -> Thread | None:
        ...

    @overload
    @classmethod
    def for_subject(cls, type_: str, id_: str, init_missing: Literal[True]) -> Thread:
        ...

    @classmethod
    def for_subject(
        cls, type_: str, id_: str, init_missing: bool = False
    ) -> Optional[Thread]:
        if subject := cls.locate_subject(type_, id_):
            id_ = str(subject.id)

        thread = (
            model.Session.query(cls)
            .filter(cls.subject_type == type_, cls.subject_id == id_)
            .one_or_none()
        )

        if thread is None and init_missing:
            thread = cls(subject_type=type_, subject_id=id_)
        return thread
