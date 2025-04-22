from __future__ import annotations
from typing import Any
from ckan import authz
import ckan.model as model
import ckan.plugins.toolkit as tk
from . import config
from urllib.parse import urlencode
from ckan.common import _
from ckan.lib.helpers import helper_functions as h


def comments_is_moderator(user: model.User, comment: Any, thread: Any) -> bool:
    context = {
        'model': model,
        'session': model.Session,
        'user': user.name,
        'auth_user_obj': tk.g.userobj
    }
    return authz.is_authorized_boolean('is_content_editor', context)


def is_moderator(user: model.User, comment: Any, thread: Any) -> bool:
    func = config.moderator_checker() or comments_is_moderator
    return func(user, comment, thread)


def get_organization_id_for_user(context):
    model = context["model"]
    user = context.get('user')
    user_obj = model.User.get(user)

    if authz.auth_not_logged_in(context):  return None
    
    results = model.Session.query(model.Group) \
        .filter(model.Group.type == 'organization') \
        .filter(model.Group.state == 'active') \
        .join(model.Member, model.Group.id == model.Member.group_id) \
        .filter(model.Member.table_id == user_obj.id)
    
    if results and results.first():
        return results.first().id
    else:
        return None



def check_list_view_auth():
    context = {
        'model': model,
        'session': model.Session,
        'user': tk.g.user or tk.g.author,
        'auth_user_obj': tk.g.userobj,
    }

    try:
        tk.check_access('comments_comment_list', context)
    except tk.NotAuthorized:
        return tk.abort(
            401,
            _('User not authorized to see the comments'))


def check_status_update_view_auth(id):
    context = {
        'model': model,
        'session': model.Session,
        'user': tk.g.user or tk.g.author,
        'auth_user_obj': tk.g.userobj,
    }

    try:
        tk.check_access('comments_comment_show', context, {'id':id})
    except tk.NotAuthorized:
        return tk.abort(
            401,
            _('User not authorized to see the comments'))
    except tk.ObjectNotFound:
        return tk.abort(
            404,
            _('Comment not found'))
    


def read_view(id):
    context = {
        'model': model,
        'session': model.Session,
        'user': tk.g.user or tk.g.author,
        'auth_user_obj': tk.g.userobj
    }
    data_dict = {'id': id}

    try:
        comment = tk.get_action('comments_comment_show')(context, data_dict)
    except tk.ObjectNotFound:
        return tk.abort(404, _('Comment not found'))
    except tk.NotAuthorized:
        return tk.abort(401, _('Unauthorized to view Comment'))

    return tk.render(u'comments/detail.html', extra_vars={"comment":comment})


def pager_url(params_nopage,
               q: Any = None,  # noqa
               page = None) -> str:
    params = list(params_nopage)
    params.append((u'page', page))
    return _url_with_params(h.url_for('comments.index'), params)

def _url_with_params(url: str, params) -> str:
    params = _encode_params(params)
    return url + u'?' + urlencode(params)

def _encode_params(params):
    return [(k, v.encode(u'utf-8') if isinstance(v, str) else str(v))
            for k, v in params]


