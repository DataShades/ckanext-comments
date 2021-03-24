from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Text

from .base import Base

from ckan.model.types import make_uuid

if TYPE_CHECKING:
    from .comment import Comment


class Thread(Base):
    __tablename__ = "comments_threads"

    id: str = Column(Text, primary_key=True, default=make_uuid)
    object_id: str = Column(Text, nullable=False)
    object_type: str = Column(Text, nullable=False)

    created_at: datetime = Column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    comments: list[Comment]

    def __repr__(self):
        return (
            "Thread("
            f"id={self.id!r}, "
            f"object_type={self.object_type!r}, "
            f"object_id={self.object_id!r}"
            ")"
        )
