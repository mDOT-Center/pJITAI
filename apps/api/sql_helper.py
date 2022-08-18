import traceback
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from apps import db
from apps.api.models import Data, AlgorithmTunedParams


def get_data(algo_id:str, user_id:str=None):
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    if user_id:
        data = Data.query.filter(Data.algo_uuid==algo_id).filter(Data.user_id==user_id).order_by(Data.upload_timestamp.desc())
    else:
        data = Data.query.filter(Data.algo_uuid==algo_id).order_by(Data.upload_timestamp.desc())
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


def get_tuned_params(user_id:str=None):
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    if user_id:
        tuned_params = AlgorithmTunedParams.query.filter(AlgorithmTunedParams.user_id==user_id).order_by(AlgorithmTunedParams.upload_timestamp.desc())

    else:
        tuned_params = AlgorithmTunedParams.query.order_by(AlgorithmTunedParams.upload_timestamp.desc())

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