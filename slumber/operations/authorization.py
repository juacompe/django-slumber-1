"""
    Implements authorization checks for users.
"""
from slumber.operations import InstanceOperation


class PermissionCheck(InstanceOperation):
    """Allows for checking if a given user has a specific permission.
    """
    def __init__(self, *args, **kwargs):
        super(PermissionCheck, self).__init__(*args, **kwargs)
        self.regex = '([^/]+)/([^/]+)/'

    def get(self, _request, response, _appname, _modelname, pk, permission):
        """Implements the permission lookup.
        """
        user = self.model.model.objects.get(pk=pk)
        response['is-allowed'] = user.has_perm(permission.replace('-', '.'))
