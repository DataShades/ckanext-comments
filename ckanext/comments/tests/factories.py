import factory
from factory.fuzzy import FuzzyText

import ckanext.comments.model as model

import ckan.tests.helpers as helpers
import ckan.tests.factories as factories


class Thread(factory.Factory):
    """A factory class for creating CKAN datasets."""

    class Meta:
        model = model.Thread

    subject_id = factory.LazyAttribute(lambda _: factories.Dataset()["id"])
    subject_type = "package"

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        context = {"user": factories._get_action_user_name(kwargs)}
        thread_dict = helpers.call_action(
            "comments_thread_create", context=context, **kwargs
        )
        return thread_dict


class Comment(factory.Factory):
    """A factory class for creating CKAN datasets."""

    class Meta:
        model = model.Comment

    thread = factory.LazyAttribute(lambda _: Thread())
    content = FuzzyText("content:", 140)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        context = {"user": factories._get_action_user_name(kwargs)}

        thread = kwargs.pop("thread")
        kwargs["subject_id"] = thread["subject_id"]
        kwargs["subject_type"] = thread["subject_type"]

        comment_dict = helpers.call_action(
            "comments_comment_create", context=context, **kwargs
        )
        return comment_dict
