# coding:utf-8
from common.functions import log_success, log_fail_items
from urllib.parse import urlparse
import requests
import time
import os
import sys
sys.path.append('../')


class push:
    def __init__(self):
        self.faild_keys = ['not_valid', 'not_same_site']

    def start(self, site, token, urls_file):
        (scheme, netloc, path, params, query, fragment) = urlparse(site)

        url = "http://data.zz.baidu.com/urls?site=%s&token=%s" % (site, token)
        date = time.strftime('%Y-%m-%d-%H',time.localtime(time.time()))

        with open(urls_file, 'r') as f:
            data = '\n'.join([l.strip() for l in f.readlines() if l.strip()])

        headers = {
            'User-Agent': 'curl/7.12.1',
            'Host': 'data.zz.baidu.com',
            'Content-Type': 'text/plain',
            'Content-Length': str(len(data)),
        }

        response = requests.post(url, data=data, headers=headers).json()

        log_success(netloc, date, response['remain'], response['success'])
        [log_fail_items(netloc, date, k, response[k])
         for k in self.faild_keys if k in response]

    def __del__(self):
        pass
