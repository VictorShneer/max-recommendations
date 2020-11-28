"""
class can build performance table 
and time series data with GR newsletters
data collected from CH and GR account
"""

from app.grhub.grmonster import GrMonster
import json
import pandas as pd

class MetrikaReport(object):
    report_json = {}
    no_email_regex = '^no-email*'    


    def __init__(self, clientid_convers_df, time_series_goals_df = pd.DataFrame()):
        self.clientid_convers_df = clientid_convers_df
        self.time_series_goals_df = time_series_goals_df
        print(clientid_convers_df.loc[clientid_convers_df['Email'].apply(type) != str])
        clientid_convers_df = clientid_convers_df.loc[clientid_convers_df['Email'].apply(type) == str]
        print(clientid_convers_df.loc[clientid_convers_df['Email'].apply(type) != str])
        self.email_visits_slice_df = self.clientid_convers_df[~self.clientid_convers_df['Email'].str.contains(self.no_email_regex)]
        self.no_email_visits_slice_df = self.clientid_convers_df[self.clientid_convers_df['Email'].str.contains(self.no_email_regex)]

    def generate_joined_json_for_time_series(self, time_series_df, messages_df):
        time_series_df_raw = time_series_df[['Date','total_goals','goals_with_email','goals_just_after_email']]
        if messages_df.shape[0] == 0:
            time_series_messages_df = time_series_df_raw  
            time_series_messages_df['point'] = None
            time_series_messages_df['subject'] = None
        else:
            messages_df_aggr = messages_df.groupby('send_on').agg({'subject':lambda s: ' '.join(s)})
            messages_df_aggr.reset_index(level=0, inplace=True)
            messages_df_aggr['point'] = 'point { size: 8; shape-type: star; fill-color: #a52714;}'
            time_series_messages_df = time_series_df_raw.merge(messages_df_aggr, how='left', left_on='Date', right_on='send_on')
            time_series_messages_df.drop(['send_on'], axis=1, inplace=True)
        # # TODO: columns mess
        time_series_messages_df = time_series_messages_df[['Date','goals_with_email','goals_just_after_email','point','subject']]
        time_series_json = time_series_messages_df.to_json(orient='split')
        return json.loads(time_series_json)

    def load_email_visits_table(self):
        email_convers_df= self.email_visits_slice_df.astype(str)
        email_convers_json = email_convers_df.to_json(default_handler=str, orient='table', index=False)
        self.report_json['conv_data'] = json.loads(email_convers_json)

    def load_pie(self):
        # calc pie numbers
        goals_no_email_count = self.no_email_visits_slice_df['Всего целей выполнено'].sum()  
        goals_from_email_count = self.clientid_convers_df['Кол-во целей после прямого перехода из email'].sum() 
        goals_has_email_count =  self.email_visits_slice_df['Всего целей выполнено'].sum()         
        # store pie data
        self.report_json['goals_no_email_count'] = str(goals_no_email_count)
        self.report_json['goals_associate_with_email_count'] = str(goals_has_email_count - goals_from_email_count)
        self.report_json['goals_from_email_count'] = str(goals_from_email_count)

    def load_summary(self):
        # store summary data
        self.report_json['total_unique_visitors'] = str(self.clientid_convers_df.shape[0]) 
        self.report_json['total_email_visitors'] = str(self.email_visits_slice_df.shape[0])

    def load_time_series(self,broadcast_messages_since_date_subject_df):
        # time series builder
        time_series_goals_json =  self.generate_joined_json_for_time_series(self.time_series_goals_df, broadcast_messages_since_date_subject_df)
        # store time series
        self.report_json['time_series_data'] = time_series_goals_json

# I forgot what does it mean :((
# *** ALL YOU NEED TO MAKE self.load_clientid_email_table *** ALL YOU NEED TO MAKE self.load_clientid_email_table
#           # clientid_convers_df = clientid_convers_df[COLUMNS]
#           # clientid_convers_df= clientid_convers_df.astype(str)
#           # clientid_convers_json = clientid_convers_df.to_json(default_handler=str, orient='table', index=False)
#           # report_json['conv_data'] =json.loads(clientid_convers_json)
# *** ALL YOU NEED TO MAKE self.load_clientid_email_table *** ALL YOU NEED TO MAKE self.load_clientid_email_table
