import urllib.request, json 
import numpy as np
from statistics import NormalDist
from scipy.linalg import block_diag
from scipy.stats import t
#from copy import deepcopy

# This file is currently wrong in that it needs to be modified to be workable with the interface

# Setup default parameters
# The default values won't be changed by the user. Only the algorithm designer (e.g., Susan's students) may want to change them.
_default_mu = 0.0
_default_sigma_2 = 1.0
_default_sigma0_2 =1.0
_default_L = 5
_default_beta_sigma0_2 = 1.0 

# The dictionary will have the covariate name as the key and the value from the UI as the value
def compute_probability(data, action_state_dict):
    # do something with the parameters_json
    num_states=len(data['covariates'])
    action_center_ind=np.zeros((num_states,1))
    state_lower=np.zeros((num_states,1))
    state_upper=np.zeros((num_states,1))
    
    # need to be updated for the intercept too
    alpha0_mu=[]
    alpha0_std_Sigma=[]
    beta_mu=[]
    beta_std_Sigma=[]
    default_alpha_ind=[] 
    default_beta_ind=[] 
    
    action_state_name=[]

    # Set up parameters in the covariates
    count=0
    for i in data['covariates']:

        state_lower[count]=float(data['covariates'][i]['covariate_min_val'])
        state_upper[count]=float(data['covariates'][i]['covariate_max_val'])
        alpha0_mu.append( float(data['covariates'][i]['main_effect_prior_mean']) )
        alpha0_std_Sigma.append( float(data['covariates'][i]['main_effect_prior_standard_deviation']) )

        # Check if the mean and the std are default values
        if(alpha0_mu[-1]==_default_mu and alpha0_std_Sigma[-1]**2==_default_sigma_2):
            default_alpha_ind.append(1)
        else:
            default_alpha_ind.append(0)

        if(data['covariates'][i]['tailoring_variable']=='yes'):
            action_center_ind[count]=1
            action_state_name.append(data['covariates'][i]['covariate_name'])
            beta_mu.append( float(data['covariates'][i]['interaction_coefficient_prior_mean']) )
            beta_std_Sigma.append( float(data['covariates'][i]['interaction_coefficient_prior_standard_deviation']) )

            # Check if the mean and the std are default values
            if(beta_mu[-1]==_default_mu and beta_std_Sigma[-1]**2==_default_sigma_2):
                default_beta_ind.append(1)
            else:
                default_beta_ind.append(0)            

        count=count+1

    # Set up parameters in the model settings (TO-DO'S: NOTICE THAT WE NEED THE NOISE VARIANCE TOO)

    ### TO-DO's

    L=float(data['model_settings']['noise_degree_of_freedom'])
    # Need to check if var_noise is the default. If yes, then set it to zero.
    var_noise=float(data['model_settings']['noise_scale'])
    

    ###

    reward_lower=float(data['model_settings']['min_proximal_outcome'])
    reward_upper=float(data['model_settings']['max_proximal_outcome'])

    alpha0_mu.append( float(data['model_settings']['intercept_prior_mean']) )
    alpha0_std_Sigma.append( float(data['model_settings']['intercept_prior_standard_deviation']) )

    if(alpha0_mu[-1]==_default_mu and alpha0_std_Sigma[-1]**2==_default_sigma_2):
        default_alpha_ind.append(1)
    else:
        default_alpha_ind.append(0)

    beta_mu.append( float(data['model_settings']['treatment_prior_mean']) )
    beta_std_Sigma.append( float(data['model_settings']['treatment_prior_standard_deviation']) )

    if(beta_mu[-1]==_default_mu and beta_std_Sigma[-1]**2==_default_sigma_2):
        default_beta_ind.append(1)
    else:
        default_beta_ind.append(0) 

    # Then modify the dimensionality of the mu's and ind's
    alpha0_mu=np.expand_dims(alpha0_mu,axis=1)
    beta_mu=np.expand_dims(beta_mu,axis=1)
    default_alpha_ind=np.expand_dims(default_alpha_ind,axis=1)
    default_beta_ind=np.expand_dims(default_beta_ind,axis=1)
    alpha0_std_Sigma=np.array(alpha0_std_Sigma)
    beta_std_Sigma=np.array(beta_std_Sigma)

    # Set up parameters in the intervention settings
    lower_clip=float(data['intervention_settings']['intervention_probability_lower_bound'])
    upper_clip=float(data['intervention_settings']['intervention_probability_upper_bound'])

    # Here is the list of parameters we need:
    # default_alpha_ind, alpha0_mu, alpha0_std_Sigma, default_beta_ind, beta_mu, beta_std_Sigma, L, var_noise, action_center_ind
    # lower_clip, upper_clip
    # If the var_noise is using default values, set it to be zero for function init_theta
    
    state_med = 0.5* (state_lower + state_upper)
    state_half_range = 0.5* (state_upper - state_lower)
    reward_med = 0.5* (reward_lower + reward_upper)
    reward_half_range = 0.5* (reward_upper - reward_lower)

    stand_beta_mu, stand_beta_Sigma, L, stand_noise = init_theta(default_alpha_ind, alpha0_mu, alpha0_std_Sigma, default_beta_ind, beta_mu, beta_std_Sigma, L, var_noise, \
               state_med, state_half_range, reward_med, reward_half_range, action_center_ind)


    # kwargs will the key-value paramters, you can itereate over it and get the values
    # Goal: create stand_action_state
    ## This part: Discuss with Ali
    ## For now, let's assume the order is the same 

    stand_action_state=[]
    idx_beta=(action_center_ind==1)
    beta_state_med=state_med[idx_beta.flatten(),:]
    beta_state_half_range=state_half_range[idx_beta.flatten(),:]

