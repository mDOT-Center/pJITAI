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

import traceback
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from apps import db
from apps.api.models import Data, AlgorithmTunedParams, Decision

def save_decision(decision: Decision):
    try:
        db.session.add(decision)
        db.session.commit()
    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
        return {"ERROR": resp}
    except:
        print(traceback.format_exc())

def get_decision_data(algo_id: str, user_id: str = None):    
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    if user_id:
        data = Decision.query.filter(Decision.algo_uuid == algo_id).filter(Decision.user_id == user_id).order_by(Decision.timestamp.desc())
    else:
        data = Decision.query.filter(Decision.algo_uuid == algo_id).order_by(Decision.timestamp.desc())
    if data:
        df_from_records = pd.read_sql(data.statement, db.session().bind)
        return df_from_records
    return pd.DataFrame()

def get_merged_data(algo_id: str, user_id: str = None):
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    if user_id:
        data = Data.query.outerjoin(Decision, Decision.decision_id == Data.decision_id).add_entity(Decision).filter(Data.user_id == user_id).order_by(Data.timestamp.desc())
    else:
        data = Data.query.outerjoin(Decision, Decision.decision_id == Data.decision_id).add_entity(Decision).order_by(Data.timestamp.desc())
    if data:
        df_from_records = pd.read_sql(data.statement, db.session().bind)
    
        result = pd.concat([df_from_records, df_from_records['values'].apply(json_to_series)], axis=1)
        result.drop('values', axis=1, inplace=True)
        result.drop('id_1', axis=1, inplace=True)
        result.drop('user_id_1', axis=1, inplace=True)
        result.drop('algo_uuid_1', axis=1, inplace=True)
        result.drop('decision_id_1', axis=1, inplace=True)
        result.rename(columns={"timestamp_1": "decision__timestamp", 
                               "decision": "decision__decision", 
                               "decision_options": "decision__decision_options", 
                               "status_code": "decision__status_code", 
                               "status_message": "decision__status_message"},inplace=True)
        return result
    return pd.DataFrame()


def get_data(algo_id: str, user_id: str = None):
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    if user_id:
        data = Data.query.filter(Data.algo_uuid == algo_id).filter(Data.user_id == user_id).order_by(Data.timestamp.desc())
    else:
        data = Data.query.filter(Data.algo_uuid == algo_id).order_by(Data.timestamp.desc())
    if data:
        df_from_records = pd.read_sql(data.statement, db.session().bind)

        result = pd.concat([df_from_records, df_from_records['values'].apply(json_to_series)], axis=1)
        result.drop('values', axis=1, inplace=True)
        return result
    return pd.DataFrame()


def json_to_series(variable_list):
    keys = []
    values = []

    for variable in variable_list:
        keys.append(variable['name'])
        values.append(variable['value'])
        for validation_key, validation_value in variable['validation'].items():
            keys.append(f'{variable["name"]}_validation_{validation_key}')
            values.append(validation_value)

    return pd.Series(values, index=keys)


def get_tuned_params(user_id: str = None):
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    if user_id:
        tuned_params = AlgorithmTunedParams.query.filter(
            AlgorithmTunedParams.user_id == user_id).order_by(
            AlgorithmTunedParams.timestamp.desc())

    else:
        tuned_params = AlgorithmTunedParams.query.order_by(AlgorithmTunedParams.timestamp.desc())

    if tuned_params:
        df_from_records = pd.read_sql(tuned_params.statement, db.session().bind)
        return df_from_records
    return pd.DataFrame()


def store_tuned_params(user_id, configuration):
    try:
        algo_params = AlgorithmTunedParams(user_id=user_id, configuration=configuration)
        db.session.add(algo_params)
        db.session.commit()
    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
        return {"ERROR": resp}
    except:
        print(traceback.format_exc())
