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
    user_id = db.Column('user_id', db.String(36))
    algo_uuid = db.Column('algo_uuid', db.String(36))
    upload_timestamp = db.Column('upload_timestamp', db.DateTime, default=datetime.now())
    #timestamp = db.Column('timestamp', db.String(64))
    decision_timestamp = db.Column('decision_timestamp', db.String(64))
    proximal_outcome_timestamp = db.Column('proximal_outcome_timestamp', db.String(64))
    decision = db.Column('decision', db.Integer)
    proximal_outcome = db.Column('proximal_outcome', db.Float)

    values = db.Column('values', db.JSON)

    '''
    "timestamp": "2022-06-16T19:05:23.495427-05: 00", # timestamp of the row
                    "decision_timestamp": "2022-06-16T19:05:23.495427-05: 00",
                    "decision": 1,
                    "proximal_outcome_timestamp": "2022-06-16T19:05:23.495427-05: 00",
                    "proximal_outcome": 50,
    '''

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
    upload_timestamp = db.Column('upload_timestamp', db.DateTime, default=datetime.now())

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
    upload_timestamp = db.Column('upload_timestamp', db.DateTime, default=datetime.now())

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}