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
from apps.api.sql_helper import get_tuned_params, store_tuned_params
from apps.learning_models.learning_model_service import get_all_available_models
import traceback

from .util import time_8601, get_class_object
from threading import Thread


def _validate_algo_data(uuid: str, feature_values: list) -> list:
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()
    if not algo:
        raise Exception(f'ERROR: Invalid algorithm ID.')
    algorithm_features_ = algo.configuration.get('features', [])
    feature_map = {}
    for ft in algorithm_features_:
        feature_map[algorithm_features_[ft]
                    ['feature_name']] = algorithm_features_[ft]

    # Check input_request to ensure that the number of items matches what is expected
    if len(feature_values) == len(feature_map):
        # iterate over input_request and validate against the algorithm's specification
        _is_valid(feature_values, feature_map)
    else:
        raise Exception(
            f"Array out of bounds: input: {len(feature_values)}, expected: {len(feature_map)}")

    return feature_values


def _is_valid(feature_vector: dict, features_config: dict) -> dict:
    input_features = set()
    for val in feature_vector:
        input_features.add(val['name'])

    # Check for missing features
    for f in features_config:
        if f not in input_features:
            raise Exception(
                f"Missing feature: {f}, expected: {features_config.keys()}")

    for val in feature_vector:
        validation = dict()
        validation['status_code'] = StatusCode.SUCCESS.value

        feature_name = val['name']
        feature_value = val['value']

        if feature_name not in features_config:
            raise Exception(
                f"Received unknown feature: {feature_name}, expected: {features_config.keys()}")

        # This is the defined configuration for the algorithm
        ft_def = features_config[feature_name]

        feature_value_type = type(feature_value)
        # This is teh defined data type of the feature defined in the config
        feature_data_type = ft_def['feature_data_type']
        if feature_data_type != feature_value_type.__name__:
            raise Exception(
                f"Incorrect feature type for {feature_name}, expected: {feature_data_type} received: {feature_value_type}")

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
            except Exception as e:
                validation['status_code'] = StatusCode.ERROR.value
                validation['status_message'] = f'{feature_name} {e}'
        elif feature_data_type == 'float':
            try:
                feature_value = float(feature_value)
                lower_bound_value = str(ft_def['feature_lower_bound'])
                if 'inf' not in lower_bound_value:
                    lower_bound = float(lower_bound_value)
                    if feature_value < lower_bound:
                        validation['status_code'] = StatusCode.WARNING_OUT_OF_BOUNDS.value
                upper_bound_value = str(ft_def['feature_upper_bound'])
                if 'inf' not in upper_bound_value:
                    upper_bound = float(upper_bound_value)
                    if feature_value > upper_bound:
                        validation['status_code'] = StatusCode.WARNING_OUT_OF_BOUNDS.value
            except:
                print('value is not an float')
                validation['status_code'] = StatusCode.ERROR.value

        val['validation'] = validation
    return feature_vector


def _make_decision(uuid: str, user_id: str, input_data: list) -> dict:
    # algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).filter(Algorithms.created_by==user_id).first()  # This gets the algorithm from the system
    #  The above line doesn't seem to work. Override by Anand
    algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).first()
    cls = get_class_object("apps.learning_models." +
                           algorithm.type + "." + algorithm.type)
    obj = cls()
    obj.as_object(algorithm)  # TODO: What does this do?

    tuned_params = get_tuned_params(user_id=user_id)

    result = obj.decision(user_id, tuned_params, input_data)

    return result


def _save_each_data_row(user_id: str, decision_timestamp, decision, proximal_outcome_timestamp, proximal_outcome, data: list, algo_uuid=None) -> dict:
    resp = "Data has successfully added"
    try:
        data_obj = Data(algo_uuid=algo_uuid,
                        values=data,
                        user_id=user_id,
                        decision_timestamp=decision_timestamp,
                        decision=decision,
                        proximal_outcome_timestamp=proximal_outcome_timestamp,
                        proximal_outcome=proximal_outcome)
        db.session.add(data_obj)
        db.session.commit()

    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
        raise Exception(f'Error saving data: {resp}')
    except:
        raise Exception(f'Error saving data: {resp}')


def _add_log(log_detail: dict, algo_uuid=None) -> dict:
    resp = "Data has successfully added"
    try:
        log = Logs(algo_uuid=algo_uuid, details=log_detail,
                   created_on=time_8601())
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


