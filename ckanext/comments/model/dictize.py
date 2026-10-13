from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, Optional, cast

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
    count = None

    if context.get("include_comments"):
        query = Comment.by_thread(cast(str, obj.id))
        if context.get("newest_first"):
            query = query.order_by(None).order_by(Comment.created_at.desc())

        include_author = tk.asbool(context.get("include_author"))
        after_date = context.get("after_date")

        # let's make it a bit more efficient
        if include_author:
            query = query.options(joinedload(Comment.user))

        approved_filter = Comment.state == Comment.State.approved
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

        combine = context.get("combine_comments")
        limit = context.get("limit")
        offset = context.get("offset") or 0

        if combine:
            root_query = query.filter(Comment.reply_to_id.is_(None))
            count = root_query.count()
            if limit is None and not offset:
                comments = list(query)
            else:
                comments = _comments_page_with_replies(
                    query, root_query, limit=limit, offset=offset
                )
        else:
            count = query.count()
            if offset:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            comments = list(query)

        comments_dictized = [
            comment_dictize(comment, context) for comment in comments
        ]
        if combine:
            comments_dictized = combine_comments(comments_dictized)

    extras: dict[str, Any] = {"comments": comments_dictized}
    if count is not None:
        extras["count"] = count
    return d.table_dictize(obj, context, **extras)


def _comments_page_with_replies(
    query: Any,
    root_query: Any,
    limit: Optional[int],
    offset: int,
) -> list[Comment]:
    """Return a page of root comments plus their reply trees.

    Pagination applies only to root comments (``reply_to_id is None``). All
    nested replies for the selected roots are included so ``combine_comments``
    can rebuild complete trees.
    """
    roots_page = root_query.offset(offset)
    if limit is not None:
        roots_page = roots_page.limit(limit)

    root_ids = [comment.id for comment in roots_page]
    if not root_ids:
        return []

    selected: dict[str, Comment] = {
        comment.id: comment
        for comment in query.filter(Comment.id.in_(root_ids))
    }
    frontier = set(root_ids)
    while frontier:
        children = list(query.filter(Comment.reply_to_id.in_(frontier)))
        frontier = set()
        for child in children:
            if child.id in selected:
                continue
            selected[child.id] = child
            frontier.add(child.id)

    # Keep the filtered query order among selected comments
    return list(query.filter(Comment.id.in_(selected.keys())))


def comment_dictize(obj: Comment, context: Any, **extra: Any) -> dict[str, Any]:
    extra["approved"] = obj.is_approved()

    if context.get("include_author"):
        author = obj.get_author()
        if author:
            extra["author"] = get_dictizer(type(author))(author, context.copy())
        else:
            log.error("Missing author for comment: %s", obj)
            extra["author"] = None
    return d.table_dictize(obj, context, **extra)


register_dictizer(model.User, md.user_dictize)
register_dictizer(Thread, thread_dictize)
register_dictizer(Comment, comment_dictize)
