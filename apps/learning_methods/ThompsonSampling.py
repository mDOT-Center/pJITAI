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

from apps.api.models import Decision
from apps.learning_methods.LearningMethodBase import LearningMethodBase
import pandas as pd
from apps.api.sql_helper import get_data, get_merged_data
from apps.api.codes import StatusCode
from apps.api.util import time_8601
import random

# These are libraries hsinyu include
import numpy as np
from scipy.stats import t

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
        # For now you can change it to "model parameters"
        self.standalone_parameters = {
            # I may want to change the names of all of these
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
        # For now you can change it to "intervention parameters"
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
            # I'm not sure what the unit should be
            "fixed_randomization_period": {
                "description": "length of the fixed randomization period",
                "type": "float",
                "lower_bound": 0,
                "upper_bound": "inf",
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

        # These need to be read from the web user interface
        # I added "value" to represent what each option means in the linear regression. It's super important.
        decision_options = [
            {
                'name': 'Do Nothing',
                'value': 0,
                'prob':0.7,
            },
            {
                'name': 'Send an Intervention',
                'value': 1,
                'prob':0.3,
            }
        ]

        # Initialize all the global parameters appropriately
        self.initialize_from_defaults()

        # Accessing tuned parameters
        # Parameters are access by column name and first row

        try:
            theta_mu = tuned_params.iloc[0]['theta_mu']
            theta_Sigma = tuned_params.iloc[0]['theta_Sigma']
            degree = tuned_params.iloc[0]['degree']
            scale = tuned_params.iloc[0]['scale']
            
        except Exception as e: # Something is wrong or data is missing, assuming defaults
            theta_mu = self._theta_mu_ini
            theta_Sigma = self._theta_Sigma_ini
            degree = self._degree_ini
            scale = self._scale_ini

        # Setup the state
        state=[]
        for feature_name in self._feature_name_list:
            # We will need to check the eligibility as well!
            if(input_data.iloc[0][feature_name+'_validation_status_code']=='SUCCESS'):
                state.append(input_data.iloc[0][feature_name])
        state=np.array([state]).T

        # Check whether it's eligible 
        if(False):
            pi=0

        # Check whether all the covariates are valid => If not, what should we do?
        elif(len(state)!=self._state_dim):
            pi=0
        
        # Check whether it's fixed randomization period
        elif(False):
            # There is a missing parameter from the web interface as well
            print("To-Do")

        # Personalization (Thompson Sampling)
        else:
            beta_mu=theta_mu[self._alpha_len:]
            beta_Sigma=theta_Sigma[self._alpha_len:,:][:,self._alpha_len:]

            # mu_t and Sigma_t are associated with the f(S)*beta
            mu_t=np.matmul(np.transpose(self.action_center(state)),beta_mu)
            Sigma_t=np.matmul(np.transpose(self.action_center(state)),beta_Sigma)

            # Notice that the posterior variance of f(S)*beta is scaled by the scale of the inverse chi-square distribution
            Sigma_t= scale*np.matmul(Sigma_t,self.action_center(state))

            # f(S)*beta is a multivariate t distribution with mean mu_t, variance Sigma_t, and degree of freedom L
            pi=1-t.cdf(0, degree, loc=mu_t, scale=Sigma_t)
            pi=max(self._lower_clip,pi)
            pi=min(self._upper_clip,pi)

        random_number=random.uniform(0,1)
        if(pi>random_number):
            my_decision = 1 # decision_options[1]['name']
        else:
            my_decision = 0 # decision_options[0]['name']

        # We need to record pi as well

        decision = Decision(user_id=user_id,
                            algo_uuid=self.uuid,
                            decision=my_decision,
                            decision_options=decision_options,
                            status_code = StatusCode.SUCCESS.value,
                            status_message = "Decision made successfully")

        return decision

    def update(self) -> dict:
        data = get_merged_data(algo_id=self.uuid)

        columns = ['timestamp', 'user_id']
        
        
        # Create column names for the datafram        

        columns.append('theta_mu')
        columns.append('theta_Sigma')
        columns.append('degree')
        columns.append('scale')

        result = pd.DataFrame([], columns=columns)

        # I move the initialization out because it only needs to be done once for everyone
        self.initialize_from_defaults()

        for u in data.user_id.unique():
            result_data = [time_8601(), u]

            theta_mu, theta_Sigma, degree, scale = self.update_parameters(data[data.user_id==u])
            
            result_data.append(theta_mu)
            result_data.append(theta_Sigma)
            result_data.append(degree)
            result_data.append(scale)
            temp = pd.DataFrame([result_data], columns=columns)
            result = pd.concat([result, temp], ignore_index=True)

        return result

    # Create all the tuned parameters from the parameters read from the web user interface
     # This should match the "parameter_initialization" here: https://github.com/StatisticalReinforcementLearningLab/mDOT_toolbox/blob/master/TS_Toolbox_inverse_gamma_v1.py
    def initialize_from_defaults(self):
        # Let's for now not set it as numpy array
        # We can also initialize the following as an numpy array. Not sure what we prefer. For now, I keep everything consistent.
        alpha0_mu=[]
        beta_mu=[]
        alpha0_std_sigma=[]
        beta_std_sigma=[]
        action_center_ind=[]

        feature_name_list=[]

        for key, feature in self.features.items():
            index = int(key)-1  #TODO: Why do I have to change the type on the index? and subtract 1
            # There might be a better way to do this. Let me try to be safe to ensure the order of the features is consistent.
            feature_name = feature['feature_name']
            feature_name_list.append(feature_name)
            alpha0_mu.append(float(feature['feature_parameter_alpha0_mu']))
            alpha0_std_sigma.append(float(feature['feature_parameter_alpha0_sigma']))
            if(feature['feature_parameter_beta_selected_features']=='yes'):
                beta_mu.append(float(feature['feature_parameter_beta_mu']))
                beta_std_sigma.append(float(feature['feature_parameter_beta_sigma']))
                action_center_ind.append(1)
            else:
                action_center_ind.append(0)
 
        
            
        alpha0_mu.append(float(self.standalone_parameters['alpha_0_mu_bias']))
        beta_mu.append(float(self.standalone_parameters['beta_sigma_bias']))
        alpha0_std_sigma.append(float(self.standalone_parameters['alpha_0_sigma_bias']))
        beta_std_sigma.append(float(self.standalone_parameters['beta_sigma_bias']))


        # Let's setup all the global parameters
        # This degree_ini is missing. This one should be read from the web user interface. We need more inputs!
        self._degree_ini=1
        self._scale_ini=float(self.standalone_parameters['noice'])
        self._lower_clip=float(self.other_parameters['lower_clip'])
        self._upper_clip=float(self.other_parameters['upper_clip'])
        self._state_dim=len(self.features.items()) # Number of states
        self._action_center_ind=np.array([action_center_ind]).T # Which of these states are tailoring variables
        self._alpha_len=len(alpha0_mu)+len(beta_mu)
        # This is for reading through the values of each feature and the validation code
        self._feature_name_list=feature_name_list

        
        # We can initialize theta_mu and theta_sigma here
        # Eventually the standardization would need to happen here
        # Right now we haven't changed theta_Sigma with respect to the scaling parameter of the noise
        theta_mu_ini=np.array([alpha0_mu+beta_mu+beta_mu]).T
        theta_sigma_list=alpha0_std_sigma+beta_std_sigma+beta_std_sigma
        theta_Sigma_ini=np.diag(np.array(theta_sigma_list)**2/self._scale_ini)
        
        self._theta_mu_ini=theta_mu_ini
        self._theta_Sigma_ini=theta_Sigma_ini


    # This function should match with the "update" function here: https://github.com/StatisticalReinforcementLearningLab/mDOT_toolbox/blob/master/TS_Toolbox_inverse_gamma_v1.py
    def update_parameters(self, data):
        # I want to select all the data with valid validation status code (ask Tim) and concatenate the data into a matrix of ...
        # I'll use a for loop for now 
        # (This is a lame implementation but is the most careful one)
        #state_list=[]
        Phi_all=np.array([],dtype=float).reshape(len(self._theta_mu_ini),0)
        reward_all=[]
        for row in data.itertuples():
            state=[]
            for feature_name in self._feature_name_list:
                # We will need to check the eligibility as well!
                if(getattr(row,feature_name+'_validation_status_code')=='SUCCESS'):
                    state.append(getattr(row,feature_name))
            # If all the states are "valid"
            if(len(state)==self._state_dim):
                state=np.array([state]).T
                # Check how to grab the decision and how the decision is coded in numerical values
                action=getattr(row,'decision')
                # we will need to grab the intervention probability as well
                pi=0.5
                Phi=self.reward_model(state,action,pi)
                Phi_all=np.hstack((Phi_all,Phi))
                reward_all.append(getattr(row,'proximal_outcome'))
            
        reward_all=np.array([reward_all]).T

        # Now we are ready to update theta
        # Right now I did not handle ill-conditioned matrix
        theta_Sigma=np.linalg.inv(np.linalg.inv(self._theta_Sigma_ini)+np.matmul(Phi_all,np.transpose(Phi_all)))
        theta_mu=np.matmul(np.linalg.inv(self._theta_Sigma_ini),self._theta_mu_ini)+np.matmul(Phi_all,reward_all)
        theta_mu=np.matmul(theta_Sigma,theta_mu)

        # Now we update the noise
        degree=self._degree_ini+len(reward_all)
        tmp0=reward_all-np.matmul(np.transpose(Phi_all),self._theta_mu_ini)
        tmp=np.linalg.solve(np.matmul(np.matmul(np.transpose(Phi_all),self._theta_Sigma_ini),Phi_all)+np.identity(len(reward_all)), tmp0)
        scale=1/degree*(len(reward_all)*self._scale_ini+np.matmul(np.transpose(tmp0),tmp))

        return theta_mu, theta_Sigma, degree, scale

    # The follows are helper functions for Thompson sampling

    # g(S) in Peng's paper
    def baseline(self, state):
        return np.concatenate((state,np.ones((1,1))),axis=0)

    # f(S) in Peng's paper
    def action_center(self, state):
        idx=(self._action_center_ind==1)
        tmp=state[idx.flatten(),:]
        tmp=np.concatenate((tmp,np.ones((1,1))),axis=0)
        return tmp

    # THis is the model for generating Phi(State,Action)
    def reward_model(self, state, action, pi):
        Phi=np.concatenate((self.baseline(state),pi*self.action_center(state)),axis=0)
        Phi=np.concatenate((Phi,(action-pi)*self.action_center(state)),axis=0)
        return Phi
