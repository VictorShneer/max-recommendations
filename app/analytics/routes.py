from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.analytics import bp
import requests
from app.analytics.utils import current_user_own_integration, create_url_for_query, send_request_to_clickhouse
import traceback
from pprint import pprint
import pandas as pd
from app.analytics.forms import AnalyticsBar
from collections import defaultdict
from io import StringIO
import base64
import urllib.parse
import numpy as np

@bp.route('/analytics/<integration_id>', methods = ['GET', 'POST'])
@login_required
@current_user_own_integration
def generate_values(integration_id):
    form = AnalyticsBar()
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    # print(form)
    try:
        # Getting the data needed for the drop down menu
        list_of_column_names = ['OperatingSystem','RegionCity','URL','MobilePhone','MobilePhoneModel', 'Browser']
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
    return render_template('analytics.html', list=a, form=form)



@bp.route('/analytics/getdata', methods = ['GET','POST'])
@login_required
# @current_user_own_integration
def process_values():
    if request.method == 'POST':
        try:
            #geting the dict from the form
            dict_of_requests = {}
            dict = request.form.to_dict(flat=False)
            integration_id = request.form["integration_id"]
            for i in dict:
                for k in dict[i]:
                    if k == '0' or k == 'Не выбрано' or k == '' or i == 'csrf_token':
                        pass
                    else:
                        dict_of_requests[i] = dict[i]
            # print(dict_of_requests)

            #changing the values for the query
            spravochnik = {'1':['>='], '2':['<='],'3':['=']}
            for i in dict_of_requests:
                for k in dict_of_requests[i]:
                    for j in spravochnik:
                        if k == j and i not in ('DeviceCategory', 'amount_of_visits', 'amount_of_goals'):
                            dict_of_requests[i] = spravochnik[j]
            # print(dict_of_requests)

            #trying to concat the fucking query
            #TO DO: last value
            word = "WHERE"
            for index, i in enumerate(dict_of_requests):
                if i in ('DeviceCategory', 'OperatingSystem', 'RegionCity', 'MobilePhone', 'MobilePhoneModel', 'Browser'):
                    word = word + ' h.' + i + ' IN (' + str(dict_of_requests[i]).strip('[]') + ') AND'
                elif i in ('clause_visits'):
                    word = word + ' h.Date ' + str(dict_of_requests[i]).strip("'['']'")
                elif i in ('Date'):
                    word = word + ' ' + str(dict_of_requests[i]).strip('['']') + ' AND'
                elif i in ('GoalsID'):
                    for j in dict_of_requests[i]:
                        print('Here is j' + j)
                        word = word + ' has(h.GoalsID,' + str(j) + ') !=0 or'
            word = word[:-3]
            word = word + " GROUP BY emails, ClientID"
            #getting the answer from the db
            create_url = create_url_for_query("SELECT h.ClientID, base64Decode(extractURLParameter(v.StartURL, 'mxm')) as emails FROM {crypto}.hits_raw_{integration_id} h JOIN georgelocal.visits_raw_1 v on v.ClientID = h.ClientID  {smth};".\
                                                format(crypto= current_user.crypto, integration_id=integration_id,smth=word),current_user.crypto)
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




    @bp.route('/analytics/getdata123', methods = ['GET','POST'])
    @login_required
    # @current_user_own_integration
    def process_values():
        if request.method == 'POST':
            try:
                #geting the dict from the form
                dict_of_requests = {}
                dict = request.form.to_dict(flat=False)
                pprint(dict)
            #     for i in dict:
            #         for k in dict[i]:
            #             if k == '0' or k == 'Не выбрано' or k == '' or i == 'csrf_token':
            #                 pass
            #             else:
            #                 dict_of_requests[i] = dict[i]
            #     # print(dict_of_requests)
            #
            #     #changing the values for the query
            #     spravochnik = {'1':['>='], '2':['<='],'3':['=']}
            #     for i in dict_of_requests:
            #         for k in dict_of_requests[i]:
            #             for j in spravochnik:
            #                 if k == j and i not in ('DeviceCategory', 'amount_of_visits', 'amount_of_goals'):
            #                     dict_of_requests[i] = spravochnik[j]
            #     # print(dict_of_requests)
            #
            #     #trying to concat the fucking query
            #     #TO DO: last value
            #     word = "WHERE URL LIKE '%mxm=%' and "
            #     for i in dict_of_requests:
            #         if i in ('DeviceCategory', 'OperatingSystem', 'RegionCity', 'MobilePhone', 'MobilePhoneModel', 'Browser'):
            #             word = word + ' ' + i + ' IN (' + str(dict_of_requests[i]).strip('[]') + ') and'
            #         elif i in ('clause_visits'):
            #             word = word[:-4]
            #             word = word + ' and Date ' + str(dict_of_requests[i]).strip("'['']'")
            #         elif i in ('Date'):
            #             word = word + ' ' + str(dict_of_requests[i]).strip('['']') + ' and'
            #         elif i in ('GoalsID'):
            #             word = word[:-4]
            #             word = word + ' and GoalsID  IN (' + str(dict_of_requests[i]).strip('['']') + ') and'
            #     word = word[:-4]
            #     word = word + " GROUP BY ClientID, extractURLParameter(URL, 'mxm')"
            #     #getting the answer from the db
            #     create_url = create_url_for_query("SELECT ClientID, extractURLParameter(URL, 'mxm') FROM db1.{crypto}_hits_{integration_id} {smth};".\
            #                                         format(crypto= current_user.crypto, integration_id=integration_id,smth=word))
            #     print(create_url)
            #     get_data = send_request_to_clickhouse(create_url).text
            #
            #     #doing magic with the data
            #     file_from_string = StringIO(get_data)
            #     columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, names = ["ClientID", "Hash"])
            #     pprint(columns_df)
            #     list_of_emails = []
            #     for index, row in columns_df[['Hash']].iterrows():
            #         if row.values[0] is not np.nan:
            #             d = base64.b64decode(row.values[0])
            #             s2 = d.decode("UTF-8")
            #             list_of_emails.append(s2)
            #         else:
            #             pass
            #     df_of_emails = pd.DataFrame(list_of_emails, columns = ["Email"])
            #     pprint(df_of_emails)
            #     #making json
            #     front_end_df= df_of_emails.astype(str)
            #     json_to_return = front_end_df.to_json(default_handler=str, orient='table', index=False)
            #
            #     return json_to_return
            except Exception as err:
                print(err)
            return render_template('index.html')
        elif request.method == 'GET':
            print("last hui")
        return render_template('after_analytics.html')
