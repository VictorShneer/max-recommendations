import requests

def get_newsletters_names(key):
    HEADERS = {"X-Auth-Token": "api-key {}".format(key)}
    url = 'https://api3.getresponse360.com/v3/newsletters?fields=name'
    r = requests.get(url, headers=HEADERS)
    if(r.status_code != 200):
        return {'u':'f'}
    return {n['newsletterId']:n['name'] for n in r.json()}
# u0bwk7n5i3u9w2g2hndz8yn346x361g0
