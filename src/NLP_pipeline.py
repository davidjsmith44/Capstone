''' Initial NLP Pipeline '''


def create_speech_dfs(df, date, numb_speeches):
    '''
    For a given date, the most recent speeches numb_speeches and the next date speeches
    are returned as dataframes

    INPUTS:
        df - the dataframe of all fed speeches
        date - the date needed to include no speeches before
        num_speeches - the number of most recent speeches to include

    OUTPUTS:
        hist_df - this is a subset of the original dataframe with same columns
        new_df - a subset of the original dataframe for the new speeches
    '''
    hist_df = df[df['date']< date]
    if len(hist_df)> numb_speeches:
            hist_df = hist_df.iloc[0:numb_speeches]

    new_df = df[df['date']==date]

    return hist_df, new_df


def implement_ftidf_model(df):
    '''
    This takes the smaller version of the speeches and retuns the tf_idf calculations
    NOTE: NEED TO ADD HYPERPARAMETER DICTIONARY TO THIS
    '''

    doc_list = list(df['text'])
    tfidvect =TfidfVectorizer(lowercase=True,
                          stop_words='english',
                          max_features = 1000,
                          norm = 'l2',
                          use_idf = True,
                          smooth_idf=True,
                          sublinear_tf = False)
    tfidf_vectorized = tfidvect.fit_transform(doc_list).toarray()
    tfidvect.fit_transform(doc_list)
    # can this just be tfidvect.fit_transform(doc_list) without the assignment??
    return tfidvect, tfidf_vectorized


def transform_new_speech(new_df, model):
    '''
    takes the model fit on historical speeches and fits the new text to this model
    returns new_tokens which can go into the similarity calculation
    '''
    new_text = new_df['text']
    new_tokens = model.transform(new_text)
    return new_tokens

def calculate_similarity(new_tokens, tfid_vectorized):
    '''
    This function takes the new tokens and the model for the history of n_speeches and
    calculates the cosine similarity
    two numbers are returned
        cost_last  - the cosine similarity with the new speeches and the last speeches
        cos_avg_n  - the average cosine similariy over the last n speeches
    '''

    cosine_sims = linear_kernel(new_tokens, tfid_vectorized)
    # n
    # NOTE: Need to handle the case where there are multiple speeches on the current date

    cos_last = cosine_sims[0]
    cos_avg_n = np.mean(cosine_sims)

    #need to deal with what happens whern there are multiple date
    if len(cos_last) > 1:
        cos_last = np.mean(cos_last)
        cos_avg_n = np.mean(cos_avg_n)

    return cos_last, cos_avg_n


def loop_through_dataframe(df, n_speeches):
    '''
    Attempting to start with the most recent speech and work backwards historically creating
    a list of cosine similarities

    Within the loops to the speeches
        -calculate the date
        -Pass date and dataframe to create_speech_dfs
            -returns new_df and hist_df
        -Fit the hist_df to a model
        -put the new_df into the model
        -calculate the cosines
        -put the cosines into the original dataframe

    '''
    unique_dates = df['date'].unique()
    ts_dates = np.zeros_like(unique_dates)
    ts_cos_last = np.zeros((len(unique_dates),1))
    ts_cos_avg_n = np.zeros((len(unique_dates),1))

    #for i in range(len(df)- n_speeches):
    for i in range(len(unique_dates)- 50):
        print(i)
        this_date = df['date'][i]
        h_df, n_df = create_speech_dfs(df, this_date, n_speeches)

        tfidvect, tfidf_vectorized  = implement_ftidf_model(h_df)

        new_tokens = transform_new_speech(n_df, tfidvect)

        cos_last, cos_avg_n = calculate_similarity(new_tokens, tfidf_vectorized)

        ts_dates[i] = this_date
        ts_cos_last[i] = cos_last
        ts_cos_avg_n[i] = cos_avg_n

    return ts_dates, ts_cos_last, ts_cos_avg_n


