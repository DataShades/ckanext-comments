[![Tests](https://github.com/DataShades/ckanext-comments/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-comments/actions/workflows/test.yml)

# ckanext-comments

Add comment-trees to CKAN pages.

This plugins provides comment threads linked to any of the main CKAN entities:

* datasets
* resources
* groups
* organizations
* users.

All the features are API-first, so anything you can do via UI, can be done via API.

No changes to the WebUI are done by default. One have to include a snippet into
Jinja2 template in order to show the comments on a page.
```jinja2
{# subject_type := package | group | resource | user #}
{% snippet 'comments/snippets/thread.html', subject_id=pkg.id, subject_type='package' %}
```

:info: For the datasets it also can be achieved by enabling
`ckanext.comments.enable_default_dataset_comments` option.

## Requirements

* python >= 3.7
* CKAN >= 2.9

## Installation

To install ckanext-comments:

1. Install python package
  ```sh
  pip install ckanext-comments
  ```

1. Add `comments` to the `ckan.plugins` setting in your CKAN
   config file

1. Apply database migrations
  ```sh
  ckan db upgrade -p comments
  ```

1. Add `cooments/snippets/thread.html` to your `package/read.html` template, like this:
  ```jinja2
  {% ckan_extends %}

  {% block primary_content_inner %}
    {{ super() }}
    {% snippet 'comments/snippets/thread.html', subject_id=pkg.id, subject_type='package' %}
  {% endblock primary_content_inner %}
  ```

## Config settings
```ini

# Require comment approval in order to make it visible
# (optional, default: true).
ckanext.comments.require_approval = false

# Editor(admin) can edit draft comments
# (optional, default: true).
ckanext.comments.draft_edits = true

# Author can edit own draft comments
# (optional, default: true).
ckanext.comments.draft_edits_by_author = false

# Editor(admin) can edit approved comments
# (optional, default: false).
ckanext.comments.approved_edits = false

# Author can edit own approved comments
# (optional, default: false).
ckanext.comments.approved_edits_by_author = false

# Number of reply levels that are shown on mobile layout
# (optional, default: 3).
ckanext.comments.mobile_depth_threshold = 3

# Include default thread implementation on the dataset page
# (optional, default: false).
ckanext.comments.enable_default_dataset_comments = true
```

## API

### `comments_thread_create`
Create a thread for the subject.

Args:
* subject_id(str): unique ID of the commented entity
* subject_type(str:package|resource|user|group): type of the commented entity

### `comments_thread_show`
Show the subject's thread.

Args:
* subject_id(str): unique ID of the commented entity
* subject_type(str:package|resource|user|group): type of the commented entity
* init_missing(bool, optional): return an empty thread instead of 404
* include_comments(bool, optional): show comments from the thread
* include_author(bool, optional): show authors of the comments
* combine_comments(bool, optional): combine comments into a tree-structure
* after_date(str:ISO date, optional): show comments only since the given date

### `comments_thread_delete`
Delete the thread.

Args:
* id(str): ID of the thread

### `comments_comment_create`
Add a comment to the thread.

Args:
* subject_id(str): unique ID of the commented entity
* subject_type(str:package|resource|user|group): type of the commented entity
* content(str): comment's message
* reply_to_id(str, optional): reply to the existing comment
* create_thread(bool, optional): create a new thread if it doesn't exist yet

### `comments_comment_show`
Show the details of the comment

Args:
* id(str): ID of the comment

### `comments_comment_approve`
Approve draft comment

Args:
* id(str): ID of the comment

### `comments_comment_delete`
Remove existing comment

Args:
* id(str): ID of the comment

### `comments_comment_update`
Update existing comment

Args:
* id(str): ID of the comment
* content(str): comment's message


## Tests

To run the tests, do:
```sh
pytest
```


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
