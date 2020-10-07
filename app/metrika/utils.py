from app.utils import generate_full_CH_table_name
from app.clickhousehub.clickhouse_custom_request import made_url_for_query,request_clickhouse
from flask import flash, redirect, url_for, current_app
from app.metrika.conversion_table_builder import generate_grouped_columns_sql
import requests
from io import StringIO
import pandas as pd

def get_df_from_CH(crypto, integration_id, query_template, filter_statements,request_start_date,columns):
    clickhouse_table_name = generate_full_CH_table_name(crypto, 'visits_raw', integration_id)  
    grouped_columns_sql = generate_grouped_columns_sql(filter_statements)
    query_url = made_url_for_query(\
        query_template.format(\
            clickhouse_table_name=clickhouse_table_name,\
            start_date = request_start_date,\
            grouped_columns = grouped_columns_sql
            ), crypto \
        )
    current_app.logger.info(f'### request_clickhouse start urls:\n{query_url}')
    return generate_df_from_query(query_url,columns)
def generate_df_from_query(query_url, columns):
    try:

        # get table data and prepare it
        response_with_data =request_clickhouse (query_url, current_app.config['AUTH'], current_app.config['CERTIFICATE_PATH'])
        if not response_with_data.ok:
            raise ConnectionRefusedError('Clickhouse staus code not ok')
    except ConnectionRefusedError as err:
        current_app.logger.CRITICAL(err)

    file_from_string = StringIO(response_with_data.text)
    return pd.read_csv(file_from_string,sep='\t',lineterminator='\n', names=columns)

def get_metrika_goals(metrika_key,counter_id):
    headers = {'Authorization':'OAuth {}'.format(metrika_key)}
    ROOT = 'https://api-metrika.yandex.net/'
    url = ROOT+'management/v1/counter/{}/goals'.format(counter_id)
    r = requests.get(url, headers=headers)
    return [(goal['id'],goal['name']) for goal in r.json()['goals']]

def request_min_max_visits_dates(crypto,integration_id):
    try:
        certificate_path = current_app.config['CERTIFICATE_PATH']
        auth = current_app.config['AUTH']
        clickhouse_visits_raw_table_name = generate_full_CH_table_name(crypto, 'visits_raw', integration_id)
        query_min = 'SELECT min(Date) FROM {}'.format(clickhouse_visits_raw_table_name)
        query_max = 'SELECT max(Date) FROM {}'.format(clickhouse_visits_raw_table_name)
        query_min_date = made_url_for_query(query_min, crypto)
        query_max_date = made_url_for_query(query_max, crypto)
        min_date_text = request_clickhouse(query_min_date, auth, certificate_path).text.strip()
        max_date_text = request_clickhouse(query_max_date, auth, certificate_path).text.strip()
        return min_date_text, max_date_text

    except Exception as e:
        flash('Ошибки в настройках интеграции!')
        print(f'!!!\n{e}\n!!!')
        return redirect(url_for('main.user_integrations'))



