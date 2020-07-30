import requests
import datetime
from bs4 import BeautifulSoup
import re

def get_newsletters_names(key):
    newsletters_types = ['draft','automation','broadcast','splittest']
    HEADERS = {"X-Auth-Token": "api-key {}".format(key)}
    urls = ['https://api3.getresponse360.com/v3/newsletters?'+\
        'fields=name,type,createdOn&'+\
        'sort[createdOn]=DESC&'+\
        'perPage=10&'+\
        'query[type]={}'.format(type) for type in newsletters_types]

    rs = [requests.get(url, headers=HEADERS) for url in urls]
    if(any([r.status_code != 200 for r in rs])):
        return {'u':'что-то пошло не так'}
    jsons_list = [newsletter for type in rs for newsletter in type.json()]
    jsons_dict = {news['createdOn']:news for news in jsons_list}
    return {\
        idx:{\
            'data':'{} ({})'.format(jsons_dict[n]['name'],jsons_dict[n]['type']),\
            'meta': jsons_dict[n]['newsletterId']\
            }\
                for idx,n in enumerate(sorted(jsons_dict.keys(),reverse=True))}

def get_newsletters_links_for_newsletterId(key, newsletterId):
    HEADERS = {"X-Auth-Token": "api-key {}".format(key)}
    url = 'https://api3.getresponse360.com/v3/newsletters/{}?fields=content'.format(newsletterId)
    r = requests.get(url, headers=HEADERS)
    newsletter_content= r.json()['content']
    newsletter_html = newsletter_content['html']
    return {'links':parse_links_from_content(newsletter_html)}

def parse_links_from_content(content):
    urls = set()
    soup = BeautifulSoup(content,"lxml");
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
        # href empty tag
            continue
        url = re.search(r'`(.*?)`', href)
        if url:
            urls.add(url.group(1))

    return '\n'.join(urls)

# u0bwk7n5i3u9w2g2hndz8yn346x361g0
