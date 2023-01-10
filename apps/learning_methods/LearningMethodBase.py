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

from abc import abstractmethod, ABCMeta

import pandas as pd


class LearningMethodBase(metaclass=ABCMeta):

    def __init__(self, algorithm_specs=None):

        self.uuid = None
        self.general_settings = {}
        self.intervention_settings = {}
        self.model_settings = {}
        self.covariates = {}
        self.project_status = None
        self.created_by = None
        self.modified_on = None
        self.created_on = None

        super().__init__()

    def get_parameters(self) -> dict[str, str]:
        return {k: type(v).__name__ for k, v in self.parameters.items()}

    def get_outputs(self) -> dict[str, str]:
        return {k: type(v).__name__ for k, v in self.outputs.items()}

    def get_inputs(self) -> dict[str, str]:
        return {k: type(v).__name__ for k, v in self.inputs.items()}

    def as_dict(self) -> dict:
        return self.__dict__

    def as_object(self, algorithm_specs):
        """
        Converts a dict object into class object
        :param algorithm_specs: sqlalachemy algorithm table schema
        :return:
        """

        self.uuid = algorithm_specs.uuid
        self.general_settings = algorithm_specs.general_settings
        self.intervention_settings = algorithm_specs.intervention_settings
        self.model_settings = algorithm_specs.model_settings
        self.covariates = algorithm_specs.covariates
        self.project_status = algorithm_specs.project_status
        self.created_by = algorithm_specs.created_by
        self.modified_on = algorithm_specs.modified_on
        self.created_on = algorithm_specs.created_on

    @abstractmethod
    def decision(self, user_id: str, input_data=None) -> pd.DataFrame:
        pass

    @abstractmethod
    def update(self, user_id) -> dict:
        pass

    def method_definition(self) -> dict:
        return {'inputs': self.get_inputs(), 'outputs': self.get_outputs(), 'parameters': self.get_parameters()}
