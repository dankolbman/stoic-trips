import json
import time
import unittest
from datetime import datetime

from flask import current_app, url_for
from trips import create_app, db
from trips.model import Trip

from test.utils import FlaskTestCase


class tripTestCase(FlaskTestCase):

    def test_status(self):
        """
        Test the status endpoint
        """
        resp = self.client.get('/status')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['status'], 200)
        self.assertEqual(len(json_resp['version']), 7)

    def test_new_trip(self):
        """
        Test trip creation via REST API
        """
        resp, json_resp = self.make_trip('Dan')
        # check api response
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(json_resp['message'], 'created trip')
        # check that user is in database
        self.assertEqual(Trip.query.count(), 1)
        trip = Trip.query.first()
        self.assertEqual(trip.username, 'Dan')
        self.assertEqual(trip.title, 'trip 1')
        self.assertEqual(trip.start, 'Ho Chi Minh')
        self.assertEqual(trip.finish, 'Hanoi')
        self.assertEqual(trip.public, True)
        self.assertEqual(trip.description, 'Lorem ipsum')

    def test_no_trips(self):
        """
        Test result for no trips/user
        """
        resp = self.client.get('/trips/Dan',
                               headers=self._api_headers())
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(resp.status_code, 404)

    def test_no_trip_by_id(self):
        """
        Test result for no trip by id
        """
        resp = self.client.get('/trips/Dan/122',
                               headers=self._api_headers())
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(resp.status_code, 404)

    def test_404(self):
        """
        Test result for invalid page
        """
        resp = self.client.get('/trips/Dan/122aab',
                               headers=self._api_headers())
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(json_resp['message'], 'not found')

    def test_missing_field(self):
        """
        Test repsonse when name field is missing
        """
        defaults = {'start': 'Ho Chi Minh',
                    'finish': 'Hanoi',
                    'public': True,
                    'description': 'Lorem ipsum'}
        resp = self.client.post('/trips/Dan',
                                headers=self._api_headers(username='Dan'),
                                data=json.dumps(defaults))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(json_resp['message'], 'missing fields: title')

    def test_empty_post(self):
        """
        Test repsonse when no data is posted
        """
        resp = self.client.post('/trips/Dan',
                                headers=self._api_headers(username='Dan'))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertIn('Failed to decode', json_resp['message'])

    def test_single_trip(self):
        """
        Test repsonse of single trip
        """
        resp, trip1 = self.make_trip('Dan', title='Dans trip')
        tid = trip1['trip']['id']
        self.assertEqual(trip1['trip']['title'], 'Dans trip')
        resp = self.client.get('/trips/Dan/'+str(tid),
                               headers=self._api_headers(username='Dan'))
        trip2 = json.loads(resp.data.decode('utf-8'))
        self.assertDictEqual(trip1['trip'], trip2['trip'])
        self.assertEqual(type(trip1['trip']['id']), int)

    def test_multi_user(self):
        """
        Test that /trips will return trips from different users
        """
        resp, json_resp = self.make_trip('Dan', title='Dans trip')
        resp, json_resp = self.make_trip('Bob', title='Bobs trip')
        self.assertEqual(Trip.query.count(), 2)
        resp = self.client.get('/trips/')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 2)

    def test_delete(self):
        """
        Test deletion of trips
        """
        resp, json_resp = self.make_trip('Dan', title='Dans trip')
        resp, json_resp = self.make_trip('Bob', title='Bobs trip')
        resp, json_resp = self.make_trip('Dan', title='Dans 2nd trip')
        self.assertEqual(Trip.query.count(), 3)
        resp = self.client.delete('/trips/Dan/1')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(resp.status_code, 403)

        resp = self.client.delete('/trips/Dan/1',
                                  headers=self._api_headers(username='Bob'))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(resp.status_code, 403)

        resp = self.client.delete('/trips/Dan/1',
                                  headers=self._api_headers(username='Dan'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Trip.query.count(), 2)

        resp = self.client.delete('/trips/Dan/1',
                                  headers=self._api_headers(username='Dan'))
        self.assertEqual(resp.status_code, 404)

    def test_size_param(self):
        """
        Test the ?size param
        """
        for i in range(4):
            resp = self.make_trip('Dan', title='Dans trip')
        for i in range(3):
            resp = self.make_trip('Bob', title='Bobs trip')
        for i in range(13):
            resp = self.make_trip('Dan', title='Dans trip')
            resp = self.make_trip('Bob', title='Bobs trip')
        self.assertEqual(Trip.query.count(), 33)
        # Test size
        resp = self.client.get('/trips/',
                               headers=self._api_headers(),
                               query_string=dict(size=5))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(len(json_resp['trips']), 5)
        self.assertEqual(json_resp['total'], 33)

        resp = self.client.get('/trips/Dan',
                               headers=self._api_headers(),
                               query_string=dict(size=8))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(len(json_resp['trips']), 8)
        self.assertEqual(json_resp['total'], 17)

    def test_start_param(self):
        """
        Test the ?start param
        """
        t0 = datetime.utcnow().isoformat()
        for i in range(4):
            resp = self.make_trip('Dan', title='Dans', created_at=t0)
        for i in range(3):
            resp = self.make_trip('Bob', title='Bobs', created_at=t0)
        time.sleep(0.1)
        t1 = datetime.utcnow().isoformat()
        time.sleep(0.1)
        t2 = datetime.utcnow().isoformat()
        for i in range(2):
            resp = self.make_trip('Dan', title='Dans', created_at=t2)
            resp = self.make_trip('Bob', title='Bobs', created_at=t2)
        self.assertEqual(Trip.query.count(), 11)
        # Test start
        resp = self.client.get('/trips/',
                               headers=self._api_headers(),
                               query_string=dict(start=t1))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(len(json_resp['trips']), 4)
        self.assertEqual(json_resp['total'], 4)

        resp = self.client.get('/trips/Dan',
                               headers=self._api_headers(),
                               query_string=dict(start=t1))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(len(json_resp['trips']), 2)
        self.assertEqual(json_resp['total'], 2)

    def test_auth(self):
        """
        Test the authorization when posting to /trips/username/
        """
        trip = {'title': 'trip 1',
                'description': 'Lorem ipsum'}
        resp = self.client.post('/trips/Dan',
                                headers=self._api_headers(),
                                data=json.dumps(trip))
        self.assertEqual(resp.status_code, 403)
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['message'], 'not allowed')
