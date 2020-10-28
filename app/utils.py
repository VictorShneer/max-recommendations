"""
these functions
handle needs thats can appear in diffent places of the app
"""
import base64
import requests

def encode_this_string(string):
    byte_string = string.encode("utf-8")
    byte_encoded = base64.b64encode(byte_string)
    return byte_encoded.decode("utf-8")

def decode_this_string(sting):
    byte_string = sting.encode('utf-8')
    byte_decoded = base64.b64decode(byte_string)
    return byte_decoded.decode('utf-8')

def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def get_metrika_goals(metrika_key,counter_id):
    headers = {'Authorization':'OAuth {}'.format(metrika_key)}
    ROOT = 'https://api-metrika.yandex.net/'
    url = ROOT+'management/v1/counter/{}/goals'.format(counter_id)
    r = requests.get(url, headers=headers)
    return [(goal['id'],goal['name']) for goal in r.json()['goals']]

def generate_full_CH_table_name(db_name, table_name, integration_id):
    return f'{db_name}.{table_name}_{integration_id}'