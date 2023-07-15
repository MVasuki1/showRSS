#!/usr/bin/python3
import subprocess
import requests
import re
import logging
import json
import collections
from lxml import etree
import lxml.html
from io import StringIO
import sys
import yaml
import os
from snowfl_parser import Snowfl
import urllib.parse
requests.adapters.DEFAULT_RETRIES = 5
logging.basicConfig(level=logging.DEBUG)
nyaa_session = requests.Session()
tgx_session = requests.Session()
nyaa_headers = headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'sec-ch-ua': '"Chromium";v="113", "Not-A.Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (X11; CrOS aarch64 13597.84.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5672.95 Safari/537.36',
}

def snowfl_parser(search, uniq_regex=None, *args, **kwargs):
    search_term = urllib.parse.quote_plus(search)
    snowfl = Snowfl()
    resp = snowfl.search(search_term)
    resp = sorted(resp, key=lambda x: x['seeds'], reverse=True)
    episodes_conf = []
    uniq_ep = {}
    for episode in resp:
        name = episode['name']
        torrent_link = episode['link']
        size = episode['size']
        add_time = episode['age']

        if uniq_regex is None:
            uniq_regex = r'E\d\d'
        ep_no_match = re.search(uniq_regex, name)
        if not ep_no_match:
            continue
        ep_no = ep_no_match.group()
        if ep_no in uniq_ep:
            continue
        uniq_ep[ep_no] = name
        ep_row = {
            'title': name,
            'link': torrent_link,
            'size': size,
            'pubDate': add_time
        }
        episodes_conf.append(ep_row)
        logging.info('Fetch Episode')
        logging.info(ep_row)
    
    # Only fetch last 36 episodes for any show
    return sorted(episodes_conf, key=lambda x: x['title'],reverse=True)[:36]

def nyaasi_parser(search, uniq_regex=None, *args, **kwargs):
    BASE_URL="https://nyaa.iss.ink/?f=0&c=0_0&q="
    r = nyaa_session.get(f"{BASE_URL}{search}", headers=nyaa_headers, timeout=120)
    logging.info(r.status_code)
    if r.status_code != 200:
        return []
    handle = StringIO(r.content.decode())
    root = lxml.html.parse(handle)
    table_xpath_list = [
        '/html/body/div[1]/div[1]/table',
        '/html/body/div[1]/div[2]/table',
    ]
    for table_xpath in table_xpath_list:
        episodes_div_list = root.xpath(f'{table_xpath}/tbody[1]/tr')  
        if len(episodes_div_list) != 0:
            break
    episodes_conf = []
    uniq_ep = {}
    for episode_div in episodes_div_list:
        erow = episode_div.xpath('td')
        name = erow[1].xpath('a')[-1].get('title')
        torrent_link = list(erow[2].xpath('a')[1].iterlinks())[0][2]
        size = erow[3].text_content()
        add_time = erow[4].text_content()
        if uniq_regex is None:
            uniq_regex = r'E\d\d'
        ep_no_match = re.search(uniq_regex, name)
        if not ep_no_match:
            continue
        ep_no = ep_no_match.group()
        if ep_no in uniq_ep:
            continue
        uniq_ep[ep_no] = name
        ep_row = {
            'title': name,
            'link': torrent_link,
            'size': size,
            'pubDate': add_time
        }
        episodes_conf.append(ep_row)
        logging.info('Fetch Episode')
        logging.info(ep_row)
    return sorted(episodes_conf, key=lambda x: x['title'],reverse=True)[:36]

def njav_parser(*args, **kwargs):
    first_page = kwargs["first_page"]
    episodes_list = []
    page_list = subprocess.check_output(f'curl "{first_page}"' + ''' | pup 'a[class="page-link"] json{}' | jq -r '.[]|.href' | sort -V''', shell=True, executable='/bin/bash').decode().strip().split('\n')
    print(page_list)
    page_list[0] = first_page
    page_list = page_list[0:int(kwargs["page_limit"])]
    print(page_list)
    for page in page_list:
        page = page.replace('amp;', '')
        episodes = subprocess.check_output(f'curl "{page}"' + " | pup 'div[class=box-item] div a json{}' | jq -r '.[]|.href'", shell=True, executable='/bin/bash').decode().strip().split('\n')
        print(episodes)
        episodes_list.extend(list(dict.fromkeys(episodes)))
    with open('/tmp/test.txt', 'w') as f:
        f.write(json.dumps(episodes_list))
    return [{"title": i.split('/')[-1], "link": f"https://njav.tv/en/{i}"} for i in episodes_list]


