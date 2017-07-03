from flask import request, jsonify, session, abort
from datetime import datetime
from dateutil import parser
from sqlalchemy import desc

from flask_restplus import Api, Resource, Namespace, fields
from flask_jwt import _jwt_required, JWTError, current_identity
from .. import db
from ..model import Trip


api = Namespace('trips', description='Trip service', catch_all_404s=True)


trip_model = api.model('Trip', {
        'id': fields.Integer(description='Id of the trip'),
        'title': fields.String(description='Title of the trip'),
        'username': fields.String(description='Creator\'s username'),
        'created_at': fields.DateTime(description='Time of creation'),
        'start': fields.String(description='Location of trip start'),
        'finish': fields.String(description='Location of trip end'),
        'public': fields.Boolean(description='Is the trip public'),
        'description': fields.String(description='Description of the trip')
    })


paginated = api.model('PagedTrips', {
        'trips': fields.List(fields.Nested(trip_model), allow_null=True),
        'total': fields.Integer(description='Number of results'),
        'message': fields.String(description='Response message')
    })


resp_model = api.model('TripResp', {
        'trip': fields.Nested(trip_model, default={}),
        'message': fields.String(description='Response message')
    })


def belongs_to(username):
    """
    Checks a username against the username in the JWT token
    """
    try:
        _jwt_required(None)
        if not current_identity['username'] == username:
            abort(403, 'not allowed')
    except JWTError as e:
        abort(403, 'not allowed')

    return True


@api.route('/status')
class Status(Resource):
    def get(self, **kwargs):
        return {'version': '1.0'}, 200


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
        if total == 0:
            abort(404, 'user does not exist or has no trips')

        return {'trips': [t.to_json() for t in trips],
                'total': total,
                'message': 'found trips for {}'.format(username)}, 200

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
            return {'trip': {},
                    'message': 'missing fields: '+' '.join(missing)}, 400

        trip = Trip(username=username, **trip)
        db.session.add(trip)
        db.session.commit()
        return {'trip': trip,
                'message': 'created trip'}, 201


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
        if trip is None:
            abort(404, 'no trip with this id for this user')

        return {'trip': trip,
                'message': 'found trip'}, 200

    @api.doc(responses={403: 'not allowed',
                        404: 'not found',
                        200: 'post deleted'})
    def delete(self, username, trip_id):
        """
        Delete a trip

        TODO: Delete all blurbs/images/lines/points
        """
        # check the trip belongs to the authenticated user
        allowed = belongs_to(username)
        if allowed is not True:
            return allowed
        trip = Trip.query.get(trip_id)
        if trip is None:
            abort(404, 'not found')
        db.session.delete(trip)
        db.session.commit()
