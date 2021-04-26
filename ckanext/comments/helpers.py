from __future__ import annotations

from typing import Any, Optional

import ckan.plugins.toolkit as tk

import ckanext.comments.const as const


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
    return tk.asint(tk.config.get(const.CONFIG_MOBILE_THRESHOLD, const.DEFAULT_MOBILE_THRESHOLD))
