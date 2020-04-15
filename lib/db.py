from models.base import Base

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import force_auto_coercion, force_instant_defaults

force_auto_coercion()
force_instant_defaults()
db = SQLAlchemy(model_class=Base)
