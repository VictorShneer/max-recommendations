"""
analytics routes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.analytics import bp
import requests
from app.analytics.utils import current_user_own_integration, \
                                create_url_for_query, \
                                send_request_to_clickhouse, \
                                request_ch_for_initial_data, \
                                build_df_from_CH_response, \
                                translate_form_dict_to_query, \
                                validate_external_segment_name, \
                                validate_analytics_form, \
                                build_analytics_search_json
from app.grhub.grmonster import GrMonster
import traceback
from pprint import pprint
import pandas as pd
from app.analytics.forms import AnalyticsBar, Filters
from collections import defaultdict
from io import StringIO
import base64
import urllib.parse
import numpy as np
import concurrent.futures
import binascii
from app.analytics.analytics_consts import COLUMNS, INITIAL_QUERY,INITIAL_QUERY_COLUMNS
from app.utils import get_metrika_goals
import json
from flask import jsonify

# send search contacs to GR campaing by http API
@bp.route('/analytics/send_search_contacts/<integration_id>', methods=['POST'])
@current_user_own_integration
@login_required
def send_search_contacts(integration_id):
    integration = Integration.query.filter_by(id = integration_id).first_or_404()
    try:
        current_user.launch_task('send_search_contacts_to_gr', \
                                    'Загрузка контактов в GR, прогресс: ', \
                                    request.form['contactsList'].split(','), \
                                    request.form['campaignId'],\
                                    integration.api_key,\
                                    current_user.id)
        db.session.commit()
    except:
        return {'status':'<400>'}
    return {'status':'<200>'}

# send search contacs to GR campaing by FTP
@bp.route('/analytics/ftp_search_contacts/<integration_id>', methods=['POST'])
@current_user_own_integration
@login_required
def ftp_search_contacts(integration_id):
    integration = Integration.query.filter_by(id = integration_id).first_or_404()
    grmonster = GrMonster(integration.api_key,\
                          ftp_login = integration.ftp_login, \
                          ftp_pass = integration.ftp_pass)
    if not validate_external_segment_name(request.form['external_name']):
        abort(404)
    try:
        current_user.launch_task('send_search_contacts_to_gr_ftp', \
                                    'Загрузка контактов в GR FTP, прогресс: ', \
                                    request.form['contactsList'].split(','), \
                                    request.form['external_name'],\
                                    grmonster,\
                                    current_user.id)
        db.session.commit()
    except:
        return {'status':'<400>'}
    return {'status':'<200>'}

# this route hande POST new GR campaign by http API
@bp.route('/analytics/create_gr_campaign/<integration_id>', methods=["POST"])
@current_user_own_integration
@login_required
def create_gr_campaign_route(integration_id):
    integration = Integration.query.filter_by(id = integration_id).first_or_404()
    grmonster = GrMonster(api_key = integration.api_key, callback_url=integration.callback_url)
    grmonster.create_gr_campaign(request.form['gr_campaign_name'])
    return '<200>'

# this route handle initial analytics page call
# make first request to CH and GR to get initial integration data
# like dates ranges, GR campaigns and YM goals
# TODO need refactor
@bp.route('/analytics/<integration_id>', methods = ['GET', 'POST'])
@login_required
@current_user_own_integration
def generate_values(integration_id):
    form = AnalyticsBar()
    filters_form = Filters()
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    initial_response_raw =request_ch_for_initial_data(current_user.crypto, integration_id, INITIAL_QUERY)
    if not initial_response_raw.ok:
        flash('Ошибка или создание интеграции не завершено')
        return redirect(url_for('main.user_integrations'))
    inital_data_df = build_df_from_CH_response(initial_response_raw, INITIAL_QUERY_COLUMNS)
    goals = get_metrika_goals(integration.metrika_key,integration.metrika_counter_id)
    grmonster = GrMonster(integration.api_key)
    gr_campaigns = grmonster.get_gr_campaigns()      
    # get unique values for every choice
    uniqueOpSys = inital_data_df['OperatingSystem'].unique()
    uniqueRegCyt = inital_data_df['RegionCity'].unique()
    uniqueURL = inital_data_df['cutQueryString(URL)'].unique()
    uniquePh = inital_data_df['MobilePhone'].unique()
    uniquePhM = inital_data_df['MobilePhoneModel'].unique()
    uniqueBro = inital_data_df['Browser'].unique()
    # get initial summary data
    start_date = inital_data_df['Date'].min()
    end_date = inital_data_df['Date'].max()
    total_unique_emails = len(inital_data_df['mxm'].unique())
    # Adding choices to the forms
    form.OperatingSystem.choices = list(zip(uniqueOpSys,uniqueOpSys))
    form.RegionCity.choices = list(zip(uniqueRegCyt,uniqueRegCyt))
    form.URL.choices = list(zip(uniqueURL,uniqueURL))
    form.GoalsID.choices = goals
    form.MobilePhone.choices = list(zip(uniquePh,uniquePh))
    form.MobilePhoneModel.choices = list(zip(uniquePhM,uniquePhM))
    form.Browser.choices = list(zip(uniqueBro,uniqueBro))
    return render_template('analytics.html',\
                            form=form,\
                            filters_form=filters_form,\
                            gr_campaigns = gr_campaigns,\
                            start_date=start_date,\
                            end_date=end_date,\
                            total_unique_emails=total_unique_emails,
                            integration_name=integration.integration_name)

# this route handle analytics form send
# here we make calls to CH to get visitors
# that meet conditions choosed by user in /analytics/<integration_id> route 
@bp.route('/analytics/getdata', methods = ['GET','POST'])
@login_required
def process_values():
    # TODO check if current_us owns integration
    #geting the dict from the form
    integration_id = request.form["integration_id"]
    form_dic=request.form.to_dict(flat=False)
    query = translate_form_dict_to_query(form_dic,integration_id)
    create_url = create_url_for_query(query,current_user.crypto)
    ch_response = send_request_to_clickhouse(create_url)
    analytics_search_df = build_df_from_CH_response(ch_response, COLUMNS)
    json_to_return = build_analytics_search_json(analytics_search_df)
    return json_to_return
