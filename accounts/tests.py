import datetime
import json

from django.db import connection
from django.test import Client
from rest_framework import status

from accounts.models import User, UserManager, Role, Token

from rest_framework.test import APITestCase


class UserModelTests(APITestCase):
    def test_user_manager_fails_without_email_address(self):
        manager = UserManager()
        with self.assertRaises(ValueError):
            manager._create_user(password='12345')

    def test_can_create_user_with_email_and_password(self):
        user = User.objects.create_user(email='email@reelio.com', password='12345')
        user.save()

    def test_will_fail_with_duplicate_user(self):
        user = User.objects.create_user(email='none@reelio.com', password='12345')
        user.save()

        with self.assertRaises(ValueError):
            User.objects.create_user(email='none@reelio.com', password='12345')

    def test_can_create_superuser_with_email_and_password(self):
        user = User.objects.create_superuser(email='admin@reelio.com', password='12345')
        user.save()

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_user_permissions_set_properly(self):
        user = User.objects.create_user(email='user@reelio.com', password='12345')
        user.save()

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_user_email_set_as_shortname(self):
        user = User.objects.create_superuser(email='admin@reelio.com', password='12345')
        user.save()

        self.assertEquals(user.get_short_name(), 'admin@reelio.com')


class RoleModelTests(APITestCase):
    def test_role_can_save(self):
        role = Role(name='manager')
        role.save()

        self.assertEquals(role.name, 'manager')
        self.assertEquals(str(role), 'manager')


class APITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='none@reelio.com', password='12345')
        self.user.save()

    def tearDown(self):
        pass

    def test_can_register_new_user(self):
        c = Client()
        response = c.post('/v1/register/', {
            "email": "dave@reelio.com",
            "password": "12345"
        })

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)

        response = c.get('/v1/user/{}/'.format(response.data['id']))

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['email'], "dave@reelio.com")

    def test_cannot_register_without_password(self):
        c = Client()
        response = c.post('/v1/register/', {
            "email": "dave@reelio.com"
        })

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_authenticate_user(self):
        c = Client()
        response = c.post('/v1/auth/', {
            "email": "none@reelio.com",
            "password": "12345"
        })

        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue('token' in response.data)
        self.assertTrue('user' in response.data)

    def test_authentication_fails_with_bad_password(self):
        c = Client()
        response = c.post('/v1/auth/', {
            "email": "notme@reelio.com",
            "password": "1"
        })

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_add_role_to_user(self):
        user = User.objects.create_user(email='notme@reelio.com', password='12345')
        user.save()

        role = Role(name='manager')
        role.save()
        _id = user.id
        path = '/v1/user/{}/roles'.format(_id)

        c = Client()

        response = c.post(path, json.dumps({
            'roles': [str(role.id)]
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_will_throw_404_on_invalid_user_id(self):
        user = User.objects.create_user(email='notme@reelio.com', password='12345')
        user.save()

        role = Role(name='manager')
        role.save()
        _id = "9674cd52-37b0-4460-a69b-1563f0aed93a"
        path = '/v1/user/{}/roles'.format(_id)

        c = Client()

        response = c.post(path, json.dumps({
            'roles': [str(role.id)]
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_role_will_throw_500_error_on_invalid_role_id(self):
        user = User.objects.create_user(email='notme@reelio.com', password='12345')
        user.save()

        _id = user.id
        path = '/v1/user/{}/roles'.format(_id)

        c = Client()

        response = c.post(path, json.dumps({
            'roles': ["9674cd52-37b0-4460-a69b-1563f0aed93a"]
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_can_overwrite_user_roles(self):
        user = User.objects.create_user(email='notme@reelio.com', password='12345')
        user.save()

        role = Role(name='agent')
        role.save()
        _id = user.id
        path = '/v1/user/{}/'.format(_id)

        c = Client()

        response = c.put(path, json.dumps({
            'role': [str(role.id)]
        }), content_type='application/json')
        print(response.data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_overwrite_role_will_throw_500_error_on_invalid_role_id(self):
        user = User.objects.create_user(email='notme@reelio.com', password='12345')
        user.save()

        _id = user.id
        path = '/v1/user/{}/role/'.format(_id)

        c = Client()

        response = c.put(path, json.dumps({
            'roles': ["9674cd52-37b0-4460-a69b-1563f0aed93a"]
        }), content_type='application/json')
        print(response.data)
        self.assertEquals(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_can_remove_user_roles(self):
        user = User.objects.create_user(email='notme@reelio.com', password='12345')
        user.save()

        role = Role(name='agent')
        role.save()
        _id = user.id
        path = '/v1/user/{}/roles'.format(_id)

        c = Client()

        response = c.delete(path, json.dumps({
            'roles': [str(role.id)]
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_remove_role_will_throw_500_error_on_invalid_role_id(self):
        user = User.objects.create_user(email='notme@reelio.com', password='12345')
        user.save()

        _id = user.id
        path = '/v1/user/{}/roles'.format(_id)

        c = Client()

        response = c.delete(path, json.dumps({
            'roles': ["9674cd52-37b0-4460-a69b-1563f0aed93a"]
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_can_request_a_password_reset(self):
        user = User.objects.create_user(email='notme@reelio.com', password='12345')
        user.save()

        c = Client()

        response = c.post('/v1/request_password_change', json.dumps({
            "email": "notme@reelio.com"
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_can_confirm_a_new_user(self):
        token = Token(user_id=self.user.id, type='VERIFY')
        token.save()

        c = Client()
        response = c.post('/v1/confirm/{}/'.format(token.id))

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_fails_if_confirm_token_expired(self):
        timestamp = datetime.datetime.now() - datetime.timedelta(days=2)
        token = Token(user_id=self.user.id, type='VERIFY')
        token.save()

        # Overwrite token expiration time
        cursor = connection.cursor()
        cursor.execute("UPDATE communication_token SET expires='{}' WHERE id='{}'; ".format(str(timestamp), token.id))

        c = Client()
        response = c.post('/v1/confirm/{}/'.format(token.id))

        self.assertEquals(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_reset_expired_token(self):
        token = Token(user_id=self.user.id, type='VERIFY')
        token.save()

        c = Client()
        response = c.post('/v1/reset_confirm/{}/'.format(token.id), json.dumps({
            'email': 'none@reelio.com'
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_request_password_reset(self):

        c = Client()
        response = c.post('/v1/request_password_change/', json.dumps({
            'email': 'none@reelio.com'
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_reset_password(self):
        token = Token(user_id=self.user.id, type='RESET')
        token.save()

        c = Client()
        response = c.post('/v1/change_password/{}/'.format(token.id), json.dumps({
            'email': 'none@reelio.com',
            'password': '09876'
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_password_reset_fails_with_expired_token(self):
        timestamp = datetime.datetime.now() - datetime.timedelta(days=2)

        token = Token(user_id=self.user.id, type='RESET')
        token.save()

        # Overwrite token expiration time
        cursor = connection.cursor()
        cursor.execute("UPDATE accounts_token SET expires='{}' WHERE id='{}'; ".format(str(timestamp), token.id))

        c = Client()
        response = c.post('/v1/change_password/{}/'.format(token.id), json.dumps({
            'email': 'none@reelio.com',
            'password': '09876'
        }), content_type='application/json')

        self.assertEquals(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)