from __future__ import annotations

import logging
from typing import Callable
from werkzeug.utils import import_string

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.comments.model import Comment
import ckanext.comments.const as const

log = logging.getLogger(__name__)
_auth = {}


def _can_edit(state: str, by_author: bool = False) -> bool:
    if state == Comment.State.draft:
        if by_author:
            return tk.asbool(
                tk.config.get(
                    const.CONFIG_DRAFT_EDITS_BY_AUTHOR,
                    const.DEFAULT_DRAFT_EDITS_BY_AUTHOR,
                )
            )
        return tk.asbool(
            tk.config.get(
                const.CONFIG_DRAFT_EDITS,
                const.DEFAULT_DRAFT_EDITS,
            )
        )
    elif state == Comment.State.approved:
        if by_author:
            return tk.asbool(
                tk.config.get(
                    const.CONFIG_APPROVED_EDITS_BY_AUTHOR,
                    const.DEFAULT_APPROVED_EDITS_BY_AUTHOR,
                )
            )
        return tk.asbool(
            tk.config.get(
                const.CONFIG_APPROVED_EDITS,
                const.DEFAULT_APPROVED_EDITS,
            )
        )
    log.warning("Unexpected comment state: %s", state)
    return False


def is_moderator(user: model.User, comment: Comment) -> bool:
    return user.sysadmin


def _is_moderator(user: model.User, comment: Comment) -> bool:
    checker = tk.config.get(const.CONFIG_MODERATOR_CHECKER, const.DEFAULT_MODERATOR_CHECKER)
    func: Callable[[model.User, Comment], bool] = import_string(checker, silent=True) or is_moderator
    return func(user, comment)


def auth(func):
    func.__name__ = f"comments_{func.__name__}"
    _auth[func.__name__] = func
    return func


def get_auth_functions():
    return _auth.copy()


@auth
def thread_create(context, data_dict):
    return {"success": True}


@auth
@tk.auth_allow_anonymous_access
def thread_show(context, data_dict):
    return {"success": True}


@auth
def thread_delete(context, data_dict):
    return {"success": False}


@auth
def comment_create(context, data_dict):
    return {"success": True}


@auth
def reply_create(context, data_dict):
    return {"success": True}


@auth
@tk.auth_allow_anonymous_access
def comment_show(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    comment = (
        context['session'].query(Comment).filter(Comment.id == id).one_or_none()
    )

    if not comment:
        raise tk.ObjectNotFound("Comment not found")
    return {
        "success": comment.is_approved()
        or comment.is_authored_by(context["user"])
    }


@auth
def comment_approve(context, data_dict):
    return {"success": False}


@auth
def comment_delete(context, data_dict):
    return {"success": False}


@auth
def comment_update(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    comment = (
        context['session'].query(Comment).filter(Comment.id == id).one_or_none()
    )

    if not comment:
        raise tk.ObjectNotFound("Comment not found")

    by_author = comment.is_authored_by(context["user"])
    if by_author or _is_moderator(context["auth_user_obj"], comment):
        return {"success": _can_edit(comment.state, by_author)}
    return {"success": False}
