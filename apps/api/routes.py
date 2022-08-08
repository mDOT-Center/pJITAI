# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import json
from functools import wraps

from apps.api import blueprint
from flask import request
from flask_login import login_required
from flask import jsonify
from apps import db
from apps.algorithms.models import Algorithms
from .models import Logs, Data
from sqlalchemy.exc import SQLAlchemyError
from apps.api.codes import StatusCode
from apps.learning_models.learning_model_service import get_all_available_models
import traceback

from .util import time_8601, get_class_object


def _validate_algo_data(uuid: str, input_request: list) -> list:  # TODO: Make this actually do something @Anand
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()  # This gets the algorithm from the system
    #algo_conf = json.dumps(algo.configuration, indent=4)
    #print(f'Alogrithm is {algo_conf}')
    algorithm_features_ = algo.configuration.get('features',[])
    feature_map = {}
    for ft in algorithm_features_:
        #print(f'ft = {algorithm_features_[ft]}')
        feature_map[algorithm_features_[ft]['feature_name']] = algorithm_features_[ft]
    if not algo:
        return {"ERROR": "Invalid algorithm ID."}

    # TODO: Check input_request to ensure that the number of items matches what is expected
    if len(input_request) > 0:  #  == len(params):
        # TODO: iterate over input_request and validate against the algorithm's specification @Anand
        #output_data = input_request
        input_features = {}
        for row in input_request:
            _is_valid(row, feature_map)
    else:
        raise Exception(
            f"Array out of bounds: input: {len(input_request)}, expected: {len(algo.configuration['features'])}")

    return input_request


def _is_valid(row: dict, features_config: dict) -> dict:  # TODO implement me
    input_features = set()
    for val in row['values']:
        input_features.add(val['name'])

    # Insert missing features with none value and add validation messages
    for f in features_config:
        if f not in input_features:
            missing = {}
            missing['name'] = f
            missing['value'] = None
            row['values'].append(missing)

    for val in row['values']:
        validation = dict()

        validation['status_code'] = StatusCode.SUCCESS.value
        #validation['status_message'] = "Feature value passed validation."

        feature_name = val['name']
        feature_value = val['value']

        if not feature_value:
            validation['status_code'] = StatusCode.WARNING_MISSING_VALUE.value
            #validation['status_message'] = f'Input feature {feature_name} is missing'
            val['validation'] = validation
            continue

        if feature_name not in features_config:
            continue

        ft_def = features_config[feature_name]
        if ft_def is None:
            continue  # Extra data passed?

        '''
        #  START: testing code -- TODO delete this block after testing
        if ft_def['feature_name'] == 'int1':
            ft_def['feature_data_type'] = 'int'
            ft_def['feature_lower_bound'] = 0
            ft_def['feature_upper_bound'] = 10
        if ft_def['feature_name'] == 'float_feature':
            ft_def['feature_lower_bound'] = 0.0
            ft_def['feature_upper_bound'] = 10.0
        print(f'validating {val} with {ft_def}')
        #  END: testing code
        '''

        feature_data_type = ft_def['feature_data_type']
        if feature_data_type == 'int':
            try:
                feature_value = int(feature_value)
                lower_bound_value = str(ft_def['feature_lower_bound'])
                if 'inf' not in lower_bound_value:
                    lower_bound = int(lower_bound_value)
                    if feature_value < lower_bound:
                        validation['status_code'] = StatusCode.WARNING_OUT_OF_BOUNDS.value
                        validation['status_message'] = f'{feature_name} with value {feature_value} is lower than the ' \
                                                       f'lower bound value {lower_bound}. '
                upper_bound_value = str(ft_def['feature_upper_bound'])
                if 'inf' not in upper_bound_value:
                    upper_bound = int(upper_bound_value)
                    if feature_value > upper_bound:
                        validation['status_code'] = StatusCode.WARNING_OUT_OF_BOUNDS.value
                        validation['status_message'] = f'{feature_name} with value {feature_value} is greater than the ' \
                                                       f'upper bound value {upper_bound}. '
            except:
                validation['status_code'] = StatusCode.ERROR.value
                validation['status_message'] = f'AAAAAAAAA {feature_name} value is not of type int.'
        elif feature_data_type == 'float':
            try:
                feature_value = float(feature_value)
                lower_bound_value = str(ft_def['feature_lower_bound'])
                if 'inf' not in lower_bound_value:
                    lower_bound = float(lower_bound_value)
                    if feature_value < lower_bound:
                        validation['status_code'] = StatusCode.WARNING_OUT_OF_BOUNDS.value
                        #validation['status_message'] = f'{feature_name} with value {feature_value} is lower than the ' \
                                                       #f'lower bound value {lower_bound}. '
                upper_bound_value = str(ft_def['feature_upper_bound'])
                if 'inf' not in upper_bound_value:
                    upper_bound = float(upper_bound_value)
                    if feature_value > upper_bound:
                        validation['status_code'] = StatusCode.WARNING_OUT_OF_BOUNDS.value
                        #validation['status_message'] = f'{feature_name} with value {feature_value} is greater than the ' \
                                                       #f'upper bound value {upper_bound}. '
            except:
                print('value is not an float')
                validation['status_code'] = StatusCode.ERROR.value
                #validation['status_message'] = f'BBBBBBBBBBB {feature_name} value is not of type float.'

        val['validation'] = validation
    return row


