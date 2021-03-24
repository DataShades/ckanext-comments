import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action


@pytest.mark.usefixtures("clean_db")
class TestThread:
    def test_thread_create(self):
        dataset = factories.Dataset()
        with pytest.raises(tk.ValidationError):
            call_action("comments_thread_create", object_id=dataset["id"])
        with pytest.raises(tk.ValidationError):
            call_action("comments_thread_create", object_type="package")
        with pytest.raises(tk.ObjectNotFound):
            call_action(
                "comments_thread_create",
                object_type="package",
                object_id="123-random",
            )

        thread = call_action(
            "comments_thread_create",
            object_type="package",
            object_id=dataset["id"],
        )

    def test_thread_show(self):
        dataset = factories.Dataset()
        thread = call_action(
            "comments_thread_create",
            object_type="package",
            object_id=dataset["id"],
        )
        with pytest.raises(tk.ValidationError):
            call_action("comments_thread_show")
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_thread_show", id="123-random")
        call_action("comments_thread_show", id=thread["id"])

    def test_thread_delete(self):
        dataset = factories.Dataset()
        thread = call_action(
            "comments_thread_create",
            object_type="package",
            object_id=dataset["id"],
        )
        with pytest.raises(tk.ValidationError):
            call_action("comments_thread_delete")
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_thread_delete", id="123-random")
        call_action("comments_thread_delete", id=thread["id"])
        with pytest.raises(tk.ObjectNotFound):
            call_action("comments_thread_show", id=thread["id"])
