"""
sub functions for various bp needs
pretty every blueprint has such module
"""
from app.models import User, Integration
from flask_login import current_user
from flask import abort
import requests
from flask import current_app
from alphabet_detector import AlphabetDetector
from app.utils import represents_int
from datetime import datetime
import validators
from io import StringIO
import pandas as pd
import json
from app.utils import generate_full_CH_table_name
from app.analytics.analytics_consts import ANALITICS_SEARCH_QUERY,\
                                            INT_COMPARISON_DIC,\
                                            COMPARISON_FIELDS
def build_analytics_search_json(analytics_search_df):
    analytics_search_df.dropna(subset=['Email'], inplace=True)
    analytics_search_df.drop_duplicates(subset=['Email'], inplace=True)
    analytics_search_df= analytics_search_df.astype(str)
    json_to_return = analytics_search_df.to_json(default_handler=str, orient='table', index=False)
    return json.loads(json_to_return)

def build_df_from_CH_response(ch_response, columns):
    ch_response_text = ch_response.text
    file_from_string = StringIO(ch_response_text)
    return pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, names=columns)

# decoration to check if user owns integration he try to access
def current_user_own_integration(function):
    def wrapper(integration_id):
        integration = Integration.query.filter_by(id=integration_id).first_or_404()
        if current_user.id != integration.user_id:
            print('Permission abort')
            abort(404)
        else:
            return function(integration_id)
    # Renaming the function name:
    wrapper.__name__ = function.__name__
    return wrapper

def create_url_for_query(query,db_name):
    host = current_app.config['CLICKHOUSE_HOST']
    return 'https://{host}:8443/?database={db}&query={query}'.format(host=host, db=db_name, query=query)

def send_request_to_clickhouse(url):
    certificate_path = 'app/YandexInternalRootCA.crt'
    auth = {'X-ClickHouse-User': current_app.config['CLICKHOUSE_LOGIN'],'X-ClickHouse-Key': current_app.config['CLICKHOUSE_PASSWORD']}
    r = requests.get(url = url, headers=auth, verify=certificate_path)
    return r

def check_if_date_legal(user_date):
    try:
        datetime.strptime(user_date, '%Y-%m-%d')
        return True
    except Exception as err:
        print('hey dog',user_date)
        return False

def validate_external_segment_name(external_segment_name):
    ad = AlphabetDetector()
    if not all([ch.isalnum() or ch=='_' for ch in external_segment_name]):
        return False
    elif not ad.only_alphabet_chars(external_segment_name, "LATIN"):
        return False
    else:
        return True

def validate_mobile_phone_model(mobile_phone_model):
    return True # TODO validate mobile_phone_model

validate_dictionary = {
    'integration_id' : represents_int,
    'DeviceCategory' : represents_int,
    'OperatingSystem' : validate_external_segment_name, # external_segment_name has the same reqs as OperatingSystem
    'RegionCity' : validate_external_segment_name, # external_segment_name has the same reqs as RegionCity (except _ and numbers allowed)
    'MobilePhone' : validate_external_segment_name, # external_segment_name has the same reqs as RegionCity (except _ and numbers allowed)
    'MobilePhoneModel' : validate_mobile_phone_model,
    'Browser': validate_external_segment_name, # external_segment_name has the same reqs as Browser
    'clause_visits' : represents_int,
    'Date' : check_if_date_legal,
    'amount_of_visits' : represents_int,
    'clause_visits_from_to' : represents_int,
    'amount_of_visits' : represents_int,
    'GoalsID' : represents_int,
    'clause_goals': represents_int,
    'amount_of_goals' : represents_int,
    'clause_url' : represents_int
}

# ,
#     'URL' : validators.url

def request_ch_for_initial_data(crypto,integration_id, query_template):
    # build CH table names    
    visits_table_name = '{}.{}_raw_{}'.format(current_user.crypto, 'visits', integration_id)
    hits_table_name = '{}.{}_raw_{}'.format(current_user.crypto, 'hits', integration_id)
    # query all stuff - dropdown chices, dates and email visitors
    query = query_template.format(hits_table_name=hits_table_name,\
                                    visits_table_name=visits_table_name)
    create_url = create_url_for_query(query, current_user.crypto)
    return send_request_to_clickhouse(create_url)

