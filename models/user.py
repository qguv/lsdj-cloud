from lib.db import db


class User(db.Model):

    invitations = db.relationship(
        'Invitation',
        back_populates='creator',
        foreign_keys='Invitation.creator_id',
    )
    invited_with = db.relationship(
        'Invitation',
        back_populates='consumer',
        foreign_keys='Invitation.consumer_id',
    )

    handle = db.Column(db.String(80), unique=True, nullable=False)
    phash = db.Column(db.Binary(60), nullable=False)

    last_login_on = db.Column(db.DateTime, nullable=True)

    def __init__(self, handle, phash):
        self.handle = handle
        self.phash = phash
