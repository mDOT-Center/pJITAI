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

import pandas as pd
from flask import jsonify, request
from flask_login import login_required
from sqlalchemy.exc import SQLAlchemyError

from apps import db
from apps.algorithms.models import Projects
from apps.api import blueprint
from apps.api.codes import StatusCode
from apps.api.sql_helper import get_tuned_params, json_to_series, save_decision, store_tuned_params
from apps.learning_methods.learning_method_service import get_all_available_methods
from .models import Data, Decision
from .util import get_class_object, pJITAI_token_required, _validate_algo_data, _add_log


def _save_each_data_row(user_id: str,
                        decision_id: str,
                        proximal_outcome_timestamp: str,
                        proximal_outcome,
                        data: list,
                        algo_uuid=None) -> dict:
    resp = "Data has successfully added"
    try:

        decision_obj = Decision.query.filter(Decision.decision_id == decision_id).first()

        if decision_obj:
            data_obj = Data(algo_uuid=algo_uuid,
                            values=data,
                            user_id=user_id,
                            decision_id=decision_id,
                            proximal_outcome_timestamp=proximal_outcome_timestamp,
                            proximal_outcome=proximal_outcome)
            db.session.add(data_obj)
            db.session.commit()
        else:
            raise Exception(f'Error saving data: {resp}. {decision_id} was not found.')

    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
        raise Exception(f'Error saving data: {resp}')
    except:
        raise Exception(f'Error saving data: {resp}')


def _do_update(algo_uuid):
    proj = Projects.query.filter(Projects.uuid == algo_uuid).first()
    proj_type = proj.general_settings.get("personalization_method")
    cls = get_class_object(f"apps.learning_methods.{proj_type}.{proj_type}")
    obj = cls()
    obj.as_object(proj)
    result = obj.update()

    for index, row in result.iterrows():
        store_tuned_params(user_id=row.user_id,
                           configuration=row.iloc[2:].to_dict())


# API METHODS ARE BELOW

@blueprint.route('<uuid>', methods=['POST'])
@pJITAI_token_required
def model(uuid: str) -> dict:
    proj = db.session.query(Projects).filter(Projects.uuid == uuid).filter(Projects.project_status == 1).first()
    result = {"status": "ERROR: Algorithm not found"}
    if proj:
        result = proj.as_dict()
    return result


@blueprint.route('<uuid>/decision', methods=['POST', 'GET'])
@pJITAI_token_required
def decision(uuid: str) -> dict:
    input_data = request.json
    try:
        
        # TODO: Do something with input_data['eligilibity'] (https://github.com/mDOT-Center/pJITAI/issues/21)
        
        validated_data = _validate_algo_data(uuid, input_data['values'])

        validated_data_df = pd.DataFrame(json_to_series(validated_data)).transpose()

        user_id = input_data['user_id'],
        input_data = validated_data_df

        proj = Projects.query.filter(Projects.uuid == uuid).first()
        proj_type = proj.general_settings.get("personalization_method")
        cls = get_class_object(f"apps.learning_methods.{proj_type}.{proj_type}")
        obj = cls()
        obj.as_object(proj)  # TODO: What does this do?

        tuned_params = get_tuned_params(user_id=user_id)
        tuned_params_df = None

        timestamp = request.json['timestamp']

        if len(tuned_params) > 0:
            tuned_params = tuned_params.iloc[0]['configuration']
            tuned_params_df = pd.json_normalize(tuned_params)

        decision = obj.decision(user_id, timestamp, tuned_params_df, input_data)
        save_decision(decision)  # Save the decision to the database
        decision_output = decision.as_dataframe()
        if len(decision_output) > 0:

            # Only one row is currently supported.  Extract it and convert to a dictionary before returning to the calling library.
            result = decision_output.iloc[0].to_dict()
            _add_log(algo_uuid=uuid, log_detail={'input_data': input_data.iloc[0].to_dict(), 'response': result,
                                                 'http_status_code': 200})
            return result, 200
        else:
            result = {
                'status_code': StatusCode.ERROR.value,
                'status_message': f'A decision was unable to be made for: {uuid} with validated data: {validated_data}'
            }
            _add_log(algo_uuid=uuid, log_detail={'input_data': input_data.iloc[0].to_dict(
            ), 'response': None, 'error': result, 'http_status_code': 400})
            return result, 400
    except Exception as e:
        traceback.print_exc()
        result = {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }
        _add_log(algo_uuid=uuid,
                 log_detail={'input_data': input_data, 'response': None, 'error': result, 'http_status_code': 400})
        return result, 400


