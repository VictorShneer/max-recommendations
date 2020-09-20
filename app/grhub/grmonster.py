import base64
import concurrent.futures
import requests
from pprint import pprint


class GrConnector(object):
    gr_api_root = 'https://api.getresponse.com/v3/'

    def __init__(self,api_key):
        self.headers = {'X-Auth-Token': f'api-key {api_key}'}


    def request_gr(self, method ,url, json={}):
        action = getattr(requests, method, None)
        if action:
            r = action(self.gr_api_root+url, \
                       headers=self.headers, \
                       json = json)
            if r.ok:
                return r
            else:
                raise Exception((f'Ошибка при попытке контакта с GetResponse\n{r.text}'))

class GrUtils(GrConnector):
    hash_email_custom_field_id = None

    def __init__(self,api_key):
        super().__init__(api_key)

    def get_gr_campaigns(self):
        r = self.request_gr('get', 'campaigns?perPage=1000')
        return [(campaign['campaignId'],campaign['name']) for campaign in r.json()]

    def get_customs(self, filter=''):
        return self.request_gr('get', f'custom-fields?perPage=1000{filter}')

    def get_id_email_dic_list(self):
        raw_contacts_response = self.request_gr('get', 'contacts?page=1&fields=email&perPage=1000')
        amount_of_next_pages_in_get_contacts = raw_contacts_response.headers['TotalPages']
        id_email_dic_list = raw_contacts_response.json()
        while int(amount_of_next_pages_in_get_contacts) > 1:
            raw_contacts_response = self.request_gr('get', f'contacts?page={amount_of_next_pages_in_get_contacts}&fields=email&perPage=1000')
            id_email_dic_list.extend(raw_contacts_response.json())
            amount_of_next_pages_in_get_contacts -= 1
        return id_email_dic_list

    def create_custom_field(self, name):
        return self.request_gr('post', 'custom-fields', json={'name':name,\
                                                    'type':'text',\
                                                    'hidden':'true',\
                                                    'values':[]})
    def create_gr_campaign(self, campaing_name):
        r = self.request_gr('post', 'campaigns', \
                    json = {'name':campaing_name, \
                            "optinTypes": {
                                "email": "single", \
                                "api": "single", \
                                "import": "single", \
                                "webform": "single" \
                            }
                        }
                    )
        return r

    def upsert_custom_field(self, contact_id, custom_field_value):
        r = self.request_gr('post', f'contacts/{contact_id}/custom-fields', \
                        json = {'customFieldValues':[{\
                                            'customFieldId':self.hash_email_custom_field_id,\
                                            'value':[custom_field_value] \
                                        }]\
                                })
        return r
class GrMonster(GrUtils):
    hashed_email_custom_field_name = 'hash_email'

    def __init__(self, api_key):
        super().__init__(api_key)

    def instantiate_contacts_with_hashed_email(self):
        if self.if_custom_field_exists(self.hashed_email_custom_field_name):
            raise Exception(f'Custom field name {self.hashed_email_custom_field_name} already in use!')
        else:
            # return list of responses for each usert request
            return self.install_hash_email_for_every_contact()

    def if_custom_field_exists(self, custom_field_name):
        custom_fields = self.get_customs()
        return custom_field_name in [custom_field['name'] for custom_field in custom_fields.json()]

    def install_hash_email_for_every_contact(self):
        id_email_dic_list = self.get_id_email_dic_list()
        self.hash_email_custom_field_id = self.create_custom_field(name=self.hashed_email_custom_field_name).json()['customFieldId']
        raw_upsert_responses_list = self.upsert_every_email_with_hashed_email(id_email_dic_list)
        # return list of responses for each usert request
        return raw_upsert_responses_list

    def hash_this_string(self, string):
        contact_email_byte = string.encode("UTF-8")
        contact_email_byte_encoded = base64.b64encode(contact_email_byte)
        return contact_email_byte_encoded.decode("UTF-8")

    def upsert_every_email_with_hashed_email(self, id_email_dic_list):
        responses = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_contact = {\
                    executor.submit(\
                        self.upsert_custom_field, \
                        contact['contactId'], \
                        self.hash_this_string(contact['email'])\
                        ): \
                    contact['email'] \
                for contact in id_email_dic_list\
            }
            for future in concurrent.futures.as_completed(future_to_contact):
                contact = future_to_contact[future]
                try:
                    response_raw = future.result()
                    responses.append(response_raw)
                except Exception as exc:
                    pprint('%r generated an exception: %s' % (contact, exc))
        return responses
