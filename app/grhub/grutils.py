from app.grhub.grconnector import GrConnector
from ftplib import FTP
import ftplib
import math

class GrUtils(GrConnector):
    hash_email_custom_field_id = None
    ftp_host = 'ftp.getresponse360.pl'

    def __init__(self,api_key, ftp_login, ftp_pass):
        super().__init__(api_key)
        self.ftp_login = ftp_login
        self.ftp_pass = ftp_pass

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

    def ftp_gr(self, url, file_buffer):
        ftp = FTP(host = self.ftp_host)
        login = ftp.login(self.ftp_login,self.ftp_pass)
        try:
            operation_response = ftp.storlines(f'STOR {url}', file_buffer)
            print(operation_response)
            ftp.quit()
        except ftplib.error_perm as err:
            ftp.quit()
            raise ConnectionRefusedError((f'Ошибка при попытке FTP загрузки\n{err}'))

    def ftp_create_dir(self, dir_path):
        ftp_obj = FTP(host = self.ftp_host)
        login = ftp_obj.login(self.ftp_login,self.ftp_pass)
        ftpResponse = ftp_obj.mkd(dir_path);
        print(ftpResponse);    
        ftp_obj.quit()


    def ftp_list_files(self, target_dir):
        ftp_obj = FTP(host = self.ftp_host)
        login = ftp_obj.login(self.ftp_login,self.ftp_pass)
        ftp_obj.cwd(target_dir)
        dir_list = ftp_obj.nlst()
        ftp_obj.quit()
        return dir_list

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

    def get_search_contacts_contacts(self, json, per_page, page):
        return self.request_gr('post',f'search-contacts/contacts?perPage={per_page}&page={page}', json=json)

    def get_total_pages_count(self, url, per_page, json={}):
        r = self.request_gr('post', url, json=json)
        total_pages = r.headers['TotalPages']
        total_pages_in_per_page_respect_raw = int(total_pages)/per_page
        return math.ceil(total_pages_in_per_page_respect_raw)

    def post_contact_to_list(self, email, campaign_id):
        return self.request_gr('post', 'contacts/', \
                            json = {'email':email, 'campaign': {'campaignId':campaign_id}})


    def get_user_details(self):
        return self.request_gr('get', 'accounts/').json()

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

    def store_external_segment(self, url, file_buffer):
        self.ftp_gr(url, file_buffer)

    def upsert_hash_field_for_contact(self, contact_id, custom_field_value):
        r = self.request_gr('post', f'contacts/{contact_id}/custom-fields', \
                        json = {'customFieldValues':[{\
                                            'customFieldId':self.hash_email_custom_field_id,\
                                            'value':[custom_field_value] \
                                        }]\
                                })
        return r
