"""
This is the core of the module inheritance structure
this class handle evere connection event
it can GET, POST, DELETE and handel conncetion errors
"""

import requests

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
                if int(r.headers['X-RateLimit-Remaining']) <= 5:
                    print(f'GR: I need a rest for {r.headers["X-RateLimit-Reset"]} seconds')
                return r
            else:
                raise ConnectionRefusedError((f'Ошибка при попытке контакта с GetResponse\n{r.text}'))



