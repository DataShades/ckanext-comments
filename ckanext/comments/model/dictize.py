from collections import defaultdict

import ckan.model as model
import ckan.lib.dictization as d
import ckan.lib.dictization.model_dictize as md

_dictizers = defaultdict(lambda: d.table_dictize)


def get_dictizer(type_):
    return _dictizers[type_]


def register_dictizer(type_, func):
    _dictizers[type_] = func


register_dictizer(model.User, md.user_dictize)
