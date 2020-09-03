import pandas as pd
import numpy as np
from urllib.parse import urlparse
from urllib.parse import parse_qs
from flask import current_app

import concurrent.futures
import urllib.request






def goalId_count(el):
    return sum((len(eval(goals)) for goals in el))

def hash_group_handler(el):
    set_el = set(el)
    # current_app.logger.info('   ### hash_group_handler HASHS:{}'.format(set_el))
    if len(set_el)>1:
        set_el.discard(-1)
        # in other words
        # if visit has different emails
        # we want mark it to ignore futher
        ## OPTIMIZE:
        if len(set_el) > 1:
            return None
    return str(set_el.pop())

#
def devide_columns_handler(df,numerator_column_name,denominator_column_name):
    result_column = (df[numerator_column_name]/df[denominator_column_name])*100
    result_column.replace(np.nan, 0, regex=True, inplace=True)
    return result_column.astype(int)

def leave_last_client_id(el):
    return list(el)[-1]

def make_utms_unique(el):
    # # OPTIMIZE:
    aggregated = []
    for utm_groups in el.values:
        aggregated.append(utm_groups)
    return ', '.join(set(aggregated))

def start_url_to_hash(url):
    parsed = urlparse(url)
    url_params = parse_qs(parsed.query)
    if 'mxm' in url_params.keys():
        return url_params['mxm'][0]
    else:
        ## OPTIMIZE:
        return -1

def build_conversion_df(visits_all_data_df):
    current_app.logger.info('### visits_all_data_df start')
    # replace StartURL with hash
    visits_all_data_df['hash'] = visits_all_data_df['StartURL'].apply(start_url_to_hash)
    # TODO delet start url from df
    # LEGACY
    # replace NaN UtmSource with 'no-email'
    # visits_all_data_df['UTMSource']\
    #     .replace(np.nan, 'no-email', regex=True, inplace=True)

    # First raw grouping. Result: not distinct ClientID column values
    max_df = visits_all_data_df.groupby(['ClientID','hash'])\
        .agg({'GoalsID': goalId_count, 'VisitID':'count'})
    max_df.reset_index(inplace=True)
    # unique ClientID extraction
    unique_client_ids = max_df['ClientID'].unique()
    # after this loop we got ClientID column with distinct values
    temp_dfs = []
    current_app.logger.info('### visits_all_data_df unique_client_ids loop start {} --->>>'.format(len(unique_client_ids)))

    # # Handle a single ClientID chunk and return single row ClientID df with ROI stats
    #
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=current_app.config['MAX_WORKERS']) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = [executor.submit(handle_unique_clientid_chunk, max_df[max_df['ClientID'] ==unique_clientid]) for unique_clientid in unique_client_ids]
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (future, exc))
            else:
                # print('%r clientId result is \n %s' % (future, data.to_string()))
                temp_dfs.append(data)
    # # LEGACY
    # for step,client_id in enumerate(unique_client_ids):
    #     print(' {} of {}\r'.format(step,len(unique_client_ids)), end="")
    #     # for every unique ClientID we group rows that belong to it
    #     temp_df = max_df[max_df['ClientID'] == client_id]
    #     #calculation metrics for result row
    #     # goals_sum_total = temp_df['GoalsID'].sum() ???
    #     max_email = temp_df[temp_df['hash'] != 'no-email']
    #     goals_email = max_email['GoalsID'].sum()
    #     max_no_email = temp_df[temp_df['hash'] == 'no-email']
    #     visits_no_email = max_no_email['VisitID'].sum()
    #     visits_email = max_email['VisitID'].sum()
    #     # for every unique ClientID we group rows that belong to it
    #     temp_df = temp_df.groupby(['ClientID'])\
    #         .agg({'hash':hash_group_handler,'GoalsID':'sum'})
    #     temp_df.reset_index(inplace=True)
    #     # ignore cases - when clientID has different emails
    #     if temp_df['hash'].values[0] == '0':
    #         continue
    #     # mark no-email with clientId
    #     # we want all anons to be unique
    #     # if temp_df['hash'].values[0] == 'no-email':
    #     #     temp_df['hash'] += temp_df['ClientID'].astype(str)
    #
    #     #assign metricts for result row
    #     temp_df['Total visits'] = visits_no_email + visits_email
    #     temp_df['Visits with out email'] = visits_no_email
    #     temp_df['Visits with email'] = visits_email
    #     temp_df['Goals complited via email'] = goals_email
    #     #prettyfing column names and appending result to array
    #     temp_df.rename(columns={'hash':'Client identities',\
    #         'GoalsID':'Total goals complited'},\
    #         inplace=True)
    #     temp_dfs.append(temp_df)

    current_app.logger.info('### visits_all_data_df unique_client_ids loop finish <<<<----')
    #contatenating unique ClientID row into DataFrame
    max_df = pd.concat(temp_dfs)
    # current_app.logger.info('### len of result {}'.format(len(max_df)))
    # max_df.dropna(inplace=True)
    # current_app.logger.info('### len of not none result {}'.format(len(max_df)))
    max_df.reset_index(inplace=True, drop=True)
    max_df = max_df.groupby(['Client identities'])\
        .agg({'ClientID':leave_last_client_id,\
        'Total goals complited':'sum',
        'Total visits':'sum',
        'Visits with out email':'sum',
        'Visits with email' :'sum',
        'Goals complited via email':'sum'
        })
    max_df.reset_index(inplace=True, drop=False)

    # LEGACY
    # # handle utm intersections
    # temp_dfs = []
    # list_of_utm_sets_raw = merge([ [idx] + utm.split(', ') for idx,utm in max_df['Client identities'].iteritems()])
    # list_of_utm_indx_lists = [[el for el in list(set) if type(el) == int] for set in list_of_utm_sets_raw]
    # for list_of_utm_indx in list_of_utm_indx_lists:
    #     temp_df = max_df.loc[list_of_utm_indx]
    #     temp_df['temp_col'] = 0
    #     temp_df = temp_df.groupby(['temp_col']).agg(\
    #                                     {'ClientID':leave_last_client_id,\
    #                                     'Client identities':make_utms_unique,\
    #                                     'Total goals complited':'sum',\
    #                                     'Total visits':'sum',\
    #                                     'Visits with out email':'sum',\
    #                                     'Visits with email':'sum',\
    #                                     'Goals complited via email':'sum'})
    #     temp_dfs.append(temp_df)
    # #contatenating intersections UTMs into single DataFrame
    # max_df = pd.concat(temp_dfs)
    # max_df.reset_index(inplace=True, drop=True)

    #calculating metrics
    max_df['Conversion (TG/TV)'] = devide_columns_handler(max_df,'Total goals complited','Total visits')
    max_df['Email visits share'] = devide_columns_handler(max_df,'Visits with email','Total visits')
    max_df['NO-Email visits share'] = devide_columns_handler(max_df,'Visits with out email','Total visits')
    max_df['Email power proportion'] = devide_columns_handler(max_df,'Goals complited via email','Total goals complited')

    return max_df

