from sqlalchemy_utils import UUIDType

from lib.db import db

from datetime import datetime, timedelta


class Invitation(db.Model):

    creator_id = db.Column(UUIDType, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship(
        'User',
        back_populates='invitations',
        foreign_keys=[creator_id],
    )

    consumer_id = db.Column(
        UUIDType,
        db.ForeignKey('user.id'),
        unique=True,
        nullable=True,
    )
    consumer = db.relationship(
        'User',
        back_populates='invited_with',
        foreign_keys=[consumer_id],
    )

    used = db.Column(db.DateTime, nullable=True)

    expires = db.Column(db.DateTime, nullable=True)

    def __init__(self, creator):
        self.creator_id = creator.id
        self.expires = datetime.utcnow() + timedelta(days=7)

    def __str__(self):
        return self.id
