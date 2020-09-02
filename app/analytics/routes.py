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

@bp.route('/analytics/<integration_id>', methods = ['GET', 'POST'])
@login_required
@current_user_own_integration
def generate_values(integration_id):
    form = AnalyticsBar()
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    # print(form)
    try:
        # Getting the data needed for the drop down menu
        list_of_column_names = ['DeviceCategory','OperatingSystem','RegionCity','URL','GoalsID']
        list_of_answers = []
        for i in range(len(list_of_column_names)):
            create_url = create_url_for_query('SELECT {smth} FROM db1.{crypto}_hits_{integration_id} GROUP BY {smth2};'.\
                            format(crypto= current_user.crypto, integration_id=integration.id,smth=list_of_column_names[i],smth2=list_of_column_names[i]))
            get_data = send_request_to_clickhouse(create_url).text
            list_of_answers.append(get_data)
            i += 1
        # Generating readable data for the drop down menu
        df = pd.DataFrame(list_of_answers, columns=['Values'])
        a = df.Values.str.split("\n")
        for idx,val in a.items():
            a[idx] = [v for v in val if v != '']
            a[idx].append('Не выбрано')

        # Adding choices to the forms
        form.DeviceCategory.choices = [(g,g) for g in a[0]]
        form.OperatingSystem.choices = [(g,g) for g in a[1]]
        form.RegionCity.choices = [(g,g) for g in a[2]]
        form.URL.choices = [(g,g) for g in a[3]]
        form.GoalsID.choices = [(g,g) for g in a[4]]
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
            word = 'WHERE'
            for i in dict_of_requests:
                if i in ('DeviceCategory', 'OperatingSystem', 'RegionCity'):
                    word = word + ' ' + i + ' IN (' + str(dict_of_requests[i]).strip('[]') + ') and'
                elif i in ('clause_visits'):
                    word = word[:-4]
                    word = word + ' and Date ' + str(dict_of_requests[i]).strip("'['']'")
                elif i in ('Date'):
                    word = word + ' ' + str(dict_of_requests[i]).strip('['']') + '    '
            word = word[:-4]
            #getting the answer from the db
            create_url = create_url_for_query('SELECT ClientID, URL FROM db1.{crypto}_hits_{integration_id} {smth};'.\
                                                format(crypto= current_user.crypto, integration_id=integration_id,smth=word))
            print(create_url)
            get_data = send_request_to_clickhouse(create_url).text

            #doing magic with the data
            file_from_string = StringIO(get_data)
            columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None)
            pprint(columns_df)

            #making json
            front_end_df= columns_df.astype(str)
            json_to_return = front_end_df.to_json(default_handler=str, orient='table', index=False)

            return json_to_return
        except Exception as err:
            print(err)
        return render_template('index.html')
    elif request.method == 'GET':
        print("last hui")
    return render_template('after_analytics.html')
