from apps.learning_models.LearningModelBase import LearningModelBase
from apps.algorithms.models import Algorithms
from apps.api.codes import StatusCode
from apps.api.util import time_8601


class RandomSampling(LearningModelBase):

    def __init__(self):
        super().__init__()
        self.type = "RandomSampling"  # this should be same as class name
        self.description = 'some demo def.'
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
        # TODO: move to base class??
        # TODO: Not needed, more discussion is required
        self.availability = {
            "name": "availability",
            "description": "Do we need to check the availability of data",
            "type": "int",
            "default_value": 1
        }

        self.outputs = {'scaling_factor': 1.453, 'num': 148932}
        self.inputs = {'data': []}




    # def decision(self, command: str, user_id=None) -> tuple(str, str):
    #     # TODO: Load algorithm parameters from the datastore and configure by user @Ali
    #
    #     # TODO: implement this
    #     result = {  # TODO: Remove this when the above works
    #         'timestamp': time_8601(),  # TODO: Ensure that this timestamp represents that appropriate timestamp
    #         'user_id': user_id,
    #         'values': [  # values
    #             {
    #                 'name': 'decision_1',
    #                 'probability': 0.3
    #             },
    #             {
    #                 'name': 'decision_2',
    #                 'probability': 0.2
    #             },
    #             {
    #                 'name': 'decision_3',
    #                 'probability': 0.5
    #             },
    #         ],
    #         'status_code': StatusCode.SUCCESS.value,
    #         'status_message': "Decision made successfully"
    #     }
    #     return result

    def decision(self, algorithm_parameters:dict,input_data=None) -> dict:
        # TODO: Load algorithm parameters from the datastore and configure by user @Ali

        cls_obj = self.as_object(algorithm_parameters)
        # TODO: do something with parameters and input_data


        result = {  # TODO: Remove this when the above works
            'timestamp': time_8601(),  # TODO: Ensure that this timestamp represents that appropriate timestamp
            'user_id': "123-123-123-123",
            'values': [  # values
                {
                    'name': 'decision_1',
                    'probability': 0.3
                },
                {
                    'name': 'decision_2',
                    'probability': 0.2
                },
                {
                    'name': 'decision_3',
                    'probability': 0.5
                },
            ],
            'status_code': StatusCode.SUCCESS.value,
            'status_message': "Decision made successfully"
        }
        return result


    def update(self, command: str) -> dict:
        # TODO: implement this
        # This should read the data and update the model

        # TODO: Load algorithm parameters from the datastore and configure by user @Ali

        # TODO: Store tuned parameters to the datastore by user @Ali
        return {"UPDATE": "success"}

    
    
    # TODO: @Ali Where is the required "update" method?


