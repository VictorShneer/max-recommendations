import traceback
import requests
from io import StringIO
import ast
import numpy as np
import requests
import json
import base64
import pandas as pd
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.metrika import bp
from app.clickhousehub.clickhouse_custom_request import made_url_for_query,request_clickhouse
from app.metrika.secur import current_user_own_integration
from app.metrika.send_hash_to_gr import add_custom_field
from app.metrika.conversion_table_builder import generate_grouped_columns_sql
from app.grhub.grmonster import GrMonster
from app.utils import decode_this_string,encode_this_string
from operator import itemgetter
from app.tasks import send_message # TODO send_message should be in main

COLUMNS = ['Email', \
            'Total Visits', \
            'Total Visits From Newsletter', \
            'Total Goals Complited', \
            'Total Goals From Newsletter', \
            'Conversion (TG/TV)', \
            'Email power proportion']

VISITS_RAW_QUERY = '''
    select * from(
        SELECT
            CASE  when extractURLParameter(StartURL, 'mxm') != ''
                  then base64Decode(extractURLParameter(StartURL, 'mxm'))
                  else concat('no-email',toString(ClientID)) end as email,

            sum(case when Date >= '{start_date}'
                then 1 else 0 end) as total_visits,

            sum(case when extractURLParameter(StartURL, 'mxm') != ''
                and (Date >= '{start_date}')
                then 1 else 0 end) as total_visits_from_newsletter,

            sum(case when 1
                {grouped_columns}
                then length(GoalsID) else 0 end) as total_goals,

            sum(case when extractURLParameter(StartURL, 'mxm') != ''
                {grouped_columns}
                then length(GoalsID) else 0 end) as total_goals_from_newsletter,

            multiply(intDivOrZero(total_goals, total_visits),100) as conversion,
            multiply(intDivOrZero(total_goals_from_newsletter, total_goals),100) as emailpower
        FROM {clickhouse_table_name}
        group by email
    )
    where total_visits != 0
'''


@bp.route('/metrika/<integration_id>/get_data')
@login_required
def metrika_get_data(integration_id):
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        print('Permission abort')
        abort(404)

    request_start_date = request.args.get('start_date')
    request_goals = request.args.get('goals')
    # TODO: validate start_date, goals
    current_app.logger.info("### selected-goals {}".format(request_goals))
    clickhouse_table_name = '{}.{}_raw_{}'.format(current_user.crypto, 'visits', integration_id)
    grouped_columns_sql = generate_grouped_columns_sql({'start_date':[request_start_date], 'goals':request_goals.split(',')})
    url_for_columns = made_url_for_query('DESC {}'.format(clickhouse_table_name), current_user.crypto)
    url_for_visits_all_data = made_url_for_query(\
        VISITS_RAW_QUERY.format(\
            clickhouse_table_name=clickhouse_table_name,\
            start_date = request_start_date,\
            grouped_columns = grouped_columns_sql
            ), current_user.crypto \
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
            print(response_with_visits_all_data.text)
            print()
            print(response_with_columns_names.text)
    except:
        flash('{} Ошибки в запросе или в настройках итеграции!'.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))

    file_from_string = StringIO(response_with_visits_all_data.text)
    visits_all_data_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', names=COLUMNS)

    if request_goals:
        visits_all_data_df = visits_all_data_df[visits_all_data_df['Total Goals Complited']!=0]

    max_df = visits_all_data_df

#    max_no_email_1graph = [ [int(max_row['Total Visits']),int(max_row['Conversion (TG/TV)'])] for _, max_row in max_df[max_df['Total Visits From Newsletter'] != 0][['Total Visits','Conversion (TG/TV)']].iterrows() ] # 1 график - без email
#    max_email_1graph = [ [int(max_row['Total Visits']),int(max_row['Conversion (TG/TV)'])] for _, max_row in max_df[max_df['Total Visits From Newsletter'] == 0][['Total Visits','Conversion (TG/TV)']].iterrows() ] # 1 график - с email

