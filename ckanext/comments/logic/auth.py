import ckan.plugins.toolkit as tk

_auth = {}


def auth(func):
    _auth[f"comments_{func.__name__}"] = func
    return func


def get_auth_functions():
    return _auth.copy()


@auth
@tk.auth_disallow_anonymous_access
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
@tk.auth_disallow_anonymous_access
def comment_create(context, data_dict):
    return {"success": True}


@auth
def comment_approve(context, data_dict):
    return {"success": False}


@auth
def comment_delete(context, data_dict):
    return {"success": False}


@auth
def comment_update(context, data_dict):
    return {"success": False}
