from __future__ import annotations

from typing import Any, Optional, Union

import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.comments.const as const
from .model import Comment

_helpers = {}


def get_helpers():
    return _helpers.copy()


def helper(func):
    func.__name__ = f"comments_{func.__name__}"
    _helpers[func.__name__] = func
    return func


@helper
def thread_for(id_: Optional[str], type_: str) -> dict[str, Any]:
    thread = tk.get_action("comments_thread_show")(
        None,
        {
            "subject_id": id_,
            "subject_type": type_,
            "include_comments": True,
            "combine_comments": True,
            "include_author": True,
            "init_missing": True,
        },
    )
    return thread


@helper
def mobile_depth_threshold():
    return tk.asint(
        tk.config.get(
            const.CONFIG_MOBILE_THRESHOLD, const.DEFAULT_MOBILE_THRESHOLD
        )
    )


@helper
def author_of(id_: str) -> Optional[model.User]:
    comment = (
        model.Session.query(Comment).filter(Comment.id == id_).one_or_none()
    )
    if not comment:
        return None
    return comment.get_author()


@helper
def subject_of(id_: str) -> Union[model.Package, None]:
    comment = (
        model.Session.query(Comment).filter(Comment.id == id_).one_or_none()
    )
    if not comment:
        return None
    return comment.thread.get_subject()
