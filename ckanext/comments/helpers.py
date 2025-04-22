from __future__ import annotations

from typing import Any, Optional

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.comments.model.thread import Subject

from . import config
from .model import Comment
import ckan.lib.helpers as h
_ = tk._
_helpers = {}


def get_helpers():
    helpers = _helpers.copy()

    if "csrf_input" not in tk.h:
        helpers["csrf_input"] = lambda: ""

    return helpers


def helper(func):
    func.__name__ = f"comments_{func.__name__}"
    _helpers[func.__name__] = func
    return func


@helper
def thread_for(id_: Optional[str], type_: str) -> dict[str, Any]:
    thread = tk.get_action("comments_thread_show")(
        {},
        {
            "subject_id": id_,
            "subject_type": type_,
            "include_comments": True,
            "combine_comments": True,
            "include_author": True,
            "init_missing": True,
        },
    )
    return thread


@helper
def mobile_depth_threshold() -> int:
    return config.mobile_depth_threshold()


@helper
def author_of(id_: str) -> Optional[model.User]:
    comment = model.Session.query(Comment).filter(Comment.id == id_).one_or_none()
    if not comment:
        return None
    return comment.get_author()


@helper
def subject_of(id_: str) -> Optional[Subject]:
    comment = model.Session.query(Comment).filter(Comment.id == id_).one_or_none()
    if not comment:
        return None
    return comment.thread.get_subject()


@helper
def enable_default_dataset_comments() -> bool:
    return config.use_default_dataset_comments()


@helper
def annonymouse_image(size: int = 26):
    return h.snippet(
            'user/snippets/placeholder.html',
            size=size, user_name=_("Anonymous User"))


@helper
def comment_metatdata(comment):
    return [
        {
            'label': _("Dataset"),
            'value': comment['package']['display_name'],
            'type': 'link',
            'url': h.url_for('dataset.read', id=comment['package']['id']),
        },
        {
            'label': _("Author"),
            'value': comment['author']['fullname'] or comment['author']['name'],
            'type': 'text',
        },
        {
            'label': _("Government Entity"),
            'value': comment['package']['organization']['display_name'],
            'type': 'link',
            'url': h.url_for('organization.read', id=comment['package']['organization']['id']),
        },
        {
            'label': _("Status"),
            'value': comment['state'],
            'type': 'text',
        },
        {
            'label': _("Hidden"),
            'value': str(comment['hidden']),
            'type': 'text',
        },
        {
            'label': _("Pinned"),
            'value': str(comment['pinned']),
            'type': 'text',
        },
        {
            'label': _("Content"),
            'value': h.render_markdown(comment['content']),
            'type': 'text',
        },
        {
            'label': _("Date Created"),
            'value': comment['created_at'],
            'type': 'date',
        }
    ]


@helper
def entity_options():
    context = {'user': tk.c.user}
    data_dict = { }
    orgs = tk.get_action('organization_list_as_options')(context, data_dict)
    return [{'text':_('Select Government Entity'), 'value':''}] + [
        {'text':h.truncate(org['display_name'], 30), 'value':org['id']}
        for org in orgs
    ]


@helper
def status_options():
    return [
        {'text': _('Select State'), 'value': ''},
        {'text': _('Pending'), 'value': 'draft'},
        {'text': _('Approved'), 'value': 'approved'},
        {'text': _('Rejected'), 'value': 'rejected'},
        ]

@helper
def status_dict():
    return {
        'draft': _('Pending'),
        'approved': _('Approved'),
        'rejected': _('Rejected')
    }