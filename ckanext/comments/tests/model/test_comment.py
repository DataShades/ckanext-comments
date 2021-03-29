from ckan.tests.helpers import call_action
import pytest

import ckan.model as model
import ckan.tests.factories as factories

import ckanext.comments.model as c_model
from ckanext.comments.exceptions import UnsupportedAuthorType


def test_approval():
    c = c_model.Comment(state=c_model.Comment.State.draft)
    assert not c.is_approved()
    c.approve()
    assert c.is_approved()


@pytest.mark.usefixtures("clean_db")
class TestComment:
    def test_authored_by(self, Comment):
        author = factories.User()
        not_author = factories.User()
        comment = Comment(author_type="user", author_id=author["id"])
        c = (
            model.Session.query(c_model.Comment)
            .filter_by(id=comment["id"])
            .one()
        )
        assert c.is_authored_by(author["id"])
        assert c.is_authored_by(author["name"])
        assert not c.is_authored_by(not_author["id"])
        assert not c.is_authored_by(not_author["name"])

    def test_dictize(self, Comment):
        author = factories.User()
        comment = Comment(author_type="user", author_id=author["id"])
        c = (
            model.Session.query(c_model.Comment)
            .filter_by(id=comment["id"])
            .one()
        )

        assert c.dictize({"model": model}) == comment

        dictized = c.dictize({"model": model, "include_author": True})
        dictized_author = dictized.pop("author")
        assert dictized == comment

        author.pop("email")
        author.pop("apikey")
        assert author == dictized_author

    def test_by_thread(self, Comment, Thread):
        th = Thread()
        c1 = Comment(thread=th)
        c2 = Comment(thread=th)
        c3 = Comment()

        g1, g2, g3 = (
            [c.id for c in group]
            for group in [
                c_model.Comment.by_thread(c["thread_id"]) for c in [c1, c2, c3]
            ]
        )

        assert g1 == g2
        assert g1 == [c1["id"], c2["id"]]
        assert g3 == [c3["id"]]

    def test_dictize_thread(self, Comment, Thread):
        sysadmin = factories.Sysadmin()
        user = factories.User()
        th = Thread()
        c1 = Comment(thread=th)
        c2 = Comment(thread=th, user=user)
        c3 = Comment(thread=th)
        call_action("comments_comment_approve", id=c1["id"])

        comments = c_model.Comment.dictize_thread(
            th["id"], {"model": model, "user": ""}
        )
        assert len(comments) == 1
        assert "author" not in comments[0]
        assert comments[0]["approved"]

        comments = c_model.Comment.dictize_thread(
            th["id"], {"model": model, "user": "", "include_author": True}
        )
        assert len(comments) == 1
        assert "author" in comments[0]

        comments = c_model.Comment.dictize_thread(
            th["id"], {"model": model, "user": user["name"]}
        )
        assert len(comments) == 2
        assert comments[0]["approved"]
        assert not comments[1]["approved"]

        comments = c_model.Comment.dictize_thread(
            th["id"], {"model": model, "user": "", "ignore_auth": True}
        )
        assert len(comments) == 3
        assert not comments[1]["approved"]
        assert not comments[2]["approved"]

        comments = c_model.Comment.dictize_thread(
            th["id"], {"model": model, "user": sysadmin["name"]}
        )
        assert len(comments) == 3

    def test_get_author(self):
        user = factories.User()
        comment = c_model.Comment(author_type="fairy")
        with pytest.raises(UnsupportedAuthorType):
            comment.get_author()

        comment.author_type = "user"
        assert comment.get_author() is None

        comment.author_id = user["id"]
        assert comment.get_author().name == user["name"]
