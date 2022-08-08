from apps.learning_models.LearningModelBase import LearningModelBase
import pandas as pd
class ThompsonSampling(LearningModelBase):

    def __init__(self):
        super().__init__()
        self.type = "ThompsonSampling" #this should be same as class name
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
                "upper_bound":"inf",
                "inclusive": [True,True],
                "default_value": 0.9
            },
            "alpha0_sigma": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound":"inf",
                "inclusive": [False,True],
                "default_value": 0.9
            },
            "beta_selected_features": {
                "description": "Some description",
                "type": "str",
                "lower_bound": "no",
                "upper_bound":"yes",
                "inclusive": [True,True],
                "default_value": "yes"
            },
            "beta_mu": {
                "description": "Some description",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound":"inf",
                "inclusive": [True,True],
                "default_value": 0.99
            },
            "beta_sigma": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound":"inf",
                "inclusive": [False,True],
                "default_value": 0.9
            }
        }
        # TODO: change name -> standalone_parameters
        self.standalone_parameters = {
            "alpha_0_mu_bias": {
                "description": "Some description",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound":"inf",
                "inclusive": [True,True],
                "default_value": 0.31
            },
            "alpha_0_sigma_bias": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound":"inf",
                "inclusive": [False,True],
                "default_value": 0.32
            },
            "beta_mu_bias" : {
                "description": "Some description",
                "type": "float",
                "lower_bound": "-inf",
                "upper_bound":"inf",
                "inclusive": [True,True],
                "default_value": 0.33
            },
            "beta_sigma_bias": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound":"inf",
                "inclusive": [False,True],
                "default_value": 0.34
            },
            "noice": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound":"inf",
                "inclusive": [False,True],
                "default_value": 0.35
            }

        }
        self.other_parameters = {
            "lower_clip": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound":1,
                "inclusive": [True,True],
                "default_value": 0.39
            },
            "upper_clip": {
                "description": "Some description",
                "type": "float",
                "lower_bound": 0,
                "upper_bound":1,
                "inclusive": [True,True],
                "default_value": 0.8
            }
        }

        # TODO: move to base class??
        self.tuning_scheduler = {
            "name": "update_interval",
            "description": "time interval between running algorithm and update policy. Time is in seconds/minutes???",
            "type": "float",
            "lower_bound": 0,
            "upper_bound":"pinf",
            "inclusive": [True,True],
            "default_value": 0.39
        }


    def decision(self,  user_id:str, input_data=None) -> pd.DataFrame:
        # TODO: Load algorithm parameters from the datastore and configure by user @Ali
        return {"RUN": "success"}
    
    def update(self, user_id) -> dict:

        # TODO: Load algorithm parameters from the datastore and configure by user @Ali
        
        # TODO: Store tuned parameters to the datastore by user @Ali
        return {"UPDATE": "success"}