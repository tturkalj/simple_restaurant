from flask_sqlalchemy import Model, SQLAlchemy
from sqlalchemy import MetaData, Column, Integer, DateTime, Boolean

from util import now

naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s"
}

class BaseModel(Model):
    id = Column(Integer, primary_key=True)
    created_date = Column(DateTime, nullable=False, default=now())
    last_changed_date = Column(DateTime, nullable=False, default=now())
    deleted = Column(Boolean, nullable=False, default=False)


metadata = MetaData(naming_convention=naming_convention)
db = SQLAlchemy(model_class=BaseModel, metadata=metadata)
