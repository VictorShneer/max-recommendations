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
            create_url = create_url_for_query('SELECT {smth} FROM db1.hits_georgefinal GROUP BY {smth2};'.format(smth=list_of_column_names[i],smth2=list_of_column_names[i]))
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
        form.device_category.choices = [(g,g) for g in a[0]]
        form.operating_system.choices = [(g,g) for g in a[1]]
        form.region_city.choices = [(g,g) for g in a[2]]
        form.url.choices = [(g,g) for g in a[3]]
        form.goals_id.choices = [(g,g) for g in a[4]]
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
            print(request.form['operating_system'])
        except Exception as err:
            pass
        return render_template('index.html')
    elif request.method == 'GET':
        print("last hui")
    return render_template('after_analytics.html')
