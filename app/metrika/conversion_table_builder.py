import pandas as pd
import numpy as np

def goalId_count(el):
    return sum([len(eval(goals)) for goals in el])

def utm_source_handler(el):
    set_el = set(el)
    if len(set_el)>1:
        set_el.discard('no-email')
    return ', '.join(set_el)

def devide_columns_handler(df,numerator_column_name,denominator_column_name):
    result_column = (df[numerator_column_name]/df[denominator_column_name])*100
    result_column.replace(np.nan, 0, regex=True, inplace=True)
    return result_column.astype(int)

def leave_last_client_id(el):
    return list(el)[-1]

def make_utms_unique(el):
    aggregated = []
    for utm_groups in el.values:
        aggregated.append(utm_groups)
    return ', '.join(set(aggregated))

def build_conversion_df(visits_all_data_df):
    # replace NaN UtmSource with 'no-email'
    visits_all_data_df['UTMSource']\
        .replace(np.nan, 'no-email', regex=True, inplace=True)
    # First raw grouping. Result: not distinct ClientID column values
    max_df = visits_all_data_df.groupby(['ClientID','UTMSource'])\
        .agg({'GoalsID': [goalId_count], 'VisitID':['count']})
    # drop multilevel columns after grouping
    max_df.columns =max_df.columns.droplevel(0)
    max_df.reset_index(inplace=True)
    # unique ClientID extraction
    unique_client_ids = max_df['ClientID'].unique()
    # after this loop we got ClientID column with distinct values
    temp_dfs = []
    for client_id in unique_client_ids:
        # for every unique ClientID we group rows that belong to it
        temp_df = max_df[max_df['ClientID'] == client_id]
        #calculation metrics for result row
        goals_sum_total = temp_df['goalId_count'].sum()
        max_email = temp_df[temp_df['UTMSource'] != 'no-email']
        goals_email = max_email['goalId_count'].sum()
        max_no_email = temp_df[temp_df['UTMSource'] == 'no-email']
        visits_no_email = max_no_email['count'].sum()
        visits_email = max_email['count'].sum()
        # for every unique ClientID we group rows that belong to it
        temp_df = temp_df.groupby(['ClientID'])\
            .agg({'UTMSource':[utm_source_handler],'goalId_count':['sum']})
        # drop multilevel columns after grouping
        temp_df.columns =temp_df.columns.droplevel(0)
        temp_df.reset_index(inplace=True)
        if temp_df['utm_source_handler'].values[0] == 'no-email':
            temp_df['utm_source_handler'] += temp_df['ClientID'].astype(str)
        #assign metricts for result row
        temp_df['Total visits'] = visits_no_email + visits_email
        temp_df['Visits with out email'] = visits_no_email
        temp_df['Visits with email'] = visits_email
        temp_df['Goals complited via email'] = goals_email
        #prettyfing column names and appending result to array
        temp_df.rename(columns={'utm_source_handler':'Client identities',\
            'sum':'Total goals complited'},\
            inplace=True)
        temp_dfs.append(temp_df)

    #contatenating unique ClientID row into DataFrame
    max_df = pd.concat(temp_dfs)
    max_df.reset_index(inplace=True, drop=True)


    # handle utm intersections
    temp_dfs = []
    list_of_utm_sets_raw = merge([ [idx] + utm.split(', ') for idx,utm in max_df['Client identities'].iteritems()])
    list_of_utm_indx_lists = [[el for el in list(set) if type(el) == int] for set in list_of_utm_sets_raw]
    for list_of_utm_indx in list_of_utm_indx_lists:
        temp_df = max_df.loc[list_of_utm_indx]
        temp_df['temp_col'] = 0
        temp_df = temp_df.groupby(['temp_col']).agg(\
                                        {'ClientID':leave_last_client_id,\
                                        'Client identities':make_utms_unique,\
                                        'Total goals complited':'sum',\
                                        'Total visits':'sum',\
                                        'Visits with out email':'sum',\
                                        'Visits with email':'sum',\
                                        'Goals complited via email':'sum'})
        temp_dfs.append(temp_df)


    #contatenating intersections UTMs into single DataFrame
    max_df = pd.concat(temp_dfs)
    max_df.reset_index(inplace=True, drop=True)
    #calculating metrics
    max_df['Conversion (TG/TV)'] = devide_columns_handler(max_df,'Total goals complited','Total visits')
    max_df['Email visits share'] = devide_columns_handler(max_df,'Visits with email','Total visits')
    max_df['NO-Email visits share'] = devide_columns_handler(max_df,'Visits with out email','Total visits')
    max_df['Email power proportion'] = devide_columns_handler(max_df,'Goals complited via email','Total goals complited')



    return max_df

def merge(lsts):
    sets = [set(lst) for lst in lsts if lst]
    merged = True
    while merged:
        merged = False
        results = []
        while sets:
            common, rest = sets[0], sets[1:]
            sets = []
            for x in rest:
                if x.isdisjoint(common):
                    sets.append(x)
                else:
                    merged = True
                    common |= x
            results.append(common)
        sets = results
    return sets
