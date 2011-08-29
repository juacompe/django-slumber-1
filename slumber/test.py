"""
    A test version of the client.
"""
import mock

from slumber.connector.dictobject import DictObject


def _do_get(model, **query):
    """Implements a mocked version of the get operator.
    """
    for i in model.instances:
        found = True
        for k, v in query.items():
            found = found and getattr(i, k) == v
        if found:
            return i
    assert False, "The instance was not found"


class _DataConfiguration(DictObject):
    """Mock slumber data.
    """
    def __init__(self, **instances):
        super(_DataConfiguration, self).__init__()
        for model, instances in instances.items():
            root = self
            for k in model.split('__')[:-1]:
                if not hasattr(root, k):
                    setattr(root, k, DictObject())
                root = getattr(root, k)
            model_name = model.split('__')[-1]
            model_type = type(model_name, (DictObject,), {})
            setattr(model_type, 'instances',
                [model_type(**i) for i in instances])
            setattr(model_type, 'get', classmethod(_do_get))
            setattr(root, model_name, model_type)


class _MockClient(object):
    """A mock client that searches the current data stack for the data.
    """
    DATA_STACK = []
    def _flush_client_instance_cache(self):
        """Empty stub so that the middleware works in tests.
        """

    def __getattr__(self, name):
        """Try to find the attribute in the data stack.
        """
        return getattr(_MockClient.DATA_STACK[-1], name)


def mock_client(**instances):
    """Replaces the client with a mocked client that provides access to the
    provided applications, models and instances.
    """
    data = _DataConfiguration(**instances)
    def decorator(test_method):
        """The actual decorator that is going to be used on the test method.
        """
        @mock.patch('slumber._client', _MockClient())
        def test_wrapped(test, *a, **kw):
            """The wrapper for the test method.
            """
            try:
                _MockClient.DATA_STACK.insert(0, data)
                return test_method(test, *a, **kw)
            finally:
                _MockClient.DATA_STACK.remove(data)
        test_wrapped.__doc__ = test_method.__doc__
        return test_wrapped
    return decorator
