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
from functools import wraps

import pandas as pd
from apps import db
from apps.algorithms.models import Algorithms
from apps.api import blueprint
from apps.api.codes import StatusCode
from apps.api.sql_helper import get_tuned_params, json_to_series, store_tuned_params
from apps.learning_models.learning_model_service import get_all_available_models
from flask import jsonify, request
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError

from .models import Data, Logs
from .util import get_class_object, pJITAI_token_required, time_8601, _validate_algo_data


def _save_each_data_row(user_id: str,
                        decision_timestamp: str,
                        decision,
                        proximal_outcome_timestamp: str,
                        proximal_outcome,
                        data: list,
                        algo_uuid=None) -> dict:
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


def _add_log(log_detail: dict, algo_uuid=None) -> dict:  # TODO: This should be moved to the utils file?
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


def _do_update(algo_uuid):
    algorithm = Algorithms.query.filter(Algorithms.uuid == algo_uuid).first()
    cls = get_class_object(f"apps.learning_models.{algorithm.type}.{algorithm.type}")
    obj = cls()
    obj.as_object(algorithm)
    result = obj.update()

    for index, row in result.iterrows():
        store_tuned_params(user_id=row.user_id,
                           configuration=row.iloc[2:].to_dict())


# API METHODS ARE BELOW

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
        validated_data = _validate_algo_data(uuid, input_data['values'])

        validated_data_df = pd.DataFrame(json_to_series(validated_data)).transpose()

        user_id = input_data['user_id'],
        input_data = validated_data_df

        algorithm = Algorithms.query.filter(Algorithms.uuid == uuid).first()
        cls = get_class_object(f"apps.learning_models.{algorithm.type}.{algorithm.type}")
        obj = cls()
        obj.as_object(algorithm)  # TODO: What does this do?

        tuned_params = get_tuned_params(user_id=user_id)
        tuned_params_df = None
        if len(tuned_params) > 0:
            tuned_params = tuned_params.iloc[0]['configuration']
            tuned_params_df = pd.json_normalize(tuned_params)

        decision_output = obj.decision(user_id, tuned_params_df, input_data)

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
        validated_input_data = _validate_algo_data(uuid, input_data['values'])
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


@blueprint.route('<uuid>/update', methods=['POST'])
@pJITAI_token_required
def update(uuid: str) -> dict:
    input_data = request.json
    try:
        '''
        Call the alogrithm update method

        '''
        # TODO: Something like this for async calls?
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