#     count=0
#     for k,v in kwargs.items():
#         #here you have variable name as k and value of the variable as v

#         curr_stand_action_state= (v-beta_state_med[count])/(beta_state_half_range[count])
#         stand_action_state.append(curr_stand_action_state)
#         # if k=="Some_var_name":
#         #     print("If code", k,v)
    
    for k in range(len(beta_state_med)):
        v=float(action_state_dict[action_state_name[k]])
        curr_stand_action_state= (v-beta_state_med[k])/(beta_state_half_range[k])
        stand_action_state.append(curr_stand_action_state)
    
    pi = decision(stand_action_state, stand_beta_mu, stand_beta_Sigma, L, stand_noise, lower_clip, upper_clip)

    return pi*100

# The following is my helper function


def init_theta(default_alpha_ind, alpha0_mu, alpha0_std_Sigma, default_beta_ind, beta_mu, beta_std_Sigma, L, var_noise, \
               state_med, state_half_range, reward_med, reward_half_range, action_center_ind):
    # First setup L and the noise
    if(L < 3):
        L = _default_L
    if(var_noise == 0):
        var_noise = _default_sigma0_2 * reward_half_range**2
        stand_noise = _default_sigma0_2
    else:
        stand_noise = var_noise / (reward_half_range**2)
          
    default_beta_ind_no_intercept = np.copy(default_beta_ind)
        
        
    # First, transform the standard deviation of alpha0 and beta to a scale of the noise variance (Eq. A.7)
    beta_sigma_2 = (beta_std_Sigma**2)/var_noise*(L-2)/L
            
    # Setup the unstandardized beta priors with the default (without the intercept)
    default_beta_ind_no_intercept[-1] = 0
    idx_beta=(action_center_ind==1)
    beta_state_half_range=state_half_range[idx_beta.flatten(),:]
    idx=(default_beta_ind_no_intercept==1)
        
    if(idx.sum()>0):
        idx_no_intercept=idx[:-1,:]
        beta_mu[idx.flatten(),:] = _default_mu*\
            reward_half_range*np.ones((idx.sum(),1))/beta_state_half_range[idx_no_intercept.flatten(),:]
        beta_sigma_2[idx.flatten()] = _default_sigma_2*\
            np.ones((idx.sum()))/(beta_state_half_range[idx_no_intercept.flatten(),0]**2)
                
    # Setup the unstandardized beta priors for the intercept
    if(default_beta_ind[-1]==1):
        idx_beta=(action_center_ind==1)
        beta_state_med=state_med[idx_beta.flatten(),:]
        beta_mu[-1,:] = _default_mu*reward_half_range-sum(beta_mu[:-1,:]*beta_state_med)
        tmp_sigma_2 = beta_sigma_2[:-1]*(beta_state_med[:,0]**2)
        tmp = _default_sigma_2-tmp_sigma_2.sum()
        if(tmp<0):
            beta_sigma_2[-1]=_default_beta_sigma0_2
        else:
            beta_sigma_2[-1]=tmp
            

        
    # Setup the transformation matrix for alpha0
    idx_beta=(action_center_ind==1)
    beta_state_half_range=state_half_range[idx_beta.flatten(),:]
    tmp = np.append(beta_state_half_range[:,0],1)
    B_beta = np.diag(tmp)
    beta_state_med=state_med[idx_beta.flatten(),:]
    B_beta[-1,:-1] = beta_state_med[:,0]
    Sigma_beta = np.diag(beta_sigma_2)
        
    # Transform the mean and the variance
    stand_beta_mu=1/reward_half_range*np.matmul(B_beta,beta_mu)
    stand_beta_Sigma=np.matmul(np.matmul(B_beta,Sigma_beta),np.transpose(B_beta))
        
    return stand_beta_mu, stand_beta_Sigma, L, stand_noise

def decision(stand_action_state, stand_beta_mu, stand_beta_Sigma, L, stand_noise, lower_clip, upper_clip):

        
    # mu_t and Sigma_t are associated with the f(S)*beta
    stand_action_state=np.concatenate((stand_action_state, np.ones((1,1))),axis=0)
    mu_t=np.matmul(np.transpose(stand_action_state),stand_beta_mu)
    Sigma_t=np.matmul(np.transpose(stand_action_state),stand_beta_Sigma)
        
    # Notice that the posterior variance of f(S)*beta is scaled by noise
    Sigma_t= stand_noise*np.matmul(Sigma_t,stand_action_state)
    scale_t=np.sqrt(Sigma_t[0,0])
    pi=1-t.cdf(0, L, loc=mu_t[0,0], scale=scale_t)
    pi=max(lower_clip,pi)
    pi=min(upper_clip,pi)

    return pi 
