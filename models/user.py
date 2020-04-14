from sqlalchemy_utils import UUIDType

from app import db

from datetime import datetime


class User(db.Model):
    id = db.Column(UUIDType, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.now, nullable=False)

    handle = db.Column(db.String(80), unique=True, nullable=False)
    phash = db.Column(db.Binary(60), nullable=False)

    invitation_cooldown_expires = db.Column(db.DateTime, nullable=True)

    last_login_on = db.Column(db.DateTime, nullable=False)

    invited_on = db.Column(db.DateTime, nullable=False)
    invited_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False,
    )
    joined_on = db.Column(db.DateTime, nullable=False)
