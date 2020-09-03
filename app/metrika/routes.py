import traceback
import requests
from io import StringIO
import ast
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
import pandas as pd
from app.models import User, Integration
from app import db
from app.metrika import bp
from app.clickhousehub.clickhouse_custom_request import made_url_for_query,request_clickhouse
from app.metrika.conversion_table_builder import build_conversion_df
from app.metrika.secur import current_user_own_integration
from app.metrika.send_hash_to_gr import add_custom_field

PROPERTY_TO_SQL_DIC = {'start_date':'>','goals':'IN'}


@bp.route('/metrika/<integration_id>/get_data')
@login_required
def metrika_get_data(integration_id):
    current_app.logger.info('### metrika/id/get_data')
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        print('Permission abort')
        abort(404)



    request_start_date = request.args.get('start_date')

    request_goals = request.args.get('goals')
    print(request_goals)
    print(request_start_date)
    print('#'*10)
    current_app.logger.info("### selected-goals {}".format(request_goals))
    clickhouse_table = '{}_{}_{}'.format(current_user.crypto, 'visits', integration_id)

    url_for_columns = made_url_for_query('DESC {}'.format(clickhouse_table))
    if request_start_date =='':
        url_for_visits_all_data = made_url_for_query(\
        "SELECT * FROM {}".format(clickhouse_table)\
        )
    else:
        url_for_visits_all_data = made_url_for_query(\
        "SELECT * FROM {} WHERE Date > toDate('{}')".format(clickhouse_table,request_start_date)\
        )

    try:

        current_app.logger.info('### request_clickhouse start urls: {}\n{}'.format(url_for_columns,url_for_visits_all_data))
        # get column names 1
        response_with_columns_names = request_clickhouse(url_for_columns, current_app.config['AUTH'], current_app.config['CERTIFICATE_PATH'])
        # get table data and prepare it
        response_with_visits_all_data =request_clickhouse (url_for_visits_all_data, current_app.config['AUTH'], current_app.config['CERTIFICATE_PATH'])
        if any([\
                response_with_columns_names.status_code != 200,\
                response_with_visits_all_data.status_code !=200\
                ]):
            flash('Некорректная в дата!')
    except:
        flash('{} Ошибки в запросе или в настройках итеграции!'.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))
	# goals = r.json()['goals']
	# my_item = next((item for item in goals if item['name'] == 'form_submit'), None)
	# print(my_item)

    current_app.logger.info('### request_clickhouse done! columns: {}\ndata: {}'.format(response_with_columns_names, response_with_visits_all_data))
    # prepare it column names
    file_from_string = StringIO(response_with_columns_names.text)
    columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, usecols=[0])
    list_of_column_names = columns_df[0].values
    # finishing visits all table
    file_from_string = StringIO(response_with_visits_all_data.text)
    try:
        current_app.logger.info("### build_conversion_df start columns: {} ".format(list_of_column_names))

        visits_all_data_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', names=list_of_column_names, usecols=['ClientID','GoalsID', 'UTMSource','VisitID','StartURL'])
        max_df = build_conversion_df(visits_all_data_df)
    except Exception as err:
        current_app.logger.info('### build_conversion_df EXCEPTION {}'.format(err))
        abort(404)
    # building max data frame



    max_no_email_1graph = [ [int(max_row['Visits with out email']),int(max_row['Conversion (TG/TV)'])] for _, max_row in max_df[['Visits with out email','Conversion (TG/TV)']].iterrows() ] # 1 график - без email
    max_email_1graph = [ [int(max_row['Visits with email']),int(max_row['Conversion (TG/TV)'])] for _, max_row in max_df[['Visits with email','Conversion (TG/TV)']].iterrows() ] # 1 график - с email



    max_no_email_1graph = [ [int(max_row['Total visits']),int(max_row['Conversion (TG/TV)'])] for _, max_row in max_df[max_df['Visits with email'] != 0][['Total visits','Conversion (TG/TV)']].iterrows() ] # 1 график - без email
    max_email_1graph = [ [int(max_row['Total visits']),int(max_row['Conversion (TG/TV)'])] for _, max_row in max_df[max_df['Visits with email'] == 0][['Total visits','Conversion (TG/TV)']].iterrows() ] # 1 график - с email
    if (len(max_no_email_1graph) == 0):
        max_no_email_1graph = [[0,0]]
    if (len(max_email_1graph) == 0):
        max_email_1graph = [[0,0]]


    conv_email_sum = max_df[max_df['Visits with email'] != 0]['Conversion (TG/TV)'].sum()
    conv_no_email_sum = max_df[max_df['Visits with email'] == 0]['Conversion (TG/TV)'].sum()


    front_end_df = max_df[['ClientID', 'Client identities', 'Total goals complited', 'Total visits', 'Visits with email','Goals complited via email', 'Conversion (TG/TV)', 'Email power proportion']]
    front_end_df= front_end_df.astype(str)
    json_to_return = front_end_df.to_json(default_handler=str, orient='table', index=False)

    json_to_return =json.loads(json_to_return)
    json_to_return['conv_email_sum'] = str(conv_email_sum)
    json_to_return['conv_no_email_sum'] = str(conv_no_email_sum)
    json_to_return['max_no_email_1graph'] = json.dumps(max_no_email_1graph)
    json_to_return['max_email_1graph'] = json.dumps(max_email_1graph)

    return json_to_return

