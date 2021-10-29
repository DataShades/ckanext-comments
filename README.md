[![Tests](https://github.com/DataShades/ckanext-comments/workflows/Tests/badge.svg?branch=main)](https://github.com/DataShades/ckanext-comments/actions)

# ckanext-comments

Add comment-trees to CKAN pages

## Requirements

* python >= 3.7
* CKAN >= 2.9

## Installation

To install ckanext-comments:

1. Install python package

        pip install ckanext-comments

1. Add `comments` to the `ckan.plugins` setting in your CKAN
   config file

1. Apply database migrations

        ckan db upgrade -p comments

1. Add `cooments/snippets/thread.html` to your `package/read.html` template, like this:

        {% ckan_extends %}
        {% block primary_content_inner %}
            {{ super() }}
            {% snippet 'comments/snippets/thread.html', subject_id=pkg.id, subject_type='package' %}
        {% endblock primary_content_inner %}

## Config settings


	# Require comment approval in order to make it visible
	# (optional, default: true).
	ckanext.comments.require_approval = false

	# Editor(admin) can edit draft comments
	# (optional, default: true).
    ckanext.comments.draft_edits = true

	# Editor(admin) can edit approved comments
	# (optional, default: false).
    ckanext.comments.approved_edits = false

	# Author can edit own draft comments
	# (optional, default: false).
    ckanext.comments.draft_edits_by_author = false

	# Author can edit own approved comments
	# (optional, default: false).
    ckanext.comments.approved_edits_by_author = false

	# Number of reply levels that are shown on mobile layout
	# (optional, default: 3).
    ckanext.comments.mobile_depth_threshold = 3

## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