# fit this dataframe to the last vectorization
#new_tokens = tfidvect.transform(new_text)
#cosine_sims = linear_kernel(new_tokens, tfidf_vectorized)
#cosine_sims.shape


if __name__ == '__main__':


    # Mother of all import statements
    import string
    import numpy as np
    import pandas as pd

    from nltk.corpus import stopwords
    from nltk.tokenize import RegexpTokenizer
    from nltk.stem.porter import PorterStemmer

    from nltk.tokenize import word_tokenize
    from nltk.stem.porter import PorterStemmer
    from nltk.stem.snowball import SnowballStemmer
    from nltk.stem.wordnet import WordNetLemmatizer

    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.metrics.pairwise import linear_kernel

    import os

    # Importing all of the Fed Speeches
    import pickle
    df = pickle.load( open( "../data/all_fed_speeches", "rb" ) )
    df.info()

    df.sort_values(by=['date'], ascending = False, inplace = True)
    df.reset_index(drop=True, inplace=True)

    ''' List of variables to include '''
    n_speeches = 10

    ts_dates, ts_cos_last, ts_cos_avg_n = loop_through_dataframe(df, n_speeches)
    ts_dates = np.reshape(ts_dates, (-1,1))
    #df_dict = {'date':ts_dates, 'cos_last': ts_cos_last, 'cos_avg_n':ts_cos_avg_n}
    #df_index = np.arange(len(ts_dates))
    #df_index = np.reshape(df_index, (-1,1))
    #df_cos_sim = pd.DataFrame({'dates': ts_dates, 'cos_last':ts_cos_last,
    #    'cos_avg_n':ts_cos_avg_n}, index=df_index)
    #df_cos_sim = pd.DataFrame.from_dict(df_dict)
    #df_cos_sim = pd.DataFrame({'cos_last':ts_cos_last,
    #    'cos_avg_n':ts_cos_avg_n})
    #print(df_cos_sim).info()

    os.chdir("..")
    pickle_out = open('../data/ts_cosine_sim', 'wb')
    pickle.dump([ts_cos_last, ts_cos_avg_n, ts_dates], pickle_out)
    pickle_out.close()

    # create a date, filter the df and run the word processing on this date
    #this_date = datetime.datetime(2017, 1, 15)
    #recent_df = create_speech_list(df, date, numb_speeches)
    #recent_model = implement_ftidf_model(df)


    # working on the cosine similarities !!!
    # create the new dataframe of the next speech = called df_new
    #new_text = df_new['text']
    # fit this dataframe to the last vectorization
    #new_tokens = tfidvect.transform(new_text)
    #cosine_sims = linear_kernel(new_tokens, tfidf_vectorized)
    #cosine_sims.shape

    #cos_avg_n = np.zeros_like(df['date'])
    #cos_last = np.zeros_like(df['date'])
    #df['cos_last'] = cos_last
    #df['cos_avg_n'] = cos_avg_n


    # create list of dates where there was at least one speech and sort
    #unique_dates = df['date'].unique()
    #unique_dates = np.sort(unique_dates)

    # create array to hold cosine similarities and words based on n_speeches
    # the original dataframe 'df' is sorted with the first speech being the most current
    # pull the last n_speeches
    #first_date = df['date'].iloc[-n_speeches]
    #unique_date = unique_dates >= first_date
    #ud = np.datetime_as_string(unique_dates, 'D')
    # NOTE: Need to fix if there are two speeches on the same date - adjust the cosine similarity


    '''
    NEED TO DO TODAY
    1. determine how to do cosine similarity of a new speech relative
        to the last n speeches (out of sample forecast)
    2. Finally make the call in what type of speeches we are going to
        use in this model (FOMC only?)
    3. Create data pipeline for the quandl interest rate pull and
        publish initial results to github
    4. Look at initial autocorrelations for this model of just interest rates
    5. Get out the histocial eigenvalues and start plotting them
    6. Plot the impact on interest rates due to the eignvalues
    7. Determine game plan to close the loop!!!

    '''