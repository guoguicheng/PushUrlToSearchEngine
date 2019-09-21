# coding:utf-8
import requests
import os
import datetime
import sys
from driver.baidu import push as baidu_push


def baidu():
    cwd = os.getcwd()
    push = baidu_push()

    """for k in baidu_site_config:
        site = baidu_site_config[k]['site']
        token = baidu_site_config[k]['token']
        urls_file = os.path.join(cwd, 'urls', k+".txt")
        push.start(site, token, urls_file)"""
    #push.urls_to_db(os.path.join(cwd,'urls','urls.txt'))
    push.urlsubmit()


if __name__ == "__main__":
    baidu()
