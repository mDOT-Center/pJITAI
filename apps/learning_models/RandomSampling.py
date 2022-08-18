from apps.learning_models.LearningModelBase import LearningModelBase
from apps.algorithms.models import Algorithms
from apps.api.codes import StatusCode
from apps.api.util import time_8601
import random
import pandas as pd
from apps.api.sql_helper import get_data
from apps.api.sql_helper import get_tuned_params, store_tuned_params
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


    def decision(self,  user_id:str, tuned_params=None, input_data=None) -> pd.DataFrame:
        
        # Accessing tuned parameters
        # Parameters are access by column name and first row
        
        total_step_count = tuned_params.iloc[0]['total_step_count']
        
        
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
            if random_number > cum_sum_list[i] and random_number <= cum_sum_list[i+1]:
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


    def update(self) -> dict:
        data = get_data(algo_id=self.uuid)
        
        columns=['timestamp','user_id','most_recent_step_count','total_step_count']
        result = pd.DataFrame([], columns=columns)
        
        for u in data.user_id.unique():
            most_recent_step_count = data[data.user_id == u].iloc[-1].step_count
            total_step_count = sum(data[data.user_id == u]['step_count'])
            
            temp = pd.DataFrame([[time_8601(), u, most_recent_step_count, total_step_count]], columns=columns)
            result = pd.concat([result, temp], ignore_index=True)
        
        return result
