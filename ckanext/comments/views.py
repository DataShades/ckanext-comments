from __future__ import annotations
from ckan.logic import parse_params
import ckan.plugins.toolkit as tk
from flask import Blueprint

__all__ = [
    "bp",
]

bp = Blueprint("comments", __name__)


@bp.route("/thread/<subject_type>/<subject_id>/comment/post", methods=["POST"])
def post_comment(subject_type: str, subject_id: str):
    data = parse_params(tk.request.form)
    data.update(
        {
            "subject_id": subject_id,
            "subject_type": subject_type,
            "create_thread": "true",
        }
    )

    try:
        tk.get_action("comments_comment_create")({}, data)
    except tk.ValidationError:
        tk.h.flash_error(tk._("Cannot save a comment"))
    except tk.NotAuthorized:
        return tk.abort(403, tk._("Not authorized to post a comment"))

    came_from = (
        tk.request.args.get("came_from")
        or tk.request.headers.get("referer")
        or tk.url_for("home.index")
    )
    return tk.redirect_to(came_from)
