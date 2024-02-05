from __future__ import annotations
from typing import Any

import ckan.model as model

from . import config


def comments_is_moderator(user: model.User, comment: Any, thread: Any) -> bool:
    return user.sysadmin


def is_moderator(user: model.User, comment: Any, thread: Any) -> bool:
    func = config.moderator_checker() or comments_is_moderator
    return func(user, comment, thread)