#    if (len(max_no_email_1graph) == 0):
#        max_no_email_1graph = [[0,0]]
#    if (len(max_email_1graph) == 0):
#        max_email_1graph = [[0,0]]


    conv_email_sum = max_df[max_df['Total Visits From Newsletter'] != 0]['Conversion (TG/TV)'].sum()
    conv_no_email_sum = max_df[max_df['Total Visits From Newsletter'] == 0]['Conversion (TG/TV)'].sum()
    goals_email_sum = max_df[max_df['Total Visits From Newsletter'] != 0]['Total Goals From Newsletter'].sum()
    goals_no_email_sum = max_df['Total Goals Complited'].sum() - goals_email_sum
    visits_email_sum = max_df[max_df['Total Visits From Newsletter'] != 0]['Total Visits From Newsletter'].sum()
    visits_no_email_sum = max_df['Total Visits'].sum() - visits_email_sum

    front_end_df = max_df[['Email', 'Total Visits', 'Total Visits From Newsletter','Total Goals Complited', 'Total Goals From Newsletter', 'Conversion (TG/TV)', 'Email power proportion']]
    front_end_df= front_end_df.astype(str)
    json_to_return = front_end_df.to_json(default_handler=str, orient='table', index=False)
    json_to_return =json.loads(json_to_return)
    json_to_return['conv_email_sum'] = str(conv_email_sum)
    json_to_return['conv_no_email_sum'] = str(conv_no_email_sum)
#    json_to_return['max_no_email_1graph'] = json.dumps(max_no_email_1graph)
#    json_to_return['max_email_1graph'] = json.dumps(max_email_1graph)
    json_to_return['total_unique_visitors'] = str(front_end_df.shape[0])
    temp_all_visots = front_end_df.shape[0]
    total_email_visitors = temp_all_visots - front_end_df[front_end_df['Email'].str.contains("no-email")].shape[0]
    json_to_return['total_email_visitors'] = str(total_email_visitors)
    json_to_return['goals_email_sum'] = str(goals_email_sum)
    json_to_return['goals_no_email_sum'] = str(goals_no_email_sum)
    json_to_return['visits_email_sum'] = str(visits_email_sum)
    json_to_return['visits_no_email_sum'] = str(visits_no_email_sum)
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
        clickhouse_raw_table_name = '{}.{}_raw_{}'.format(current_user.crypto, 'visits', integration_id)
        # query_count = 'SELECT count(Date) FROM {}'.format(clickhouse_raw_table_name)
        query_min = 'SELECT min(Date) FROM {}'.format(clickhouse_raw_table_name)
        query_max = 'SELECT max(Date) FROM {}'.format(clickhouse_raw_table_name)
        # query_data_length = made_url_for_query(query_count, current_user.crypto)
        query_min_date = made_url_for_query(query_min, current_user.crypto)
        query_max_date = made_url_for_query(query_max, current_user.crypto)
        # data_length_text =request_clickhouse(query_data_length, auth, certificate_path).text
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
    goals = [(goal['id'],goal['name']) for goal in r.json()['goals']]

    if (current_user.email == 'sales@getresponse.com'):
        return render_template('metrika_example.html')
    else:
        return render_template(\
            'metrika.html',\
            min_date=min_date_text.strip(),\
            max_date=max_date_text.strip(),\
            integration_name=integration.integration_name,\
            integration_id=integration_id,\
            goals=goals)

@bp.route('/metrika/callback_add_custom_field/<identificator>', methods = ['GET','POST'])
def callback_add_custom_field(identificator):
    identificator_decoded=decode_this_string(identificator)
    user_id, integration_id = itemgetter(0, 1)(identificator_decoded.split('-'))
    integration = Integration.query.filter_by(id = int(integration_id)).first()
    user = User.query.filter_by(id = int(user_id)).first()
    action = request.args.get('action')
    print(action)
    print(action == 'subscribe')
    print(user == integration.user)
    send_message(user.id, f'Пришел callback {str(datetime.now())}')
    if user == integration.user and action == 'subscribe':
        gr_monster = GrMonster(api_key=integration.api_key, callback_url=integration.callback_url)
        contact_email = request.args.get('contact_email')
        contact_id = request.args.get('CONTACT_ID')
        gr_monster.set_hash_email_custom_field_id()
        print(gr_monster.hash_email_custom_field_id)

        gr_monster.upsert_hash_field_for_contact(contact_id,encode_this_string(contact_email))

    return redirect(url_for('main.index'))
