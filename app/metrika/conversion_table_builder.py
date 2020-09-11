import pandas as pd
import numpy as np
from flask import current_app
import concurrent.futures
import numpy as np
from app.clickhousehub.clickhouse_custom_request import made_url_for_query,request_clickhouse
from app.clickhousehub.clickhouse import upload
from app.clickhousehub.clickhouse import get_clickhouse_data
from urllib.parse import urlparse, parse_qs
from io import StringIO
from app.clickhousehub.configs.config import CONFIG


CREATE_PRE_AGGR_TABLE_QUERY =  '''
    CREATE TABLE {table_name} (
        clientid UInt32,
        clientemail String,
        totalgoals UInt32,
        firsttimevisit Date,
        goalsall String,
        totalvisits UInt32,
        visitswithoutemail UInt32,
        visitswithemail UInt32,
        countgoalswithemail UInt32,
        goalswithemail String
    ) ENGINE = Log
'''

RENAME = {\
    'clientid':'ClientID',\
    'clientemail':'Client identities',\
    'totalgoals':'Total goals complited',\
    'totalvisits':'Total visits',\
    'visitswithoutemail':'Total Visits No Email',\
    'visitswithemail': 'Total Visits Email',\
    'countgoalswithemail':'Total goals with Email',\
    'goalswithemail':'Goals complited with email',\
    }


PROPERTY_TO_SQL_DIC = {'start_date':'''firsttimevisit >= '{res}' ''',\
                        'goals':'''position(goalsall, '{res}') != 0 '''}

def generate_grouped_columns_sql(restrictions):
    return ''


def generate_where_statement(restrictions):
    where_clause = ''
    # delete empty restrictions, for the cases when you have no goals to filter with
    restrictions_not_empty = {k: v for k, v in restrictions.items() if v != ['']}
    for key,values in restrictions_not_empty.items():
        # every where state should be in (   )
        where_clause += '('
        # every where state come as array
        for i,value in enumerate(values):
            # every where state has its own format in PROPERTY_TO_SQL_DIC
            state = PROPERTY_TO_SQL_DIC[key].format(res=value)
            # if it is last restrition in array we don't put OR
            if i != len(values)-1:
                where_clause += (state + ' OR ')
            else:
                where_clause+=state
        # close ) and add AND for the new WHERE state
        where_clause += ')'
        where_clause += ' AND '
    # delete last AND
    where_clause = where_clause[:-4]
    print(where_clause)
    return where_clause


def build_conversion_df(visits_pre_aggr_df):
    ## group that shit
    max_df = visits_pre_aggr_df.groupby(['clientemail'])\
        .agg({'clientid':leave_last_client_id,\
        'totalgoals':'sum',\
        'totalvisits':'sum',\
        'visitswithoutemail':'sum',\
        'visitswithemail' :'sum',\
        'countgoalswithemail':'sum',\
        'goalswithemail':goalsId_handler,\
        'goalsall':goalsId_handler,\
        'firsttimevisit':min
        })
    # max_df = visits_pre_aggr_df.groupby(['Client identities'])\
    #     .agg({'ClientID':leave_last_client_id,\
    #     'Total goals complited':'sum',
    #     'Total visits':'sum',
    #     'Visits with out email':'sum',
    #     'Visits with email' :'sum',
    #     'Goals complited via email':'sum'
    #     })
    max_df.reset_index(inplace=True, drop=False)
    max_df.rename(columns=RENAME, inplace=True)
    #calculating metrics
    max_df['Conversion (TG/TV)'] = devide_columns_handler(max_df,'Total goals complited','Total visits')
    max_df['Email visits share'] = devide_columns_handler(max_df,'Total Visits Email','Total visits')
    max_df['NO-Email visits share'] = devide_columns_handler(max_df,'Total Visits No Email','Total visits')
    max_df['Email power proportion'] = devide_columns_handler(max_df,'Total goals with Email','Total goals complited')
    return max_df

