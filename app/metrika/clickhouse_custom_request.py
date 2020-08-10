import requests
from flask import current_app

def made_url_for_query(query, integration):
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
