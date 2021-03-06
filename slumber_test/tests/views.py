from simplejson import loads

from django.contrib.auth.models import User, Permission
from django.test import TestCase

from slumber_test.models import Pizza, PizzaPrice


def _perform(client, method, url, data):
    response = getattr(client, method)(url, data,
        HTTP_HOST='localhost', REMOTE_ADDR='127.0.0.1')
    if response.status_code == 200:
        return response, loads(response.content)
    else:
        return response, {}


class ViewTests(TestCase):
    """Base class for view tests that give us some user agent functionality.
    """
    def do_get(self, url, query = {}):
        return _perform(self.client, 'get', url, query)

    def do_post(self, url, body):
        return _perform(self.client, 'post', url, body)


class TestViewErrors(ViewTests):

    def test_method_error(self):
        response, json = self.do_post('/slumber/slumber_test/Pizza/instances/', {})
        self.assertEquals(response.status_code, 403)

    def test_invalid_method(self):
        response = self.client.get('/slumber/slumber_test/Pizza/instances/',
            REQUEST_METHOD='PURGE', HTTP_HOST='localhost', REMOTE_ADDR='127.0.0.1')
        self.assertEquals(response.status_code, 403, response.content)


class TestBasicViews(ViewTests):

    def test_applications(self):
        response, json = self.do_get('/slumber/')
        apps = json['apps']
        self.assertEquals(apps['slumber_test'], '/slumber/slumber_test/')

    def test_model_search_success(self):
        response, json = self.do_get('/slumber/', {'model': 'slumber_test.Pizza'})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'],
            'http://localhost/slumber/slumber_test/Pizza/')

    def test_model_search_invalid(self):
        response, json = self.do_get('/slumber/', {'model': 'nota.model'})
        self.assertEquals(response.status_code, 404)


    def test_application_with_models(self):
        response, json = self.do_get('/slumber/slumber_test/')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(json['models']))
        self.assertEquals(json['models']['Pizza'],
            '/slumber/slumber_test/Pizza/')


    def test_application_without_models(self):
        response, json = self.do_get('/slumber/slumber_test/no_models/')
        self.assertEquals(response.status_code, 200)
        self.assertFalse(len(json['models']))


    def test_instance_metadata_pizza(self):
        response, json = self.do_get('/slumber/slumber_test/Pizza/')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(json['fields'].has_key('for_sale'))
        self.assertEquals(json['fields']['for_sale']['type'],
            'django.db.models.fields.BooleanField')
        self.assertEquals(json['operations']['instances'],
            '/slumber/slumber_test/Pizza/instances/')
        self.assertFalse(json['operations'].has_key('data'), json['operations'])
        self.assertTrue(json['operations'].has_key('get'), json['operations'])

    def test_instance_metadata_pizzaprice(self):
        response, json = self.do_get('/slumber/slumber_test/PizzaPrice/')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(json['fields'].has_key('pizza'))
        self.assertEquals(json['fields']['pizza']['type'],
            '/slumber/slumber_test/Pizza/')

    def test_model_metadata_user(self):
        response, json = self.do_get('/slumber/django/contrib/auth/User/')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(json['operations'].has_key('authenticate'), json['operations'])
        self.assertEquals(json['operations']['authenticate'],
            '/slumber/django/contrib/auth/User/authenticate/')

    def test_instance_metadata_user(self):
        user = User(username='test-user')
        user.save()
        response, json = self.do_get('/slumber/django/contrib/auth/User/data/%s/' %
            user.pk)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(json['operations'].has_key('has-permission'), json['operations'])


    def test_instance_puttable(self):
        response, json = self.do_get('/slumber/slumber_test/Pizza/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json['puttable'], [['id'], ['name']])


    def test_model_operation_instances_no_instances(self):
        response, json = self.do_get('/slumber/slumber_test/Pizza/instances/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json['page']), 0)

    def test_model_operation_instances_one_instance(self):
        Pizza(name='S1', for_sale=True).save()
        response, json = self.do_get('/slumber/slumber_test/Pizza/instances/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json['page']), 1)

    def test_model_operation_instances_twelve_instances(self):
        for i in range(12):
            Pizza(name='S%s' % i, for_sale=True).save()
        response, json = self.do_get('/slumber/slumber_test/Pizza/instances/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json['page']), 10)
        self.assertEquals(json['next_page'],
            '/slumber/slumber_test/Pizza/instances/?start_after=3')
        response, json = self.do_get('/slumber/slumber_test/Pizza/instances/',
            {'start_after': '3'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json['page']), 2)
        self.assertEquals(json['next_page'],
            '/slumber/slumber_test/Pizza/instances/?start_after=1')
        response, json = self.do_get('/slumber/slumber_test/Pizza/instances/',
            {'start_after': '1'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json['page']), 0)
        self.assertFalse(json.has_key('next_page'), json)


    def test_instance_creation_get(self):
        response, json = self.do_get('/slumber/slumber_test/Pizza/create/')
        self.assertEquals(response.status_code, 403, response.content)

    def test_instance_creation_post(self):
        response, json = self.do_post('/slumber/slumber_test/Pizza/create/',
            {'name': 'Test Pizza', 'for_sale': ''})
        self.assertTrue(json['created'])
        self.assertEquals(Pizza.objects.count(), 1)
        self.assertEquals(Pizza.objects.all()[0].name, 'Test Pizza')
        self.assertFalse(Pizza.objects.all()[0].for_sale)


    def test_update_instance(self):
        s = Pizza(name='S1', for_sale=True)
        s.save()
        response, json = self.do_post('/slumber/slumber_test/Pizza/update/1/', {
            'name': 'New pizza'})
        self.assertEquals(response.status_code, 302)
        n = Pizza.objects.get(pk=1)
        self.assertEquals(n.name, "New pizza")


    def test_get_instance(self):
        s = Pizza(name='S1', for_sale=True)
        s.save()
        response, json = self.do_get('/slumber/slumber_test/Pizza/')
        get_url = json['operations']['get']
        self.assertEquals(get_url, '/slumber/slumber_test/Pizza/get/')
        def check_query(query):
            response, json = self.do_get(get_url, query)
            self.assertEquals(response.status_code, 302, response)
            self.assertEquals(response['location'],
                'http://localhost/slumber/slumber_test/Pizza/data/%s/' % s.pk)
        check_query({'pk': s.pk})
        check_query({'id': s.pk})
        check_query({'name': s.name})

    def test_instance_data_pizza(self):
        s = Pizza(name='S1', for_sale=True)
        s.save()
        response, json = self.do_get('/slumber/slumber_test/Pizza/data/%s/' % s.pk)
        self.maxDiff = None
        self.assertEquals(json, dict(
            _meta={'message': 'OK', 'status': 200},
            identity='/slumber/slumber_test/Pizza/data/1/',
            display='S1',
            operations=dict(
                data='/slumber/slumber_test/Pizza/data/1/',
                delete='/slumber/slumber_test/Pizza/delete/1/',
                update='/slumber/slumber_test/Pizza/update/1/'),
            fields=dict(
                id=dict(data=s.pk, kind='value', type='django.db.models.fields.AutoField'),
                for_sale=dict(data=s.for_sale, kind='value', type='django.db.models.fields.BooleanField'),
                max_extra_toppings=dict(data=s.max_extra_toppings, kind='value', type='django.db.models.fields.IntegerField'),
                name=dict(data=s.name, kind='value', type='django.db.models.fields.CharField'),
                exclusive_to={'data': None, 'kind': 'object', 'type': '/slumber/slumber_test/Shop/'}),
            data_arrays=dict(
                prices='/slumber/slumber_test/Pizza/data/%s/prices/' % s.pk)))

    def test_instance_data_pizzaprice(self):
        s = Pizza(name='p1', for_sale=True)
        s.save()
        p = PizzaPrice(pizza=s, date='2010-01-01')
        p.save()
        response, json = self.do_get('/slumber/slumber_test/PizzaPrice/data/%s/' % p.pk)
        self.assertEquals(json, dict(
            _meta={'message': 'OK', 'status': 200},
            identity='/slumber/slumber_test/PizzaPrice/data/1/',
            display="PizzaPrice object",
            operations=dict(
                data='/slumber/slumber_test/PizzaPrice/data/1/',
                delete='/slumber/slumber_test/PizzaPrice/delete/1/',
                update='/slumber/slumber_test/PizzaPrice/update/1/'),
            fields=dict(
                id={'data': 1, 'kind': 'value', 'type': 'django.db.models.fields.AutoField'},
                pizza={'data': {
                        'type': '/slumber/slumber_test/Pizza/', 'display':'p1',
                        'data': '/slumber/slumber_test/Pizza/data/1/'},
                    'kind': 'object', 'type': '/slumber/slumber_test/Pizza/'},
                date={'data': '2010-01-01', 'kind': 'value', 'type': 'django.db.models.fields.DateField'},
            ),
            data_arrays={'amounts': '/slumber/slumber_test/PizzaPrice/data/1/amounts/'}))

    def test_instance_data_array(self):
        s = Pizza(name='P', for_sale=True)
        s.save()
        for p in range(15):
            PizzaPrice(pizza=s, date='2011-04-%s' % (p+1)).save()
        response, json = self.do_get('/slumber/slumber_test/Pizza/data/%s/prices/' % s.pk)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json['page']), 10, json)
        self.assertTrue(json.has_key('next_page'), json)
        self.assertEquals(json['next_page'],
            '/slumber/slumber_test/Pizza/data/1/prices/?start_after=6',
            json['next_page'])
        response, json = self.do_get('/slumber/slumber_test/Pizza/data/1/prices/',
            {'start_after': '6'})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(json['page']), 5)
        self.assertEquals(json['page'][0], {
            'type': '/slumber/slumber_test/PizzaPrice/',
            'pk': 5, 'data': '/slumber/slumber_test/PizzaPrice/data/5/', 'display': 'PizzaPrice object'})
        self.assertFalse(json.has_key('next_page'), json.keys())


    def test_delete_instance(self):
        s = Pizza(name='P')
        s.save()
        response, json = self.do_get('/slumber/slumber_test/Pizza/data/%s/' % s.pk)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(json['operations'].has_key('delete'), json['operations'])
        response, json = self.do_post(json['operations']['delete'], {})
        self.assertEquals(response.status_code, 200)
        with self.assertRaises(Pizza.DoesNotExist):
            Pizza.objects.get(pk=s.pk)


class TestUserViews(ViewTests):
    authn = '/slumber/django/contrib/auth/User/authenticate/'
    perm = '/slumber/django/contrib/auth/User/has-permission/%s/%s/'

    def setUp(self):
        self.user = User(username='test-user')
        self.user.set_password('password')
        self.user.save()

    def test_user_not_found(self):
        response, json = self.do_post(self.authn, dict(username='not-a-user', password=''))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json['authenticated'], False, json)
        self.assertIsNone(json['user'], json)

    def test_user_wrong_password(self):
        response, json = self.do_post(self.authn,
            dict(username=self.user.username, password='wrong'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json['authenticated'], False, json)
        self.assertIsNone(json['user'], json)

    def test_user_authenticates(self):
        response, json = self.do_post(self.authn,
            dict(username=self.user.username, password='password'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json['authenticated'], True, json)
        self.assertEquals(json['user'], {'pk': self.user.pk})

    def test_user_permission_no_permission(self):
        response, json = self.do_get(self.perm % (self.user.pk, 'foo.example'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json['is-allowed'], False, json)

    def test_user_permission_is_allowed(self):
        permission = Permission(content_type_id=1, name='Can something',
            codename='can_something')
        permission.save()
        self.user.user_permissions.add(permission)
        response, json = self.do_get(self.perm % (self.user.pk, 'auth.can_something'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json['is-allowed'], True, json)

    def test_user_permission_not_allowed(self):
        permission = Permission(content_type_id=1, name='Can something',
            codename='can_something')
        permission.save()
        response, json = self.do_get(self.perm % (self.user.pk, 'auth.can_something'))
        self.assertEquals(response.status_code, 200)
        self.assertEquals(json['is-allowed'], False, json)
