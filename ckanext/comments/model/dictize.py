from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

from sqlalchemy import and_
from sqlalchemy.orm import joinedload

import ckan.lib.dictization as d
import ckan.lib.dictization.model_dictize as md
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.comments.model import Comment, Thread

from ..utils import is_moderator

if TYPE_CHECKING:
    from typing import TypedDict

    class CommentDict(TypedDict):
        id: str
        reply_to_id: str
        replies: Optional[list[CommentDict]]


_dictizers: dict[type, Callable[..., dict[str, Any]]] = defaultdict(
    lambda: d.table_dictize
)

log = logging.getLogger(__name__)


def get_dictizer(type_: type):
    return _dictizers[type_]


def register_dictizer(type_: type, func: Any):
    _dictizers[type_] = func


def combine_comments(comments: list["CommentDict"]):
    replies: dict[Optional[str], list["CommentDict"]] = {None: []}
    for comment in comments:
        comment["replies"] = replies.setdefault(comment["id"], [])
        reply_to = comment["reply_to_id"]
        replies.setdefault(reply_to, []).append(comment)
    return replies[None]


def thread_dictize(obj: Thread, context: Any) -> dict[str, Any]:
    comments_dictized = None

    if context.get("include_comments"):
        query = Comment.by_thread(cast(str, obj.id))

        # Handle sorting based on pinned_first and newest_first
        order_clauses = []
        if context.get("pinned_first"):
            order_clauses.append(Comment.pinned.desc())
        if context.get("newest_first"):
            order_clauses.append(Comment.created_at.desc())
        else:
            order_clauses.append(Comment.created_at.asc())

        # Apply the order_by clauses if there are any
        if order_clauses:
            query = query.order_by(None).order_by(*order_clauses)
        
        include_author = tk.asbool(context.get("include_author"))
        after_date = context.get("after_date")

        # let's make it a bit more efficient
        if include_author:
            query = query.options(joinedload(Comment.user))

        approved_filter = and_(
            Comment.state.in_([Comment.State.approved]),
            Comment.hidden != True
        )
        user = model.User.get(context["user"])

        if context.get("ignore_auth"):
            pass
        elif user is None:
            query = query.filter(approved_filter)
        elif not is_moderator(user, None, obj):
            own_filter = (Comment.author_type == "user") & (
                Comment.author_id == user.id
            )
            query = query.filter(approved_filter | own_filter)  # type: ignore

        if after_date:
            date_filer = Comment.created_at >= after_date
            query = query.filter(date_filer)

        comments_dictized = []

        for comment in query:
            assert isinstance(comment, Comment)
            dictized = comment_dictize(comment, context)
            comments_dictized.append(dictized)
        if context.get("combine_comments"):
            comments_dictized = combine_comments(comments_dictized)
    return d.table_dictize(obj, context, comments=comments_dictized)


def comment_dictize(obj: Comment, context: Any, **extra: Any) -> dict[str, Any]:
    extra["approved"] = obj.is_approved()

    
    subject = obj.thread.get_subject()
    extra['package'] = {
        'id': subject.id,
        'name': subject.name,
        'display_name': subject.title,
        'organization': {'id': subject.owner_org}
    }
    try:
        pkg_dict = tk.get_action('package_show')(
            {**context, 'ignore_auth': True},
            {'id': subject.id}
        )
        extra['package']['display_name'] = pkg_dict.get('display_name')
        extra['package']['organization'] = pkg_dict.get('organization')
    except:
        pass
    
    if context.get("include_author"):
        author = obj.get_author()
        if author:
            extra["author"] = get_dictizer(type(author))(author, context.copy())
            extra["user_info"] = tk.get_action('user_management_show')({**context, 'ignore_auth':True}, {'id':author.id})
        else:
            log.error("Missing author for comment: %s", obj)
            extra["author"] = None
    return d.table_dictize(obj, context, **extra)


register_dictizer(model.User, md.user_dictize)
register_dictizer(Thread, thread_dictize)
register_dictizer(Comment, comment_dictize)
