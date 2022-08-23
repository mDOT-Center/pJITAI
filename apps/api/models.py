'''
Copyright (c) 2022 University of Memphis, mDOT Center. All rights reserved. 

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer. 

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution. 

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''


from dataclasses import dataclass
from datetime import datetime
from apps import db


def time_8601(time=datetime.now()) -> str:
    return time.astimezone().isoformat()

@dataclass
class AlgorithmTunedParams(db.Model):
    __tablename__ = 'algorithm_tuned_params'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column('user_id', db.String(36))
    timestamp = db.Column('timestamp',
                          db.String,
                          default=time_8601())
    configuration = db.Column('configuration', db.JSON)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@dataclass
class Data(db.Model):

    __tablename__ = 'data'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column('user_id', db.String(36))
    algo_uuid = db.Column('algo_uuid', db.String(36))  # TODO: Are are these the correct timestamps needed?
    upload_timestamp = db.Column('upload_timestamp',
                                 db.String,
                                 default=time_8601())
    decision_timestamp = db.Column('decision_timestamp', db.String(64))
    proximal_outcome_timestamp = db.Column('proximal_outcome_timestamp',
                                           db.String(64))
    decision = db.Column('decision', db.Integer)
    proximal_outcome = db.Column('proximal_outcome', db.Float)

    values = db.Column('values', db.JSON)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@dataclass
class Log(db.Model):
    __tablename__ = 'logs'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    algo_uuid = db.Column('algo_uuid', db.String(36))
    details = db.Column('details', db.JSON)
    timestamp = db.Column('timestamp',
                          db.String,
                          default=time_8601())

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
    details = db.Column('details', db.JSON)
    timestamp = db.Column('timestamp',
                          db.String,
                          default=time_8601())

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
