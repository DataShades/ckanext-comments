from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, remote, foreign

import ckan.model as model
import ckan.lib.dictization as d
from ckan.model.types import make_uuid

from .base import Base
from . import Thread


class Comment(Base):
    __tablename__ = "comments_comments"

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

    thread: Thread = relationship(Thread)

    user: Optional[model.User] = relationship(
        model.User,
        backref="comments",
        primaryjoin=(author_type == "user")
        & (model.User.id == foreign(author_id)),
    )

    reply_to: Optional[Comment] = relationship(
        "Comment", primaryjoin=id == reply_to_id
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

    def approve(self) -> None:
        self.state = self.State.approved

    def is_approved(self) -> bool:
        return self.state == self.State.approved

    def is_authored_by(self, name: str) -> bool:
        if self.user:
            return name == self.user.name or name == self.user.id
        return False

    def dictize(self, context):
        return d.table_dictize(self, context.copy())
