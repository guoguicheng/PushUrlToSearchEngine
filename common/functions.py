import os
import time


def log_fail_items(domain, date, data):
    """记录提交失败地址"""
    with open(os.path.join(os.getcwd(), 'log/%s_%s_urls.txt' % (domain, date)), 'w+') as f:
        f.writelines([item+'\n' for item in data])


def log_success(domain, date, data):
    """记录提交成功地址"""
    with open(os.path.join(os.getcwd(), 'log/%s_%s_push.log' % (domain, date)), 'w+') as f:
        f.writelines([item+'\n' for item in data])


def update_status(mydb, status, url_id):
    """更新url提交结果"""
    current_time = int(time.time())
    update_sql = """UPDATE urls SET status=%s,updated_time=%s WHERE id = %s"""
    param = (status, current_time, url_id)
    mydb.execute(update_sql, param)
