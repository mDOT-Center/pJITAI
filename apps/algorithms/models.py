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
from flask_login import UserMixin
from datetime import datetime
from apps import db, login_manager
from sqlalchemy.exc import SQLAlchemyError

from apps.authentication.util import hash_pass

def save(obj) -> None:
    try:
        db.session.add(obj)
        db.session.commit()

    except SQLAlchemyError as e:
        db.session.rollback()
        db.session.close()
        error = str(e.__dict__['orig'])
        raise Exception(e)

def delete_from_db(obj) -> None:
    try:
        db.session.delete(obj)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        db.session.close()
        error = str(e.__dict__['orig'])
        raise Exception(e)
    return

@dataclass
class Algorithms(db.Model):
    __tablename__ = 'algorithms'
    id = db.Column(db.Integer,
                   primary_key=True,
                   nullable=False)
    created_by = db.Column(db.Integer,
                           db.ForeignKey('users.id'),
                           nullable=False)
    uuid = db.Column('uuid', db.String(36))
    name = db.Column('name', db.String(256))
    auth_token = db.Column('auth_token', db.String(36))
    description = db.Column('description', db.Text)
    study_name = db.Column('study_name', db.String(100))
    version = db.Column('version', db.Integer)
    type = db.Column('type', db.String(100))
    configuration = db.Column('configuration', db.JSON)
    finalized = db.Column('finalized', db.Integer, default=0)
    modified_on = db.Column('modified_on', db.DateTime, default=datetime.now())
    created_on = db.Column('created_on', db.DateTime, default=datetime.now())
    __table_args__ = (db.UniqueConstraint(
        'name', 'type', name='unique_name_type'),)

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

    def save(self):
        save(self)
    def delete(self):
        delete_from_db(self)


@dataclass
class Projects(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer,
                   primary_key=True,
                   nullable=False)
    created_by = db.Column(db.Integer,
                           db.ForeignKey('users.id'),
                           nullable=False)
    uuid = db.Column(db.String(36))
    general_settings = db.Column(db.JSON, default={})
    intervention_settings = db.Column(db.JSON, default={})
    model_settings = db.Column(db.JSON, default={})
    project_status = db.Column(db.Integer, default=0)
    algo_type = db.Column(db.String(100))
    modified_on = db.Column(db.DateTime, default=datetime.now())
    created_on = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                if not isinstance(value, dict):
                    value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.name)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def save(self):
        save(self)
    def delete(self):
        delete_from_db(self)
