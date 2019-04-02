''' Post Data Pull Workflow

At this point in the program we have pulled and processed both the Fed speeches and interest rate date.
FED SPEECHES
    The results of this process have been saved in a pickle file in the data subdirectory called
        'ts_cosine_sim.p'
        It contains a list with the following three variables [ts_cos_last, ts_cos_avg_n, ts_date]
            ts_cos_last     contains the cosine similarity of the last fed speech to the ones on the ts_date
            ts_cos_avg_n    contains the cos. sim of the last 50 speeches to the ones made on ts_date
            ts_date is      contains the date in a crappy np.datetime64 object

    os.chdir("..")
    pickle_out = open('../data/ts_cosine_sim', 'wb')
    pickle.dump([ts_cos_last, ts_cos_avg_n, ts_dates], pickle_out)
    pickle_out.close()

INTEREST RATE DATA
    The interest rate data has been pulled from quandl and pre-processed. The data sits in a file called 'interest_rate_data.p'


STEPS:
    1. Load up the interest rate data
    2. Split into train/test
    3. Convert into three datasets
        raw yields
        discrete forwards
        cont.comp forwards
    4. EDA on the data in the training + cv set
    5. build model pipeline
        -estimate parameters of the model over the training set
        -build CV update parameters/etc
    6. Compare the results

'''

# SOMEWHERE HERE WE SHOULD DO EDA ON THESE FOR THE PRESENTATION

''' Working on the Gaussian Model for the MVP on base level rates '''
def forecast_gaussian(X):
    ''' Mean zero interest rates we just take the change here '''
    fcst = 0
    return fcst

''' ARIMA MODEL ON BASE RATES
For now lets just look at the 10 year
'''

def build_ARIMA_model(X, ar, ma, diff_ord, target):

    model = pf.ARIMA(data=X, ar=4, ma=4, integ = diff_ord, target=target, family = pf.Normal())

    # Estimate the latent variables with a maximum likelihood estimation
    model.fit("MLE")
    #x.summary()
    pred = model.predict(h=1)
    last_rate = X['10 YR'][-1]
    this_shock = pred['Differenced 10 YR'].iloc[0]
    next_rate = last_rate + this_shock

    return next_rate

def update_cv_data(X_train, X_cv, i):

    temp = X_cv[0:i]
    frames = [X_train, temp]
    X_this_cv = pd.concat(frames)

    return X_this_cv

def create_cv_forecasts(X_train, X_cv, dict_params):
    cv_len = len(X_cv)
    forecasts = np.zeros(shape=[cv_len,1])
    ar = dict_params['ar']
    ma = dict_params['ma']
    diff_ord = dict_params['diff_ord']
    target = dict_params[target]
    for i in range(cv_len):
        print(i)
        this_X = update_cv_data(X_train, X_cv, i)
        forecasts[i] = build_ARIMA_model(this_X, ar, ma, diff_ord,
                            target, family = pf.Normal())
    return forecasts

def cross_validate_models(model_list, X_train, X_cv):
    '''
    Building a overlaying function that handles the cross validation

    Will take as an input model_list that includes the model type
    and all of the hyper parameters of the model

    INPUTS:
        X_train -   the dataframe containing the training dataset
        X_cv -      the dataframe containing the cross_val dataset
        model_list  A dictionary containing the hyper parameters
                     of the model

    OUTPUTS
        The forecast of the model (one day interest rate forecast) will be stored
        in the model_list['foreacst'] section

 'model_type'    {'Gaussian', 'ARIMA', 'ARIMAX'}
    'name'          name given to model for charting purposes
    'target_class'  {'rates', 'forwards', 'cc_forwards'}
    'hyper_parms'    A dictoinary containing the hyperparmeters of the model
    'forecast'      A zero, initially that get populated with the daily forecasts over CV period

    '''
    # setting up the initial arima model
    for idx, item in enumerate(model_list):
        # Making sure we use the correct interest rate transformation

        if item['target_class']=='rates':
            print('This one uses rates')

        elif item['target_class']=='forwards':
            print('This model uses forwards')
        elif item['target_class']=='cc_forwards':
            print("This model uses continuously compounded forwards")

        if item['model_type']== 'ARIMA':
            model_list[i]['forecast'] = create_cv_forecasts(X_train, X_cv, item['hyper_params'])

    return model_list





#Load up interest rate data
import numpy as np
import pandas as pd
import pyflux as pf
import datetime as datetime
import matplotlib.pyplot as plt

