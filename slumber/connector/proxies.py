"""
    Proxies are used as base types for instances so that new APIs can be added.
"""
from urlparse import urljoin

from django.contrib.auth.models import User

from slumber.connector.ua import get, post


def attach_to_local_user(remote_user):
    """Return the local user with the remote user object attached to it.
    """
    user, created = User.objects.get_or_create(
        username=remote_user.username)
    if created:
        for attr in ['is_active', 'is_staff', 'date_joined', 'is_superuser',
                'first_name', 'last_name', 'email']:
            v = getattr(remote_user, attr)
            setattr(user, attr, v)
        user.save()
    user.remote_user = remote_user
    return user


class UserInstanceProxy(object):
    """Proxy that allows forwarding of the User API.
    """

    def has_perm(self, permission):
        """Forward the permission check.
        """
        # We're accessing attributes that are providec by the  other types
        # pylint: disable = E1101
        _, json = get(urljoin(self._operations['has-permission'], permission))
        return json['is-allowed']

    def has_module_perms(self, module):
        """Forward the permission check.
        """
        # We're accessing attributes that are providec by the  other types
        # pylint: disable = E1101
        _, json = get(urljoin(self._operations['module-permissions'], module))
        return json['has_module_perms']

    def get_group_permissions(self):
        """Forward the group permissions.
        """
        # We're accessing attributes that are providec by the  other types
        # pylint: disable = E1101
        _, json = get(self._operations['get-permissions'])
        return set(json['group_permissions'])

    def get_all_permissions(self):
        """Forward access to all of the permissions.
        """
        # We're accessing attributes that are providec by the  other types
        # pylint: disable = E1101
        _, json = get(self._operations['get-permissions'])
        return set(json['all_permissions'])


class UserModelProxy(object):
    """Contains the model methods that need to be exposed within the client.
    """

    def authenticate(self, **kwargs):
        """Allow a forwarded request for authentication.
        """
        # We're accessing attributes that are providec by the  other types
        # pylint: disable = E1101
        _, json = post(self._operations['authenticate'], kwargs)
        if json['authenticated']:
            # Pylint can't see the __call__ implemented in another base class
            # pylint: disable = E1102
            remote_user = self(urljoin(self._url, json['user']['url']),
                json['user']['display_name'])
            return attach_to_local_user(remote_user)
