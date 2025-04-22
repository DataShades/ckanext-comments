from __future__ import annotations

from typing import Any
import ckan.plugins.toolkit as tk
from ckan import authz

from ckanext.comments.model import Comment

_ = tk._

_validators: dict[str, Any] = {}


def validator(func: Any):
    _validators[f"comments_{func.__name__}"] = func
    return func


def get_validators():
    return _validators.copy()


@validator
def comment_exists(value: Any, context: Any):
    comment = context["session"].query(Comment).filter_by(id=value).one_or_none()
    if not comment:
        raise tk.Invalid(_("Comment does not exist"))
    return value


@validator
def valid_organization(organization_id, context):
    if not organization_id: return None
    result = tk.get_action('organization_show')(context,{'id':organization_id})
    
    if not result:
        raise tk.Invalid(_('%s: %s with id: %s') % (_('Not found'), _('Organization'), organization_id))
    return result.get('id')


@validator
def valid_state(value):
    valid_states = {v for k, v in vars(Comment.State).items() if not k.startswith('_')}
    if not value:
        return ''

    if value not in valid_states:
        raise tk.Invalid(_("Invalid state: %s." % value))
    return value

@validator
def valid_user(value, context):
    model = context['model']
    passed_user_obj = model.User.get(value)

    if not passed_user_obj:
        raise tk.Invalid(_("Invalid user id."))

    if authz.is_authorized_boolean('is_portal_admin', context)\
            or authz.is_authorized_boolean('is_content_editor', context):
        return passed_user_obj.id
    else:
        raise tk.Invalid(_("User not authorized filter comments based on author."))