def handle_unique_clientid_chunk(temp_df):
    #calculation metrics for result row
    max_email = temp_df[temp_df['hash'] != -1]
    goals_email = max_email['GoalsID'].sum()
    max_no_email = temp_df[temp_df['hash'] == -1]
    visits_no_email = max_no_email['VisitID'].sum()
    visits_email = max_email['VisitID'].sum()
    # for every unique ClientID we group rows that belong to it
    temp_df = temp_df.groupby(['ClientID'])\
        .agg({'hash':hash_group_handler,'GoalsID':'sum'})
    temp_df.reset_index(inplace=True)
    # ignore cases - when clientID has different emails
    # mark no-email with clientId
    # we want all anons to be unique
    # if temp_df['hash'].values[0] == 'no-email':
    #     temp_df['hash'] += temp_df['ClientID'].astype(str)

    # name -1 to 'no-email'
    temp_df.loc[temp_df['hash'] == '-1', 'hash'] = 'no-email'
    #assign metricts for result row
    temp_df['Total visits'] = visits_no_email + visits_email
    temp_df['Visits with out email'] = visits_no_email
    temp_df['Visits with email'] = visits_email
    temp_df['Goals complited via email'] = goals_email
    #prettyfing column names and appending result to array
    temp_df.rename(columns={'hash':'Client identities',\
        'GoalsID':'Total goals complited'},\
        inplace=True)
    return temp_df

# LEGACY
# def merge(lsts):
#     sets = [set(lst) for lst in lsts if lst]
#     merged = True
#     while merged:
#         merged = False
#         results = []
#         while sets:
#             common, rest = sets[0], sets[1:]
#             sets = []
#             for x in rest:
#                 if x.isdisjoint(common):
#                     sets.append(x)
#                 else:
#                     merged = True
#                     common |= x
#             results.append(common)
#         sets = results
#     return sets
