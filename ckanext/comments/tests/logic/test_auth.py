import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import call_auth, call_action


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
    def test_basic_permissions(self, func, results):
        users = ("", factories.User()["name"], factories.Sysadmin()["name"])
        for user, result in zip(users, results):
            context = {"model": model, "user": user}
            auth = f"comments_{func}"
            if result:
                assert call_auth(auth, context)
            else:
                with pytest.raises(tk.NotAuthorized):
                    call_auth(auth, context)

    def test_comment_show(self, Comment):
        user = factories.User()
        anon_ctx = {"model": model, "user": ""}
        user_ctx = {"model": model, "user": user["name"]}
        comment = Comment(user=user)
        with pytest.raises(tk.NotAuthorized):
            call_auth(
                "comments_comment_show", anon_ctx.copy(), id=comment["id"]
            )
        assert call_auth(
            "comments_comment_show", user_ctx.copy(), id=comment["id"]
        )

        call_action("comments_comment_approve", id=comment["id"])
        assert call_auth(
            "comments_comment_show", anon_ctx.copy(), id=comment["id"]
        )
        assert call_auth(
            "comments_comment_show", user_ctx.copy(), id=comment["id"]
        )
