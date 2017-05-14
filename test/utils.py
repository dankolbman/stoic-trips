import jwt
import json
import unittest
from trips import create_app, db


class FlaskTestCase(unittest.TestCase):
    """ Contains base logic for setting up a Flask app """

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _api_headers(self, username=None):
        """
        Returns headers for a json request along with a JWT for authenticating
        as a given user
        """
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        if username:
            auth = jwt.encode({"identity": {"username": username},
                               "nbf": 1493862425,
                               "exp": 9999999999,
                               "iat": 1493862425},
                              "secret", algorithm="HS256")
            headers['Authorization'] = 'JWT ' + auth.decode('utf-8')
        return headers

    def make_trip(self, username, **kwargs):
        """
        Makes a trip via the REST API
        """
        defaults = {'name': 'trip 1',
                    'start': 'Ho Chi Minh',
                    'finish': 'Hanoi',
                    'public': True,
                    'description': 'Lorem ipsum'}
        defaults.update(**kwargs)
        resp = self.client.post('/trips/'+username,
                                headers=self._api_headers(username=username),
                                data=json.dumps(defaults))
        json_resp = json.loads(resp.data.decode('utf-8'))
        return json_resp
