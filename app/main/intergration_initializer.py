from flask import app
from app.clickhousehub.metrica_logs_api import handle_integration_tables
def create_integration_tables(crypto, id):
    params = ['-source=hits', '-mode=history']
    handle_integration_tables(crypto, params)
    params = ['-source=visits', '-mode=history']
    handle_integration_tables(crypto, params)

# python metrica_logs_api.py -mode history -source hits

# python metrica_logs_api.py -mode history -source visits
