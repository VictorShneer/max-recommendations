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
                return r
            else:
                raise ConnectionRefusedError((f'Ошибка при попытке контакта с GetResponse\n{r.text}'))
