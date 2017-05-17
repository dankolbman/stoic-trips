from flask import request, jsonify, session
from datetime import datetime
from dateutil import parser
from sqlalchemy import desc

from flask_restplus import Api, Resource, Namespace, fields
from flask_jwt import _jwt_required, JWTError, current_identity
from .. import db
from ..model import Trip


api = Namespace('trips', description='Trip service')


trip_model = api.model('Trip', {
        'id': fields.String(description='Title of the trip'),
        'title': fields.String(description='Title of the trip'),
        'username': fields.String(description='Creator\'s username'),
        'created_at': fields.DateTime(description='Time of creation'),
        'start': fields.String(description='Location of trip start'),
        'finish': fields.String(description='Location of trip end'),
        'public': fields.Boolean(description='Is the trip public'),
        'description': fields.String('Description of the trip')
    })


paginated = api.model('PagedTrips', {
        'trips': fields.List(fields.Nested(trip_model)),
        'total': fields.Integer(description='Number of results'),
        'message': fields.String(description='Response message'),
        'status': fields.Integer(description='Response HTTP status code'),
    })


resp_model = api.model('TripResp', {
        'trip': fields.Nested(trip_model),
        'message': fields.String(description='Response message'),
        'status': fields.Integer(description='Response HTTP status code')
    })


def belongs_to(username):
    """
    Checks a username against the username in the JWT token
    """
    try:
        _jwt_required(None)
        if not current_identity['username'] == username:
            return {'status': 403, 'message': 'not allowed'}, 403
    except JWTError as e:
        return {'status': 403, 'message': 'not allowed'}, 403

    return True


@api.route('/status')
class Status(Resource):
    def get(self, **kwargs):
        return {'status': 200,
                'version': '1.0'}, 200


@api.route('/')
class Trips(Resource):
    @api.marshal_with(paginated)
    @api.doc(responses={200: 'found trips'},
             params={'start': 'Return only trips starting after this time',
                     'size': 'Number of trips to retrieve'})
    def get(self, **kwargs):
        """
        List all trips
        """
        epoch = datetime.fromtimestamp(0).isoformat()
        start = request.args.get('start', epoch, type=str)
        start_dt = parser.parse(start)
        size = request.args.get('size', 10, type=int)

        q = (Trip.query.order_by(desc(Trip.created_at))
                       .filter(Trip.created_at > start_dt))
        trips = q.limit(size)
        total = q.count()
        q = Trip.query.order_by(desc(Trip.created_at))

        return {'trips': [t.to_json() for t in trips], 'total': total}, 200


@api.route('/<string:username>')
class UserTrips(Resource):
    @api.marshal_with(paginated)
    @api.doc(responses={200: 'found trips'},
             params={'start': 'Return only trips starting after this time',
                     'size': 'Number of trips to retrieve'})
    def get(self, username):
        """
        List trips for a user
        """
        epoch = datetime.fromtimestamp(0).isoformat()
        start = request.args.get('start', epoch, type=str)
        start_dt = parser.parse(start)
        size = request.args.get('size', 10, type=int)

        q = (Trip.query.filter_by(username=username)
                       .order_by(desc(Trip.created_at))
                       .filter(Trip.created_at > start_dt))
        trips = q.limit(size)
        total = q.count()

        return {'trips': [t.to_json() for t in trips], 'total': total}, 200

    @api.marshal_with(resp_model)
    @api.doc(responses={201: 'created trip'})
    def post(self, username):
        """
        Create a trip
        """
        allowed = belongs_to(username)
        if allowed is not True:
            return allowed
        trip = request.json
        missing = []
        for field in ['title']:
            if field not in trip:
                missing.append(field)
        if missing:
            return {'trip': [],
                    'message': 'missing fields: '+' '.join(missing),
                    'status': 400}, 400

        trip = Trip(username=username, **trip)
        db.session.add(trip)
        db.session.commit()
        return {'trip': trip,
                'message': 'created trip',
                'status': 201}, 201


@api.route('/<string:username>/<int:trip_id>')
class UserTrip(Resource):
    @api.marshal_with(resp_model)
    @api.doc(responses={200: 'found trip'})
    def get(self, username, trip_id):
        """
        Get a specific trip
        """
        trip = (Trip.query.filter_by(username=username)
                          .filter_by(id=trip_id)
                          .first())

        return {'trip': trip,
                'message': 'found trip',
                'status': 200}, 200
