import traceback

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from apps import db
from apps.api.models import Data, AlgorithmTunnedParams


def get_data(algo_id:str, user_id:str=None):
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    if user_id:
        data = Data.query.filter(Data.algo_uuid==algo_id).filter(Data.user_id==user_id).order_by(Data.upload_timestamp.desc()).all()
    else:
        data = Data.query.filter(Data.algo_uuid==algo_id).order_by(Data.upload_timestamp.desc()).all()
    if data:
        df_from_records = pd.read_sql(data[0].query.statement, db.session().bind)
        return df_from_records
    return pd.DataFrame()


def get_tuned_params(user_id:str=None):
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    if user_id:
        tunned_params = AlgorithmTunnedParams.query.filter(AlgorithmTunnedParams.user_id==user_id).order_by(AlgorithmTunnedParams.upload_timestamp.desc()).first()
        qry = tunned_params
    else:
        tunned_params = AlgorithmTunnedParams.query.order_by(AlgorithmTunnedParams.upload_timestamp.desc()).all()
        if tunned_params:
            qry = tunned_params[0]
    if tunned_params:
        df_from_records = pd.read_sql(qry.query.statement, db.session().bind)
        return df_from_records
    return pd.DataFrame()


def store_tuned_params(user_id, configuration):
    try:
        algo_params = AlgorithmTunnedParams(user_id=user_id, configuration=configuration)
        db.session.add(algo_params)
        db.session.commit()
    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
        return {"ERROR": resp}
    except:
        print(traceback.format_exc())