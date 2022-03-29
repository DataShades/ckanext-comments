try:
    import ckan.plugins.toolkit as tk

    ckanext = tk.signals.ckanext
except AttributeError:
    from blinker import Namespace

    ckanext = Namespace()

created = ckanext.signal(u"comments:created")
"""Sent when a new comment created.
Params:
    sender: Thread ID
    comment: comment dictionary
"""

approved = ckanext.signal(u"comments:approved")
"""Sent when an existing comment is approved.
Params:
    sender: Thread ID
    comment: comment dictionary
"""

updated = ckanext.signal(u"comments:updated")
"""Sent after an update of exisning comment.
Params:
    sender: Thread ID
    comment: comment dictionary
"""

deleted = ckanext.signal(u"comments:deleted")
"""Sent when a comment is deleted.
Params:
    sender: Thread ID
    comment: comment dictionary
"""
