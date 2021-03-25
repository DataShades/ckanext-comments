import ckan.plugins.toolkit as tk
import ckan.model as model
from ckanext.comments.model import Comment

_auth = {}


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
@tk.auth_allow_anonymous_access
def comment_show(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    comment: Comment = (
        model.Session.query(Comment).filter(Comment.id == id).one_or_none()
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
    return {"success": False}
