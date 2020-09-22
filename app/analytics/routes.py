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
from app.analytics.forms import AnalyticsBar
from collections import defaultdict
from io import StringIO
import base64
import urllib.parse
import numpy as np
import concurrent.futures

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
def generate_values(integration_id):
    form = AnalyticsBar()
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    # print(form)
    try:
        # Getting the data needed for the drop down menu
        list_of_column_names = ['OperatingSystem','RegionCity','cutQueryString(URL)','MobilePhone','MobilePhoneModel', 'Browser']
        list_of_answers = []
        for i in range(len(list_of_column_names)):
            create_url = create_url_for_query('SELECT {smth} FROM {crypto}.hits_raw_{integration_id} GROUP BY {smth2};'.\
                            format(crypto = current_user.crypto, integration_id = integration.id,smth = list_of_column_names[i],smth2 = list_of_column_names[i]), current_user.crypto)
            get_data = send_request_to_clickhouse(create_url).text
            list_of_answers.append(get_data)
            i += 1
        # Generating readable data for the drop down menu
        df = pd.DataFrame(list_of_answers, columns=['Values'])
        a = df.Values.str.split("\n")
        for idx,val in a.items():
            a[idx] = [v for v in val if v != '']
            # a[idx].append('Не выбрано')

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
        grmonster = GrMonster(integration.api_key)
        gr_campaigns = grmonster.get_gr_campaigns()
        # Adding choices to the forms
        form.OperatingSystem.choices = [(g,g) for g in a[0]]
        form.RegionCity.choices = [(g,g) for g in a[1]]
        form.URL.choices = [(g,g) for g in a[2]]
        form.GoalsID.choices = [(g[0],g[1]) for g in goals]
        form.MobilePhone.choices = [(g,g) for g in a[3]]
        form.MobilePhoneModel.choices = [(g,g) for g in a[4]]
        form.Browser.choices = [(g,g) for g in a[5]]
        #
        # if form.validate_on_submit():
        #     return redirect(url_for('analytics.after_analytics'))
    except Exception as e:
        traceback.print_exc()
        flash('{} Ошибки в настройках интеграции!'.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))
        # return render_template('analytics.html')
    return render_template('analytics.html', list=a, form=form, gr_campaigns = gr_campaigns)



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

            for index, i in enumerate(dict_of_requests):
                if i in ('clause_visits_from_to'):
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
                            having = having + " arrayStringConcat(groupArray(h.URL)) like '%" + j + "%' OR "
                        elif str(dict_of_requests['clause_url']).strip("'['']'") == '2':
                            having = having + " has(groupArray(cutQueryString(h.URL)), '" + j + "') OR "

            if having == 'HAVING':
                having = having[:-6]
            else:
                having = having[:-3]

            whole = f"""
            SELECT h.ClientID, base64Decode(extractURLParameter(v.StartURL, 'mxm')) as emails
            FROM {current_user.crypto}.hits_raw_{integration_id} h
            JOIN georgelocal.visits_raw_1 v on v.ClientID = h.ClientID
            {where}
            GROUP BY emails, ClientID
            {having};"""

            whole = whole. replace("#", "%")
            #getting the answer from the db
            create_url = create_url_for_query(whole,current_user.crypto)
            print(create_url)
            get_data = send_request_to_clickhouse(create_url).text

            #doing magic with the data
            file_from_string = StringIO(get_data)
            columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, names = ["ClientID", "Hash"])
            columns_df = columns_df.dropna()
            columns_df = columns_df.drop_duplicates()
            pprint(columns_df)
            front_end_df= columns_df.astype(str)
            json_to_return = front_end_df.to_json(default_handler=str, orient='table', index=False)

            return json_to_return
        except Exception as err:
            print(err)
        return render_template('index.html')
    elif request.method == 'GET':
        print("last hui")
    return render_template('after_analytics.html')
