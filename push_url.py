# coding:utf-8
import requests
import os
import datetime
import sys
from driver.baidu import push as baidu_push
from driver.google import push as google_push
from driver.bing import push as bing_push
from driver.so import push as so_push
from driver.sogou import push as sogou_push
from config.baidu import baidu_site_config


def baidu():
    cwd = os.getcwd()
    push = baidu_push()

    for k in baidu_site_config:
        site = baidu_site_config[k]['site']
        token = baidu_site_config[k]['token']
        urls_file = os.path.join(cwd, 'urls', k+".txt")
        push.start(site, token, urls_file)


if __name__ == "__main__":
    baidu()
