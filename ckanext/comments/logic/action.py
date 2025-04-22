from datetime import datetime

import ckan.lib.dictization as d
import ckan.plugins.toolkit as tk
from ckan.logic import validate

import ckanext.comments.logic.schema as schema
from ckanext.comments.model import Comment, Thread
from ckanext.comments.model.dictize import get_dictizer

import ckanext.comments.utils as utils
from ckan import authz

from .. import config, signals

_ = tk._
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
            {"id": ["Thread for the given subject_id and subject_type already exists"]}
        )
    if thread.get_subject() is None:
        raise tk.ObjectNotFound("Cannot find subject for thread")

    context["session"].add(thread)
    context["session"].commit()
    thread_dict = get_dictizer(type(thread))(thread, context)
    return thread_dict


@action
@validate(schema.thread_show)
@tk.side_effect_free
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

    context["newest_first"] = data_dict["newest_first"]
    context["pinned_first"] = data_dict["pinned_first"]

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
        thread_dict = tk.get_action("comments_thread_show")(context.copy(), thread_data)
    except tk.ObjectNotFound:
        if not data_dict["create_thread"]:
            raise
        thread_dict = tk.get_action("comments_thread_create")(
            context.copy(), thread_data
        )

    author_id = data_dict.get("author_id")
    can_set_author_id = context.get("ignore_auth") or context["auth_user_obj"].sysadmin

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
        extras=data_dict["extras"],
        author_id=author_id,
        reply_to_id=reply_to_id,
        anonymous= data_dict.get('anonymous')
    )

    author = comment.get_author()
    if author is None:
        raise tk.ObjectNotFound(_("Cannot find author for comment"))
    # make sure we are not messing up with name_or_id
    comment.author_id = author.id

    if not config.approval_required():
        comment.approve()
    context["session"].add(comment)
    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.created.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.comment_show)
@tk.side_effect_free
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
        raise tk.ObjectNotFound(_("Comment not found"))
    
    context["include_author"] = True
    comment_dict = get_dictizer(type(comment))(comment, context)
    return comment_dict


@action
@validate(schema.comment_approve)
def comment_approve(context, data_dict):
    tk.check_access("comments_comment_approve", context, data_dict)
    return patch_comment(context, data_dict, {'state': Comment.State.approved})

@action
@validate(schema.comment_approve)
def comment_reject(context, data_dict):
    tk.check_access("comments_comment_approve", context, data_dict)
    return patch_comment(context, data_dict, {'state': Comment.State.rejected})
    

def patch_comment(context, data_dict, updated_dict):

    comment = (
        context["session"]
        .query(Comment)
        .filter(Comment.id == data_dict["id"])
        .one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound(_("Comment not found"))
    
    comment.patch_comment(**updated_dict)
    
    context["session"].commit()

    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.approved.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@validate(schema.comment_approve)
def comment_hide(context, data_dict):
    tk.check_access("comments_comment_approve", context, data_dict)
    return patch_comment(context, data_dict, {'hidden': True})


@action
@validate(schema.comment_approve)
def comment_unhide(context, data_dict):
    tk.check_access("comments_comment_approve", context, data_dict)
    return patch_comment(context, data_dict, {'hidden': False})


@action
@validate(schema.comment_approve)
def comment_pin(context, data_dict):
    tk.check_access("comments_comment_approve", context, data_dict)
    return patch_comment(context, data_dict, {'pinned': True})


@action
@validate(schema.comment_approve)
def comment_unpin(context, data_dict):
    tk.check_access("comments_comment_approve", context, data_dict)
    return patch_comment(context, data_dict, {'pinned': False})



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
        raise tk.ObjectNotFound(_("Comment not found"))

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
        raise tk.ObjectNotFound(_("Comment not found"))

    comment.patch_comment(**{
        'content': data_dict["content"],
        'state': Comment.State.draft,
        'hidden': comment.hidden or False,
        'pinned': comment.pinned or False,
        'modified_at': datetime.utcnow(),
    })

    context["session"].commit()
    comment_dict = get_dictizer(type(comment))(comment, context)

    signals.updated.send(comment.thread_id, comment=comment_dict)
    return comment_dict


@action
@tk.side_effect_free
@validate(schema.comments_search_schema)
def comment_search(context, data_dict):
    tk.check_access("comments_comment_list", context, data_dict)
    
    model = context["model"]
    user = context.get('user')
    user_obj = model.User.get(user)


    offset = data_dict.pop('page', 1) - 1
    limit = data_dict.pop('limit', 20)


    if not (authz.is_authorized_boolean('is_portal_admin', context) \
            or authz.is_authorized_boolean('is_content_editor', context)):
        data_dict['author_id'] = user_obj.id

    query = Comment.advance_filter(**data_dict)
    search_count = query.count()


    if limit > -1:
        query = query.offset(offset * limit).limit(limit)    
    context["include_author"] = True

    return {
        'total': search_count,
        'items': [
            get_dictizer(type(comment))(comment, context)
            for comment in query.all()
        ]
    }


@action
@validate(schema.generate_statics_schema)
@tk.side_effect_free
def generate_statistics(context, data_dict):
    tk.check_access("comments_comment_list", context, data_dict)
    
    model = context["model"]
    user = context.get('user')
    user_obj = model.User.get(user)
    
    user_org = utils.get_organization_id_for_user(context)

    if authz.is_authorized_boolean('is_portal_admin', context)\
                or authz.is_authorized_boolean('is_content_editor', context):
        return Comment.generate_statistics(
            organization_id=data_dict.get('organization_id', None)
        )
    elif user_org:
        return Comment.generate_statistics(
            organization_id=user_org
        )
    else:
        return Comment.generate_statistics(
            organization_id=data_dict.get('organization_id', None),
            author_id=user_obj.id
        )

