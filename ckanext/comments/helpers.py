from __future__ import annotations

from typing import Any, Optional

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.comments.model import Thread, Comment

_helpers = {}


def get_helpers():
    return _helpers.copy()


def helper(func):
    func.__name__ = f"comments_{func.__name__}"
    _helpers[func.__name__] = func
    return func


@helper
def thread_for(id: Optional[str]) -> dict[str, Any]:
    try:
        thread = tk.get_action("comments_thread_show")(
            None, {"id": id, "include_comments": True}
        )
    except tk.ObjectNotFound:
        thread = Thread(id=id).dictize({'model': model})
    return thread

@helper
def prepare_comment(comment: dict)->dict:
    if comment['author_type'] == 'user':
        comment['user'] = tk.get_action('user_show')(None, {'id': comment['author_id']})
        comment['approved'] = comment['state'] == Comment.State.approved
    return comment
