import traceback
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
from app.metrika.clickhouse_custom_request import made_url_for_query,request_clickhouse
from app.metrika.conversion_table_builder import build_conversion_df
from app.metrika.secur import current_user_own_integration
from app.metrika.send_hash_to_gr import add_custom_field

@bp.route('/metrika/<integration_id>/get_data')
@login_required
def metrika_get_data(integration_id):
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        print('Permission abort')
        abort(404)


    request_start_date = request.args.get('start_date')

    url_for_columns = made_url_for_query('DESC visits_all', integration)
    if request_start_date =='':
        url_for_visits_all_data = made_url_for_query(\
        "SELECT * FROM visits_all",\
        integration\
        )
    else:
        url_for_visits_all_data = made_url_for_query(\
        "SELECT * FROM visits_all WHERE Date > toDate('{}')".format(request_start_date),\
        integration\
        )

    try:
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

    # prepare it column names
    file_from_string = StringIO(response_with_columns_names.text)
    columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, usecols=[0])
    list_of_column_names = columns_df[0].values
    # finishing visits all table
    file_from_string = StringIO(response_with_visits_all_data.text)
    try:
        visits_all_data_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', names=list_of_column_names, usecols=['ClientID','GoalsID', 'UTMSource','VisitID'])
        max_df = build_conversion_df(visits_all_data_df)
    except:
        print('Table building abort')
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

    #max_no_email_1graph = max_df[max_df['Visits with email'] != 0][['Visits with email','Conversion (TG/TV)']]
    # print(max_no_email_1graph)
    # print(max_email_1graph)

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
        # visits_table = ''.join([current_user.crypto, '_visits_all'])
        # print(visits_table)
        visits_table = 'visits_all'
        query_data_length = made_url_for_query('SELECT count(Date) FROM {}'.format(visits_table),integration)
        query_min_date = made_url_for_query('SELECT min(Date) FROM {}'.format(visits_table),integration)
        query_max_date = made_url_for_query('SELECT max(Date) FROM {}'.format(visits_table),integration)
        data_length_text =request_clickhouse(query_data_length, auth, certificate_path).text
        min_date_text = request_clickhouse(query_min_date, auth, certificate_path).text
        max_date_text = request_clickhouse(query_max_date, auth, certificate_path).text

    except Exception as e:
        traceback.print_exc()
        flash('{} Ошибки в настройках интеграции!'.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))

    if (current_user.email == 'sales@getresponse.com'):
        return render_template('metrika_example.html')
    else:
        return render_template(\
            'metrika.html',\
            min_date=min_date_text,\
            max_date=max_date_text,\
            data_length = data_length_text,\
            integration_name=integration.integration_name,\
            integration_id=integration_id)

@bp.route('/metrika/callback_add_custom_field', methods = ['GET'])
def callback_add_custom_field():
    action = request.args.get('action')
    contact_email = request.args.get('contact_email')
    contact_id = request.args.get('CONTACT_ID')
    custom_field_id= 'nZT'  #TODO id кастомного поля, для каждого клиента должен быть свой (в ссылке прописать), пока зашит с моего акка
    if (action == 'subscribe'): #проверяем, что коллбек именно на подписку
        add_custom_field(contact_email, contact_id, custom_field_id)
    return redirect(url_for('main.index'))
