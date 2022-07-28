# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
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
    if not algo:
        return {"ERROR": "Invalid algorithm ID."}
    name = algo.type
    obj = get_class_object("apps.learning_models." + name + "." + name)
    params = obj.parameters
    # TODO: Check input_request to ensure that the number of items matches what is expected
    if len(input_request) == len(params):
        # TODO: iterate over input_request and validate against the algorithm's specification @Anand
        output_data = input_request
        for row in output_data:
            _is_valid(row, params)
    else:
        raise Exception(
            f"Array out of bounds: input: {len(input_request)}, expected: {len(algo.configuration['features'])}")

    return output_data


def _is_valid(row: dict, params: dict) -> dict:  # TODO implement me
    validation = dict()
    validation['status.code'] = StatusCode.SUCCESS.value
    validation['status_message'] = "All data values passed validation."


def _make_decision(uuid: str, user_id: str, input_data: list) -> dict:
    #algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).filter(Algorithms.created_by==user_id).first()  # This gets the algorithm from the system

    #  The above line doesn't seem to work. Override by Anand
    algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).first()
    if not algorithm:
        return {"ERROR": "Invalid algorithm and/or user ID."}
    name = algorithm.type
    obj = get_class_object("apps.learning_models." + name + "." + name)

    result = obj().decision(algorithm.configuration, input_data)
    
    return result



'''
{
                    "timestamp": "2022-06-16T19:05:23.495427-05: 00",
                    "decision_timestamp": "2022-06-16T19:05:23.495427-05: 00",
                    "decision": 1,
                    "proximal_outcome_timestamp": "2022-06-16T19:05:23.495427-05: 00",
                    "proximal_outcome": 50,
                    "values": [
                        {
                            "name": "step_count",
                            "value": 500
                        }
                    ]
                }
'''


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
                        timestamp=data['timestamp'],
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


@blueprint.route('<uuid>/', methods=['POST'])
# @rl_token_required
def model(uuid: str) -> dict:
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()
    result = {"status": "ERROR: Algorithm not found"}
    if algo:
        result = algo.as_dict()
    return result


@blueprint.route('<uuid>/decision2', methods=['POST', 'GET'])
#@rl_token_required
def decision2(uuid: str) -> dict:

    try:
        decision_output = _make_decision(uuid, 1, None)
        return decision_output
    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }


@blueprint.route('<uuid>/decision', methods=['POST', 'GET'])
#@rl_token_required
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
    # print(request.json)
    # _validate_algo_data(input_data['values'], algo.parameters)  # FIXME
    #print(f'{len(algo.configuration["features"])}')
    try:
        #print(f'input_data = {input_data["values"]}')
        for row in input_data['values']:
            check = True
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


@blueprint.route('<uuid>/update2', methods=['POST'])
# TODO Something like this?  @Ali @rl_server_token_required # Make sure this only exposed on the server
# @rl_token_required # FIXME TODO
def update2(uuid: str) -> dict:
    input_data = request.json
    try:
        return {
            "status_code": StatusCode.SUCCESS.value,
            "status_message": f"Update successful for algorithm instance {uuid}"
        }
        # _run_update_on_algorithm(uuid)

        # if decision_output:
        #     return decision_output
        # else:
        #     return {'status_code': StatusCode.ERROR.value,
        #             # TODO: this needs to be some sort of error response in the decision fails.
        #             'status_message': f'A decision was unable to be made for: {uuid}'}
    except Exception as e:
        traceback.print_exc()
        return {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }


@blueprint.route('<uuid>/update', methods=['POST'])
# TODO Something like this?  @Ali @rl_server_token_required # Make sure this only exposed on the server
# @rl_token_required # FIXME TODO
def update(uuid: str) -> dict:
    input_data = request.json
    try:
        algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).first()
        #TODO: @Ali It doesn't make sense to me that the  configuration is the input_data.  For now, there will be no parameters and the 'update' will retraint the model for all users in the backend.
        algorithm.configuration = input_data
        db.session.commit()

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


@blueprint.route('/algorithms/<algo_id>', methods=['GET'])  # or UUID
@login_required
def algorithms(algo_id):
    algo = db.session.query(Algorithms).filter(Algorithms.id == algo_id).filter(Algorithms.finalized == 1).first()
    if not algo:
        return {"status": "error",
                "message": "Algorithm ID does not exist or algorithm has not been finalized yet."}, 400
    else:
        return algo.as_dict()
