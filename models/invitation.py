from sqlalchemy_utils import UUIDType

from lib.db import db


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

    def __str__(self):
        return self.id
