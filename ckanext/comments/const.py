CONFIG_REQUIRE_APPROVAL = "ckanext.comments.require_approval"

CONFIG_MODERATOR_CHECKER = "ckanext.comments.moderator_checker"

CONFIG_DRAFT_EDITS = "ckanext.comments.draft_edits"
CONFIG_APPROVED_EDITS = "ckanext.comments.approved_edits"

CONFIG_DRAFT_EDITS_BY_AUTHOR = "ckanext.comments.draft_edits_by_author"
CONFIG_APPROVED_EDITS_BY_AUTHOR = "ckanext.comments.approved_edits_by_author"

CONFIG_MOBILE_THRESHOLD = 'ckanext.comments.mobile_depth_threshold'

DEFAULT_REQUIRE_APPROVAL = True
DEFAULT_MODERATOR_CHECKER = "ckanext.comments.logic.auth:is_moderator"

DEFAULT_DRAFT_EDITS = True
DEFAULT_APPROVED_EDITS = False

DEFAULT_DRAFT_EDITS_BY_AUTHOR = False
DEFAULT_APPROVED_EDITS_BY_AUTHOR = False

DEFAULT_MOBILE_THRESHOLD = 3
