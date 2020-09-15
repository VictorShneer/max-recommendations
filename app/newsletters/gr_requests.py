import requests
import datetime
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse,parse_qsl,urlencode,urlunparse

def wrap_links(links):
    params = {"mxm":"[[hash_metrika]]"}
    w_links = []
    for url in links:
        url_parse = urlparse(url)
        query = url_parse.query
        url_dict = dict(parse_qsl(query))
        url_dict.update(params)
        url_new_query = urlencode(url_dict)
        url_parse = url_parse._replace(query=url_new_query)
        new_url = urlunparse(url_parse)
        w_links.append(new_url)
    return {link : w_link for link,w_link in zip(links,w_links)}


def replace_link_in_content(content, links):
    wrapped_links_dic = wrap_links(links)
    soup = BeautifulSoup(content['html'],"lxml");
    for a in soup.findAll('a'):
        for link,w_link in wrapped_links_dic.items():
            if link in a['href']:
                a['href'] = a['href'].replace(link, w_link)
                break
    return str(soup)

def gr_post_wrapped_newsletter(key, newsletter_id, links):
    HEADERS = {"X-Auth-Token": "api-key {}".format(key)}
    url = 'https://api.getresponse.com/v3/newsletters/{}'.format(newsletter_id)
    r = requests.get(url, headers=HEADERS)
    newsletter_content= r.json()['content']
    wrapped_html = replace_link_in_content(newsletter_content, links)
    url = 'https://api.getresponse.com/v3/newsletters/'
    json = {\
                'content':{'html':wrapped_html},\
                'name':r.json()['name']+' wrapped', \
                'type': 'draft', \
                'subject': r.json()['subject'], \
                'fromField': r.json()['fromField'], \
                'replyTo': r.json()['replyTo'], \
                'campaign': r.json()['campaign'], \
                'sendSettings': r.json()['sendSettings'],
                'editor': r.json()['editor'] \
    }
    r = requests.post(url, headers=HEADERS, json=json)
    if r.status_code != 201:
        print(r.text)
        raise Exception('Opps! Post wrapped newsletter failed')


def get_newsletters_names(key):
    newsletters_types = ['draft','automation','broadcast','splittest']
    HEADERS = {"X-Auth-Token": "api-key {}".format(key)}
    urls = ['https://api.getresponse.com/v3/newsletters?'+\
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
    url = 'https://api.getresponse.com/v3/newsletters/{}?fields=content'.format(newsletterId)
    r = requests.get(url, headers=HEADERS)
    newsletter_content= r.json()['content']
    newsletter_html = newsletter_content['html']
    return {link:link for link in parse_links_from_content(newsletter_html)}

def parse_links_from_content(content):
    urls = set()
    soup = BeautifulSoup(content,"lxml");
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
        # href empty tag
            continue
        url = re.search(r'http[\w:/.\[\]=?&]*', href)
        if url:
            urls.add(url.group(0))

    return urls

# u0bwk7n5i3u9w2g2hndz8yn346x361g0