def _make_decision(uuid: str, user_id: str, input_data: list) -> dict:
    # algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).filter(Algorithms.created_by==user_id).first()  # This gets the algorithm from the system

    #  The above line doesn't seem to work. Override by Anand
    algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).first()
    if not algorithm:
        return {"ERROR": "Invalid algorithm and/or user ID."}
    name = algorithm.type
    cls = get_class_object("apps.learning_models." + name + "." + name)
    # populate object with algo parameters
    obj = cls()
    obj.as_object(algorithm)


    # TODO - need to load the tuned parameters FIXME
    #TODO: get rid of () @ali
    result = obj.decision(user_id, input_data)
    # TODO Turn into JSON for transport. Result datatype is Pandas dataframe
    return result


def _save_each_data_row(user_id: str, data: dict, algo_uuid=None) -> dict:  # TODO: Make this actually do something
    # TODO: Save each row in data in the SQL storage layer @Ali

    resp = "Data has successfully added"
    result = {
        'user_id': user_id,
        'timestamp': time_8601(),
        'status_code': StatusCode.SUCCESS.value,
        'status_message': f"Saved {len(data)} rows of data"
    }
    try:
        data_obj = Data(algo_uuid=algo_uuid,
                        values=data['values'],
                        user_id=user_id,
                        #timestamp=data['timestamp'],
                        decision_timestamp=data['decision_timestamp'],
                        decision=data['decision'],
                        proximal_outcome_timestamp=data['proximal_outcome_timestamp'],
                        proximal_outcome=data['proximal_outcome'])
        db.session.add(data_obj)
        db.session.commit()
    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
        return {"ERROR": resp}
    except:
        print(traceback.format_exc())

    return result


def _add_log(log_detail: dict, algo_uuid=None) -> dict:
    resp = "Data has successfully added"
    try:
        log = Logs(algo_uuid=algo_uuid, details=log_detail, created_on=time_8601())
        db.session.add(log)
        db.session.commit()
    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
        return resp
    except:
        print(traceback.format_exc())

    return {"msg": resp}


def rl_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('rltoken')
        if not token:
            return {'ERROR': 'Token is not present'}
        result = db.session.query(Algorithms).filter(Algorithms.auth_token == token).first()
        if not result:
            return {'ERROR': 'Invalid token'}
        # TODO: Check if the token matches the one present for the algorithm in question @Ali
        # TODO: Add token to the algorithm and WebUI (View Algorithm) @Ali

        return f(*args, **kwargs)

    return decorated


@blueprint.route('<uuid>', methods=['POST'])
# @rl_token_required
def model(uuid: str) -> dict:
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()
    result = {"status": "ERROR: Algorithm not found"}
    if algo:
        result = algo.as_dict()
    return result

@blueprint.route('tst', methods=['POST','GET'])
# @rl_token_required
def tst() -> dict:
    import pandas as pd
    algo = Algorithms.query.filter(Algorithms.uuid.like("123")).first()
    df_from_records = pd.DataFrame.from_records(algo)
    print(df_from_records.head(5))

@blueprint.route('<uuid>/dd', methods=['POST', 'GET'])
# @rl_token_required
def dd(uuid: str) -> dict:
    decision_output = _make_decision(uuid, 123, [])

@blueprint.route('<uuid>/decision', methods=['POST', 'GET'])
# @rl_token_required
def decision(uuid: str) -> dict:
    input_data = request.json
    try:
        # validated_data = _validate_algo_data(uuid, input_data['values']) TODO
        validated_data = input_data

        decision_output = _make_decision(uuid, input_data['user_id'], validated_data)

        if decision_output:
            return decision_output
        else:
            return {'status_code': StatusCode.ERROR.value,
                    # TODO: this needs to be some sort of error response in the decision fails.
                    'status_message': f'A decision was unable to be made for: {uuid} '}
    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }


