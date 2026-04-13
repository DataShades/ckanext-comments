from __future__ import annotations

import datetime as dt
from typing import Any
from ckan import types
import pytest

import ckan.model as model
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action

import ckanext.comments.model as c_model
from ckanext.comments.model.dictize import comment_dictize, thread_dictize


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestDictize:
    def test_thread_dictize(
        self, thread: dict[str, Any], comment_factory: types.TestFactory
    ):
        comment = comment_factory(
            subject_id=thread["subject_id"],
            subject_type=thread["subject_type"],
        )
        call_action("comments_comment_approve", id=comment["id"])

        th = model.Session.query(c_model.Thread).filter_by(id=thread["id"]).one()
        dictized = thread_dictize(th, {"model": model, "user": ""})
        assert thread == dictized

        dictized = thread_dictize(
            th, {"model": model, "user": "", "include_comments": True}
        )
        comments = dictized.pop("comments")
        dictized["comments"] = None
        assert thread == dictized
        assert len(comments) == 1

    def test_comment_dictize(self, comment_factory: types.TestFactory):
        author = factories.User()
        comment = comment_factory(author_type="user", author_id=author["id"])
        c = model.Session.query(c_model.Comment).filter_by(id=comment["id"]).one()

        assert comment_dictize(c, {"model": model}) == comment

        dictized = comment_dictize(c, {"model": model, "include_author": True})
        dictized_author = dictized.pop("author")
        assert dictized == comment

        author.pop("email")
        author.pop("apikey")
        assert author == dictized_author

    def test_thread_dictize_with_comments(
        self, comment_factory: types.TestFactory, thread_factory: types.TestFactory
    ):
        sysadmin = factories.Sysadmin()
        user = factories.User()
        th = thread_factory()
        c1 = comment_factory(
            subject_id=th["subject_id"],
            subject_type=th["subject_type"],
        )
        c2 = comment_factory(
            subject_id=th["subject_id"], subject_type=th["subject_type"], user=user
        )
        c3 = comment_factory(
            subject_id=th["subject_id"],
            subject_type=th["subject_type"],
        )
        call_action("comments_comment_approve", id=c1["id"])
        thread = model.Session.query(c_model.Thread).filter_by(id=th["id"]).one()
        comments = thread_dictize(
            thread, {"model": model, "user": "", "include_comments": True}
        )["comments"]
        assert len(comments) == 1
        assert "author" not in comments[0]
        assert comments[0]["approved"]

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": "",
                "include_comments": True,
                "include_author": True,
            },
        )["comments"]
        assert len(comments) == 1
        assert "author" in comments[0]

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": user["name"],
                "include_comments": True,
                "include_author": True,
            },
        )["comments"]
        assert len(comments) == 2
        assert comments[0]["approved"]
        assert not comments[1]["approved"]

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": "",
                "include_comments": True,
                "ignore_auth": True,
            },
        )["comments"]
        assert len(comments) == 3
        assert not comments[1]["approved"]
        assert not comments[2]["approved"]

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": sysadmin["name"],
                "include_comments": True,
                "include_author": True,
            },
        )["comments"]
        assert len(comments) == 3

    def test_thread_dictize_comments_filter_by_date(
        self, comment_factory: types.TestFactory, thread_factory: types.TestFactory
    ):
        th = thread_factory()
        c1 = comment_factory(
            subject_id=th["subject_id"],
            subject_type=th["subject_type"],
        )
        comment_factory(
            subject_id=th["subject_id"],
            subject_type=th["subject_type"],
        )
        sysadmin = factories.Sysadmin()

        thread = model.Session.query(c_model.Thread).filter_by(id=th["id"]).one()

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": sysadmin["name"],
                "include_comments": True,
            },
        )["comments"]
        assert len(comments) == 2

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": sysadmin["name"],
                "include_comments": True,
                "after_date": (dt.datetime.now() + dt.timedelta(days=1)).isoformat(),
            },
        )["comments"]
        assert len(comments) == 0

        # Send a comment to the past :)
        comment = model.Session.query(c_model.Comment).get(c1.get("id"))
        comment.created_at = dt.datetime.now() - dt.timedelta(days=3)
        model.Session.commit()

        comments = thread_dictize(
            thread,
            {
                "model": model,
                "user": sysadmin["name"],
                "include_comments": True,
                "after_date": (dt.datetime.now() - dt.timedelta(days=1)).isoformat(),
            },
        )["comments"]
        assert len(comments) == 1
