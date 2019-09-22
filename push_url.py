# coding:utf-8
from driver.baidu import push as baidu_push
import argparse
import requests
import os
import datetime
import sys
from driver.baidu import push as baidu_push

parser = argparse.ArgumentParser()
parser.description = 'url数据导入数据库'
parser.add_argument("-i", "--import-file", help="url文件名称",
                    type=str, default=None, required=False)
args = parser.parse_args()


def baidu(args):
    """提交百度"""
    cwd = os.getcwd()
    push = baidu_push()
    if(args.import_file):
        push.urls_to_db(os.path.join(cwd, 'urls', args.import_file))
    else:
        push.urlsubmit()


if __name__ == "__main__":

    baidu(args)
