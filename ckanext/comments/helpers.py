from __future__ import annotations

from typing import Any, Optional

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.comments.model.thread import Subject

from . import config
from .model import Comment

_helpers = {}


def get_helpers():
    helpers = _helpers.copy()

    if "csrf_input" not in tk.h:
        helpers["csrf_input"] = lambda: ""

    return helpers


def helper(func):
    func.__name__ = f"comments_{func.__name__}"
    _helpers[func.__name__] = func
    return func


@helper
def thread_for(id_: Optional[str], type_: str) -> dict[str, Any]:
    thread = tk.get_action("comments_thread_show")(
        {},
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
def mobile_depth_threshold() -> int:
    return config.mobile_depth_threshold()


@helper
def author_of(id_: str) -> Optional[model.User]:
    comment = model.Session.query(Comment).filter(Comment.id == id_).one_or_none()
    if not comment:
        return None
    return comment.get_author()


@helper
def subject_of(id_: str) -> Optional[Subject]:
    comment = model.Session.query(Comment).filter(Comment.id == id_).one_or_none()
    if not comment:
        return None
    return comment.thread.get_subject()


@helper
def enable_default_dataset_comments() -> bool:
    return config.use_default_dataset_comments()
