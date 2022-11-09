from datetime import datetime

import ckan.lib.dictization as d
import ckan.plugins.toolkit as tk
from ckan.logic import validate

import ckanext.comments.logic.schema as schema
from ckanext.comments.model import Thread, Comment
from ckanext.comments.model.dictize import get_dictizer

import ckanext.comments.const as const
from .. import signals

_actions = {}


def action(func):
    func.__name__ = f"comments_{func.__name__}"
    _actions[func.__name__] = func
    return func


def get_actions():
    return _actions.copy()


@action
@validate(schema.thread_create)
def thread_create(context, data_dict):
    """Create a thread for the subject.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity

    """
    tk.check_access("comments_thread_create", context, data_dict)
    thread = Thread.for_subject(
        data_dict["subject_type"], data_dict["subject_id"], init_missing=True
    )

    if thread.id:
        raise tk.ValidationError(
            {
                "id": [
                    "Thread for the given subject_id and subject_type already exists"
                ]
            }
        )
    subject = thread.get_subject()
    if subject is None:
        raise tk.ObjectNotFound("Cannot find subject for thread")
    # make sure we are not messing up with name_or_id
    thread.subject_id = subject.id

    context["session"].add(thread)
    context["session"].commit()
    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.thread_show)
def thread_show(context, data_dict):
    """Show the subject's thread.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity
        init_missing(bool, optional): return an empty thread instead of 404
        include_comments(bool, optional): show comments from the thread
        include_author(bool, optional): show authors of the comments
        combine_comments(bool, optional): combine comments into a tree-structure
        after_date(str:ISO date, optional): show comments only since the given date
    """
    tk.check_access("comments_thread_show", context, data_dict)
    thread = Thread.for_subject(
        data_dict["subject_type"],
        data_dict["subject_id"],
        init_missing=data_dict["init_missing"],
    )
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")

    context["include_comments"] = data_dict["include_comments"]
    context["combine_comments"] = data_dict["combine_comments"]
    context["include_author"] = data_dict["include_author"]
    context["after_date"] = data_dict.get("after_date")

    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.thread_delete)
def thread_delete(context, data_dict):
    """Delete the thread.

    Args:
        id(str): ID of the thread
    """
    tk.check_access("comments_thread_delete", context, data_dict)
    thread = (
        context["session"]
        .query(Thread)
        .filter(Thread.id == data_dict["id"])
        .one_or_none()
    )
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")
    context["session"].delete(thread)
    context["session"].commit()
    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.comment_create)
def comment_create(context, data_dict):
    """Add a comment to the thread.

    Args:
        subject_id(str): unique ID of the commented entity
        subject_type(str:package|resource|user|group): type of the commented entity
        content(str): comment's message
        reply_to_id(str, optional): reply to the existing comment
        create_thread(bool, optional): create a new thread if it doesn't exist yet
    """
    tk.check_access("comments_comment_create", context, data_dict)

    thread_data = {
        "subject_id": data_dict["subject_id"],
        "subject_type": data_dict["subject_type"],
    }
    try:
        thread_dict = tk.get_action("comments_thread_show")(
            context.copy(), thread_data
        )
    except tk.ObjectNotFound:
        if not data_dict["create_thread"]:
            raise
        thread_dict = tk.get_action("comments_thread_create")(
            context.copy(), thread_data
        )

    author_id = data_dict.get("author_id")
    can_set_author_id = (
        context.get("ignore_auth") or context["auth_user_obj"].sysadmin
    )

    if not author_id or not can_set_author_id:
        author_id = context["user"]

    reply_to_id = data_dict.get("reply_to_id")
    if reply_to_id:
        parent = tk.get_action("comments_comment_show")(
            context.copy(), {"id": reply_to_id}
        )
        if parent["thread_id"] != thread_dict["id"]:
            raise tk.ValidationError(
                {"reply_to_id": ["Coment is owned by different thread"]}
            )

    comment = Comment(
        thread_id=thread_dict["id"],
        content=data_dict["content"],
        author_type=data_dict["author_type"],
        author_id=author_id,
        reply_to_id=reply_to_id,
    )

    author = comment.get_author()
    if author is None:
        raise tk.ObjectNotFound("Cannot find author for comment")
    # make sure we are not messing up with name_or_id
    comment.author_id = author.id

    if not tk.asbool(
        tk.config.get(
            const.CONFIG_REQUIRE_APPROVAL, const.DEFAULT_REQUIRE_APPROVAL
        )
    ):
        comment.approve()
    context["session"].add(comment)
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.created.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.comment_show)
def comment_show(context, data_dict):
    """Show the details of the comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_show", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment_dict = get_dictizer(type(comment))(comment, context)
    return comment_dict


@action
@validate(schema.comment_approve)
def comment_approve(context, data_dict):
    """Approve draft comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_approve", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment.approve()
    context["session"].commit()

    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.approved.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.comment_delete)
def comment_delete(context, data_dict):
    """Remove existing comment

    Args:
        id(str): ID of the comment
    """
    tk.check_access("comments_comment_delete", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    context["session"].delete(comment)
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.deleted.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.comment_update)
def comment_update(context, data_dict):
    """Update existing comment

    Args:
        id(str): ID of the comment
        content(str): comment's message
    """

    tk.check_access("comments_comment_update", context, data_dict)
    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )

    if comment is None:
        raise tk.ObjectNotFound("Comment not found")

    comment.content = data_dict["content"]
    comment.modified_at = datetime.utcnow()
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.updated.send(comment.thread_id, comment=comment_dict)
    return comment_dict
