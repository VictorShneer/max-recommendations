
from io import StringIO
import ast
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
import pandas as pd
from app.models import User, Integration
from app import db
from app.metrika import bp
from app.metrika.clickhouse import made_url_for_query,request_clickhouse
from app.metrika.conversion_table_builder import build_conversion_df



@bp.route('/metrika/<integration_id>', methods = ['POST','GET'])
@login_required
def metrika(integration_id):
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if current_user != integration.user:
        abort(404)
    try:
        url_for_columns = made_url_for_query('DESC visits_all', integration)
        url_for_visits_all_data = made_url_for_query('SELECT * FROM visits_all',integration)
        certificate_path = 'app/YandexInternalRootCA.crt'
        auth = {
        'X-ClickHouse-User': integration.clickhouse_login,
        'X-ClickHouse-Key': integration.clickhouse_password
        }
        # get column names 1
        response_with_columns_names = request_clickhouse(url_for_columns, auth, certificate_path)
        # get table data and prepare it
        response_with_visits_all_data =request_clickhouse (url_for_visits_all_data, auth, certificate_path)
    except:
        flash('{} Ошибки в настройках итеграции!'.format(integration.integration_name))
        return redirect(url_for('main.user_integrations'))

    # prepare it column names
    file_from_string = StringIO(response_with_columns_names.text)
    columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, usecols=[0])
    list_of_column_names = columns_df[0].values
    # finishing visits all table
    file_from_string = StringIO(response_with_visits_all_data.text)
    visits_all_data_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', names=list_of_column_names, usecols=['ClientID','Date','GoalsID', 'UTMSource','VisitID'])
    # building max data frame
    max_df = build_conversion_df(visits_all_data_df)

    max_no_email_1graph = [ [max_row['Visits with out email'],max_row['Conversion (TG/TV)']] for _, max_row in max_df[['Visits with out email','Conversion (TG/TV)']].iterrows() ] # 1 график - без email
    max_email_1graph = [ [max_row['Visits with email'],max_row['Conversion (TG/TV)']] for _, max_row in max_df[['Visits with email','Conversion (TG/TV)']].iterrows() ] # 1 график - с email

    conv_email_sum = 0
    conv_no_email_sum = 0
    for _, max_row in max_df[['Visits with email','Conversion (TG/TV)']].iterrows():
        if max_row[0] == 0:
            conv_no_email_sum = conv_no_email_sum + max_row[1]
        else:
            conv_email_sum = conv_email_sum + max_row[1]
    print(conv_email_sum)
    print(conv_no_email_sum)




    front_end_df = max_df[['ClientID', 'Client identities', 'Total goals complited', 'Total visits', 'Visits with email','Goals complited via email', 'Conversion (TG/TV)', 'Email power proportion']]
    front_end_df= front_end_df.astype(str)
    # front_end_df.to_json(path_or_buf='~/Documents/metrika.json', default_handler=str, orient='table')
    return render_template('metrika.html', table=front_end_df, titles=front_end_df.columns.values, graph_1=max_email_1graph, graph_1_no_email=max_no_email_1graph, conv_email_sum=conv_email_sum, conv_no_email_sum=conv_no_email_sum)
