from __future__ import annotations
from typing import Any

from factory.declarations import LazyAttribute
from factory.fuzzy import FuzzyText

import ckan.tests.factories as factories

import ckanext.comments.model as model

import pytest
from pytest_factoryboy import register


@pytest.fixture
def clean_db(reset_db: Any, migrate_db_for: Any):
    reset_db()
    migrate_db_for("comments")


@register
class ThreadFactory(factories.CKANFactory):
    """A factory class for creating CKAN datasets."""

    class Meta:
        model = model.Thread
        action = "comments_thread_create"

    subject_id = LazyAttribute(lambda _: factories.Dataset()["id"])
    subject_type = "package"


@register
class CommentFactory(factories.CKANFactory):
    """A factory class for creating CKAN datasets."""

    class Meta:
        model = model.Comment
        action = "comments_comment_create"

    subject_id = LazyAttribute(lambda _: factories.Dataset()["id"])
    subject_type = "package"
    create_thread = True
    content = FuzzyText("content:", 140)
