from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Integration
from app import db
from app.analytics import bp
from app.analytics.utils import current_user_own_integration, create_url_for_query, send_request_to_clickhouse
import traceback
from pprint import pprint
import pandas as pd


@bp.route('/analytics/<integration_id>', methods = ['GET'])
@login_required
@current_user_own_integration
def generate_values(integration_id):
    try:
        # Getting the data needed for the drop down menu
        list_of_column_names = ['DeviceCategory','OperatingSystem','RegionCity','URL']
        list_of_answers = []
        for i in range(len(list_of_column_names)):
            create_url = create_url_for_query('SELECT {smth} FROM db1.hits_georgefinal GROUP BY {smth2};'.format(smth=list_of_column_names[i],smth2=list_of_column_names[i]))
            get_data = send_request_to_clickhouse(create_url).text
            list_of_answers.append(get_data)
            i += 1
        # Generating readable data for the drop down menu
        df = pd.DataFrame(list_of_answers, columns=['Values'])
        a = df.Values.str.split("\n")

    except Exception as e:
        traceback.print_exc()
        flash('{} Ошибки в настройках интеграции!'.format(Integration.integration_name))
        return render_template('analytics.html')
    return render_template('analytics.html', list = a)
