from ckan.logic.schema import validator_args
import ckan.plugins.toolkit as tk


@validator_args
def thread_create(not_empty, one_of):
    return {
        "subject_id": [
            not_empty,
        ],
        "subject_type": [
            not_empty,
            one_of(["package", "resource", "user", "group"]),
        ],
    }


@validator_args
def thread_show(default, boolean_validator, ignore_missing, isodate):
    schema = thread_create()
    schema.update(
        {
            "init_missing": [default(False), boolean_validator],
            "include_comments": [default(False), boolean_validator],
            "include_author": [default(False), boolean_validator],
            "combine_comments": [default(False), boolean_validator],
            "after_date": [ignore_missing, isodate],
        }
    )
    return schema


@validator_args
def thread_delete(not_empty):
    return {"id": [not_empty]}


@validator_args
def comment_create(
    not_empty, one_of, default, boolean_validator, ignore_missing
):
    return {
        "subject_id": [
            not_empty,
        ],
        "subject_type": [
            not_empty,
            one_of(["package", "resource", "user", "group"]),
        ],
        "content": [
            not_empty,
        ],
        "author_id": [
            ignore_missing,
        ],
        "author_type": [default("user"), one_of(["user"])],
        "reply_to_id": [
            ignore_missing,
            tk.get_validator("comments_comment_exists"),
        ],
        "create_thread": [default(False), boolean_validator],
    }


@validator_args
def comment_show(not_empty):
    return {"id": [not_empty]}


@validator_args
def comment_approve(not_empty):
    return {"id": [not_empty]}


@validator_args
def comment_delete(not_empty):
    return {"id": [not_empty]}


@validator_args
def comment_update(not_empty):
    return {
        "id": [not_empty],
        "content": [not_empty],
    }
