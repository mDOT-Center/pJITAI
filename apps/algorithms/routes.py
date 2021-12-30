# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import datetime

from flask import render_template, request

import json
from apps import db
from flask_login import login_required, current_user
from apps.algorithms import blueprint
from apps.authentication.models import Users
from apps.algorithms.models import Algorithms
from apps.learning_models.learning_model_service import get_all_available_models

# @blueprint.route('/prebuilt-algorithms', methods=['GET', 'POST'])
# def view_prebuilt_algorithms():
#
#     prebuilt_algorithms = db.session.query(PrebuiltAlgorithms).filter(PrebuiltAlgorithms.type=="prebuilt").all()
#     print(prebuilt_algorithms[0])
#
#     return render_template('algorithms/algorithms_definitions.html',
#                            msg='No Message',
#                            prebuilt_algorithms=prebuilt_algorithms)

@blueprint.route('/algorithms_definitions', methods=['GET'])
@login_required
def algorithms_definitions():

    algorithms_definitions = list_algorithms()
    return render_template('algorithms/algorithms_definitions.html',
                           msg='No Message',
                           algorithms_definitions=algorithms_definitions)

@blueprint.route('/my_algorithms', methods=['GET', 'POST'])
@login_required
def my_algorithms():

    prebuilt_algorithms = db.session.query(PrebuiltAlgorithms).filter(PrebuiltAlgorithms.algorithm_type=="custom").all()
    return render_template('algorithms/algorithms_definitions.html',
                           msg='No Message',
                           prebuilt_algorithms=prebuilt_algorithms)


# @blueprint.route('/algorithm_form/<algorithm_id>', methods=['GET', 'POST'])
# def algorithm_form(algorithm_id):
#
#     prebuilt_algorithms = db.session.query(PrebuiltAlgorithms).filter(PrebuiltAlgorithms.id == algorithm_id).all()
#
#     return render_template('algorithms/algorithm_form.html',
#                            msg='No Message',
#                            prebuilt_algorithms=prebuilt_algorithms[0])


@blueprint.route('/algorithm_form2/<algorithm_name>', methods=['GET', 'POST'])
@login_required
def algorithm_form2(algorithm_name):

    algorithm_definition = list_algorithms(algorithm_name)

    return render_template('algorithms/add_algorithm.html',
                           msg='No Message',
                           algorithm_definition=algorithm_definition)

@blueprint.route('/add_update_algo/', methods=['GET', 'POST'])
@login_required
def add_update_algo():
    if 'add_update_algo' in request.form:
        created_by = current_user.get_id()
        uuid = "123-123-123-123"
        algorithm_name = request.form.get("algorithm_name")
        algorithm_description = request.form.get("algorithm_description")
        study_name = "rl-demo"
        version = 1
        algorithm_type = request.form.get("algorithm_type")
        configuration = {}
        modified_on = datetime.datetime.now()

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
        configuration["standalone_parameter"] = standalone_parameter
        configuration["other_parameter"] = other_parameter
        if request.form.get("availability"):
            configuration["availability"] = {"availability":request.form.get("availability")}

        existing_algo = db.session.query(Algorithms).filter(Algorithms.name == algorithm_name & Algorithms.type==algorithm_type).first()
        if not existing_algo:
            created_on = datetime.datetime.now()
            algo = Algorithms(created_by=created_by, uuid=uuid, name=algorithm_name, description=algorithm_description, study_name=study_name, version=version, type=algorithm_type, configuration=configuration, modified_on=modified_on, created_on=created_on)
            db.session.add(algo)
        else:
            existing_algo.ceated_by = created_by
            existing_algo.uuid = uuid
            existing_algo.name = algorithm_name
            existing_algo.description = algorithm_description
            existing_algo.study_name = study_name
            existing_algo.version = version
            existing_algo.type = algorithm_type
            existing_algo.configuration = configuration
            existing_algo.modified_on = modified_on

        db.session.commit()
        print("sss")



@blueprint.route('/list_algorithms/', methods=['GET'])
@blueprint.route('/list_algorithms/<name>', methods=['GET'])
def list_algorithms(name=None):
    algos = get_all_available_models()
    if name:
        return algos.get(name)
    else:
        return algos
