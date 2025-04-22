from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Text, Boolean, or_, func, case
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import foreign, relationship

import ckan.model as model
from ckan.model.types import make_uuid

from ckanext.comments.exceptions import UnsupportedAuthorType

from . import Thread
from .base import Base
from ckan.model.meta import Session


foreign: Any = foreign
log = logging.getLogger(__name__)

Author = model.User
AuthorGetter = Callable[[str], Optional[Author]]


class Comment(Base):
    __tablename__ = "comments_comments"
    _author_getters: dict[str, AuthorGetter] = {"user": model.User.get}

    class State:
        draft = "draft"
        approved = "approved"
        rejected = "rejected"

    id = Column(Text, primary_key=True, default=make_uuid)

    thread_id = Column(Text, ForeignKey(Thread.id), nullable=False)

    content = Column(Text, nullable=False)

    author_id = Column(Text, nullable=False)
    author_type = Column(Text, nullable=False)

    state = Column(Text, nullable=False, default=State.draft)
    
    pinned = Column(Boolean, nullable=True, default=False)
    hidden = Column(Boolean, nullable=True, default=False)

    anonymous = Column(Boolean, nullable=True, default=False)

    reply_to_id = Column(Text, ForeignKey(id), nullable=True, index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    modified_at = Column(DateTime, nullable=True)

    extras = Column(JSONB, nullable=False, default=dict)

    thread: Any = relationship(Thread, single_parent=True)

    user: Any = relationship(
        model.User,
        backref="comments",
        primaryjoin=(author_type == "user") & (model.User.id == foreign(author_id)),
        single_parent=True,
    )

    reply_to: Any = relationship(
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
    def by_thread(cls, thread_id: str):
        return (
            model.Session.query(cls)
            .filter(cls.thread_id == thread_id)
            .order_by(cls.created_at)
        )

    def approve(self) -> None:
        self.state = self.State.approved


    def is_approved(self) -> bool:
        return self.state == self.State.approved  # type: ignore


    def is_hidden(self) -> bool:
        return self.hidden
    
    def is_pinned(self) -> bool:
        return self.pinned

    def is_authored_by(self, name: str) -> bool:
        if self.user:
            return name == self.user.name or name == self.user.id
        return False

    def get_author(self) -> Optional[Author]:
        try:
            getter = self._author_getters[self.author_type]  # type: ignore
        except KeyError:
            log.error("Unknown subject type: %s", self.author_type)
            raise UnsupportedAuthorType(self.author_type)
        return getter(self.author_id)  # type: ignore

    def patch_comment(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


    @classmethod
    def advance_filter(cls, **kwargs):
        query = Session.query(cls)
        

        query = cls.filter_by_search_query(query, kwargs.pop('q', ''))
        
        query = cls.filter_by_date(query, after_date=kwargs.pop('after_date', None))
        
        query = cls.filter_by_state(query, state=kwargs.pop('state', None))
        query = cls.filter_by_organization(
            query,
            organization_id=kwargs.pop('organization_id', None)
        )

        query = cls.filter_by_author_id(query, kwargs.pop('author_id', None))
        

        sort_fields = kwargs.pop('sort', 'created_at asc').split()
        sort_field = sort_fields[0]
        sort_order = sort_fields[1]
        
        
        # if kwargs:
        #     query = query.filter_by(**kwargs)
        
        
        if sort_field:
            if hasattr(cls, sort_field):
                if sort_order == 'desc':
                    query = query.order_by(getattr(cls, sort_field).desc())
                else:
                    query = query.order_by(getattr(cls, sort_field).asc())
        
        return query

    @classmethod
    def filter_by_search_query(cls, query, search_query):
        search_terms = search_query.split()
        
        if search_terms:
            content_conditions = [cls.content.ilike(f'%{word}%') for word in search_terms]

            combined_conditions = or_(
                *content_conditions, 
                )
            query = query.filter(combined_conditions)
        
        return query

    @classmethod
    def filter_by_date(cls, query, after_date = None):
        if after_date:
            date_filer = Comment.created_at >= after_date
            query = query.filter(date_filer)

        return query

    
    @classmethod
    def filter_by_organization(cls, query, organization_id):
        if organization_id:
            query = query.join(Thread, Thread.id == cls.thread_id) \
                .join(model.Package, model.Package.id == Thread.subject_id) \
                .filter(model.Package.owner_org == organization_id)
        
        return query
    
    @classmethod
    def filter_by_state(cls, query, state=None):
        if state:
            query = query.filter(cls.state == state)
        
        return query
    
    @classmethod
    def filter_by_author_id(cls, query, author_id=None):
        if author_id:
            query = query.filter(cls.author_id == author_id)
        
        return query
    
  
    @classmethod
    def generate_statistics(cls, organization_id=None, author_id=None):
        session = Session()
        
        # Base query
        query = session.query(cls)

        if author_id:
            query = query.filter(cls.author_id == author_id)

        if organization_id:
            query = cls.filter_by_organization(
                    query,
                    organization_id=organization_id
                )
        
        total_count = query.count()
        
        # Breakdown by state
        status_breakdown = query.with_entities(
            cls.state, func.count(cls.id)
        ).group_by(cls.state).all()
        
        status_dict = {state: count for state, count in status_breakdown}


        # Breakdown by hidden
        hide_breakdown = query.with_entities(
            cls.hidden, func.count(cls.id)
        ).group_by(cls.hidden).all()
        
        hide_dict = {hidden: count for hidden, count in hide_breakdown}


        # Breakdown by pinned
        pin_breakdown = query.with_entities(
            cls.pinned, func.count(cls.id)
        ).group_by(cls.pinned).all()
        
        pin_dict = {pinned: count for pinned, count in pin_breakdown}
        

        # Breakdown by Packages

        with_comments = Session.query(model.Package) \
            .filter(model.Package.type == 'dataset')\
            .filter(model.Package.state == 'active')\
            .join(Thread, (Thread.subject_id == model.Package.id) & (Thread.subject_type == 'package')) \
            .join(Comment, Thread.id == Comment.thread_id) \
            .distinct().count()
        
        no_comments = Session.query(model.Package) \
            .filter(model.Package.type == 'dataset')\
            .filter(model.Package.state == 'active')\
            .outerjoin(Thread, (Thread.subject_id == model.Package.id) & (Thread.subject_type == 'package')) \
            .outerjoin(Comment, Thread.id == Comment.thread_id) \
            .filter(Comment.id == None) \
            .count()
        
        package_comment_breakdown = {
            'no_comments': no_comments,
            'with_comments': with_comments
        }

        statistics = {
            'total': total_count,
            'state_breakdown': status_dict,
            'hide_breakdown': hide_dict,
            'pin_breakdown': pin_dict,
            'package_comment_breakdown': package_comment_breakdown
        }
        
        return statistics
    
