import traceback

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from apps import db
from apps.api.models import Data, AlgorithmParams


def get_data(algo_id:str, user_id:str=None):
    '''
    Get data from data table, created pandas DF (parse all the dict and convert them into columns)
    :param algo_id:
    :param user_id:
    :return: pandas DF
    '''
    data = Data.query.filter(Data.algo_uuid==algo_id).filter(Data.user_id==user_id).all()
    df_from_records = pd.read_sql(data.query.statement, db.session().bind)
    return df_from_records


def store_algorithm_params(user_id, configuration):
    try:
        algo_params = AlgorithmParams(user_id=user_id, configuration=configuration)
        db.session.add(algo_params)
        db.session.commit()
    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
        return {"ERROR": resp}
    except:
        print(traceback.format_exc())