import pytest

import ckan.model as model
from ckanext.comments.model import Thread, Comment


class TestComment:
    def test_relationships(self):
        c = Comment(state=Comment.State.draft)
        assert not c.is_approved()
        c.approve()
        assert c.is_approved()