def tgx_parser(search, uniq_regex=None, *args, **kwargs):
    for i in range(0,3):
        BASE_URL="https://tgx.sb/torrents.php?search="
        r = tgx_session.get(f"{BASE_URL}{search}")
        r_content = r.content.decode('ISO-8859-1')
        logging.info(len(r_content))
        if len(r_content) != 0:
            break
    handle = StringIO(r_content)
    root = lxml.html.parse(handle)
   
    episodes_div_list = root.xpath('/html/body/div[2]/div/div/div[2]/div/div[2]/div/div/div')[0].xpath('div')[1:]
    
    episodes_conf = []
    uniq_ep = {}
    for episode_div in episodes_div_list:
        erow = episode_div.xpath('div')
        name = erow[3].xpath('div/a[1]')[0].text_content()
        torrent_link = list(erow[4].xpath('a')[1].iterlinks())[0][2]
        size = erow[7].text_content()
        add_time = erow[11].text_content()
        if uniq_regex is None:
            uniq_regex = r'E\d\d'
        ep_no_match = re.search(uniq_regex, name)
        if not ep_no_match:
            continue
        ep_no = ep_no_match.group()
        if ep_no in uniq_ep:
            continue
        uniq_ep[ep_no] = name
        ep_row = {
            'title': name,
            'link': torrent_link,
            'size': size,
            'pubDate': add_time
        }
        episodes_conf.append(ep_row)
        logging.info('Fetch Episode')
        logging.info(ep_row)
    return sorted(episodes_conf, key=lambda x: x['title'],reverse=True)[:36]


def gen_xml_from_list(l: list, title: str):
    xml=f"<rss>\n<channel>\n<title>{title}</title>"
    for r in l:
        e = "\n".join([f'<{key}>{value}</{key}>' for key, value in r.items()])
        row_xml = f"<item>\n{e}\n</item>"
        xml = xml + "\n" + row_xml
    xml = xml + "\n</channel>\n</rss>" 
    return xml       

def get_a_minus_b(l1, l2):
    r1 = {row['title']: idx for idx, row in enumerate(l1)}
    r2 = {row['title']: idx for idx, row in enumerate(l2)}
    diff_keys = set(list(r1.keys())) - set(list(r2.keys()))
    return sorted([l1[r1[key]] for key in diff_keys], key=lambda x: x['title'], reverse=True)

today = subprocess.check_output(['date', '+%u']).decode().strip()
if __name__ == '__main__':
    with open('shows.yml', 'r') as f:
        shows = yaml.safe_load(f.read())
    show_id_list = list(shows.keys())
    if len(sys.argv) > 1:
        show_id_list = list(map(lambda x: int(x), sys.argv[1].strip(",").split(',')))

    index_parser_dict = {
        'tgx': tgx_parser,
        "nyaasi": nyaasi_parser,
        "snowfl": snowfl_parser,
        "njav": njav_parser,
    }
    
    for show_id in show_id_list:
        show_conf = shows[show_id]

        # Only scrape for shows that are airing today/yesterday
        # if parser is running for all episodes len > 3
        if len(show_id_list) > 3:
            if today not in str(show_conf['schedule']):
                continue

        logging.info(f'Fetching results for {show_conf["name"]} schedule {show_conf["schedule"]}')

        if os.path.exists(f'./json/{show_id}.json'):
            with open(f'./json/{show_id}.json', 'r') as f:
                old_episodes_conf = json.loads(f.read())
        else:
            old_episodes_conf = []

        # Already parsed
        if len(old_episodes_conf) == show_conf['episodes']:
            continue

        if show_conf['index'] not in index_parser_dict:
            # Parser for torrent index should be implemented
            continue
        for i in range(1,5):
            episodes_conf = index_parser_dict[show_conf['index']](**show_conf)
            if len(episodes_conf) != 0:
                break

        if len(episodes_conf) == 0:
            continue

        new_ep = get_a_minus_b(episodes_conf, old_episodes_conf)
        print(new_ep)
        new_ep_len = len(new_ep)
        #new_ep_len = len(episodes_conf) - len(old_episodes_conf)
        logging.info(f'New Episodes count {new_ep_len}')
        # The RSS feed shoule be updated only if there are new records
        if new_ep_len > 0:
            with open(f'./json/{show_id}.json', 'w') as f:
                f.write(json.dumps(episodes_conf))
            with open(f'./rss/{show_id}.rss', 'w') as f:
                f.write(gen_xml_from_list(episodes_conf, show_conf['name']))
