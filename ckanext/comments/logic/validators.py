import ckan.plugins.toolkit as tk
from ckanext.comments.model import Comment


_validators = {}


def validator(func):
    _validators[f"comments_{func.__name__}"] = func
    return func


def get_validators():
    return _validators.copy()


@validator
def comment_exists(value, context):
    comment = (
        context["session"].query(Comment).filter_by(id=value).one_or_none()
    )
    if not comment:
        raise tk.Invalid("Comment does not exist")
    return value
