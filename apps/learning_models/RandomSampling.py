from apps.learning_models.LearningModelBase import LearningModelBase
from apps.algorithms.models import Algorithms
from apps.api.codes import StatusCode
from apps.api.util import time_8601
import random
import pandas as pd
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
    

        self.outputs = {'scaling_factor': 1.453, 'num': 148932} #TODO: @Ali What is this?
        self.inputs = {'data': []} #TODO: @Ali What is this?


    def decision(self,  algorithm_parameters:dict, user_id:str, input_data=None) -> pd.DataFrame:
        
        cls_obj = self.as_object(algorithm_parameters)
        # TODO: do something with parameters and input_data

        my_class = cls_obj.initialize(algorithm_parameters)
        
        # TODO: Remove this once the data method is implemented
        # TODO: A method to retrieve data from the DB 
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

        result = pd.DataFrame([], columns=['timestamp','user_id','selection'])

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
    def update(self, algorithm_parameters:dict, command: str) -> dict:
        cls_obj = self.as_object(algorithm_parameters)
        
        # This should read the data and update the model

        # TODO: Load algorithm parameters from the datastore and configure by user @Ali

        # TODO: Store tuned parameters to the datastore by user @Ali
        
        
        
        result = {
            'timestamp': time_8601(),
            'status_code': StatusCode.SUCCESS.value,
            'status_message': "Update process successfully initiated.  Please allow enough time for it to complete before retrieving new data."
        }
        result = pd.DataFrame(result, index=[0])
        
        return result

    
    
    # TODO: @Ali Where is the required "update" method?


