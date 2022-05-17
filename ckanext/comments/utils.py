from werkzeug.utils import import_string

import ckan.model as model
import ckanext.comments.const as const
import ckan.plugins.toolkit as tk


def comments_is_moderator(user: model.User, comment, thread) -> bool:
    return user.sysadmin


def is_moderator(user: model.User, comment, thread) -> bool:
    checker = tk.config.get(
        const.CONFIG_MODERATOR_CHECKER, const.DEFAULT_MODERATOR_CHECKER
    )
    func = import_string(checker, silent=True) or comments_is_moderator
    return func(user, comment, thread)
