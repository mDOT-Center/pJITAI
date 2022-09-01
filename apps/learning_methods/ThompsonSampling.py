'''
Copyright (c) 2022 University of Memphis, mDOT Center and Harvard University. 
All rights reserved. 

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

from apps.learning_methods.LearningMethodBase import LearningMethodBase
import pandas as pd
from apps.api.sql_helper import get_data
from apps.api.util import time_8601

class ThompsonSampling(LearningMethodBase):

    def __init__(self):
        super().__init__()
        self.type = "ThompsonSampling"  # this should be same as class name
        self.description = 'This is the thomson sampling algorithm definition.'
        # TODO: for all sigma range (0 to +inf) and for all mu, (-inf, +inf), Noise is same like sigma
        # technical section: param section for behav scitn.
        # help /FAQ
        # more info/tutorial
        # should have a left/right pane on the same screen
        # after run, finalize/contract (create a micro service, create a new url, where a 3rd party can accesss the finalized algo)

        self.parameters = {
            "alpha0_mu": {
                "description": "baseline prior mean",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 0
            },
            "alpha0_sigma": {
                "description": "baseline prior std",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 3.16
            },
            "beta_selected_features": {
                "description": "tailoring variable or not",
                "type": "str",
                "lower_bound": "no",
                "upper_bound": "yes",
                "inclusive": [True, True],
                "default_value": "yes"
            },
            "beta_mu": {
                "description": "tailored effect prior mean",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 0
            },
            "beta_sigma": {
                "description": "tailored effect prior std",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 3.16
            }
        }
        # TODO: change name -> standalone_parameters
        self.standalone_parameters = {
            "alpha_0_mu_bias": {
                "description": "intercept prior mean",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 0
            },
            "alpha_0_sigma_bias": {
                "description": "intercept prior std",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 3.16
            },
            "beta_mu_bias": {
                "description": "main effect prior mean",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 0
            },
            "beta_sigma_bias": {
                "description": "main effect prior std",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 3.16
            },
            "noise_scale": {
                "description": "scaling parameter of scaled inverse chi square",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 1
            },

            "noise_degree": {
                "description": "degree of freedom of scaled inverse chi square",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, False],
                "default_value": 0.2
            }

        }
        self.other_parameters = {
            "lower_clip": {
                "description": "randomization probability lower bound",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": 1,
                "inclusive": [True, True],
                "default_value": 0.1
            },
            "upper_clip": {
                "description": "randomization probability upper bound",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": 1,
                "inclusive": [True, True],
                "default_value": 0.8
            },
            # I'm not sure what the unit should  be
            "fixed_randomization_period": {
                "description": "length of the fixed randomization period",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": inf,
                "inclusive": [True, False],
                "default_value": 3
            },
            "fixed_randomization_probability": {
                "description": "fixed randomization probability",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": 1,
                "inclusive": [True, True],
                "default_value": 0.3
            }
        },

        # TODO: move to base class??
        self.tuning_scheduler = {
            "name": "update_interval",
            "description": "time interval between running algorithm and update policy. Time is in seconds/minutes???",
            "type": "float",
            "lower_bound": 0,
            "upper_bound": "pinf",
            "inclusive": [True, True],
            "default_value": 0.39
        }

    def decision(self,  user_id: str, tuned_params=None, input_data=None) -> pd.DataFrame:
        # TODO: Load algorithm parameters from the datastore and configure by user @Ali
        return {"RUN": "success"}

    def update(self) -> dict:
        data = get_data(algo_id=self.uuid)


        columns = ['timestamp', 'user_id']
        

        for key, feature in self.features.items():
            feature_name = feature['feature_name']
            a0_mu = f'${feature_name}_alpha0_mu'
            a0_sigma = f'${feature_name}_alpha0_sigma'

            columns.append(a0_mu)
            columns.append(a0_sigma)

        result = pd.DataFrame([], columns=columns)

        for u in data.user_id.unique():
            result_data = [time_8601(), u]
            for key, feature in self.features.items():
                index = int(key)-1  #TODO: Why do I have to change the type on the index? and subtract 1
                feature_name = feature['feature_name']
                feature_alpha0_mu = feature['feature_parameter_alpha0_mu']

                # TODO: Do something with the data...
                # 
                # 

                feature_alpha0_mu_data = feature_alpha0_mu

                result_data.append(feature_alpha0_mu_data)
                result_data.append(feature_alpha0_sigma_data)

            temp = pd.DataFrame([result_data], columns=columns)
            result = pd.concat([result, temp], ignore_index=True)

        return result

