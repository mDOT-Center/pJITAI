# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import json

from apps.api import blueprint
from flask import render_template, request
from flask_login import login_required
from flask import jsonify
from jinja2 import TemplateNotFound
from datetime import datetime
from apps import db
from apps.algorithms.models import Algorithms
from apps.learning_models.learning_model_service import get_all_available_models

# @blueprint.route('/<algo_name>/<type>') #or UUID
# @login_required
# def index(algo_name):
#     # all finalized algorithms could be accessed using this api point
#     return "api code for "+algo_name

@blueprint.route('<uuid>/', methods=['GET'])
#@login_required
def index():
    return {"status":"success", "message":"Model name: TODO", "model":"mode file - TODO"}

@blueprint.route('<uuid>/decision', methods=['POST'])
def decision(uuid):
    """
    Same input like batch_update
    Inputs: list of features and params, param whether run algo for one user or all users, weights associated with user-id (map for weights users)
    Output: list of probs and actions
    Process:
        make a call to the algorithm
        returns probabilities of all the potential options
    :param query:
    :return:
    """
    return {"status":"success", "message":"Decision for algo ID: "+uuid}


@blueprint.route('<uuid>/batch_update', methods=['POST', 'GET']) #or UUID
def batch_update(uuid):
    """
    Input: json data structure (structure?)
    https://github.com/mDOT-Center/reinforcement-learning/blob/main/cloud/notes/thompson_sampling_example.json - 242
    Process:
        convert json into binary data structure (e.g., numpy) (question: what data will be sent from phone)
        make a call to the algorithm
        returns a data structure (structure???) (e.g., posterior_sampling_weights)

    :return:
    """
    # algo_uuid = uuid
    # data = request.form.get("data")
    # from modules.demo_algorithm.demo import demo_method
    # result = demo_method(data)
    # result["params"] = jsonify(request.form).json
    # return result
    return {"status":"success", "message":"Batch updated for Model ID: "+uuid}


@blueprint.route('<uuid>/validate', methods=['POST'])
#@login_required
def validate(uuid):
    return {"status":"success", "message":"Data validated for algo ID: "+uuid}


@blueprint.route('/run_algo/<algo_type>', methods=['POST']) #or UUID
@login_required
def run_algo(algo_type):
    # all finalized algorithms could be accessed using this api point
    algo_definitions = get_all_available_models()
    algo_info = {}
    form_type = request.form.get("form_type")
    if algo_type not in algo_definitions:
        return {"status":"error","message":algo_type+" does not exist."},400
    if not request.form:
        return {"status":"error", "message":"Form cannot be empty."},400

    if form_type=="add" or form_type=="new":
        if not request.form.get("algorithm_name"):
            return {"status":"error", "message":"Algorithm name cannot be empty."},400

        algo_info["name"] = request.form.get("algorithm_name")
        algo_info["description"] = request.form.get("algorithm_description")
        algo_info["type"] = request.form.get("algorithm_type")
        configuration = {}

        features = {}
        standalone_parameter = {}
        other_parameter ={}

        for param in request.form:
            arr = param. split("__")
            if param.startswith("feature"):
                if not features.get(arr[-1]):
                    features[arr[-1]] = {}
                features[arr[-1]].update({arr[0]:request.form[param]})
            elif param.startswith("standalone_parameter"):
                standalone_parameter.update({arr[1]:request.form[param]})
            elif param.startswith("other_parameter"):
                other_parameter.update({arr[1]:request.form[param]})

        configuration["features"] = features
        configuration["standalone_parameters"] = standalone_parameter
        configuration["other_parameters"] = other_parameter
        configuration["tuning_scheduler"] = {}
        if request.form.get("availability"):
            configuration["availability"] = {"availability":request.form.get("availability")}

        algo_info["features"] = features
        algo_info["standalone_parameter"] = standalone_parameter
        algo_info["other_parameter"] = other_parameter

        #return algo_info
        return {"status":"success", "message":"Algorithm ran successfully. Output is TODO"}
    return {"status":"error", "message":"Some error occurred. Check the logs."},400


@blueprint.route('/search/<query>', methods=['POST','GET']) #or UUID
@login_required
def search(query):
    results = []
    search = "%{}%".format(query)
    algos = Algorithms.query.filter(Algorithms.name.like(search) | Algorithms.type.like(search)).all()
    if not algos:
        return {"status":"error", "message":"No result found."},400
    else:
        for al in algos:
            results.append(al.as_dict())
        #print(algos)
        return jsonify(results)

@blueprint.route('/algorithms/<id>', methods=['GET']) #or UUID
@login_required
def algorithms(id):
    algo = db.session.query(Algorithms).filter(Algorithms.id == id).filter(Algorithms.finalized==1).first()
    if not algo:
        return {"status":"error", "message":"Algorithm ID does not exist or algorithm has not been finalized yet."},400
    else:
        return algo.as_dict()