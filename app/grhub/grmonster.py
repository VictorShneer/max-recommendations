import base64
import concurrent.futures
from pprint import pprint
from app.grhub.grutils import GrUtils

class GrMonster(GrUtils):
    hashed_email_custom_field_name = 'hash_email'


    def __init__(self, api_key, integration_id, user_id, callback_url):
        super().__init__(api_key)
        self.integration_id = integration_id
        self.user_id = user_id
        self.callback_url = callback_url

    def instantiate_contacts_with_hashed_email(self):
        if self.if_custom_field_exists(self.hashed_email_custom_field_name):
            raise Exception(f'Custom field name {self.hashed_email_custom_field_name} already in use!')
        else:
            return self.install_hash_email_for_every_contact()  # return list of responses for each usert request

    def if_custom_field_exists(self, custom_field_name):
        custom_fields = self.get_customs()
        return custom_field_name in [custom_field['name'] for custom_field in custom_fields.json()]

    def install_hash_email_for_every_contact(self):
        id_email_dic_list = self.get_id_email_dic_list()
        self.hash_email_custom_field_id = self.create_custom_field(name=self.hashed_email_custom_field_name).json()['customFieldId']
        raw_upsert_responses_list = self.upsert_every_email_with_hashed_email(id_email_dic_list)
        return raw_upsert_responses_list # return list of responses for each usert request

    def encode_this_string(self, string):
        contact_email_byte = string.encode("UTF-8")
        contact_email_byte_encoded = base64.b64encode(contact_email_byte)
        return contact_email_byte_encoded.decode("UTF-8")

    def set_callback_if_not_busy(self):
        # if ConnectionRefusedError then callback is free
        try:
            callback = self.get_callbacks()
            pprint(f'{callback.json()} already set PANIC')
        except ConnectionRefusedError as err:
            callback_identifier = '-'.join([str(self.integration_id), str(self.user_id)])
            callback_identifier_encoded = self.encode_this_string(callback_identifier)
            set_callback_response = self.set_callback(self.callback_url+callback_identifier_encoded,['subscribe'])
            print(set_callback_response)

    def upsert_every_email_with_hashed_email(self, id_email_dic_list):
        responses = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_contact = {\
                    executor.submit(\
                        self.upsert_custom_field, \
                        contact['contactId'], \
                        self.encode_this_string(contact['email'])\
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
