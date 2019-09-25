#!/usr/bin/python
# -*- coding: UTF-8 -*-
from config.database import mysql
import MySQLdb
import MySQLdb.cursors
import sys
sys.path.append('../')

# 打开数据库连接


class Mysql:

    def open(self):
        self.db = MySQLdb.connect(
            host=mysql['host'],
            user=mysql['user'],
            passwd=mysql['passwd'],
            db=mysql['db'],
            port=mysql['port'],
            charset=mysql['charset']
        )

    def execute(self, sql, param, fetch=False):

        cursor = self.db.cursor()
        data = cursor.execute(sql, param)
        self.db.commit()
        if fetch:
            data = cursor.fetchall()
        cursor.close()

        return data

    def close(self, db):
        db.close()