import os
import pickle

os.chdir('..')
X = pickle.load(open("data/interest_rate_data", "rb" ))
X_fwds = pickle.load(open('data/forward_rates', 'rb'))
X_zeros = pickle.load(open('data/zero_rates', 'rb'))


#df_FX = pickle.load( open( "data/FX_data", "rb" ) )
fed_metrics = pickle.load( open( "data/more_fed_speeches", "rb" ) )
cos_last = fed_metrics[0]
cos_avg_n = fed_metrics[1]
fed_dates = fed_metrics[2]

# set up zeros in the columns
X['cos_last'] = 0
X_fwds['cos_last']=0
X_zeros['cos_last']=0
X['cos_avg'] = 0
X_fwds['cos_avg']=0
X_zeros['cos_avg']=0

for i in range(len(fed_dates)):
    X['cos_last'].loc[ts_dates[i]] = cos_last[i]
    X['cos_avg'].loc[ts_dates[i]] = cos_avg_n[i]

    X_zeros['cos_last'].loc[ts_dates[i]] = cos_last[i]
    X_zeros['cos_avg'].loc[ts_dates[i]] = cos_avg_n[i]

    X_zeros['cos_last'].loc[ts_dates[i]] = cos_last[i]
    X_zeros['cos_avg'].loc[ts_dates[i]] = cos_avg_n[i]

print(X.describe())

# cannot use train/test split on this because it is time series
total_obs = len(X)
train_int = int(round(total_obs*.7, 0))
cv_int = int(round(total_obs*.85, 0))

fwd_train = X_fwds[0:train_int]
fwd_cv = X_fwds[train_int:cv_int]
fwd_test = X_fwds[cv_int:]

zero_train = X_zeros[0:train_int]
zero_cv = X_zeros[train_int:cv_int]
zero_test = X_zeros[cv_int:]

X_train = X[0:train_int]
X_cv = X[train_int:cv_int]
X_test = X[cv_int:]


dict_params = {'ar':1, 'ma': 1, "diff_ord": 1, 'target':'10 YR'}

'''
Need to include a dictionary that stores all of the results of the models
'''

dict_results = {'Model': model.model_name,
              'hyperparams': dict_params,
              'forecast': forecasts}

models = []


''' Setting up the hyperparameters
The data for models is stored in a list called 'model_list'
Each entru in the list contains a dictionary with the following keys
    'model_type'    {'Gaussian', 'ARIMA', 'ARIMAX'}
    'name'          name given to model for charting purposes
    'target_class'  {'rates', 'forwards', 'cc_forwards'}
    'hyper_parms'    A dictoinary containing the hyperparmeters of the model
    'forecast'      A zero, initially that get populated with the daily forecasts over CV period

    The 'hyper_params' dictionary will be different for every class in the model.

    EXAMPLE for arima class
        hyper_params= {'ar':1, 'ma': 1, "diff_ord": 1, 'target':'10 YR'}
    '''
#Store relevant information in the models list
model_list = []

this_name = 'Normal ARIMA(1,1,1)'
hyper_params= {'ar':1, 'ma': 1, "diff_ord": 1, 'target':'10 YR'}
forecast = 0
model_inputs = {'model_type': 'ARIMA'
                'name': this_name,
                'target_class': 'rates'
                'hyper_params': hyper_params,
                'foreacst': forecasts}

this_name = 'Normal ARIMA(2,1,2)'
hyper_params= {'ar':2, 'ma': 2, "diff_ord": 1, 'target':'10 YR'}
forecast = 0
model_inputs = {'model_type': 'ARIMA',
                'name': this_name,
                'target_class': 'rates',
                'hyper_params': hyper_params,
                'foreacst': forecast}
model_list.append(model_inputs)

''' First ARIMAX model '''
#NOTE: We need to store the formula for the ARIMA model in the hyper_params
this_name = 'Normal ARIMAX(1,1,1)'
hyper_params = {'ar': 1, 'ma':1, 'diff_ord':1, 'target': '10 YR',
                'formula':'10 YR ~ 1 + cos_sim + crisis'}
forecast = 0
model_inputs = {'model_type': 'ARIMAX',
                'name': this_name,
                'target_class': 'rates',
                'hyper_params': hyper_params,
                'foreacst': forecast}
model_list.append(model_inputs)

model_list = cross_validate_models(model_list, X_train, X_cv)

