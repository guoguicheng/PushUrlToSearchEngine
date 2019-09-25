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
import threadpool
import threading
import multiprocessing
sys.path.append('../')

requests.packages.urllib3.disable_warnings()
requests.adapters.DEFAULT_RETRIES = 5

finished = 0


class push:
    """
    像百度提交请求收录url
    """

    def __init__(self):
        self.submit_url = "https://ziyuan.baidu.com/linksubmit/urlsubmit"
        self.base_sleep_time = 0
        self.success_urls = []
        self.fail_urls = []
        self.time_sleep = 1
        self.faild_keys = ['not_valid', 'not_same_site']
        self.user_agents = baidu_config.user_agent_list
        self.proxie_stack = []
        self.db_pool = {}
        self.push_header = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "ziyuan.baidu.com",
            "Origin": "https://ziyuan.baidu.com",
            "Pragma": "no-cache",
            "Referer": "https://ziyuan.baidu.com/linksubmit/url",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Request-By": "baidu.ajax",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "close"
        }
        self.init()

    def init(self):
        print("开始加载cookie")
        self.cookies = self.get_cookies()
        print("开始连接数据库")
        self.mydb = Mysql()
        self.mydb.open()
        print("开始初始化代理")
        self.get_proxies()

    def urls_to_db(self, urls_file):
        """ url文件写入数据库 """
        urls = []

        with open(urls_file, 'r') as f:
            urls = f.readlines()
        total = len(urls)
        finished = 0

        insert_sql = """INSERT INTO urls(url,created_time) VALUES(%s,%s)"""
        for url in urls:
            if not url.split():
                continue
            current_time = int(time.time())
            param = (url.split(), current_time)
            self.mydb.execute(insert_sql, param)
            finished += 1
            print("\r[SAVING]total:%d,finished:%d" % (total, finished), end="")
        print("\nDONE!")

    # 获取代理ip{因为本地ip在换了多个cookie以后，百度那边做了记录，不换ip提交就是失败}
    # ip有时效性为5分钟
    #  建议在获取ip成功后拿去验证下是不是之前用过的ip，是否可以用再去请求提交

    def get_proxies(self, init=True):
        """获取代理地址"""

        if not init and len(self.proxie_stack) > 0:
            return self.proxie_stack.pop()

        headers = {
            'User-Agent': random.choice(self.user_agents)
        }
        api = "http://http.tiqu.alicdns.com/getip3?num=10&type=2&pro=620000&city=621000&yys=0&port=12&pack=65613&ts=0&ys=0&cs=0&lb=1&sb=0&pb=4&mr=1&regions="
        response = requests.get(url=api, headers=headers).json()
        for item in response['data']:
            proxies = {
                'http': 'http://%s:%d' % (item['ip'], item['port']),
                'https': 'https://%s:%d' % (item['ip'], item['port'])
            }
            self.proxie_stack.append(proxies)

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
        thread_id = threading.currentThread().ident
        data = self.db_pool[thread_id].execute(
            select_sql, param, True)

        return data

    def urlsubmit(self):
        """使用代理方式提交url"""
        print("开始提交url")
        total_sql = """SELECT count(*) as num FROM urls WHERE status=0 AND deleted_time IS NULL"""
        (row,) = self.mydb.execute(total_sql, (), True)
        total = row[0]
        if total == 0:
            return
        offset = 500
        page = math.ceil(total/offset)

        thread_num = int(multiprocessing.cpu_count()/(1-0.2))
        # 页数小于线程数
        if page < thread_num:
            offset = math.ceil(total/thread_num)
            page = thread_num

        # 总量小于线程数
        if total < thread_num:
            thread_num = total
            page = total
            offset = 1
        pool = threadpool.ThreadPool(thread_num)

        # 每个线程执行多少页
        num = math.ceil(page/thread_num)
        print("开始%d线程，共%d页，每线程处理%d页,每页%d条" % (thread_num, page, num, offset))
        par_list = []
        for i in range(thread_num):
            par_list.append(([i*num, i*num+num, offset, total], None))
        print(par_list)
        request = threadpool.makeRequests(
            self.start_process, par_list)
        [pool.putRequest(req) for req in request]
        pool.wait()

    def start_process(self, start_page, end_page, offset, total):
        """开始任务"""
        global finished
        thread_id = threading.currentThread().ident
        self.db_pool[thread_id] = Mysql()
        self.db_pool[thread_id].open()
        for p in range(start_page, end_page):
            url_list = self.get_urls(p, offset)
            for item in url_list:
                msg = self.post_url(item[1], item[0])
                finished += 1
                print("%s\n\r[PUSH]:%.2f%%\n" %
                      (msg, round(finished/total*100, 2)), end="")

    def test_proxies(self, proxies):
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
            'Connection': 'keep-alive'
        }
        p = requests.get('http://icanhazip.com',
                         headers=header, proxies=proxies)
        print(proxies, p.text)

    def post_url(self, url, url_id):
        """发起提交请求"""
        msg = ''
        data = {'url': url}
        thread_id = threading.currentThread().ident
        self.push_header["Cookie"] = random.choice(self.cookies)
        self.push_header["Content-Length"] = str(sys.getsizeof(data))
        self.push_header["User-Agent"] = random.choice(self.user_agents)

        proxies = self.get_proxies(False)
        # self.test_proxies(proxies)
        try:
            response = requests.post(
                url=self.submit_url, data=data, headers=self.push_header, proxies=proxies, verify=False, timeout=(3, 7))

            if response.status_code == 200:
                response_data = response.json()
                if response_data['status'] is 0:
                    # {"over":0,"status":0}
                    msg = "["+str(url_id)+"]提交成功"+response.text
                    update_status(self.db_pool[thread_id], 1, url_id)
                elif response_data['status'] is 4:  # {"status":4}
                    msg = "["+str(url_id) + "]ip或cookie已到提交的限制"+response.text
                    update_status(self.db_pool[thread_id], 0, url_id, msg)
                else:
                    msg = "["+str(url_id) + "]返回状态成功,提交失败 "+response.text
                    update_status(self.db_pool[thread_id], 0, url_id, msg)
            else:
                msg = "["+str(url_id) + "]HTTP CODE："+response.text
                update_status(self.db_pool[thread_id],
                              0, url_id, response.status_code)
                self.base_sleep_time = random.randint(1, 10)
            response.close()
        except Exception as e:
            msg = "["+str(url_id)+"]"+str(e)
            update_status(self.db_pool[thread_id], 0, url_id, '异常')
            self.base_sleep_time = random.randint(1, 10)

        # time.sleep(random.randint(self.base_sleep_time, self.base_sleep_time+5))
        time.sleep(0.01)
        return msg

    def __del__(self):
        for db in self.db_pool:
            db.close()
