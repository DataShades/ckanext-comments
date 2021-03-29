from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable, cast

from sqlalchemy.orm import Query, joinedload

import ckan.model as model
from ckanext.comments.model import Comment, Thread
import ckan.lib.dictization as d
import ckan.lib.dictization.model_dictize as md
import ckan.plugins.toolkit as tk


_dictizers: dict[type, Callable[..., dict[str, Any]]] = defaultdict(
    lambda: d.table_dictize
)

log = logging.getLogger(__name__)


def get_dictizer(type_):
    return _dictizers[type_]


def register_dictizer(type_, func):
    _dictizers[type_] = func


def thread_dictize(obj: Thread, context: dict[str, Any]) -> dict[str, Any]:
    comments_dictized = None
    if context.get("include_comments"):
        query = Comment.by_thread(obj.id)
        include_author = tk.asbool(context.get("include_author"))

        # let's make it a bit more efficient
        if include_author:
            query = cast(Query, query.options(joinedload(Comment.user)))

        approved_filter = Comment.state == Comment.State.approved
        user = model.User.get(context["user"])

        if context.get("ignore_auth"):
            pass
        elif user is None:
            query = cast(Query, query.filter(approved_filter))
        elif not user.sysadmin:
            own_filter = (Comment.author_type == "user") & (
                Comment.author_id == user.id
            )
            query = cast(Query, query.filter(approved_filter | own_filter))

        comments_dictized = []
        for comment in query:
            assert isinstance(comment, Comment)
            dictized = comment_dictize(comment, context)
            comments_dictized.append(dictized)

    return d.table_dictize(obj, context, comments=comments_dictized)


def comment_dictize(
    obj: Comment, context: dict[str, Any], **extra: Any
) -> dict[str, Any]:
    extra["approved"] = obj.is_approved()

    if context.get("include_author"):
        author = obj.get_author()
        if author:
            extra["author"] = get_dictizer(type(author))(
                author, context.copy()
            )
        else:
            log.error("Missing author for comment: %s", obj)
            extra["author"] = None
    return d.table_dictize(obj, context, **extra)


register_dictizer(model.User, md.user_dictize)
register_dictizer(Thread, thread_dictize)
register_dictizer(Comment, comment_dictize)
