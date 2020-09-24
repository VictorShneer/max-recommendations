import json
import numpy as np
from pprint import pprint

PROPERTY_TO_SQL_DIC = {'start_date':'''Date >= '{res}' ''',\
                        'goals':'''has(GoalsID, {res}) != 0 '''}

# this is what generate_grouped_columns_sql does
'''

--         and Date > '2020-06-20'
--         and (
--             has(GoalsID, 46766122) != 0
--             or
--             has(GoalsID, 46765999) != 0
--             )

'''

def generate_grouped_columns_sql(restrictions):
    columns_claise = ''
    # delete empty restrictions, for the cases when you have no goals to filter with
    restrictions_not_empty = {k: v for k, v in restrictions.items() if v != ['']}
    for key,values in restrictions_not_empty.items():
        # every where state should be in (   )
        columns_claise += 'AND ('
        # every where state come as array
        for i,value in enumerate(values):
            # every where state has its own format in PROPERTY_TO_SQL_DIC
            state = PROPERTY_TO_SQL_DIC[key].format(res=value)
            # if it is last restrition in array we don't put OR
            if i != len(values)-1:
                columns_claise += (state + ' OR ')
            else:
                columns_claise+=state
        # close ) and add AND for the new WHERE state
        columns_claise += ') '
    return columns_claise


def generate_joined_json_for_time_series(time_series_df, messages_df):
    messages_df_aggr = messages_df.groupby('send_on').agg({'subject':lambda s: ' '.join(s)})
    messages_df_aggr.reset_index(level=0, inplace=True)
    print(messages_df_aggr)
    print('\n')
    messages_df_aggr['point'] = 'point { size: 8; shape-type: star; fill-color: #a52714;}'
    time_series_df_raw = time_series_df[['Date','total_goals','goals_with_email','goals_just_after_email']]
    # print(messages_df)

    # time_series_df_raw['Date'] = time_series_df_raw['Date'].astype(str)
    time_series_messages_df = time_series_df_raw.merge(messages_df_aggr, how='left', left_on='Date', right_on='send_on')
    # print('\n')
    # print(time_series_df_raw)
    # print('\n')
    time_series_messages_df.drop(['send_on'], axis=1, inplace=True)
    # # TODO: columns mess
    time_series_messages_df = time_series_messages_df[['Date','total_goals','goals_with_email','goals_just_after_email','point','subject']]
    print(time_series_messages_df)
    # time_series_messages_df['subject'] = \
    #                 time_series_messages_df['subject']\
    #                     .apply(lambda subject: 'Тема письма: ' + str(subject))
    time_series_messages_df['goals_just_after_email']= np.random.randint(5,30,size=time_series_messages_df.shape[0])

    time_series_json = time_series_messages_df.to_json(orient='split')

    return json.loads(time_series_json)
