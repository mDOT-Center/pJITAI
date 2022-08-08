from apps.learning_models.LearningModelBase import LearningModelBase
from apps.algorithms.models import Algorithms
from apps.api.codes import StatusCode
from apps.api.util import time_8601
import random
import pandas as pd
from apps.api.sql_helper import get_tunned_params, store_tunned_params
class RandomSampling(LearningModelBase):

    def __init__(self):
        super().__init__()
        self.type = "RandomSampling"  # this should be same as class name
        self.description = 'Random Sampling lets you define a list of decisions and their associated probabilities.  It will pick at random from the list'

        self.parameters = {
            
        }
        
        self.standalone_parameters = {
            

        }
        self.other_parameters = {
            
        }


        # TODO: @Ali This is not needed for RandomSampling but can be left in place.
        # TODO: @Ali Update Interval needs to be better defined.
        self.tuning_scheduler = {
            "name": "update_interval",
            "description": "time interval between running algorithm and update policy. Time is in seconds/minutes???",
            "default_value": 86400 # TODO: Daily
        }


    def decision(self,  user_id:str, input_data=None) -> pd.DataFrame:

        # TODO: getting default algo object of an algo
        #cls_obj = self.as_object(algorithm_parameters)

        #TODO: get data from algo_params table and populate object per user
        #TODO: tunned_parameters = self.get_tunned_parameters(user_id)
            #TODO: return type would be pandas dict
            #TODO: select * from algo_params where user_id=user_id order by desc limit 1
        #TODO: tunned_parameters.get("param_name")

        # TODO: do something with parameters and input_data

        #my_class = cls_obj.initialize(algorithm_parameters)
        
        # TODO: Remove this once the data method is implemented
        # TODO: A method to retrieve data from the DB
        # TODO: part of algorithm (inside algo params)
        # decision_options = my_class.getDecisionOptions()

        decision_options = [
            {
                'name': 'Do Nothing',
                'value': 0.2,
            },
            {
                'name': 'MARS Intervention',
                'value': 0.3,
            },
            {
                'name': 'Headspace',
                'value': 0.25,
            },
            {
                'name': 'Offer Encouragement',
                'value': 0.25,
            }
        ]
        
        s = 0
        cum_sum_list = [0]
        for decision in decision_options:
            s += decision['value']
            cum_sum_list.append(s)
        
        random_number = random.random()
        selection = 0
        for i,v in enumerate(cum_sum_list):
            if v > cum_sum_list[i] and v <= cum_sum_list[i+1]:
                selection = i
        
        my_decision = decision_options[selection]['name']

        result = {
            'timestamp': time_8601(),
            'user_id': user_id,
            'selection': my_decision,
            'status_code': StatusCode.SUCCESS.value,
            'status_message': "Decision made successfully"
        }

        result = pd.DataFrame(result, index=[0])
        
        # Example Result:
        #                              timestamp user_id  selection status_code              status_message
        #    0  2022-08-04T12:44:34.194011-05:00  user_1  Headspace     SUCCESS  Decision made successfully
        return result


    # TODO: How to handle this call if it is async from the REST API?
    def update(self, user_id) -> dict:

        # This should read the data and update the model

        # TODO: Load algorithm parameters from the datastore and configure by user @Ali
        tunned_params = get_tunned_params(user_id)

        # TODO: Store tuned parameters to the datastore by user @Ali
        store_tunned_params(user_id, tunned_params)

        #TODO: above TODOs don't make sense. Maybe missing any processing? @tim

        result = {
            'timestamp': time_8601(),
            'status_code': StatusCode.SUCCESS.value,
            'status_message': "Update process successfully initiated.  Please allow enough time for it to complete before retrieving new data."
        }
        result = pd.DataFrame(result, index=[0])
        
        return result

    
    
    # TODO: @Ali Where is the required "update" method?


