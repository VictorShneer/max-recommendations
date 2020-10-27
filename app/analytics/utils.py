"""
sub function
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


def validate_analytics_form(analitics_form_dic):
    print(analitics_form_dic)
    for key, values_list in analitics_form_dic.items():
        print(key)
        if key not in validate_dictionary.keys():
            continue
        for value in values_list:
            print('\t', value)
            if not validate_dictionary[key](value):
                return False
    return True