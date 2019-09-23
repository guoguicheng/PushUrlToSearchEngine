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
        self.base_sleep_time = 0
        self.success_urls = []
        self.fail_urls = []
        self.time_sleep = 1
        self.faild_keys = ['not_valid', 'not_same_site']
        self.user_agents = baidu_config.user_agent_list
        self.cookies = self.get_cookies()
        self.mydb = Mysql()
        self.mydb.open()
        self.push_header = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": "ziyuan.baidu.com",
            "Origin": "https://ziyuan.baidu.com",
            "Pragma": "no-cache",
            "Referer": "https://ziyuan.baidu.com/linksubmit/url",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Request-By": "baidu.ajax",
            "X-Requested-With": "XMLHttpRequest",
        }

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
            print("\r\033[95m[SAVING]\033[0m \033[94mtotal\033[0m:%d,\033[94mfinished\033[0m:%d" % (
                total, finished), end="")
        print("\n\033[94mDONE\033[0m")

    # 获取代理ip{因为本地ip在换了多个cookie以后，百度那边做了记录，不换ip提交就是失败}
    # ip有时效性为5分钟
    #  建议在获取ip成功后拿去验证下是不是之前用过的ip，是否可以用再去请求提交

    def get_proxies(self):
        """获取代理地址"""
        headers = {
            'User-Agent': random.choice(self.user_agents)
        }
        #api = 'http://api.wandoudl.com/api/ip?app_key=95ceb15ce05f89b0aef10a6c906ff91a&pack=205700&num=1&xy=2&type=2&lb=\r\n&mr=1&'
        api = "http://api.wandoudl.com/api/ip?app_key=cc62678d82db31f3d127da47fc089b70&pack=207323&num=20&xy=1&type=2&lb=\r\n&mr=1&"
        response = requests.get(url=api, headers=headers).json()
        ip = response["data"][0]["ip"]
        port = response["data"][0]["port"]

        ips = dict()
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
            idx = 0
            for row in url_list:
                msg = self.post_url(row[1], row[0])
                idx += 1
                print("\r\033[95m[PUSH]\033[0m finished[\033[94m%d%%\033[0m]  %s" % (
                    int((p*offset+idx)/row[0]*100), msg), end="")

    def post_url(self, url, url_id):
        """发起提交请求"""

        msg = ''
        data = {'url': url}
        self.push_header["Cookie"] = random.choice(self.cookies)
        self.push_header["Content-Length"] = str(sys.getsizeof(data))
        self.push_header["User-Agent"] = random.choice(self.user_agents)
        #headers['Cookie']="BAIDUID=B30BE6FEA0C79D62B7EC016B4D880E8E:FG=1; BIDUPSID=B30BE6FEA0C79D62B7EC016B4D880E8E; PSTM=1564829515; uc_login_unique=6ce0a03b3a8f6030c714294b311d59c7; uc_recom_mark=cmVjb21tYXJrXzI3MTg3NDgz; delPer=0; H_PS_PSSID=1458_21082_29523_29721_29568_29220_22158; PSINO=7; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; __cas__st__=NLI; __cas__id__=0; Hm_lvt_6f6d5bc386878a651cb8c9e1b4a3379a=1569066651,1569125907,1569127914,1569244953; BDUSS=FiYmFDZEVzNjQybDB1bTg3UjFneG1PSHBqOEE1NU1IaThwdTk1Rk1FOVNWTEJkRVFBQUFBJCQAAAAAAAAAAAEAAADvYfVLX01BTmVhcnRoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFLHiF1Sx4hdY2; SITEMAPSESSID=mgpkhb9246hukg397jjbq0pi74; lastIdentity=PassUserIdentity; Hm_lpvt_6f6d5bc386878a651cb8c9e1b4a3379a=1569245036"

        proxies = self.get_proxies()

        try:
            response = requests.post(
                url=self.submit_url, data=data, headers=self.push_header, proxies=proxies)
            if response.status_code == 200:
                response_data = response.json()
                if response_data['status'] is 0:
                    msg = "提交成功"+response.text  # {"over":0,"status":0}
                    update_status(self.mydb, 1, url_id)
                elif response_data['status'] is 4:  # {"status":4}
                    msg = 'ip或cookie已到提交的限制'+response.text
                    update_status(self.mydb, 0, url_id, msg)
                else:
                    msg = '返回状态成功,提交失败 '+response.text
                    update_status(self.mydb, 0, url_id, msg)
            else:
                msg = 'HTTP CODE：'+response.text
                update_status(self.mydb, 0, url_id, response.status_code)
                self.base_sleep_time = random.randint(1, 10)

        except Exception as e:
            msg = '异常:'+e
            update_status(self.mydb, 0, url_id, msg)
            self.base_sleep_time = random.randint(1, 10)

        #time.sleep(random.randint(self.base_sleep_time, self.base_sleep_time+5))
        return msg

    def __del__(self):
        pass
