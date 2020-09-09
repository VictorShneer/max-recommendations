import time
import jwt
import requests
from flask import current_app

CH_HEADERS = {'Authorization': '''Bearer '''}

BODY_GRANT = {
  "permission": {
    "databaseName": ''
  }
}

BODY_CREATE_DB = {
  "databaseSpec": {
    "name": ''
  }
}

PATH_GRANT =       '''users/{userName}:grantPermission'''
PATH_CREATE_DB =   '''databases'''

CH_API_ROOT =      '''https://mdb.api.cloud.yandex.net/managed-clickhouse/v1/clusters/{clusterId}/'''
YC_OPERATION_URL = '''https://operation.api.cloud.yandex.net/operations/{operation_id}'''
CH_CLUSTER_ID = "c9q7kkb9jlvtk0jjtk07"


def request_iam():
    service_account_id = current_app.config['SERVICE_ID']
    key_id = current_app.config['KEY_IDENTIFIER'] # The ID of the Key resource belonging to the service account.

    with current_app.open_resource('clickhousehub/privatk') as private:
      private_key = private.read() # Reading the private key from the file.

    now = int(time.time())
    payload = {
            'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            'iss': service_account_id,
            'iat': now,
            'exp': now + 360}

    # JWT generation.
    encoded_token = jwt.encode(
        payload,
        private_key,
        algorithm='PS256',
        headers={'kid': key_id})


    r = requests.post('https://iam.api.cloud.yandex.net/iam/v1/tokens', \
                        headers={'Content-Type': 'application/json'}, \
                        json = {"jwt": encoded_token.decode()})
    if r.status_code == 200:
        current_app.logger.info('IAM OK!')
        CH_HEADERS['Authorization'] += r.json()['iamToken']
        return True
    else:
        current_app.logger.info('IAM NOT OK! PANIC!')
        return False

def is_operation_done(operation_id):
    is_done = False
    enough = 20
    while not is_done and enough>=0:
        current_app.logger.info('wait {}'.format(enough))
        time.sleep(1)
        r=requests.get(YC_OPERATION_URL.format(operation_id=operation_id),\
                                                headers=CH_HEADERS)
        is_done = r.json()['done']
        enough-=1
    if is_done:
        current_app.logger.info('operation done!')
        return True
    else:
        current_app.logger.info('opration failed!')
        return False

def give_user_grant(user_name, db_name):
    BODY_GRANT['permission']['databaseName'] = db_name
    r = requests.post(CH_API_ROOT.format(clusterId=CH_CLUSTER_ID) + \
                        PATH_GRANT.format(userName=user_name), \
                        headers=CH_HEADERS, \
                        json=BODY_GRANT \
                        )

    if r.status_code == 200:
        current_app.logger.info('Task to GRANT {} for {} is set'.format(db_name, user_name))
        op_id = r.json()['id']
        if not is_operation_done(op_id):
            raise Exception
    else:
        print(r.status_code)

def create_ch_db(db_name):
    current_app.logger.info('Creating db START')
    BODY_CREATE_DB['databaseSpec']['name'] = db_name
    r = requests.post(CH_API_ROOT.format(clusterId=CH_CLUSTER_ID) + \
                        PATH_CREATE_DB, \
                        headers=CH_HEADERS, \
                        json=BODY_CREATE_DB \
                        )
    if r.status_code == 200:
        current_app.logger.info('Task to db create set SUCCESS')
        op_id = r.json()['id']
        if not is_operation_done(op_id):
            raise Exception('Operation not done for a long time')
    else:
        current_app.logger.info(r.headers)
        current_app.logger.info(r.text)
        raise Exception('Status code not 200')

def made_url_for_query(query):
    host = current_app.config['CLICKHOUSE_HOST']
    db = current_app.config['CLICKHOUSE_DB']

    return 'https://{host}:8443/?database={db}&query={query}'.format(
        host=host,
        db=db,
        query=query)

def request_clickhouse(url, headers, verify):
    r = requests.get(
        url = url,
        headers=headers,
        verify=verify
        )
    return r
