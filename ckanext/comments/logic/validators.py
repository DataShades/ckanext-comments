from __future__ import annotations

from typing import Any
import ckan.plugins.toolkit as tk

from ckanext.comments.model import Comment

_validators: dict[str, Any] = {}


def validator(func: Any):
    _validators[f"comments_{func.__name__}"] = func
    return func


def get_validators():
    return _validators.copy()


@validator
def comment_exists(value: Any, context: Any):
    comment = context["session"].query(Comment).filter_by(id=value).one_or_none()
    if not comment:
        raise tk.Invalid("Comment does not exist")
    return value
