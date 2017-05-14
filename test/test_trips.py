import json
import time
import unittest
from datetime import datetime

from flask import current_app, url_for
from trips import create_app, db
from trips.model import Trip

from test.utils import FlaskTestCase, api_headers, make_trip


class tripTestCase(FlaskTestCase):

    def test_new_trip(self):
        """
        Test trip creation via REST API
        """
        resp = self.client.post('/trips/Dan',
                                headers=api_headers(),
                                data=json.dumps({'name': 'trip 1',
                                                 'start': 'Ho Chi Minh',
                                                 'finish': 'Hanoi',
                                                 'public': True,
                                                 'description': 'Lorem ipsum'})
                                )
        json_resp = json.loads(resp.data.decode('utf-8'))
        # check api response
        self.assertEqual(json_resp['status'], 201)
        self.assertEqual(json_resp['message'], 'created trip')
        # check that user is in database
        self.assertEqual(Trip.query.count(), 1)
        trip = Trip.query.first()
        self.assertEqual(trip.username, 'Dan')
        self.assertEqual(trip.name, 'trip 1')
        self.assertEqual(trip.start, 'Ho Chi Minh')
        self.assertEqual(trip.finish, 'Hanoi')
        self.assertEqual(trip.public, True)
        self.assertEqual(trip.description, 'Lorem ipsum')

    def test_multi_user(self):
        """
        Test that /trips will return trips from different users
        """
        resp = make_trip(self.client, 'Dan', name='Dans trip')
        resp = make_trip(self.client, 'Bob', name='Bobs trip')
        self.assertEqual(Trip.query.count(), 2)
        resp = self.client.get('/trips/')
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(json_resp['total'], 2)

    def test_size_param(self):
        """
        Test the ?size param
        """
        for i in range(4):
            resp = make_trip(self.client, 'Dan', name='Dans trip')
        for i in range(3):
            resp = make_trip(self.client, 'Bob', name='Bobs trip')
        for i in range(13):
            resp = make_trip(self.client, 'Dan', name='Dans trip')
            resp = make_trip(self.client, 'Bob', name='Bobs trip')
        self.assertEqual(Trip.query.count(), 33)
        # Test size
        resp = self.client.get('/trips/',
                                headers=api_headers(),
                                query_string=dict(size=5))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(len(json_resp['trips']), 5)
        self.assertEqual(json_resp['total'], 33)

        resp = self.client.get('/trips/Dan',
                                headers=api_headers(),
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
            resp = make_trip(self.client, 'Dan', name='Dans', created_at=t0)
        for i in range(3):
            resp = make_trip(self.client, 'Bob', name='Bobs', created_at=t0)
        time.sleep(0.1)
        t1 = datetime.utcnow().isoformat()
        time.sleep(0.1)
        t2 = datetime.utcnow().isoformat()
        for i in range(2):
            resp = make_trip(self.client, 'Dan', name='Dans', created_at=t2)
            resp = make_trip(self.client, 'Bob', name='Bobs', created_at=t2)
        self.assertEqual(Trip.query.count(), 11)
        # Test start
        resp = self.client.get('/trips/',
                                headers=api_headers(),
                                query_string=dict(start=t1))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(len(json_resp['trips']), 4)
        self.assertEqual(json_resp['total'], 4)

        resp = self.client.get('/trips/Dan',
                                headers=api_headers(),
                                query_string=dict(start=t1))
        json_resp = json.loads(resp.data.decode('utf-8'))
        self.assertEqual(len(json_resp['trips']), 2)
        self.assertEqual(json_resp['total'], 2)
