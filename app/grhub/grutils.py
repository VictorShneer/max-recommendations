from app.grhub.grconnector import GrConnector

class GrUtils(GrConnector):
    hash_email_custom_field_id = None

    def __init__(self,api_key):
        super().__init__(api_key)

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

    def disable_callback(self):
        return self.request_gr('delete', 'accounts/callbacks')

    def get_callbacks(self):
        return self.request_gr('get', 'accounts/callbacks')

    def get_gr_campaigns(self):
        r = self.request_gr('get', 'campaigns?perPage=1000')
        return [(campaign['campaignId'],campaign['name']) for campaign in r.json()]

    def get_customs(self, filter=''):
        return self.request_gr('get', f'custom-fields?perPage=1000{filter}')

    def get_id_email_dic_list(self):
        raw_contacts_response = self.request_gr('get', 'contacts?page=1&fields=email&perPage=1000')
        amount_of_next_pages_in_get_contacts = int(raw_contacts_response.headers['TotalPages'])
        id_email_dic_list = raw_contacts_response.json()
        while amount_of_next_pages_in_get_contacts > 1:
            raw_contacts_response = self.request_gr('get', f'contacts?page={amount_of_next_pages_in_get_contacts}&fields=email&perPage=1000')
            id_email_dic_list.extend(raw_contacts_response.json())
            amount_of_next_pages_in_get_contacts -= 1
        return id_email_dic_list

    def get_messages(self):
        return self.request_gr('get', 'newsletters?perPage=1000')

    def post_contact_to_list(self, email, campaign_id):
        return self.request_gr('post', 'contacts/')
        r = requests.post('https://api.getresponse.com/v3/contacts', \
                            json = {'email':email, 'campaign': {'campaignId':campaign_id}})
        return r

    def set_callback(self, url, actions):
        actions_json = {\
            "open": False,\
            "click": False,\
            "goal": False,\
            "subscribe": False,\
            "unsubscribe": False,\
            "survey": False\
        }
        for action in actions:
            actions_json[action] = True
        return self.request_gr('post','accounts/callbacks', json = {'url':url,'actions':actions_json})

    def upsert_hash_field_for_contact(self, contact_id, custom_field_value):
        r = self.request_gr('post', f'contacts/{contact_id}/custom-fields', \
                        json = {'customFieldValues':[{\
                                            'customFieldId':self.hash_email_custom_field_id,\
                                            'value':[custom_field_value] \
                                        }]\
                                })
        return r
