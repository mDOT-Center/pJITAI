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
import uuid
import pandas as pd


def time_8601() -> str:
    time=datetime.now()
    return time.astimezone().isoformat()


@dataclass
class AlgorithmTunedParams(db.Model):
    __tablename__ = 'algorithm_tuned_params'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column('user_id', db.String(36))
    timestamp = db.Column('timestamp',
                          db.String(100),
                          default=time_8601)
    configuration = db.Column('configuration', db.JSON)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@dataclass
class Decision(db.Model):

    __tablename__ = 'decision'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column('user_id', db.String(36))
    algo_uuid = db.Column('algo_uuid', db.String(36))

    decision_id = db.Column('decision_id', db.String(36), unique=True, default=uuid.uuid4, nullable=False)  # UUID

    timestamp = db.Column('timestamp',
                          db.String(100),
                          default=time_8601)
    decision = db.Column('decision', db.Integer)

    decision_options = db.Column('decision_options', db.JSON)

    status_code = db.Column('status_code', db.String(250))
    status_message = db.Column('status_message', db.String(250))

    # TODO: Add eligible variable (TWH)
    # TODO: Add eligibility vector which comes from the user API call (TWH)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dataframe(self):
        temp = self.as_dict()
        temp.pop('decision_options')
        result = pd.DataFrame(temp, index=[0])
        result['decision_options'] = None
        result['decision_options'].astype(object)
        result.at[0, 'decision_options'] = self.as_dict()['decision_options']
        return result

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


@dataclass
class Data(db.Model):

    __tablename__ = 'data'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column('user_id', db.String(36))
    algo_uuid = db.Column('algo_uuid', db.String(36))
    timestamp = db.Column('timestamp',
                          db.String(100),
                          default=time_8601)

    proximal_outcome = db.Column('proximal_outcome', db.Float)
    proximal_outcome_timestamp = db.Column('proximal_outcome_timestamp',
                                           db.String(64))

    decision_id = db.Column('decision_id', db.String(36), unique=True, nullable=False)  # UUID

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
                          db.String(100),
                          default=time_8601)

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
                          db.String(100),
                          default=time_8601)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
