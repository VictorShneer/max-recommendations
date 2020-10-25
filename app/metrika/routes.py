import json
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.metrika import bp
from app.clickhousehub.clickhouse_custom_request import made_url_for_query,request_clickhouse
from app.metrika.secur import current_user_own_integration
from app.grhub.grmonster import GrMonster
from app.utils import decode_this_string,encode_this_string
from operator import itemgetter
from app.metrika.metrika_sql_queries import TIME_SERIES_QUERY, VISITS_RAW_QUERY,TIME_SERIES_DF_COLUMNS, COLUMNS
from app.main.utils import check_if_date_legal, integration_is_ready
from app.metrika.utils import request_min_max_visits_dates,get_metrika_goals, get_df_from_CH
from app.metrika.metrika_report import MetrikaReport
from app.analytics.utils import current_user_own_integration


@bp.route('/metrika/<integration_id>/get_data')
@login_required
@current_user_own_integration
def metrika_get_data(integration_id):
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    # retrieve args and validate them
    request_start_date = request.args.get('start_date')
    request_goals = request.args.get('goals') # TODO: validate goals
    if not check_if_date_legal(request_start_date):
        print('Illigal start date')
        abort(404)
    goals_filter_array=[]
    if request_goals:
        # list + map because CH store GoalsId as ints
        # so we need ints too perform CH functions on it
        goals_filter_array=list(map(int, request_goals.split(',')))
    # TODO integrate it to class like metrika report
    time_series_goals_df = get_df_from_CH(current_user.crypto, integration_id, TIME_SERIES_QUERY,goals_filter_array,request_start_date,TIME_SERIES_DF_COLUMNS)
    clientid_convers_df = get_df_from_CH(current_user.crypto, integration_id, VISITS_RAW_QUERY,goals_filter_array,request_start_date,COLUMNS)
    # bad outside target unit logic :(
    if request_goals:
        clientid_convers_df = clientid_convers_df[clientid_convers_df['Всего целей выполнено']!=0]
    # generate report based on CH data
    metrika_report = MetrikaReport(clientid_convers_df, time_series_goals_df)
    metrika_report.load_email_visits_table()
    grmonster = GrMonster(api_key=integration.api_key, callback_url=integration.callback_url)
    broadcast_messages_since_date_subject_df = grmonster.get_broadcast_messages_since_date_subject_df(request_start_date)
    metrika_report.load_time_series(broadcast_messages_since_date_subject_df)
    metrika_report.load_pie()
    metrika_report.load_summary()
    return metrika_report.report_json

@bp.route('/metrika/<integration_id>', methods = ['GET'])
@login_required
@current_user_own_integration
def metrika(integration_id):
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    #request init info
    response, min_date_text, max_date_text = request_min_max_visits_dates(current_user.crypto,integration_id)
    if not response.ok:
        flash('Ошибка или создание интеграции не завершено')
        return redirect(url_for('main.user_integrations'))
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
    if user == integration.user and action == 'subscribe':
        gr_monster = GrMonster(api_key=integration.api_key, callback_url=integration.callback_url)
        contact_email = request.args.get('contact_email')
        contact_id = request.args.get('CONTACT_ID')
        gr_monster.set_hash_email_custom_field_id()
        gr_monster.upsert_hash_field_for_contact(contact_id,encode_this_string(contact_email))

    return redirect(url_for('main.index'))
