import pytest

import ckan.model as model
import ckan.tests.factories as factories

from ckan import types
import ckanext.comments.model as c_model
from ckanext.comments.exceptions import UnsupportedAuthorType


def test_approval():
    c = c_model.Comment(state=c_model.Comment.State.draft)
    assert not c.is_approved()
    c.approve()
    assert c.is_approved()


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestComment:
    def test_authored_by(self, comment_factory: types.TestFactory):
        author = factories.User()
        not_author = factories.User()
        comment = comment_factory(author_type="user", author_id=author["id"])
        c = model.Session.query(c_model.Comment).filter_by(id=comment["id"]).one()
        assert c.is_authored_by(author["id"])
        assert c.is_authored_by(author["name"])
        assert not c.is_authored_by(not_author["id"])
        assert not c.is_authored_by(not_author["name"])

    def test_by_thread(
        self, comment_factory: types.TestFactory, thread_factory: types.TestFactory
    ):
        th = thread_factory()
        c1 = comment_factory(
            subject_id=th["subject_id"],
            subject_type=th["subject_type"],
        )
        c2 = comment_factory(
            subject_id=th["subject_id"],
            subject_type=th["subject_type"],
        )
        c3 = comment_factory()

        g1, g2, g3 = (
            [c.id for c in group]
            for group in [
                c_model.Comment.by_thread(c["thread_id"]) for c in [c1, c2, c3]
            ]
        )

        assert g1 == g2
        assert g1 == [c1["id"], c2["id"]]
        assert g3 == [c3["id"]]

    def test_get_author(self):
        user = factories.User()
        comment = c_model.Comment(author_type="fairy")
        with pytest.raises(UnsupportedAuthorType):
            comment.get_author()

        comment.author_type = "user"
        assert comment.get_author() is None

        comment.author_id = user["id"]
        assert comment.get_author().name == user["name"]