@blueprint.route('<uuid>/upload', methods=['POST'])
@pJITAI_token_required  # TODO: This should actually check the token
def upload(uuid: str) -> dict:
    input_data = request.json
    try:
        validated_input_data = _validate_algo_data(uuid, input_data['values'])
        _save_each_data_row(input_data['user_id'],
                            decision_id=input_data['decision_id'],
                            proximal_outcome_timestamp=input_data['proximal_outcome_timestamp'],
                            proximal_outcome=input_data['proximal_outcome'],
                            data=validated_input_data,
                            algo_uuid=uuid)
        result = {
            "status_code": StatusCode.SUCCESS.value,
            "status_message": f"Data uploaded fo model {uuid}"
        }
        _add_log(algo_uuid=uuid,
                 log_detail={'input_data': validated_input_data, 'response': result, 'http_status_code': 200})
        return result, 200
    except Exception as e:
        traceback.print_exc()
        result = {
            'status_code': StatusCode.ERROR.value,
            'status_message': f'A decision was unable to be made for: {uuid} with input data: {input_data}'
        }
        _add_log(algo_uuid=uuid,
                 log_detail={'input_data': input_data, 'response': None, 'error': result, 'http_status_code': 400})
        return result, 400


@blueprint.route('<uuid>/update', methods=['POST'])
@pJITAI_token_required
def update(uuid: str) -> dict:
    input_data = request.json
    try:
        '''
        Call the alogrithm update method

        '''
        _do_update(algo_uuid=uuid)

        result = {
            "status_code": StatusCode.SUCCESS.value,
            "status_message": "Background update proceedure has been started.",
        }
        _add_log(algo_uuid=uuid, log_detail={'input_data': input_data, 'response': result, 'http_status_code': 200})
        return result, 200

    except Exception as e:
        traceback.print_exc()
        result = {
            "status_code": StatusCode.ERROR.value,
            "status_message": str(e),
        }
        _add_log(algo_uuid=uuid,
                 log_detail={'input_data': input_data, 'response': None, 'error': result, 'http_status_code': 400})
        return result, 400


# Web UI related APIs below here #TODO: Move these to a separate file?
@blueprint.route('/run_algo/<algo_type>', methods=['POST'])  # or UUID
@login_required
def run_algo(algo_type):
    # all finalized algorithms could be accessed using this api point
    algo_definitions = get_all_available_methods()
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
    proj = Projects.query.filter(Projects.general_settings.like(search_query)).all()
    if not proj:
        return {"status": "error", "message": "No result found."}, 400
    else:
        for al in proj:
            results.append(al.as_dict())
        return jsonify(results)


@blueprint.route('/projects/<uuid>', methods=['GET'])  # or UUID
@login_required
def proj(uuid):
    proj = db.session.query(Projects).filter(Projects.uuid == uuid).filter(Projects.project_status == 1).first()
    if not proj:
        return {"status": "error",
                "message": "Algorithm ID does not exist or algorithm has not been finalized yet."}, 400
    else:
        return proj.as_dict()

def get_algo_name(uuid):
    proj = db.session.query(Projects).filter(Projects.uuid == uuid).filter(Projects.project_status == 1).first()
    return proj.general_settings.get("personalization_method")