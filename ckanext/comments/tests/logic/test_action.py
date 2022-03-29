import pytest
import datetime as dt

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action

import ckanext.comments.const as const


@pytest.mark.usefixtures("clean_db")
class TestThreadCreate:
    def test_cannot_create_thread_for_missing_object(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_thread_create",
                subject_type="package",
                subject_id="123-random",
            )

    @pytest.mark.usefixtures("clean_db")
    def test_thread_create(self):
        dataset = factories.Dataset()
        call_action(
            "comments_thread_create",
            subject_type="package",
            subject_id=dataset["id"],
        )


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

    @pytest.mark.usefixtures("clean_db")
    def test_thread_show(self, Thread, Comment):
        t = Thread()
        Comment(thread=t)
        comment = Comment(thread=t)
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


class TestThreadDelete:
    def test_cannot_delete_missing_thread(self):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_thread_delete", id="123-random")

    @pytest.mark.usefixtures("clean_db")
    def test_thread_delete(self, Thread):
        thread = Thread()
        call_action("comments_thread_delete", id=thread["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_thread_show",
                subject_id=thread["subject_id"],
                subject_type=thread["subject_type"],
            )


class TestCommentCreate:
    def test_missing_subject(self, Thread):
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_comment_create",
                subject_id="random-id",
                subject_type="package",
                content="content",
            )

    @pytest.mark.usefixtures("clean_db")
    def test_missing_author(self, Thread):
        thread = Thread()
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_comment_create",
                subject_id=thread["subject_id"],
                subject_type=thread["subject_type"],
                content="content",
            )

    @pytest.mark.usefixtures("clean_db")
    def test_controlled_author(self, Thread):
        user = factories.User()
        another_user = factories.User()
        thread = Thread()
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

    @pytest.mark.usefixtures("clean_db")
    def test_comment_create(self, Thread):
        user = factories.User()
        thread = Thread()
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

    @pytest.mark.usefixtures("clean_db")
    def test_existing_reply(self, Thread, Comment):
        user = factories.User()
        thread = Thread()
        comment = Comment(thread=thread)

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

    @pytest.mark.ckan_config(const.CONFIG_REQUIRE_APPROVAL, False)
    @pytest.mark.usefixtures("clean_db")
    def test_optional_approval(self, Comment):
        comment = Comment()
        assert comment["approved"]


class TestCommentShow:
    def test_missing_comment(self, Comment):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exist")

    @pytest.mark.usefixtures("clean_db")
    def test_comment_show(self, Comment):
        c = Comment()
        comment = call_action("comments_comment_show", id=c["id"])
        assert c == comment


class TestCommentApprove:
    def test_missing_comment(self, Comment):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exists")

    @pytest.mark.usefixtures("clean_db")
    def test_comment_approve(self, Comment):
        c = Comment()
        comment = call_action("comments_comment_approve", id=c["id"])
        assert comment["state"] == "approved"


class TestCommentDelete:
    def test_missing_comment(self, Comment):
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id="not-exist")

    @pytest.mark.usefixtures("clean_db")
    def test_comment_delete(self, Comment):
        c = Comment()
        call_action("comments_comment_delete", id=c["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_comment_show", id=c["id"])


class TestCommentUpdate:
    def test_missing_comment(self, Comment):
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_comment_update", id="not-exist", content="content"
            )

    @pytest.mark.usefixtures("clean_db")
    def test_comment_update(self, Comment):
        content = "random content"
        c = Comment()

        assert c["modified_at"] is None

        call_action("comments_comment_update", id=c["id"], content=content)
        comment = call_action("comments_comment_show", id=c["id"])

        assert comment["content"] != c["content"]
        assert comment["content"] == content
        assert comment["modified_at"] > comment["created_at"]