@blueprint.route('<uuid>/upload', methods=['POST'])  # or UUID
# @rl_token_required # FIXME TODO
def upload(uuid: str) -> dict:
    input_data = request.json

    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()
    # TODO: input_data = _valdiate_algo_data(uuid, input_data['values']) @Anand

    validated_input_data = _validate_algo_data(uuid, input_data['values'])  # FIXME
    # print(f'{len(algo.configuration["features"])}')
    try:
        # print(f'input_data = {input_data["values"]}')
        for row in input_data['values']:
            check = True
            # TODO - change to nome, value, validation @Anand
            if check:  # FIXME len(row['values']) == len(algo.configuration['features']):
                # TODO: Consider validating all rows prior to saving
                response = _save_each_data_row(input_data['user_id'], row, algo_uuid=uuid)
                if response['status_code'] == StatusCode.ERROR.value:
                    raise Exception('Error saving data.')
            else:
                raise Exception(
                    f"Array out of bounds: input: {len(row['values'])}, expected: {len(algo.configuration['features'])}")
    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }

    return {
        "status_code": StatusCode.SUCCESS.value,
        "status_message": f"Batch data updated for model {uuid}"
    }


@blueprint.route('<uuid>/update', methods=['POST'])
# TODO Something like this?  @Ali @rl_server_token_required # Make sure this only exposed on the server
# @rl_token_required # FIXME TODO
def update(uuid: str) -> dict:
    input_data = request.json
    try:
        algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).first()
        '''
        Call the alogrithm update method
        
        '''
        #  The above line doesn't seem to work. Override by Anand
        algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).first()
        if not algorithm:
            return {"ERROR": "Invalid algorithm and/or user ID."}
        name = algorithm.type
        cls = get_class_object("apps.learning_models." + name + "." + name)
        obj = cls()
        obj.as_object(algorithm)
        # TODO - need to load the tuned parameters FIXME
        result = obj.update()
        # TODO - store the result in the DB. By user. in the params_algo table
        # list[dict] - dict contains all the tuned params and user id
        example_result = [
            {
                'user_id':'user_1',
                'timestamp': 'timestamp_with_tz',
                'values': {
                    'param_1': 0.34,
                    'param_2': 34.0
                }
            }
        ]

        return {'status_code': StatusCode.SUCCESS.value, "status_message": f'parameters have been updated for: {uuid}'}


    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }


# Web UI related APIs below here
@blueprint.route('/run_algo/<algo_type>', methods=['POST'])  # or UUID
@login_required
def run_algo(algo_type):
    # all finalized algorithms could be accessed using this api point
    algo_definitions = get_all_available_models()
    algo_info = {}
    form_type = request.form.get("form_type")
    if algo_type not in algo_definitions:
        return {"status": "error", "message": algo_type + " does not exist."}, 400
    if not request.form:
        return {"status": "error", "message": "Form cannot be empty."}, 400

    if form_type == "add" or form_type == "new":
        if not request.form.get("algorithm_name"):
            return {"status": "error", "message": "Algorithm name cannot be empty."}, 400

        algo_info["name"] = request.form.get("algorithm_name")
        algo_info["description"] = request.form.get("algorithm_description")
        algo_info["type"] = request.form.get("algorithm_type")
        configuration = {}

        features = {}
        standalone_parameter = {}
        other_parameter = {}

        for param in request.form:
            arr = param.split("__")
            if param.startswith("feature"):
                if not features.get(arr[-1]):
                    features[arr[-1]] = {}
                features[arr[-1]].update({arr[0]: request.form[param]})
            elif param.startswith("standalone_parameter"):
                standalone_parameter.update({arr[1]: request.form[param]})
            elif param.startswith("other_parameter"):
                other_parameter.update({arr[1]: request.form[param]})

        configuration["features"] = features
        configuration["standalone_parameters"] = standalone_parameter
        configuration["other_parameters"] = other_parameter
        configuration["tuning_scheduler"] = {}
        if request.form.get("availability"):
            configuration["availability"] = {"availability": request.form.get("availability")}

        algo_info["features"] = features
        algo_info["standalone_parameter"] = standalone_parameter
        algo_info["other_parameter"] = other_parameter

        # return algo_info
        return {"status": "success", "message": "Algorithm ran successfully. Output is TODO"}
    return {"status": "error", "message": "Some error occurred. Check the logs."}, 400


@blueprint.route('/search/<query>', methods=['POST', 'GET'])  # or UUID
@login_required
def search(query):
    results = []
    search_query = "%{}%".format(query)
    algorithm = Algorithms.query.filter(Algorithms.name.like(search_query) | Algorithms.type.like(search_query)).all()
    if not algorithm:
        return {"status": "error", "message": "No result found."}, 400
    else:
        for al in algorithm:
            results.append(al.as_dict())
        return jsonify(results)


@blueprint.route('/algorithms/<id>', methods=['GET'])  # or UUID
@login_required
def algorithms(id):
    algo = db.session.query(Algorithms).filter(Algorithms.id == id).filter(Algorithms.finalized == 1).first()
    if not algo:
        return {"status": "error",
                "message": "Algorithm ID does not exist or algorithm has not been finalized yet."}, 400
    else:
        return algo.as_dict()