def request_visits_all_df(crypto, integration_id):
    clickhouse_table_name = '{}_raw_{}'.format('visits', integration_id)

    url_for_columns = made_url_for_query('DESC {}'.format(clickhouse_table_name), crypto)
    url_for_visits_all_data = made_url_for_query("SELECT * FROM {}".format(clickhouse_table_name), crypto)
    current_app.logger.info('### request_clickhouse start urls: {}\n{}'.format(url_for_columns,url_for_visits_all_data))
    # get column names 1
    response_with_columns_names = request_clickhouse(url_for_columns, current_app.config['AUTH'], current_app.config['CERTIFICATE_PATH'])
    # get table data and prepare it
    response_with_visits_all_data =request_clickhouse(url_for_visits_all_data, current_app.config['AUTH'], current_app.config['CERTIFICATE_PATH'])
    if any([\
            response_with_columns_names.status_code != 200,\
            response_with_visits_all_data.status_code !=200\
            ]):
        current_app.logger.error('{} {} Ошибки в запросе или в настройках итеграции!'.format(crypto, integration_id))
        raise RuntimeError("request_visits_all_df ### Something bad happened")

    current_app.logger.info('### request_clickhouse done!\ncolumns: {}\n data: {}'.format(response_with_columns_names, response_with_visits_all_data))
    # prepare it column names
    file_from_string = StringIO(response_with_columns_names.text)
    columns_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', header=None, usecols=[0])
    list_of_column_names = columns_df[0].values
    # finishing visits all table
    file_from_string = StringIO(response_with_visits_all_data.text)
    current_app.logger.info(list_of_column_names)
    try:
        visits_all_data_df = pd.read_csv(file_from_string,sep='\t',lineterminator='\n', names=list_of_column_names, usecols=['ClientID','GoalsID', 'UTMSource','VisitID','StartURL','Date'])
    except Exception as err:
        current_app.logger.info('### building dataframe from string EXCEPTION {}'.format(err))
        raise RuntimeError("building dataframe from string ### Something bad happened")
    return visits_all_data_df



def make_clickhouse_pre_aggr_visits(token, counter_id,crypto,id, regular_load=False):
    current_app.logger.info("START cremake_clickhouse_pre_aggr_visitsate pre aggr templates")
    visits_raw_data_df = request_visits_all_df(crypto,id)
    current_app.logger.info("SUCCESS request_visits_all_df")
    visits_pre_aggr = build_pre_aggr_conversion_df(visits_raw_data_df)
    table_name = '{db_name}.visits_{integration_id}_pre_aggr'.format(db_name=crypto,integration_id=id)
    if not regular_load:
        ### creating pre aggr table
        current_app.logger.info("create pre aggr templates")
        query = CREATE_PRE_AGGR_TABLE_QUERY.format(\
            table_name=table_name\
        )
        get_clickhouse_data(query)
    content = visits_pre_aggr.to_csv(path_or_buf=None, sep='\t', index=False)
    upload(table_name, content)

def goalId_count(el):
    return sum((len(eval(goals)) for goals in el))

def hash_group_handler(el):
    set_el = set(el)
    if len(set_el)>1:
        set_el.discard(-1)
        # if visit has different emails
        # we want mark it to ignore futher
        if len(set_el) > 1:
            return np.nan
    return str(set_el.pop())

#
def devide_columns_handler(df,numerator_column_name,denominator_column_name):
    result_column = (df[numerator_column_name]/df[denominator_column_name])*100
    result_column.replace(np.nan, 0, regex=True, inplace=True)
    return result_column.astype(int)

def leave_last_client_id(el):
    return list(el)[-1]

def make_utms_unique(el):
    # # OPTIMIZE:
    aggregated = []
    for utm_groups in el.values:
        aggregated.append(utm_groups)
    return ', '.join(set(aggregated))

