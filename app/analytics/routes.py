from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.analytics import bp
import requests
from app.analytics.utils import current_user_own_integration, \
                                create_url_for_query, \
                                send_request_to_clickhouse
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
from app.main.utils import integration_is_ready
from app.analytics.analytics_consts import COLUMNS, INITIAL_QUERY,INITIAL_QUERY_COLUMNS
import json

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

@bp.route('/analytics/create_gr_campaign/<integration_id>', methods=["POST"])
@current_user_own_integration
@login_required
def create_gr_campaign_route(integration_id):
    integration = Integration.query.filter_by(id = integration_id).first_or_404()
    grmonster = GrMonster(api_key = integration.api_key, callback_url=integration.callback_url)
    grmonster.create_gr_campaign(request.form['gr_campaign_name'])
    return '<200>'


@bp.route('/analytics/<integration_id>', methods = ['GET', 'POST'])
@login_required
@current_user_own_integration
@integration_is_ready
def generate_values(integration_id):
    form = AnalyticsBar()
    filters_form = Filters()
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    # TODO make several try catches instad of one
    try:    
        # build CH table names    
        visits_table_name = '{}.{}_raw_{}'.format(current_user.crypto, 'visits', integration_id)
        hits_table_name = '{}.{}_raw_{}'.format(current_user.crypto, 'hits', integration_id)

        # query all stuff - dropdown chices, dates and email visitors
        query = INITIAL_QUERY.format(hits_table_name=hits_table_name,\
                                        visits_table_name=visits_table_name)
        create_url = create_url_for_query(query, current_user.crypto)
        initial_response = send_request_to_clickhouse(create_url).text
        file_from_string = StringIO(initial_response)
        inital_data_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, names=INITIAL_QUERY_COLUMNS)

        # get goals
        counter_id = integration.metrika_counter_id
        metrika_key = integration.metrika_key
        headers = {'Authorization':'OAuth {}'.format(metrika_key)}
        ROOT = 'https://api-metrika.yandex.net/'
        url = ROOT+'management/v1/counter/{}/goals'.format(counter_id)
        r = requests.get(url, headers=headers)
        current_app.logger.info('### get goals status code: {}'.format(r.status_code))
        goals = [(goal['id'],goal['name']) for goal in r.json()['goals']]

        # get gr campaigns
        grmonster = GrMonster(integration.api_key, callback_url=integration.callback_url)
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

    except Exception as e:
        traceback.print_exc()
        flash('{} Ошибки в настройках интеграции!'.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))
    return render_template('analytics.html',\
                            form=form,\
                            filters_form=filters_form,\
                            gr_campaigns = gr_campaigns,\
                            start_date=start_date,\
                            end_date=end_date,\
                            total_unique_emails=total_unique_emails,
                            integration_name=integration.integration_name)



@bp.route('/analytics/getdata', methods = ['GET','POST'])
@login_required
# @current_user_own_integration
def process_values():
    if request.method == 'POST':
        try:
            #geting the dict from the form
            dict = request.form.to_dict(flat=False)
            integration_id = request.form["integration_id"]
            dict_of_requests = {value: dict[value] for value in dict if dict[value] not in ([''], ['0'],['Не выбрано']) if value != 'csrf_token'}

            pprint(dict_of_requests)
            #changing the values for the query
            dict_of_requests = {value: '>=' if dict_of_requests[value] == ['1'] and value not in ('DeviceCategory', 'amount_of_visits', 'amount_of_goals', 'clause_url') else
                                '<=' if dict_of_requests[value] == ['2'] and value not in ('DeviceCategory', 'amount_of_visits', 'amount_of_goals', 'clause_url') else
                                '==' if dict_of_requests[value] == ['3'] and value not in ('DeviceCategory', 'amount_of_visits', 'amount_of_goals', 'clause_url') else
                                dict_of_requests[value] for value in dict_of_requests}
            #trying to concat the fucking query
            #TO DO: last value
            where = "WHERE has(v.WatchIDs, h.WatchID) = 1 AND"
            having = "HAVING"
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

            pprint(dict_of_requests)
            for index, i in enumerate(dict_of_requests):
                if i == 'clause_visits_from_to':
                    print(i)
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

            whole = f"""
            SELECT h.ClientID, base64Decode(extractURLParameter(v.StartURL, 'mxm')) as emails, OperatingSystem, RegionCity, MobilePhone, MobilePhoneModel, Browser
            FROM {current_user.crypto}.hits_raw_{integration_id} h
            JOIN {current_user.crypto}.visits_raw_{integration_id} v on v.ClientID = h.ClientID
            {where}
            GROUP BY emails, ClientID, OperatingSystem, RegionCity, MobilePhone, MobilePhoneModel, Browser
            {having};"""
            #getting the answer from the db
            create_url = create_url_for_query(whole,current_user.crypto)
            print(create_url)
            get_data = send_request_to_clickhouse(create_url).text

            #doing magic with the data
            file_from_string = StringIO(get_data)
            columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, names = ["ClientID", "hash", "OperatingSystem","RegionCity", "MobilePhone", "MobilePhoneModel", "Browser"])
            # columns_df = columns_df.hash
            columns_df = columns_df.dropna(subset=['hash'])
            columns_df = columns_df.drop_duplicates(subset=['hash'])
            count = columns_df.count()
            print(count)
            pprint(columns_df)
            front_end_df= columns_df.astype(str)
            json_to_return = front_end_df.to_json(default_handler=str, orient='table', index=False)
            json_to_return =json.loads(json_to_return)

            return json_to_return
        except Exception as err:
            print(err)
        return render_template('index.html')
    elif request.method == 'GET':
        print("last hui")
    return render_template('after_analytics.html')
