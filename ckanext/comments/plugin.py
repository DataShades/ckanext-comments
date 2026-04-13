import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

import ckanext.comments.helpers as helpers
import ckanext.comments.logic.action as action
import ckanext.comments.logic.auth as auth
import ckanext.comments.logic.validators as validators

try:
    from ckanext.theming.interfaces import ITheme
except ImportError:
    ITheme = None

@tk.blanket.config_declarations
@tk.blanket.blueprints
class CommentsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)


    if ITheme:
        plugins.implements(ITheme, inherit=True)
        def get_additional_theme_ui_sources(self):
            return ["comments/ui.html"]

    # IConfigurer

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "comments")

    # IAuthFunctions

    def get_auth_functions(self):
        return auth.get_auth_functions()

    # IActions

    def get_actions(self):
        return action.get_actions()

    # ITemplateHelpers

    def get_helpers(self):
        return helpers.get_helpers()

    # IValidators

    def get_validators(self):
        return validators.get_validators()
