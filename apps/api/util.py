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

from datetime import datetime
from functools import wraps
import inspect
import traceback
from flask import request

from apps.algorithms.models import Algorithms
from apps.api.codes import StatusCode
from apps import db
from sqlalchemy.exc import SQLAlchemyError

from .models import Log

def pJITAI_token_required(f):
    @ wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('pJITAI_token')
        if not token:
            return {
                'status_code': StatusCode.ERROR.value,
                'status_message': 'Token not found'
            }, 400

        result = db.session.query(Algorithms).filter(Algorithms.auth_token == token).first()
        if result:
            return f(*args, **kwargs)
        else:
            return {
                'status_code': StatusCode.ERROR.value,
                'status_message': 'Invalid security token'
            }, 400

    return decorated


def time_8601(time=datetime.now()) -> str:
    return time.astimezone().isoformat()

def time_8601_to_datetime(input_time):
    return datetime.fromisoformat(input_time)


def get_class_object(class_path: str):
    from importlib import import_module

    module_path, class_name = class_path.rsplit('.', 1)
    module = import_module(module_path)

    return getattr(module, class_name)


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
            raise Exception(f"Missing feature: {f}, expected: {features_config.keys()}")

    for val in feature_vector:
        validation = dict()
        validation['status_code'] = StatusCode.SUCCESS.value

        feature_name = val['name']
        feature_value = val['value']

        if feature_name not in features_config:
            raise Exception(f"Received unknown feature: {feature_name}, expected: {features_config.keys()}")

        # This is the defined configuration for the algorithm
        ft_def = features_config[feature_name]

        feature_value_type = type(feature_value)
        # This is teh defined data type of the feature defined in the config
        feature_data_type = ft_def['feature_data_type']
        if feature_data_type != feature_value_type.__name__:
            raise Exception(f"Incorrect feature type for {feature_name}, expected: {feature_data_type} received: {feature_value_type}")

        if feature_data_type == 'int':
            try:
                feature_value = int(feature_value)
                lower_bound_value = str(ft_def['feature_lower_bound'])
                if 'inf' not in lower_bound_value:
                    lower_bound = int(lower_bound_value)
                    if feature_value < lower_bound:
                        validation['status_code'] = StatusCode.WARNING_OUT_OF_BOUNDS.value
                        validation['status_message'] = f'{feature_name} with value {feature_value} is lower than the lower bound value {lower_bound}.'
                upper_bound_value = str(ft_def['feature_upper_bound'])
                if 'inf' not in upper_bound_value:
                    upper_bound = int(upper_bound_value)
                    if feature_value > upper_bound:
                        validation['status_code'] = StatusCode.WARNING_OUT_OF_BOUNDS.value
                        validation['status_message'] = f'{feature_name} with value {feature_value} is greater than the upper bound value {upper_bound}.'
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


def _add_log(algo_uuid:str=None,log_detail: dict=None, ) -> dict:  # TODO: This should be moved to the utils file?
    calling_method = inspect.stack()[1][3] # Look at the calling stack for the parent method
    calling_file = inspect.stack()[1][1]
    try:
        log_detail['calling_method'] = calling_method
        log_detail['calling_file'] = calling_file
        log = Log(algo_uuid=algo_uuid, details=log_detail, created_on=time_8601())
        db.session.add(log)
        db.session.commit()
    except SQLAlchemyError as e:
        resp = str(e.__dict__['orig'])
        db.session.rollback()
        print(traceback.format_exc())
    except:
        print(traceback.format_exc())