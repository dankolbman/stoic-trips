from datetime import datetime
from dateutil import parser
from . import db


class Trip(db.Model):
    """
    The trip model
    """
    __tablename__ = 'trips'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), index=False)
    username = db.Column(db.String(32), index=True)
    complete = db.Column(db.Boolean(), default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    start = db.Column(db.String(32))
    finish = db.Column(db.String(32))
    public = db.Column(db.Boolean(), default=True)
    description = db.Column(db.Text())

    def __init__(self, **kwargs):
        if 'created_at' in kwargs and type(kwargs['created_at']) is str:
            kwargs['created_at'] = parser.parse(kwargs['created_at'])
        super(Trip, self).__init__(**kwargs)

    def to_json(self):
        return {"id": self.id,
                "title": self.title,
                "username": self.username,
                "complete": self.complete,
                "created_at": self.created_at.isoformat(),
                "start": self.start,
                "finish": self.finish,
                "public": self.public,
                "description": self.description
                }
