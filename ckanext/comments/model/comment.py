from __future__ import annotations

import logging

from datetime import datetime
from typing import Any, Callable, Optional, Union, cast

from sqlalchemy import Column, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, foreign, Query, joinedload

import ckan.model as model

import ckan.plugins.toolkit as tk
from ckan.model.types import make_uuid

from .base import Base
from .dictize import get_dictizer
from . import Thread
from ckanext.comments.exceptions import UnsupportedAuthorType


log = logging.getLogger(__name__)

Author = Union[model.User]
AuthorGetter = Callable[[str], Optional[Author]]


class Comment(Base):
    __tablename__ = "comments_comments"
    _author_getters: dict[str, AuthorGetter] = {"user": model.User.get}

    class State:
        draft = "draft"
        approved = "approved"

    id: str = Column(Text, primary_key=True, default=make_uuid)

    thread_id: str = Column(Text, ForeignKey(Thread.id), nullable=False)

    content: str = Column(Text, nullable=False)

    author_id: str = Column(Text, nullable=False)
    author_type: str = Column(Text, nullable=False)

    state: str = Column(Text, nullable=False, default=State.draft)

    reply_to_id: Optional[str] = Column(
        Text, ForeignKey(id), nullable=True, index=True
    )

    created_at: datetime = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    modified_at: Optional[datetime] = Column(DateTime, nullable=True)

    thread: Thread = relationship(
        Thread, single_parent=True, cascade="all, delete-orphan"
    )

    user: Optional[model.User] = relationship(
        model.User,
        backref="comments",
        primaryjoin=(author_type == "user")
        & (model.User.id == foreign(author_id)),
        single_parent=True,
        cascade="all, delete-orphan",
    )

    reply_to: Optional[Comment] = relationship(
        "Comment", primaryjoin=id == reply_to_id, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            "Comment("
            f"id={self.id!r},"
            f"thread_id={self.thread_id!r},"
            f"author_id={self.author_id!r},"
            f"author_type={self.author_type!r},"
            f"reply_to_id={self.reply_to_id!r},"
            ")"
        )

    @classmethod
    def by_thread(cls, thread_id) -> Query:
        query: Query = (
            model.Session.query(cls)
            .filter(cls.thread_id == thread_id)
            .order_by(cls.created_at)
        )
        return query

    def approve(self) -> None:
        self.state = self.State.approved

    def is_approved(self) -> bool:
        return self.state == self.State.approved

    def is_authored_by(self, name: str) -> bool:
        if self.user:
            return name == self.user.name or name == self.user.id
        return False

    def dictize(self, context: dict[str, Any]) -> dict[str, Any]:
        extra: dict[str, Any] = {"approved": self.is_approved()}

        if context.get("include_author"):
            author = self.get_author()
            if author:
                extra["author"] = get_dictizer(type(author))(
                    author, context.copy()
                )
            else:
                log.error("Missing author for comment: %s", self)
                extra["author"] = None
        return get_dictizer(type(self))(self, context.copy(), **extra)

    @classmethod
    def dictize_thread(
        cls, id_: str, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        query = cls.by_thread(id_)
        include_author = tk.asbool(context.get("include_author"))

        # let's make it a bit more efficient
        if include_author:
            query = cast(Query, query.options(joinedload(cls.user)))

        approved_filter = cls.state == cls.State.approved
        user = model.User.get(context["user"])

        if context.get("ignore_auth"):
            pass
        elif user is None:
            query = cast(Query, query.filter(approved_filter))
        elif not user.sysadmin:
            own_filter = (cls.author_type == "user") & (
                cls.author_id == user.id
            )
            query = cast(Query, query.filter(approved_filter | own_filter))

        result_list = []

        for comment in query:
            assert isinstance(comment, cls)
            dictized = get_dictizer(cls)(comment, context)
            dictized["approved"] = comment.is_approved()
            if include_author:
                author = comment.user
                dictized["author"] = author and get_dictizer(type(author))(
                    author, context
                )
            result_list.append(dictized)

        return result_list

    def get_author(self) -> Optional[Author]:
        try:
            getter = self._author_getters[self.author_type]
        except KeyError:
            log.error("Unknown subject type: %s", self.author_type)
            raise UnsupportedAuthorType(self.author_type)
        return getter(self.author_id)
