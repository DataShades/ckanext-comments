from __future__ import annotations

import datetime as dt

import pytest
from typing import Any
from ckan import types
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action

from ckanext.comments import config


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestThreadCreate:
    def test_cannot_create_thread_for_missing_object(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_thread_create",
                subject_type="package",
                subject_id="123-random",
            )

    def test_thread_create(self):
        dataset = factories.Dataset()
        call_action(
            "comments_thread_create",
            subject_type="package",
            subject_id=dataset["id"],
        )


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestThreadShow:
    def test_cannot_show_missing_thread(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_thread_show",
                subject_id="123-random",
                subject_type="package",
            )

    def test_missing_thread_with_init(self):
        thread = call_action(
            "comments_thread_show",
            subject_id="123-random",
            subject_type="package",
            init_missing=True,
        )
        assert thread["id"] is None

    def test_thread_show(
        self, thread_factory: types.TestFactory, comment_factory: types.TestFactory
    ):
        t = thread_factory()
        comment_factory(
            subject_id=t["subject_id"],
            subject_type=t["subject_type"],
        )
        comment = comment_factory(
            subject_id=t["subject_id"],
            subject_type=t["subject_type"],
        )
        call_action("comments_comment_approve", id=comment["id"])
        thread = call_action(
            "comments_thread_show",
            subject_id=t["subject_id"],
            subject_type=t["subject_type"],
            include_comments=True,
        )
        assert thread["id"] == t["id"]
        assert len(thread["comments"]) == 2

        thread = call_action(
            "comments_thread_show",
            {"ignore_auth": False},
            subject_id=t["subject_id"],
            subject_type=t["subject_type"],
            include_comments=True,
        )
        assert len(thread["comments"]) == 1
        for c in thread["comments"]:
            assert c["state"] == "approved"
            assert "author" not in c

        thread = call_action(
            "comments_thread_show",
            {"ignore_auth": False},
            subject_id=t["subject_id"],
            subject_type=t["subject_type"],
            include_comments=True,
            include_author=True,
        )
        for c in thread["comments"]:
            assert c["author"] is not None

        thread = call_action(
            "comments_thread_show",
            subject_id=t["subject_id"],
            subject_type=t["subject_type"],
            include_comments=True,
            after_date=(dt.datetime.now() + dt.timedelta(days=1)).isoformat(),
        )

        assert len(thread["comments"]) == 0


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestThreadDelete:
    def test_cannot_delete_missing_thread(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_thread_delete", id="123-random")

    def test_thread_delete(self, thread: dict[str, Any]):
        call_action("comments_thread_delete", id=thread["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_thread_show",
                subject_id=thread["subject_id"],
                subject_type=thread["subject_type"],
            )


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestCommentCreate:
    def test_missing_subject(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_comment_create",
                subject_id="random-id",
                subject_type="package",
                content="content",
            )

    def test_missing_author(self, thread: dict[str, Any]):
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_comment_create",
                subject_id=thread["subject_id"],
                subject_type=thread["subject_type"],
                content="content",
            )

    def test_controlled_author(self, thread: dict[str, Any]):
        user = factories.User()
        another_user = factories.User()
        content = "random content"

        comment = call_action(
            "comments_comment_create",
            {"user": user["name"], "ignore_auth": False},
            subject_id=thread["subject_id"],
            subject_type=thread["subject_type"],
            content=content,
            author_id=another_user["name"],
        )
        assert comment["author_id"] == user["id"]

        comment = call_action(
            "comments_comment_create",
            {"user": user["name"], "ignore_auth": True},
            subject_id=thread["subject_id"],
            subject_type=thread["subject_type"],
            content=content,
            author_id=another_user["name"],
        )
        assert comment["author_id"] == another_user["id"]

    def test_comment_create(self, thread: dict[str, Any]):
        user = factories.User()
        content = "random content"

        comment = call_action(
            "comments_comment_create",
            {"user": user["name"]},
            subject_id=thread["subject_id"],
            subject_type=thread["subject_type"],
            content=content,
        )

        assert comment["content"] == content
        assert comment["author_id"] == user["id"]
        assert comment["thread_id"] == thread["id"]

    def test_existing_reply(
        self, thread: dict[str, Any], comment_factory: types.TestFactory
    ):
        user = factories.User()
        comment = comment_factory(
            subject_id=thread["subject_id"],
            subject_type=thread["subject_type"],
        )

        reply = call_action(
            "comments_comment_create",
            {"user": user["name"]},
            subject_id=thread["subject_id"],
            subject_type=thread["subject_type"],
            content="content",
            reply_to_id=comment["id"],
        )
        assert reply["reply_to_id"] == comment["id"]
        comments = call_action(
            "comments_thread_show",
            subject_id=thread["subject_id"],
            subject_type=thread["subject_type"],
            include_comments=True,
        )
        assert len(comments["comments"]) == 2
        assert not any("replies" in c for c in comments["comments"])
        comments = call_action(
            "comments_thread_show",
            subject_id=comments["subject_id"],
            subject_type=comments["subject_type"],
            include_comments=True,
            combine_comments=True,
        )
        assert len(comments["comments"]) == 1
        top = comments["comments"][0]
        assert top["id"] == comment["id"]
        assert len(top["replies"]) == 1
        assert top["replies"][0]["id"] == reply["id"]

    @pytest.mark.ckan_config(config.CONFIG_REQUIRE_APPROVAL, False)
    def test_optional_approval(self, comment: dict[str, Any]):
        assert comment["approved"]


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestCommentShow:
    def test_missing_comment(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exist")

    def test_comment_show(self, comment: dict[str, Any]):
        found = call_action("comments_comment_show", id=comment["id"])
        assert comment == found


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestCommentApprove:
    def test_missing_comment(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exists")

    def test_comment_approve(self, comment: dict[str, Any]):
        found = call_action("comments_comment_approve", id=comment["id"])
        assert found["state"] == "approved"


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestCommentDelete:
    def test_missing_comment(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exist")

    def test_comment_delete(self, comment: dict[str, Any]):
        call_action("comments_comment_delete", id=comment["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id=comment["id"])


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestCommentUpdate:
    def test_missing_comment(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_update", id="not-exist", content="content")

    def test_comment_update(self, comment: dict[str, Any]):
        content = "random content"

        assert comment["modified_at"] is None

        call_action("comments_comment_update", id=comment["id"], content=content)
        found = call_action("comments_comment_show", id=comment["id"])

        assert found["content"] != comment["content"]
        assert found["content"] == content
        assert found["modified_at"] > found["created_at"]
