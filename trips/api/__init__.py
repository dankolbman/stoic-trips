from flask_restplus import Api
from .trip import api as trip_ns

api = Api(
    title='Trips',
    version='1.0',
    description='Trip service',
    contact='Dan Kolbman',
    cantact_url='dankolbman.com',
    contact_email='dan@kolbman.com'
)

api.add_namespace(trip_ns)
