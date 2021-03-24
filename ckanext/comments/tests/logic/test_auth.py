import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import call_auth


@pytest.mark.usefixtures("clean_db")
class TestAuth:
    @pytest.mark.parametrize(
        "func,results",
        [
            ("thread_create", (False, True, True)),
            ("thread_show", (True, True, True)),
            ("thread_delete", (False, False, True)),
            ("comment_create", (False, True, True)),
            ("comment_approve", (False, False, True)),
            ("comment_delete", (False, False, True)),
            ("comment_update", (False, False, True)),
        ],
    )
    def test_permissions(self, func, results):
        users = ("", factories.User()["name"], factories.Sysadmin()["name"])
        for user, result in zip(users, results):
            context = {"model": model, "user": user}
            auth = f"comments_{func}"
            if result:
                assert call_auth(auth, context)
            else:
                with pytest.raises(tk.NotAuthorized):
                    call_auth(auth, context)
