# encoding: utf-8
from __future__ import annotations

from flask import Blueprint, request
from ckan.lib.helpers import helper_functions as h
from ckan.lib.helpers import Page


import logging
import ckan.lib.base as base
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.model as model

import ckanext.comments.utils as utils
import ckanext.comments.logic.schema as schema

from typing import Any, Optional, Union, cast
from flask import Blueprint
from flask.views import MethodView
from ckan.common import current_user, _, request

from ckan.types import Context, Response
from flask import request
from functools import partial


_get_action = logic.get_action
_tuplize_dict = logic.tuplize_dict
_clean_dict = logic.clean_dict
_parse_params = logic.parse_params


log = logging.getLogger(__name__)


blueprint = Blueprint(u'comments', __name__, url_prefix=u'/dashboard/comments')


def index():
    utils.check_list_view_auth()
    context = cast(Context, {
        u'model': model,
        u'session': model.Session,
        u'user': current_user.name,
        u'auth_user_obj': current_user,
        })

    data_dict = {**request.args}
    data_dict, errors = dict_fns.validate(data_dict, schema.comments_search_schema(), context)

    sort = data_dict.get('sort', 'created_at desc')


    limit = data_dict.get('limit', 20)
    results = tk.get_action('comments_comment_search')(
        context, {**data_dict, 'sort':sort, 'limit': limit,})
    
    comments_statistics = tk.get_action('comments_generate_statistics')(
        context, {**data_dict})

    params_nopage = [
        (k, v) for k, v in request.args.items(multi=True)
        if k != u'page'
        ]

    pager_url = partial(utils.pager_url, params_nopage)

    pagination = Page(
        collection=results['items'],
        page=data_dict.get('page', 1),
        url=pager_url,
        item_count=results.get('total'),
        items_per_page=limit,
        )
    pagination.items=results['items']

    return base.render(u'comments/search.html',
        extra_vars={
            "comments": results.get('items'),
            "comments_statistics": comments_statistics,
            "count": results.get('total'),
            u'errors': errors,
            'data_dict': data_dict,
            'selected_sorting': sort,
            'page': pagination,
            }
        )


class StatusUpdate(MethodView):
    def _prepare(self, id) -> Context:
        utils.check_status_update_view_auth(id)
        context = cast(Context, {
            u'model': model,
            u'session': model.Session,
            u'user': current_user.name,
            u'auth_user_obj': current_user,
            u'save': u'save' in request.form
        })
        return context

    def get(self,
            id: str,
            data: Optional[dict[str, Any]] = None,
            errors: Optional[dict[str, Any]] = None,
            error_summary: Optional[dict[str, Any]] = None
            ) -> Union[Response, str]:
        context = self._prepare(id)

        req_comment = _get_action(u'comments_comment_show')(context, {u'id': id})
        data = {**req_comment, **(data or {})}

        errors = errors or {}
        errors_json = h.dump_json(errors)

        return base.render(
            'comments/edit.html',
            extra_vars={
                u'data': data,
                u'errors': errors,
                u'error_summary': error_summary,
                u'action': u'edit',
                u'form_style': u'edit',
                
                u'comment': req_comment,
                u'errors_json': errors_json
            }
        )

    def post(self, id):
        context = self._prepare(id)

        data_dict = _clean_dict(
            dict_fns.unflatten(
                _tuplize_dict(_parse_params(tk.request.form))))
        data_dict.update(
            _clean_dict(
                dict_fns.unflatten(
                    _tuplize_dict(_parse_params(
                        tk.request.files)))))

        action = data_dict.get('status_update')
        data_dict['id'] = id
        try:
            if action == 'approved': 
                req_comment = tk.get_action('comments_comment_approve')(context, data_dict)

        except tk.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)


        url = h.url_for('comments.show', id=id)
        return h.redirect_to(url)


def read(id):
    return utils.read_view(id)



blueprint.add_url_rule('/status_update/<id>', view_func=StatusUpdate.as_view('edit'),
                      methods=['GET', 'POST'],
                      endpoint="status_update")

blueprint.add_url_rule('/<id>', view_func=read, endpoint="show")
blueprint.add_url_rule('/', view_func=index, endpoint="index")
