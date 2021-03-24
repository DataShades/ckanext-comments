from datetime import datetime
import ckan.model as model
from ckanext.comments.model import Thread, Comment


class TestComment:
    def test_relationships(self):
        t = Thread()
        assert t.comments == []
        c1 = Comment()
        c2 = Comment()

        assert c1.thread is None
        assert c2.thread is None

        c1.thread = t
        t.comments.append(c2)
        assert t.comments == [c1, c2]
        assert c1.thread is t
        assert c2.thread is t
