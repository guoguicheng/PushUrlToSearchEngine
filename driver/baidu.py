# coding:utf-8
from common.functions import log_success, log_fail_items
from urllib.parse import urlparse
from config.baidu import proxies, cookie
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
        date = time.strftime('%Y-%m-%d-%H', time.localtime(time.time()))

        with open(urls_file, 'r') as f:
            data = '\n'.join([l.strip() for l in f.readlines() if l.strip()])

        headers = {
            'User-Agent': 'curl/7.12.1',
            'Host': 'data.zz.baidu.com',
            'Content-Type': 'text/plain',
            'Content-Length': str(len(data)),
        }

        response = requests.post(url, data=data, headers=headers).json()

        log_success(netloc, date, response['success'])
        fails = [k for k in self.faild_keys if k in response]
        log_fail_items(netloc, date, fails)

    def urlsubmit(self, urls_file):
        submit_url = "https://ziyuan.baidu.com/linksubmit/urlsubmit"
        date = time.strftime('%Y-%m-%d-%H', time.localtime(time.time()))

        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": cookie,
            "Host": "ziyuan.baidu.com",
            "Origin": "https://ziyuan.baidu.com",
            "Pragma": "no-cache",
            "Referer": submit_url,
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36",
            "X-Request-By": "baidu.ajax",
            "X-Requested-With": "XMLHttpRequest",
        }

        success_urls = []
        fail_urls = []
        urls = []
        with open(urls_file, 'r') as f:
            urls = f.readlines()

        for url in urls:
            data = {'url': url}
            headers['Content-Length'] = str(sys.getsizeof(data))
            response = requests.post(
                submit_url, data=data, headers=headers, proxies=proxies).json()
            if response['status'] is 0:
                success_urls.append(url)
            else:
                fail_urls.append(url)
        log_success('urls', date, success_urls)
        log_fail_items('urls', date, fail_urls)

    def __del__(self):
        pass