def build_where_clause(dict_of_requests):
    #TODO: remove loop with more readable design 
    where = "WHERE has(v.WatchIDs, h.WatchID) AND"
    for index, i in enumerate(dict_of_requests):
        if i in ('DeviceCategory', 'OperatingSystem', 'RegionCity', 'MobilePhone', 'MobilePhoneModel', 'Browser'):
            where = where + ' h.' + i + ' IN (' + str(dict_of_requests[i]).strip('[]') + ') AND'
        elif i in ('clause_visits'):
            where = where + ' h.Date ' + str(dict_of_requests[i]).strip("''")
        elif i in ('Date'):
            where = where + ' ' + str(dict_of_requests[i]).strip('['']') + ' AND'
        elif i in ('GoalsID'):
            for j in dict_of_requests[i]:
                where = where + ' has(h.GoalsID,' + str(j) + ') !=0 or'
    where = where[:-3]
    return where

def build_having_clause(dict_of_requests):
    having = "HAVING"
    for index, i in enumerate(dict_of_requests):
        if i == 'clause_visits_from_to':
            having = having + ' count(v.VisitID) ' + str(dict_of_requests[i]).strip("''")
        elif i in ('amount_of_visits'):
            having = having + ' ' + str(dict_of_requests[i]).strip("'['']'") + ' AND'
        elif i in ('clause_goals'):
            having = having + ' sum(length(h.GoalsID)) ' + str(dict_of_requests[i]).strip("''")
        elif i in ('amount_of_goals'):
            having = having + ' ' + str(dict_of_requests[i]).strip("'['']'") + ' AND'
        elif i in ('URL'):
            for j in dict_of_requests['URL']:
                if str(dict_of_requests['clause_url']).strip("'['']'") == '1':
                    string = f"%{j}%"
                    having = having + " arrayStringConcat(groupArray(h.URL)) like CAST(unhex('" + string.encode("utf-8").hex() + "'), 'String') OR "
                elif str(dict_of_requests['clause_url']).strip("'['']'") == '2':
                    string = f"{j}"
                    having = having + " has(groupArray(cutQueryString(h.URL)), CAST(unhex('" + string.encode("utf-8").hex() + "'), 'String')) OR "

    if having == 'HAVING':
        having = having[:-6]
    else:
        having = having[:-3] 
    return having

def translate_form_dict_to_query(form_dict, integration_id):
    del form_dict['csrf_token']
    dict_of_requests = {key: value for key, value in form_dict.items() if value not in ([''], ['-1'],['Не выбрано'])}
    if not validate_analytics_form(dict_of_requests):
        return jsonify(message='bad request'),400
    #changing the values for the query
    dict_of_requests = {key: INT_COMPARISON_DIC[value[0]] 
                        if key in COMPARISON_FIELDS else value
                        for key,value \
                        in dict_of_requests.items()}
    where = build_where_clause(dict_of_requests)
    having = build_having_clause(dict_of_requests)
    hits_table_name = generate_full_CH_table_name(current_user.crypto,'hits_raw',integration_id)
    visits_table_name = generate_full_CH_table_name(current_user.crypto,'visits_raw',integration_id)
    query = ANALITICS_SEARCH_QUERY.format(hits_table_name=hits_table_name, \
                                    visits_table_name=visits_table_name,\
                                    where_clause = where,\
                                    having_clause = having)

    print(query)
    return query    

def validate_analytics_form(analitics_form_dic):
    print(analitics_form_dic)
    for key, values_list in analitics_form_dic.items():
        # print(key)
        if key not in validate_dictionary.keys():
            continue
        for value in values_list:
            # print('\t', value)
            if not validate_dictionary[key](value):
                return False
    return True