import ckan.lib.dictization as d
import ckan.plugins.toolkit as tk
import ckan.model as model

from ckanext.comments.model import Thread, Comment

_actions = {}


def action(func):
    _actions[f"comments_{func.__name__}"] = func
    return func


def get_actions():
    return _actions.copy()


_objects = {
    "package": model.Package,
}


@action
def thread_create(context, data_dict):
    object_type = data_dict.get("object_type", "user")
    object_id = tk.get_or_bust(data_dict, "object_id")
    try:
        object_model = _objects[object_type]
    except KeyError:
        raise tk.ValidationError(
            {"object_type": [f"Unsupported object_type <{object_type}>"]}
        )
    obj = (
        model.Session.query(object_model)
        .filter(object_model.id == object_id)
        .one_or_none()
    )
    if obj is None:
        raise tk.ObjectNotFound("Cannot find object for thread")
    thread = Thread(object_id=object_id, object_type=object_type)
    model.Session.add(thread)
    model.Session.commit()
    thread_dict = d.table_dictize(thread, context.copy())
    return thread_dict


@action
def thread_show(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    thread = model.Session.query(Thread).filter(Thread.id == id).one_or_none()
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")
    thread_dict = d.table_dictize(thread, context.copy())
    return thread_dict


@action
def thread_delete(context, data_dict):
    id = tk.get_or_bust(data_dict, "id")
    thread = model.Session.query(Thread).filter(Thread.id == id).one_or_none()
    if thread is None:
        raise tk.ObjectNotFound("Thread not found")
    model.Session.delete(thread)
    model.Session.commit()
    thread_dict = d.table_dictize(thread, context.copy())
    return thread_dict


@action
def comment_create(context, data_dict):
    return {"success": True}


@action
def comment_approve(context, data_dict):
    return {"success": False}


@action
def comment_delete(context, data_dict):
    return {"success": False}


@action
def comment_update(context, data_dict):
    return {"success": False}
