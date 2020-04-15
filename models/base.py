from flask_sqlalchemy import Model
from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import UUIDType

from datetime import datetime


class Base(Model):
    @declared_attr
    def id(cls):  # noqa
        for base in cls.__mro__[1:-1]:
            if getattr(base, '__table__', None) is not None:
                type = ForeignKey(base.id)
                break
        else:
            type = UUIDType

        return Column(type, primary_key=True)

    created = Column(DateTime, default=datetime.utcnow, nullable=False)