@bp.route('/metrika/<integration_id>', methods = ['GET'])
@login_required
def metrika(integration_id):
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        abort(404)

    try:
        certificate_path = 'app/YandexInternalRootCA.crt'
        auth = {
        'X-ClickHouse-User': current_app.config['CLICKHOUSE_LOGIN'],
        'X-ClickHouse-Key': current_app.config['CLICKHOUSE_PASSWORD']
        }
        clickhouse_table = '{}_{}_{}'.format(current_user.crypto, 'visits', integration_id)
        query_data_length = made_url_for_query('SELECT count(Date) FROM {}'.format(clickhouse_table))
        query_min_date = made_url_for_query('SELECT min(Date) FROM {}'.format(clickhouse_table))
        query_max_date = made_url_for_query('SELECT max(Date) FROM {}'.format(clickhouse_table))
        data_length_text =request_clickhouse(query_data_length, auth, certificate_path).text
        min_date_text = request_clickhouse(query_min_date, auth, certificate_path).text
        max_date_text = request_clickhouse(query_max_date, auth, certificate_path).text

    except Exception as e:
        traceback.print_exc()
        flash('{} Ошибки в настройках интеграции!'.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))

    # get goals
    counter_id = integration.metrika_counter_id
    metrika_key = integration.metrika_key
    headers = {'Authorization':'OAuth {}'.format(metrika_key)}
    ROOT = 'https://api-metrika.yandex.net/'
    url = ROOT+'management/v1/counter/{}/goals'.format(counter_id)
    r = requests.get(url, headers=headers)
    current_app.logger.info('### get goals status code: {}'.format(r.status_code))
    goals = [goal['name'] for goal in r.json()['goals']]

    if (current_user.email == 'sales@getresponse.com'):
        return render_template('metrika_example.html')
    else:
        return render_template(\
            'metrika.html',\
            min_date=min_date_text.strip(),\
            max_date=max_date_text.strip(),\
            data_length = data_length_text,\
            integration_name=integration.integration_name,\
            integration_id=integration_id,\
            goals=goals)

@bp.route('/metrika/callback_add_custom_field', methods = ['GET'])
def callback_add_custom_field():
    action = request.args.get('action')
    contact_email = request.args.get('contact_email')
    contact_id = request.args.get('CONTACT_ID')
    custom_field_id= 'Vu40V0'  #TODO id кастомного поля hash_metrika Макса
    if (action == 'subscribe'): #проверяем, что коллбек именно на подписку
        add_custom_field(contact_email, contact_id, custom_field_id)
    return redirect(url_for('main.index'))
