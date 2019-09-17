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


def baidu():
    cwd = os.getcwd()

    baidu_site = 'https://www.mxreality.cn'
    baidu_token = '37FWD4TLAKyq14R0'
    urls_file = os.path.join(cwd, 'urls.txt')
    baidu_push().start(baidu_site, baidu_token, urls_file)


if __name__ == "__main__":
    baidu()
