import pytest

import ckan.model as model

from ckan.cli.db import _resolve_alembic_config
import ckanext.comments.tests.factories as factories


@pytest.fixture
def clean_db(reset_db, monkeypatch):
    reset_db()
    monkeypatch.setattr(
        model.repo, "_alembic_ini", _resolve_alembic_config("comments")
    )
    model.repo.upgrade_db()


@pytest.fixture
def Thread():
    return factories.Thread


@pytest.fixture
def Comment():
    return factories.Comment
