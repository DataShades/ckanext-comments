import ckan.model as model


def package_getter(id: str):
    return model.Package.get(id)


def resource_getter(id: str):
    return model.Resource.get(id)


def user_getter(id: str):
    return model.User.get(id)


def group_getter(id: str):
    return model.Group.get(id)
