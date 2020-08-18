import json
import requests
import base64

def add_custom_field(contact_email,contact_id, custom_field_id):
    domain = "https://api3.getresponse360.com/v3"
    headers = {
      'X-Auth-Token': 'api-key walmu0bwal02klnvetji4x7vlix15y74', #TODO здесь должен вставляться api-ключ в gr клиента
      'Content-Type': 'application/json'
    }
    url = domain+'/contacts/'+contact_id+'/custom-fields'
    print(url)

    #создаем хэш email-а
    contact_email_byte = contact_email.encode("UTF-8")
    contact_email_byte_encoded = base64.b64encode(contact_email_byte)
    contact_email_encoded = contact_email_byte_encoded.decode("UTF-8")

    payload_add = '{\"customFieldValues\": [{\"customFieldId\": \"'+custom_field_id+'\",\"value\": [\"'+contact_email_encoded+'\"]}]}'
    response_add = requests.request("POST", url, headers=headers, data = payload_add)
    print(response_add.text.encode('utf8'))
