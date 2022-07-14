# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from dataclasses import dataclass
from flask_login import UserMixin
from datetime import datetime
from apps import db, login_manager

from apps.authentication.util import hash_pass

@dataclass
class Algorithms(db.Model):

    __tablename__ = 'algorithms'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uuid = db.Column('uuid', db.String(36))
    name = db.Column('name',db.String(256))
    auth_token=db.Column('auth_token', db.Text)
    description=db.Column('description', db.Text)
    study_name = db.Column('study_name', db.String(100))
    version = db.Column('version', db.Integer)
    type = db.Column('type', db.String(100))
    configuration=db.Column('configuration', db.JSON)
    finalized = db.Column('finalized', db.Integer, default=0)
    modified_on = db.Column('modified_on', db.DateTime, default=datetime.now())
    created_on = db.Column('created_on', db.DateTime, default=datetime.now())
    __table_args__ = (db.UniqueConstraint('name', 'type', name='unique_name_type'),)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            # if hasattr(value, '__iter__') and not isinstance(value, str):
            #     # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
            #     value = value[0]

            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

