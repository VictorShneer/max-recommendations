import concurrent.futures
from pprint import pprint
from app.grhub.grutils import GrUtils
from app.utils import encode_this_string
import pandas as pd
from pprint import pprint
import io

class GrMonster(GrUtils):
    hashed_email_custom_field_name = 'hash_metrika'
    big_enough_newsletter = 0
    # TODO default value for callback_url
    def __init__(self, api_key, callback_url = '', ftp_login = '', ftp_pass = ''):
        super().__init__(api_key,ftp_login,ftp_pass)
        self.callback_url = callback_url

    def get_broadcast_messages_since_date_subject_df(self, since_date):
        messages_raw_response = self.get_messages()
        big_enough_since_array_dic = [\
                        {'send_on':newsletter['sendOn'].split('T')[0],\
                        'subject':newsletter['subject']} \
                        for newsletter in messages_raw_response.json() \
                        if newsletter['sendOn'] > since_date and \
                        newsletter['type'] == 'broadcast' and \
                        int(newsletter['sendMetrics']['sent'])>self.big_enough_newsletter\
                        ]
        messages_df = pd.DataFrame(big_enough_since_array_dic)
        return messages_df

    def get_user_email(self):
        try: 
            return self.get_user_details()['email']
        except ConnectionRefusedError as err:
            print('Unable to get user email',err)

    #legacy
    def instantiate_contacts_with_hashed_email(self):
        if self.if_custom_field_exists(self.hashed_email_custom_field_name):
            raise KeyError(f'Custom field name {self.hashed_email_custom_field_name} already in use!')
        else:
            return self.install_hash_email_for_every_contact()  # return list of responses for each usert request

    def if_custom_field_exists(self, custom_field_name):
        custom_fields = self.get_customs()
        return custom_field_name in [custom_field['name'] for custom_field in custom_fields.json()]

    def prepare_GR_account(self):
        if self.if_custom_field_exists(self.hashed_email_custom_field_name):
            raise KeyError(f'Custom field name {self.hashed_email_custom_field_name} already in use!')
        else:
            self.hash_email_custom_field_id = self.create_custom_field(name=self.hashed_email_custom_field_name).json()['customFieldId']
            return self.hash_email_custom_field_id
    #legacy
    def install_hash_email_for_every_contact(self):
        id_email_dic_list = self.get_id_email_dic_list()
        self.hash_email_custom_field_id = self.create_custom_field(name=self.hashed_email_custom_field_name).json()['customFieldId']
        raw_upsert_responses_list = self.upsert_every_email_with_hashed_email(id_email_dic_list)
        return raw_upsert_responses_list # return list of responses for each usert request

    def set_callback_if_not_busy(self):
        # if ConnectionRefusedError then callback is free
        try:
            callback = self.get_callbacks()
            pprint(f'{callback.json()} already set PANIC')
            raise KeyError(f'Callback for this account is busy! PANIC')
        except ConnectionRefusedError as err:
            set_callback_response = self.set_callback(self.callback_url,['subscribe'])
            return set_callback_response

    def set_hash_email_custom_field_id(self):
        for custom in self.get_customs().json():
            if custom['name']==self.hashed_email_custom_field_name:
                self.hash_email_custom_field_id = custom['customFieldId']

    def store_external_segment_from_list(self, search_contacts_list, external_name):
        #data frame
        df = pd.DataFrame(search_contacts_list, columns=[external_name])
        rec = df.to_string(index=False)
        df_bytes = rec.encode('utf-8')
        # text buffer
        # set buffer start point at the begining
        s_buf = io.BytesIO(df_bytes)
        s_buf.seek(0)
        url = "/sync_external_segments/insert/" + self.get_user_email() + ".csv"
        self.store_external_segment(url, s_buf)

    def upsert_every_email_with_hashed_email(self, id_email_dic_list):
        responses = []
        print('Nubmer of contacts to init')
        print(len(id_email_dic_list))
        print('Usually it takes 0.25 sec per contact')
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_contact = {\
                    executor.submit(\
                        self.upsert_hash_field_for_contact, \
                        contact['contactId'], \
                        encode_this_string(contact['email'])\
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
