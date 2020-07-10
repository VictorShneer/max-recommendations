import requests
from flask import current_app

ROOT = 'https://api3.getresponse360.com/v3'


def send_transac(json):
    url = ROOT + '/transactional-emails'
    headers = {"X-Domain" : "test.getresponseservices.ru", "X-Auth-Token":"api-key {}".format(current_app.config['KEY'])}
    r = requests.post(url, headers=headers, json=json)
    print(r,'\n',r.json())
    try:
        get_transac(r.json()['transactionalEmailId'])
    except:
    	print('lol')

def get_from_field():
    url = ROOT + '/from-fields'
    headers = {"X-Domain" : "test.getresponseservices.ru","X-Auth-Token":"api-key {}".format(current_app._get_current_object().config['KEY'])}
    r = requests.get(url, headers=headers)
    print(r,'\n',r.json())
    return r.json()[0]['fromFieldId']


def get_transac(id):
    headers = {"X-Domain" : "test.getresponseservices.ru","X-Auth-Token":"api-key {}".format(current_app._get_current_object().config['KEY'])}
    path = "/transactional-emails/{}".format(id)
    r = requests.get(ROOT+path, headers=headers)
    print(r,'\n',r.json())

def send_email(subject, sender, recipients, text_body, html_body):
    json_dic = {"fromField":{"fromFieldId":get_from_field()},\
   "subject":'{}'.format(subject),\
   "content":{"plain":text_body,"html":html_body},\
   "recipients":{"to":{"email":recipients[0]}}}

    send_transac(json_dic)
