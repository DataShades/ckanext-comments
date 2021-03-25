[![Tests](https://github.com/DataShades/ckanext-comments/workflows/Tests/badge.svg?branch=main)](https://github.com/DataShades/ckanext-comments/actions)

# ckanext-comments

Add comment-trees to CKAN pages

## Requirements

* python >= 3.7
* CKAN >= 2.9

## Installation

To install ckanext-comments:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/DataShades/ckanext-comments.git
    cd ckanext-comments
    pip install -e .
	pip install -r requirements.txt

3. Add `comments` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Apply database migrations

    ckan db upgrade -p comments

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config settings


	# Require comment approval in order to make it visible
	# (optional, default: true).
	ckanext.comments.require_approval = false


## Developer installation

To install ckanext-comments for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/DataShades/ckanext-comments.git
    cd ckanext-comments
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