def start_url_to_hash(url):
    parsed = urlparse(url)
    url_params = parse_qs(parsed.query)
    if 'mxm' in url_params.keys():
        # print('mxm', url_params['mxm'][0])
        return url_params['mxm'][0]
    else:
        # print('-1')
        ## OPTIMIZE:
        return -1

def goalsId_handler(el):
    all_goals = []
    try:
        [all_goals.extend(eval(str(goals))) for goals in el]
    except Exception as err:
        print('here it is',err, type(el), el)
    return str(all_goals)



def build_pre_aggr_conversion_df(visits_all_data_df):
    current_app.logger.info('### visits_all_data_df start')
    # replace StartURL with hash
    visits_all_data_df['hash'] = visits_all_data_df['StartURL'].apply(start_url_to_hash)
    # make a copy of GolsID to save ids for ROI filter
    visits_all_data_df['GoalsID_2'] = visits_all_data_df['GoalsID']
    # First raw grouping. Result: not distinct ClientID column values
    max_df = visits_all_data_df.groupby(['ClientID','hash'])\
        .agg({'GoalsID':goalId_count, 'VisitID':'count',"GoalsID_2":goalsId_handler, 'Date':'min'})
    max_df.reset_index(inplace=True)
    # unique ClientID extraction
    unique_client_ids = max_df['ClientID'].unique()
    # after this loop we got ClientID column with distinct values
    temp_dfs = []
    current_app.logger.info('### visits_all_data_df unique_client_ids loop start {} --->>>'.format(len(unique_client_ids)))

    # # Handle a single ClientID chunk and return single row ClientID df with ROI stats
    #
    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(current_app.config['MAX_WORKERS'])) as executor:
        # Start the load operations and mark each future with its URL
        future_to_url = [executor.submit(handle_unique_clientid_chunk, max_df[max_df['ClientID'] == unique_clientid]) for unique_clientid in unique_client_ids]
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                data = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (future, exc))
            else:
                # print('%r clientId result is \n %s' % (future, data.to_string()))
                temp_dfs.append(data)

    current_app.logger.info('### visits_all_data_df unique_client_ids loop finish <<<<----')
    #contatenating unique ClientID row into DataFrame
    max_df = pd.concat(temp_dfs)
    current_app.logger.info('### len of result {}'.format(len(max_df)))
    max_df.dropna(inplace=True)
    current_app.logger.info('### DONE! len of not none result {}'.format(len(max_df)))

    return max_df



def handle_unique_clientid_chunk(temp_df):
    #calculation metrics for result row
    max_email = temp_df[temp_df['hash'] != -1]
    goals_email_count = max_email['GoalsID'].sum()
    goals_email = goalsId_handler(max_email['GoalsID_2'].values)
    max_no_email = temp_df[temp_df['hash'] == -1]
    visits_no_email = max_no_email['VisitID'].sum()
    visits_email = max_email['VisitID'].sum()
    # for every unique ClientID we group rows that belong to it
    temp_df = temp_df.groupby(['ClientID'])\
        .agg({'hash':hash_group_handler,\
                'GoalsID':'sum',\
                'Date':'min',\
                'GoalsID_2':goalsId_handler})
    temp_df.reset_index(inplace=True)
    #make anons unique
    # name -1 to 'no-email'
    temp_df.loc[temp_df['hash'] == '-1', 'hash'] = 'no-email' + str(temp_df['ClientID'].values[0])

    #assign metricts for result row
    temp_df['Total visits'] = visits_no_email + visits_email
    temp_df['Visits with out email'] = visits_no_email
    temp_df['Visits with email'] = visits_email
    temp_df['Count goals complited with email'] = goals_email_count
    temp_df['Goals complited with email'] = goals_email
    #prettyfing column names
    ## TODO:  turn this useless shit off
    temp_df.rename(columns={'hash':'Client identities',\
        'GoalsID':'Total goals complited',\
        'GoalsID_2':'Goals complited list'},\
        inplace=True)
    return temp_df
