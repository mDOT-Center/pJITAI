import uuid
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
        self.features=[]
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
        self.standalone_parameters = configs.get("standalone_parameters",{})
        self.other_parameters = configs.get("other_parameters",{})
        self.tuning_scheduler = configs.get("tuning_scheduler",{})
        self.features=configs.get("features",{})
        self.created_on = algorithm_specs.created_on
        self.created_by = algorithm_specs.created_by


    @abstractmethod
    def decision(self,  user_id:str, input_data=None) -> pd.DataFrame:
        pass
    
    @abstractmethod
    def update(self) -> dict:
        pass

    def model_definition(self) -> dict:
        return {'inputs': self.get_inputs(), 'outputs': self.get_outputs(), 'parameters': self.get_parameters()}