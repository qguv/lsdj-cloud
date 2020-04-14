from sqlalchemy_utils import UUIDType

from app import db


class Invitation(db.Model):
    id = db.Column(UUIDType, primary_key=True)
