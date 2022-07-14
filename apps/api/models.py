# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from dataclasses import dataclass
from datetime import datetime
from apps import db

@dataclass
class Data(db.Model):

    __tablename__ = 'data'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    algo_uuid = db.Column('algo_uuid', db.String(36))
    details=db.Column('details', db.JSON)
    created_on = db.Column('created_on', db.DateTime, default=datetime.now())

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@dataclass
class Logs(db.Model):

    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    algo_uuid = db.Column('algo_uuid', db.String(36))
    details=db.Column('details', db.JSON)
    created_on = db.Column('created_on', db.DateTime, default=datetime.now())

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

@dataclass
class Cron(db.Model):

    __tablename__ = 'cron'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    algo_uuid = db.Column('algo_uuid', db.String(36))
    details=db.Column('details', db.JSON)
    created_on = db.Column('created_on', db.DateTime, default=datetime.now())

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}