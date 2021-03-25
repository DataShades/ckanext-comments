import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action


@pytest.mark.usefixtures("clean_db")
class TestThread:
    def test_thread_create(self):
        dataset = factories.Dataset()
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_thread_create",
                subject_type="package",
                id="123-random",
            )

        thread = call_action(
            "comments_thread_create",
            subject_type="package",
            id=dataset["id"],
        )

    def test_thread_show(self, Thread, Comment):
        user = factories.User()
        t = Thread()
        Comment(thread_id=t["id"])
        comment = Comment(thread_id=t["id"])
        call_action("comments_comment_approve", id=comment["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_thread_show", id="123-random")
        thread = call_action(
            "comments_thread_show", id=t["id"], include_comments=True
        )
        assert thread["id"] == t["id"]
        assert len(thread["comments"]) == 2

        thread = call_action(
            "comments_thread_show",
            {"ignore_auth": False, "user": user["name"]},
            id=t["id"],
            include_comments=True,
        )
        assert len(thread["comments"]) == 1
        for c in thread["comments"]:
            assert c["state"] == "approved"

    def test_thread_delete(self, Thread):
        thread = Thread()
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_thread_delete", id="123-random")
        call_action("comments_thread_delete", id=thread["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_thread_show", id=thread["id"])


@pytest.mark.usefixtures("clean_db")
class TestComment:
    def test_comment_create(self, Thread):
        user = factories.User()
        thread = Thread()
        content = "random content"

        with pytest.raises(tk.ObjectNotFound):
            # real thread required
            call_action(
                "comments_comment_create",
                thread_id="not-exists",
                content=content,
            )

        with pytest.raises(tk.ObjectNotFound):
            # author is required
            call_action(
                "comments_comment_create",
                thread_id=thread["id"],
                content=content,
            )

        comment = call_action(
            "comments_comment_create",
            {"user": user["name"]},
            thread_id=thread["id"],
            content=content,
        )

        assert comment["content"] == content
        assert comment["author_id"] == user["id"]
        assert comment["thread_id"] == thread["id"]

    def test_comment_show(self, Comment):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exist")
        c = Comment()
        comment = call_action("comments_comment_show", id=c["id"])
        assert c == comment

    def test_comment_approve(self, Comment):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exists")
        c = Comment()
        comment = call_action("comments_comment_approve", id=c["id"])
        assert comment["state"] == "approved"

    def test_comment_delete(self, Comment):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exist")
        c = Comment()
        call_action("comments_comment_delete", id=c["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id=c["id"])

    def test_comment_update(self, Comment):
        content = "random content"

        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_comment_update", id="not-exist", content=content
            )
        c = Comment()

        call_action("comments_comment_update", id=c["id"], content=content)
        comment = call_action("comments_comment_show", id=c["id"])

        assert comment["content"] != c["content"]
        assert comment["content"] == content
