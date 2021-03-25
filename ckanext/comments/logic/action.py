import ckan.lib.dictization as d
import ckan.plugins.toolkit as tk
import ckan.model as model

from ckanext.comments.model import Thread, Comment

CONFIG_REQUIRE_APPROVAL = "ckanext.comments.require_approval"

_actions = {}


def action(func):
    func.__name__ = f"comments_{func.__name__}"
    _actions[func.__name__] = func
    return func


def get_actions():
    return _actions.copy()


_objects = {
    "package": model.Package,
}
_authors = {
    "user": model.User,
}


@action
def thread_create(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    subject_type = data_dict.get("subject_type", "package")
    try:
        subject_model = _objects[subject_type]
    except KeyError:
        raise tk.ValidationError(
            {"subject_type": [f"Unsupported subject_type <{subject_type}>"]}
        )
    obj = (
        model.Session.query(subject_model)
        .filter(subject_model.id == id)
        .one_or_none()
    )
    if obj is None:
        raise tk.ObjectNotFound("Cannot find subject for thread")
    thread = Thread(id=id, subject_type=subject_type)
    model.Session.add(thread)
    model.Session.commit()
    thread_dict = thread.dictize(context)
    return thread_dict


@action
def thread_show(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    tk.check_access("comments_thread_show", context, data_dict)
    thread = model.Session.query(Thread).filter(Thread.id == id).one_or_none()
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")
    context["include_comments"] = data_dict.get("include_comments", False)
    thread_dict = thread.dictize(context)
    return thread_dict


@action
def thread_delete(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    tk.check_access("comments_thread_delete", context, data_dict)
    thread = model.Session.query(Thread).filter(Thread.id == id).one_or_none()
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")
    model.Session.delete(thread)
    model.Session.commit()
    thread_dict = thread.dictize(context)
    return thread_dict


@action
def comment_create(context, data_dict):
    thread_id, content = tk.get_or_bust(data_dict, ["thread_id", "content"])
    tk.check_access("comments_comment_create", context, data_dict)
    try:
        thread_dict = tk.get_action("comments_thread_show")(
            context.copy(), {"id": thread_id}
        )
    except tk.ObjectNotFound:
        if data_dict.get('init_thread'):
            thread_dict = tk.get_action("comments_thread_create")(
                context.copy(), {"id": thread_id}
            )

    if not content:
        raise tk.ValidationError({"content": ["Cannot be empty"]})

    author_type = data_dict.get("author_type", "user")
    try:
        author_model = _authors[author_type]
    except KeyError:
        raise tk.ValidationError(
            {"author_type": [f"Unsupported author_type <{author_type}>"]}
        )

    author_id = data_dict.get("author_id")
    can_set_author_id = (
        context.get("ignore_auth") or context["auth_user_obj"].sysadmin
    )
    if not author_id or not can_set_author_id:
        author_id = context["user"]

    author = author_model.get(author_id)
    if author is None:
        raise tk.ObjectNotFound("Cannot find author for comment")
    author_id = author.id

    reply_to_id = data_dict.get("reply_to")
    if reply_to_id:
        # just make sure that comment exists
        tk.get_action("comments_comment_show")(
            context.copy(), {"id": reply_to_id}
        )
    comment = Comment(
        thread_id=thread_dict["id"],
        content=content,
        author_type=author_type,
        author_id=author_id,
        reply_to_id=reply_to_id,
    )
    if not tk.asbool(tk.config.get(CONFIG_REQUIRE_APPROVAL, True)):
        comment.approve()
    model.Session.add(comment)
    model.Session.commit()
    comment_dict = comment.dictize(context)
    return comment_dict


@action
def comment_show(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    tk.check_access("comments_comment_show", context, data_dict)
    comment = (
        model.Session.query(Comment).filter(Comment.id == id).one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment_dict = comment.dictize(context)
    return comment_dict


@action
def comment_approve(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    tk.check_access("comments_comment_approve", context, data_dict)
    comment = (
        model.Session.query(Comment).filter(Comment.id == id).one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment.approve()
    model.Session.commit()

    comment_dict = comment.dictize(context)
    return comment_dict


@action
def comment_delete(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    tk.check_access("comments_comment_delete", context, data_dict)
    comment = (
        model.Session.query(Comment).filter(Comment.id == id).one_or_none()
    )
    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    model.Session.delete(comment)
    model.Session.commit()
    comment_dict = comment.dictize(context)
    return comment_dict


@action
def comment_update(context, data_dict):
    id, content = tk.get_or_bust(data_dict, ["id", "content"])
    tk.check_access("comments_comment_update", context, data_dict)
    if not content:
        raise tk.ValidationError({"content": ["Cannot be empty"]})
    comment = (
        model.Session.query(Comment).filter(Comment.id == id).one_or_none()
    )

    if comment is None:
        raise tk.ObjectNotFound("Comment not found")
    comment.content = content
    model.Session.commit()
    comment_dict = comment.dictize(context)
    return comment_dict
