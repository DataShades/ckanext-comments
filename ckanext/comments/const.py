CONFIG_REQUIRE_APPROVAL = "ckanext.comments.require_approval"
DEFAULT_REQUIRE_APPROVAL = True

CONFIG_DRAFT_EDITS = "ckanext.comments.draft_edits"
DEFAULT_DRAFT_EDITS = True

CONFIG_DRAFT_EDITS_BY_AUTHOR = "ckanext.comments.draft_edits_by_author"
DEFAULT_DRAFT_EDITS_BY_AUTHOR = True

CONFIG_APPROVED_EDITS = "ckanext.comments.approved_edits"
DEFAULT_APPROVED_EDITS = False

CONFIG_APPROVED_EDITS_BY_AUTHOR = "ckanext.comments.approved_edits_by_author"
DEFAULT_APPROVED_EDITS_BY_AUTHOR = False

CONFIG_MOBILE_THRESHOLD = "ckanext.comments.mobile_depth_threshold"
DEFAULT_MOBILE_THRESHOLD = 3

CONFIG_MODERATOR_CHECKER = "ckanext.comments.moderator_checker"
DEFAULT_MODERATOR_CHECKER = "ckanext.comments.utils:comments_is_moderator"

CONFIG_ENABLE_DATASET = "ckanext.comments.enable_default_dataset_comments"
DEFAULT_ENABLE_DATASET = False
