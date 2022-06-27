# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import json
from functools import wraps

import Status as Status

from apps.api import blueprint
from flask import render_template, request
from flask_login import login_required
from flask import jsonify
from jinja2 import TemplateNotFound
from datetime import datetime
from apps import db
from apps.algorithms.models import Algorithms
from apps.api.codes import StatusCode
from apps.learning_models.learning_model_service import get_all_available_models
from pprint import pprint


def time_8601(time=datetime.now()) -> str:
    return time.astimezone().isoformat()


def _validate_algo_data(uuid: str, input_request: list) -> list:  # TODO: Make this actually do something @Anand
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()  # This gets the algorithm from the system

    # TODO: iterate over input_request and validate against the algorihms specification @Anand
    output_data = input_request
    output_data['status_code'] = StatusCode.SUCCESS.value
    output_data['status_message'] = "All data values passed validation."
    return output_data


def _make_decision(uuid: str, input_data: list) -> dict:  # TODO: Make this actually do something
    # TODO: Call the decision method in this specific algorithm @Ali
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()  # This gets the algorithm from the system

    # values = algo.decision(input_data)  # TODO: We need to do something that accomplishes this @Ali
    # TODO: Reformat result into an appropriate response (e.g. "values" from below)
    result = {  # TODO: Remove this when the above works
        'user_id': input_data['user_id'],
        'timestamp': time_8601(),  # TODO: Ensure that this timestamp represents that appropriate timestamp
        'values': [  # values
            {
                'name': 'decision_1',
                'probability': 0.3
            },
            {
                'name': 'decision_2',
                'probability': 0.2
            },
            {
                'name': 'decision_3',
                'probability': 0.5
            },
        ],
        'status_code': input_data['status_code'],
        'status_message': input_data['status_message']
    }
    return result


def _save_each_data_row(user_id: str, data: dict) -> dict:  # TODO: Make this actually do something
    # TODO: Save each row in data in the SQL storage layer @Ali
    print(user_id)
    pprint(data)

    result = {
        'user_id': data['user_id'],
        'timestamp': time_8601(),  # TODO: Ensure that this timestamp represents that appropriate timestamp
        'status_code': StatusCode.SUCCESS,
        'status_message': StatusCode.SAVE_SUCCESS_MESSAGE
    }
    return result


def rl_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('rltoken')
        if not token:
            return {'ERROR': 'Token is not present'}

        # TODO: Check if the token matches the one present for the algorithm in question @Ali
        # TODO: Add token to the algorithm and WebUI (View Algorithm) @Ali

        return f(*args, **kwargs)

    return decorated


@blueprint.route('<uuid>/', methods=['POST'])
@rl_token_required
def model(uuid: str) -> dict:
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()
    result = {"status": "ERROR: Algorithm not found"}
    if algo:
        result = algo.as_dict()
    return result


@blueprint.route('<uuid>/decision', methods=['POST'])
@rl_token_required
def decision(uuid: str) -> dict:
    input_data = request.json

    validated_data = _validate_algo_data(uuid, input_data['values'])

    decision_output = _make_decision(uuid, validated_data)

    if decision_output:
        return decision_output
    else:
        return {'status': "error",  # TODO: this needs to be some sort of error response in the decision fails.
                'message': f'A decision was unable to be made for: {uuid}'}


@blueprint.route('<uuid>/upload', methods=['POST'])  # or UUID
@rl_token_required
def upload(uuid: str) -> dict:
    input_data = request.json
    algo = Algorithms.query.filter(Algorithms.uuid.like(uuid)).first()
    try:
        for row in input_data['values']:
            if len(row) == algo.features.length:
                # TODO: Consider validating all rows prior to saving
                _save_each_data_row(input_data['user_id'], row)
            else:
                raise Exception("Array out of bounds")
    except Exception as e:
        return {
            "status_code": Status.ERROR,
            #  TODO: make this work    "status_message": f"Array out of bounds.  Received ({len(row)}), Expected ({algo.features.length})"
        }

    return {"status": "success", "message": "Batch updated for Model ID: " + uuid, "input_data": input_data}


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
    search = "%{}%".format(query)
    algos = Algorithms.query.filter(Algorithms.name.like(search) | Algorithms.type.like(search)).all()
    if not algos:
        return {"status": "error", "message": "No result found."}, 400
    else:
        for al in algos:
            results.append(al.as_dict())
        # print(algos)
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
