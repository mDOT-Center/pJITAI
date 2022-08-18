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
                "description": "Some description",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound": "inf",
                "inclusive": [True, True],
                "default_value": 0.9
            },
            "alpha0_sigma": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, True],
                "default_value": 0.9
            },
            "beta_selected_features": {
                "description": "Some description",
                "type": "str",
                "lower_bound": "no",
                "upper_bound": "yes",
                "inclusive": [True, True],
                "default_value": "yes"
            },
            "beta_mu": {
                "description": "Some description",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound": "inf",
                "inclusive": [True, True],
                "default_value": 0.99
            },
            "beta_sigma": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, True],
                "default_value": 0.9
            }
        }
        # TODO: change name -> standalone_parameters
        self.standalone_parameters = {
            "alpha_0_mu_bias": {
                "description": "Some description",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound": "inf",
                "inclusive": [True, True],
                "default_value": 0.31
            },
            "alpha_0_sigma_bias": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, True],
                "default_value": 0.32
            },
            "beta_mu_bias": {
                "description": "Some description",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound": "inf",
                "inclusive": [True, True],
                "default_value": 0.33
            },
            "beta_sigma_bias": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, True],
                "default_value": 0.34
            },
            "noice": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
                "inclusive": [False, True],
                "default_value": 0.35
            }

        }
        self.other_parameters = {
            "lower_clip": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": 1,
                "inclusive": [True, True],
                "default_value": 0.39
            },
            "upper_clip": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": 1,
                "inclusive": [True, True],
                "default_value": 0.8
            }
        }

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

        # TODO: Load algorithm parameters from the datastore and configure by user @Ali

        # TODO: Store tuned parameters to the datastore by user @Ali
        return {"UPDATE": "success"}
