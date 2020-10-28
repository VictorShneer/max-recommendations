"""
sub functions
handle route and differenct module need in general
"""
from app.utils import generate_full_CH_table_name
from app.clickhousehub.clickhouse_custom_request import made_url_for_query,request_clickhouse
from flask import flash, redirect, url_for, current_app
from app.metrika.sql_query_builder import generate_filter_goals_sql_clause
import requests
from io import StringIO
import pandas as pd
from app.analytics.utils import create_url_for_query, \
                                send_request_to_clickhouse
# build pandas df from CH SQL template and filter statements
def get_df_from_CH(crypto, integration_id, query_template, goals_filter_array, request_start_date, columns):
    clickhouse_table_name = generate_full_CH_table_name(crypto, 'visits_raw', integration_id)  
    goals_fiter_sql_clause = generate_filter_goals_sql_clause(goals_filter_array)
    query_url = made_url_for_query(\
        query_template.format(\
            clickhouse_table_name=clickhouse_table_name,\
            start_date = request_start_date,\
            goals_filter_clause = goals_fiter_sql_clause
            ), crypto \
        )
    current_app.logger.info(f'### request_clickhouse start urls:\n{query_url}')
    return generate_df_from_query(query_url,columns)

# build pandas df from CH response
# first requset clickhouse 
# then interpret repsponse as StringIO
# and read it as csv file
def generate_df_from_query(query_url, columns):
    try:

        # get table data and prepare it
        response_with_data =request_clickhouse (query_url, current_app.config['AUTH'], current_app.config['CERTIFICATE_PATH'])
        if not response_with_data.ok:
            raise ConnectionRefusedError(f'Clickhouse staus code not ok \n {response_with_data.text}')
    except ConnectionRefusedError as err:
        current_app.logger.critical(err)

    file_from_string = StringIO(response_with_data.text)
    return pd.read_csv(file_from_string,sep='\t',lineterminator='\n', names=columns)


def request_min_max_visits_dates(crypto,integration_id):
    try:
        certificate_path = current_app.config['CERTIFICATE_PATH']
        auth = current_app.config['AUTH']
        clickhouse_visits_raw_table_name = generate_full_CH_table_name(crypto, 'visits_raw', integration_id)
        query_min = 'SELECT min(Date) FROM {}'.format(clickhouse_visits_raw_table_name)
        query_max = 'SELECT max(Date) FROM {}'.format(clickhouse_visits_raw_table_name)
        query_min_date = made_url_for_query(query_min, crypto)
        query_max_date = made_url_for_query(query_max, crypto)
        min_date_response = request_clickhouse(query_min_date, auth, certificate_path)
        min_date_text = min_date_response.text.strip()
        max_date_text = request_clickhouse(query_max_date, auth, certificate_path).text.strip()
        return min_date_response,min_date_text, max_date_text

    except Exception as e:
        flash('Ошибки в настройках интеграции!')
        print(f'!!!\n{e}\n!!!')
        return redirect(url_for('main.user_integrations'))



