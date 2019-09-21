# coding:utf-8
from common.db import Mysql
from common.functions import log_success, log_fail_items, update_status
from urllib.parse import urlparse
from config import baidu as baidu_config
import requests
import time
import os
import sys
import json
import random
import math
sys.path.append('../')


class push:
    """
    像百度提交请求收录url
    """

    def __init__(self):
        self.submit_url = "https://ziyuan.baidu.com/linksubmit/urlsubmit"
        self.base_sleep_time = 1
        self.success_urls = []
        self.fail_urls = []
        self.time_sleep = 1
        self.faild_keys = ['not_valid', 'not_same_site']
        self.user_agents = baidu_config.user_agent_list
        self.cookies = self.get_cookies()
        self.mydb = Mysql()
        self.mydb.open()

    def urls_to_db(self, urls_file):
        """ url文件写入数据库 """
        with open(urls_file, 'r') as f:
            urls = f.readlines()

        insert_sql = """INSERT INTO urls(url,created_time) VALUES(%s,%s)"""
        for url in urls:
            if not url.split():
                continue
            current_time = int(time.time())
            param = (url.split(), current_time)
            self.mydb.execute(insert_sql, param)

    # 获取代理ip{因为本地ip在换了多个cookie以后，百度那边做了记录，不换ip提交就是失败}
    # ip有时效性为5分钟
    #  建议在获取ip成功后拿去验证下是不是之前用过的ip，是否可以用再去请求提交
    def get_proxies(self):
        """获取代理地址"""
        ips = dict()
        headers = {
            'User-Agent': random.choice(self.user_agents)
        }
        api = 'http://api.wandoudl.com/api/ip?app_key=95ceb15ce05f89b0aef10a6c906ff91a&pack=205700&num=1&xy=2&type=2&lb=\r\n&mr=1&'
        response = requests.get(url=api, headers=headers)
        json_data = json.loads(response.content.decode('utf-8'))
        ip = json_data["data"][0]["ip"]
        port = json_data["data"][0]["port"]
        ips['ip'] = ip
        ips['port'] = port

        return ips

    # 获取cookies值，一个cookie 是只能提交10个url，你看下那种效果高是选择本地还是网络请求
    def get_cookies(self):
        """获取cookies"""
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents)
            }
            response = requests.get(
                "http://pipixia.ajkseo1.cn/cookies.txt", headers=headers)
        except Exception as e:
            print(e)
        return response.text.split('\r\n')

    def start(self, site, token, urls_file):
        """正常提交需要收录的url"""
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

    def get_urls(self, page, offset):
        """获取需要提交的url列表"""
        select_sql = """SELECT id,url FROM urls urls WHERE status=0 AND deleted_time IS NULL LIMIT %s,%s"""
        param = (page*offset, offset)
        data = self.mydb.execute(select_sql, param, True)

        return data

    def urlsubmit(self):
        """使用代理方式提交url"""
        total_sql = """SELECT count(*) FROM urls WHERE status=0 AND deleted_time IS NULL"""
        (row,) = self.mydb.execute(total_sql, (), True)
        offset = 500
        page = math.ceil(row[0]/offset)

        for p in range(page):
            url_list = self.get_urls(p, offset)
            for row in url_list:
                self.post_url(row[1], row[0])

    def post_url(self, url, url_id):
        """发起提交请求"""
        # time.sleep(random.randint(self.base_sleep_time, self.base_sleep_time+15)
        data = {'url': url}
        headers = {
            'User-Agent': random.choice(self.user_agents)
        }
        headers['Content-Length'] = str(sys.getsizeof(data))
        headers['Cookie'] = random.choice(self.cookies)
        proxies = self.get_proxies()
        try:
            response = requests.post(
                url=self.submit_url, data=data, headers=headers, proxies=proxies)
            if response.status_code == 200:
                response_data = response.json()
                if response_data['status'] is 0:
                    print('提交成功')  # {"over":0,"status":0}
                    update_status(self.mydb, 1, url_id)
                elif response_data['status'] is 4:
                    # {"status":4}
                    msg = 'ip或cookie已到提交的限制'
                    print(msg, response_data)
                    update_status(self.mydb, 0, url_id, msg)
                else:
                    msg = '返回状态成功,提交失败:'
                    print(msg, response_data, proxies)
                    update_status(self.mydb, 0, url_id, msg)
            else:
                update_status(self.mydb, 0, url_id, response.status_code)
                self.base_sleep_time = random.randint(10, 30)
                print('HTTP CODE：', response.status_code)

        except Exception as e:
            update_status(self.mydb, 0, url_id, '异常')
            print(e)

    def __del__(self):
        pass