def pJITAI_token_required(f):
    @ wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('pJITAI_token')
        if not token:
            return {
                'status_code': StatusCode.ERROR.value,
                'status_message': 'Token not found'
            }, 400

        # TODO: Testing bypass until the below code is implemented properly

        # result = db.session.query(Algorithms).filter(Algorithms.auth_token == token).first()
        # if not result:
        #     return {
        #         'status_code': StatusCode.ERROR.value,
        #         'status_message': 'Algorithm authentication token is incorrect'
        #     }, 400

        # TODO: Check if the token matches the one present for the algorithm in question @Ali
        # TODO: Add token to the algorithm and WebUI (View Algorithm) @Ali

        return f(*args, **kwargs)

    return decorated


@blueprint.route('<uuid>', methods=['POST'])
@pJITAI_token_required
def model(uuid: str) -> dict:
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()
    result = {"status": "ERROR: Algorithm not found"}
    if algo:
        result = algo.as_dict()
    return result


@blueprint.route('<uuid>/decision', methods=['POST', 'GET'])
@pJITAI_token_required
def decision(uuid: str) -> dict:
    input_data = request.json
    try:
        validated_data = _validate_algo_data(uuid,
                                             input_data['values'])

        decision_output = _make_decision(uuid,
                                         input_data['user_id'],
                                         validated_data)

        if len(decision_output) > 0:
            # Only one row is currently supported.  Extract it and convert to a dictionary before returning to the calling library.
            return decision_output.iloc[0].to_dict(), 200
        else:
            return {
                'status_code': StatusCode.ERROR.value,
                'status_message': f'A decision was unable to be made for: {uuid} with validated data: {validated_data}'
            }, 400
    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }, 400


@blueprint.route('<uuid>/upload', methods=['POST'])
@pJITAI_token_required  # TODO: This should actually check the token
def upload(uuid: str) -> dict:
    input_data = request.json
    try:
        validated_input_data = _validate_algo_data(uuid,
                                                   input_data['values'])
        _save_each_data_row(input_data['user_id'],
                            decision_timestamp=input_data['decision_timestamp'],
                            decision=input_data['decision'],
                            proximal_outcome_timestamp=input_data['proximal_outcome_timestamp'],
                            proximal_outcome=input_data['proximal_outcome'],
                            data=validated_input_data,
                            algo_uuid=uuid)

        return {
            "status_code": StatusCode.SUCCESS.value,
            "status_message": f"Data uploaded for model {uuid}"
        }, 200
    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }, 400


def _do_update(algo_uuid):
    algorithm = Algorithms.query.filter(Algorithms.uuid == algo_uuid).first()
    cls = get_class_object("apps.learning_models." +
                           algorithm.type + "." + algorithm.type)
    obj = cls()
    obj.as_object(algorithm)
    result = obj.update()

    for index, row in result.iterrows():
        store_tuned_params(user_id=row.user_id,
                           configuration=row.iloc[2:].to_dict())


@blueprint.route('<uuid>/update', methods=['POST'])
# TODO Something like this?  @Ali @rl_server_token_required # Make sure this only exposed on the server
@pJITAI_token_required  # FIXME TODO
def update(uuid: str) -> dict:
    input_data = request.json
    try:
        '''
        Call the alogrithm update method

        '''
        #TODO: Something like this for async calls?
        # t = Thread(target=_do_update, args={'algo_uuid': uuid})
        # t.start()
        
        _do_update(algo_uuid=uuid)

        result = {
            "status_code": StatusCode.SUCCESS.value,
            "status_message": "Background update proceedure has been started.",
        }
        return result, 200

    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }, 400


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
            configuration["availability"] = {
                "availability": request.form.get("availability")}

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
    algorithm = Algorithms.query.filter(Algorithms.name.like(
        search_query) | Algorithms.type.like(search_query)).all()
    if not algorithm:
        return {"status": "error", "message": "No result found."}, 400
    else:
        for al in algorithm:
            results.append(al.as_dict())
        return jsonify(results)


@blueprint.route('/algorithms/<id>', methods=['GET'])  # or UUID
@login_required
def algorithms(id):
    algo = db.session.query(Algorithms).filter(
        Algorithms.id == id).filter(Algorithms.finalized == 1).first()
    if not algo:
        return {"status": "error",
                "message": "Algorithm ID does not exist or algorithm has not been finalized yet."}, 400
    else:
        return algo.as_dict()
