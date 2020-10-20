import requests
from ftplib import FTP
import ftplib


class GrConnector(object):
    gr_api_root = 'https://api.getresponse.com/v3/'
    ftp_host = 'ftp.getresponse360.com'

    def __init__(self,api_key, ftp_login, ftp_pass):
        self.headers = {'X-Auth-Token': f'api-key {api_key}'}
        self.ftp_login = ftp_login
        self.ftp_pass = ftp_pass

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

    def ftp_gr(self, url, file_buffer):
        ftp = FTP(host = self.ftp_host)
        login = ftp.login(self.ftp_login,self.ftp_pass)
        try:
            operation_response = ftp.storlines(f'STOR {url}', file_buffer)
            print(operation_response)
        except ftplib.error_perm as err:
            raise ConnectionRefusedError((f'Ошибка при попытке FTP контакта с GetResponse\n{err}'))
        ftp.quit()
