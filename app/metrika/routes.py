import json
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.metrika import bp
from app.clickhousehub.clickhouse_custom_request import made_url_for_query,request_clickhouse
from app.metrika.secur import current_user_own_integration
from app.metrika.conversion_table_builder import generate_joined_json_for_time_series
from app.grhub.grmonster import GrMonster
from app.utils import decode_this_string,encode_this_string
from operator import itemgetter
from app.metrika.metrica_consts import COLUMNS, TIME_SERIES_QUERY, VISITS_RAW_QUERY,TIME_SERIES_DF_COLUMNS
from app.main.utils import check_if_date_legal, integration_is_ready
from app.metrika.utils import request_min_max_visits_dates,get_metrika_goals, get_df_from_CH

@bp.route('/metrika/<integration_id>/get_data')
@integration_is_ready
@login_required
def metrika_get_data(integration_id):
    # check secur stuff
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        print('Permission abort')
        abort(404)
    # retrieve args and validate them
    request_start_date = request.args.get('start_date')
    request_goals = request.args.get('goals') # TODO: validate goals
    if not check_if_date_legal(request_start_date):
        print('Illigal start date')
        abort(404)
    if request_goals:
        filter_statements={'goals':request_goals.split(',')}
    else:
        filter_statements={}
    time_series_goals_df = get_df_from_CH(current_user.crypto, integration_id, TIME_SERIES_QUERY,filter_statements,request_start_date,TIME_SERIES_DF_COLUMNS)
    clientid_convers_df = get_df_from_CH(current_user.crypto, integration_id, VISITS_RAW_QUERY,filter_statements,request_start_date,COLUMNS)
    # TODO move it to SQL
    if request_goals:
        clientid_convers_df = clientid_convers_df[clientid_convers_df['Total Goals Complited']!=0]
    # calculate pie stuff
    regex = '^no-email*'    
    email_visits_slice_df = clientid_convers_df[~clientid_convers_df['Email'].str.contains(regex)]
    no_email_visits_slice_df = clientid_convers_df[clientid_convers_df['Email'].str.contains(regex)]
    goals_no_email_count = no_email_visits_slice_df['Total Goals Complited'].sum()  
    goals_from_email_count = clientid_convers_df['Total Goals From Newsletter'].sum() 
    goals_has_email_count =  email_visits_slice_df['Total Goals Complited'].sum() 
    #           # clientid_convers_df = clientid_convers_df[COLUMNS]
    # legacy    # clientid_convers_df= clientid_convers_df.astype(str)
    #           # clientid_convers_json = clientid_convers_df.to_json(default_handler=str, orient='table', index=False)
    #           # json_to_return['conv_data'] =json.loads(clientid_convers_json)
    # convert and store table data  
    email_convers_df = email_visits_slice_df[COLUMNS]
    email_convers_df= email_convers_df.astype(str)
    email_convers_json = email_convers_df.to_json(default_handler=str, orient='table', index=False)
    json_to_return = {}
    json_to_return['conv_data'] =json.loads(email_convers_json)
    # store summary data
    json_to_return['total_unique_visitors'] = str(clientid_convers_df.shape[0]) 
    json_to_return['total_email_visitors'] = str(email_visits_slice_df.shape[0]) 
    # store pie data
    json_to_return['goals_no_email_count'] = str(goals_no_email_count)
    json_to_return['goals_has_email_count'] = str(goals_has_email_count)
    json_to_return['goals_from_email_count'] = str(goals_from_email_count)
    # time series builder
    grmonster = GrMonster(api_key=integration.api_key, callback_url=integration.callback_url)
    broadcast_messages_since_date_subject_df = grmonster.get_broadcast_messages_since_date_subject_df(request_start_date)
    time_series_goals_json =  generate_joined_json_for_time_series(time_series_goals_df, broadcast_messages_since_date_subject_df)
    # store time series
    json_to_return['time_series_data'] = time_series_goals_json
    return json_to_return

@bp.route('/metrika/<integration_id>', methods = ['GET'])
@login_required
@integration_is_ready
def metrika(integration_id):
    # check secur stuff
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if not current_user_own_integration(integration, current_user):
        abort(404)
    #request init info
    min_date_text, max_date_text = request_min_max_visits_dates(current_user.crypto,integration_id)
    # get goals
    counter_id = integration.metrika_counter_id
    metrika_key = integration.metrika_key
    goals = get_metrika_goals(metrika_key,counter_id)
    # render
    if (current_user.email == 'sales@getresponse.com'):
        return render_template('metrika_example.html')
    else:
        return render_template(\
            'metrika.html',\
            min_date=min_date_text,\
            max_date=max_date_text,\
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
    user.send_message(f'Пришел callback {str(datetime.now())}')
    if user == integration.user and action == 'subscribe':
        gr_monster = GrMonster(api_key=integration.api_key, callback_url=integration.callback_url)
        contact_email = request.args.get('contact_email')
        contact_id = request.args.get('CONTACT_ID')
        gr_monster.set_hash_email_custom_field_id()
        gr_monster.upsert_hash_field_for_contact(contact_id,encode_this_string(contact_email))

    return redirect(url_for('main.index'))
