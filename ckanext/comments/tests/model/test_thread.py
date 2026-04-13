import pytest
from ckan import types
import ckan.model as model
import ckan.tests.factories as factories

import ckanext.comments.model as c_model
from ckanext.comments.exceptions import UnsupportedSubjectType


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestThread:
    def test_comments(
        self, thread_factory: types.TestFactory, comment_factory: types.TestFactory
    ):
        th = thread_factory()
        thread = model.Session.query(c_model.Thread).filter_by(id=th["id"]).one()
        assert thread.comments().count() == 0

        comment_factory(
            subject_id=th["subject_id"],
            subject_type=th["subject_type"],
        )
        assert thread.comments().count() == 1

        comment_factory(
            subject_id=th["subject_id"],
            subject_type=th["subject_type"],
        )
        assert thread.comments().count() == 2

        comment_factory()
        assert thread.comments().count() == 2

    def test_get_subject(self):
        dataset = factories.Dataset()
        th = c_model.Thread(subject_type="taxes")

        with pytest.raises(UnsupportedSubjectType):
            th.get_subject()

        th.subject_type = "package"
        assert th.get_subject() is None

        th.subject_id = dataset["id"]
        assert th.get_subject().name == dataset["name"]

    def test_for_subject(self):
        dataset = factories.Dataset()
        assert c_model.Thread.for_subject("package", dataset["id"]) is None

        th = c_model.Thread.for_subject("package", dataset["id"], init_missing=True)
        assert th.id is None
        assert th.subject_type == "package"
        assert th.subject_id == dataset["id"]
