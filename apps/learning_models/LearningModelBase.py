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


class LearningModelBase(metaclass=ABCMeta):

    def __init__(self, algorithm_specs=None):
        # self.uuid = algorithm_specs.uuid
        # self.name = algorithm_specs.name
        # self.description = algorithm_specs.description
        # self.finalized = algorithm_specs.finalized
        # configs = algorithm_specs.configuration
        # #self.parameters = configs.get("",{})
        # self.standalone_parameters = configs.get("standalone_parameters",{})
        # self.other_parameters = configs.get("other_parameters",{})
        # self.tuning_scheduler = configs.get("tuning_scheduler",{})
        # self.features=configs.get("features",{})
        # self.created_on = algorithm_specs.created_on
        # self.created_by = algorithm_specs.created_by

        self.uuid = None
        self.name = None
        self.desciption = None
        self.finalized = 0
        self.parameters = {}
        self.standalone_parameters = []
        self.other_parameters = []
        self.tuning_scheduler = {}
        self.features = []
        self.created_on = None
        self.created_by = None
        availability = {}
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
        self.name = algorithm_specs.name
        self.desciption = algorithm_specs.description
        self.finalized = algorithm_specs.finalized
        configs = algorithm_specs.configuration
        #self.parameters = configs.get("",{})
        self.standalone_parameters = configs.get("standalone_parameters", {})
        self.other_parameters = configs.get("other_parameters", {})
        self.tuning_scheduler = configs.get("tuning_scheduler", {})
        self.features = configs.get("features", {})
        self.created_on = algorithm_specs.created_on
        self.created_by = algorithm_specs.created_by

    @abstractmethod
    def decision(self,  user_id: str, input_data=None) -> pd.DataFrame:
        pass

    @abstractmethod
    def update(self, user_id) -> dict:
        pass

    def model_definition(self) -> dict:
        return {'inputs': self.get_inputs(), 'outputs': self.get_outputs(), 'parameters': self.get_parameters()}
