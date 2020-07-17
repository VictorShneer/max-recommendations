import requests


def made_url_for_query(query, integration):
    host = integration.clickhouse_host
    db = integration.clickhouse_db

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
