
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


def made_url_for_query(query):
    setup_already = Integration.query.filter_by(user_id=current_user.get_id()).first()
    host = setup_already.clickhouse_host
    db = setup_already.clickhouse_db
    return 'https://{host}:8443/?database={db}&query={query}'.format(
        host=host,
        db=db,
        query=query)

def request_clickhouse(url, headers, verify):
    return requests.get(
        url = url,
        headers=headers,
        verify=verify
        )

def goalId_count(el):
    return sum([len(eval(goals)) for goals in el])

def utm_source_handler(el):
    return ', '.join(set(el))

@bp.route('/metrika/<integration_id>', methods = ['POST','GET'])
@login_required
def metrika(integration_id):
    integration = Integration.query.filter_by(id=integration_id).first_or_404()
    if current_user != integration.user:
        abort(404)
    try:
        url_for_columns = made_url_for_query('DESC visits_all')
        url_for_visits_all_data = made_url_for_query('SELECT * FROM visits_all')
        certificate_path = 'app/YandexInternalRootCA.crt'
        auth = {
        'X-ClickHouse-User': integration.clickhouse_login,
        'X-ClickHouse-Key': integration.clickhouse_password
        }
    except:
        flash('Ошибки в настройках!')
        return render_template("error_settings.html")

    # get column names 1
    response_with_columns_names = request_clickhouse(url_for_columns, auth, certificate_path)
    file_from_string = StringIO(response_with_columns_names.text)
    columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, usecols=[0])
    list_of_column_names = columns_df[0].values

    # get table data and prepare it
    response_with_visits_all_data =request_clickhouse (url_for_visits_all_data, auth, certificate_path)
    file_from_string = StringIO(response_with_visits_all_data.text)
    visits_all_data_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', names=list_of_column_names, usecols=['ClientID','GoalsID', 'UTMSource','VisitID'])
    visits_all_data_df['UTMSource'].replace(np.nan, 'no-email', regex=True, inplace=True)

    # building max data frame
    max_df = visits_all_data_df.groupby(['ClientID','UTMSource']).agg({'GoalsID': [goalId_count], 'VisitID':['count']})
    max_df.columns =max_df.columns.droplevel(0)
    max_df.reset_index(inplace=True)
    unique_client_ids = max_df['ClientID'].unique()
    temp_dfs = []

    for client_id in unique_client_ids:
        temp_df = max_df[max_df['ClientID'] == client_id]
        max_no_email = temp_df[temp_df['UTMSource'] == 'no-email']
        max_email = temp_df[temp_df['UTMSource'] != 'no-email']
        goals_sum_total = temp_df['goalId_count'].sum()
        goals_email = max_email['goalId_count'].sum()
        visits_no_email = max_no_email['count'].sum()
        visits_email = max_email['count'].sum()

        temp_df = temp_df.groupby(['ClientID']).agg({'UTMSource':[utm_source_handler],'goalId_count':['sum']})
        temp_df.columns =temp_df.columns.droplevel(0)
        temp_df.reset_index(inplace=True)
        temp_df['Total visits'] = visits_no_email + visits_email
        temp_df['Visits with out email'] = visits_no_email
        temp_df['Visits with email'] = visits_email
        temp_df['Goals complited via email'] = goals_email
        temp_df.rename(columns={'utm_source_handler':'Client identities','sum':'Total goals complited'}, inplace=True)
        temp_dfs.append(temp_df)

    max_df = pd.concat(temp_dfs)
    max_df.reset_index(inplace=True, drop=True)

    max_df['Conversion (TG/TV)'] = (max_df['Total goals complited']/max_df['Total visits'])*100
    max_df['Conversion (TG/TV)'].replace(np.nan, 0, regex=True, inplace=True)
    max_df['Conversion (TG/TV)'] = max_df['Conversion (TG/TV)'].astype(int)

    max_df['Email visits share'] = (max_df['Visits with email']/max_df['Total visits'])*100
    max_df['Email visits share'].replace(np.nan, 0, regex=True, inplace=True)
    max_df['Email visits share'] =  max_df['Email visits share'].astype(int)

    max_df['NO-Email visits share'] = (max_df['Visits with out email']/max_df['Total visits'])*100
    max_df['NO-Email visits share'].replace(np.nan, 0, regex=True, inplace=True)
    max_df['NO-Email visits share'] =  max_df['NO-Email visits share'].astype(int)

    max_df['Email power proportion'] = (max_df['Goals complited via email']/max_df['Total goals complited'])*100
    max_df['Email power proportion'].replace(np.nan, 0, regex=True, inplace=True)
    max_df['Email power proportion'] =  max_df['Email power proportion'].astype(int)

    max_for_3graph = [ [max_row['Visits with email'],max_row['Conversion (TG/TV)']] for _, max_row in max_df[['Visits with email','Conversion (TG/TV)']].iterrows() ]

    max_no_email_2graph = [ [max_row['NO-Email visits share'],max_row['Conversion (TG/TV)']] for _, max_row in max_df[['NO-Email visits share','Conversion (TG/TV)']].iterrows() ] # 2 график - без email
    max_email_2graph = [ [max_row['Email visits share'],max_row['Conversion (TG/TV)']] for _, max_row in max_df[['Email visits share','Conversion (TG/TV)']].iterrows() ] # 2 график - с email

    max_no_email_1graph = [ [max_row['Visits with out email'],max_row['Conversion (TG/TV)']] for _, max_row in max_df[['Visits with out email','Conversion (TG/TV)']].iterrows() ] # 1 график - без email
    max_email_1graph = [ [max_row['Visits with email'],max_row['Conversion (TG/TV)']] for _, max_row in max_df[['Visits with email','Conversion (TG/TV)']].iterrows() ] # 1 график - с email

    front_end_df = max_df[['ClientID', 'Client identities', 'Total goals complited', 'Total visits', 'Visits with email','Goals complited via email', 'Conversion (TG/TV)', 'Email power proportion']]
    return render_template('metrika.html', table=front_end_df, titles=front_end_df.columns.values, graph_1=max_email_1graph, graph_1_no_email=max_no_email_1graph, graph_2=max_email_2graph, graph_2_no_email=max_no_email_2graph, graph_3=max_for_3graph)
