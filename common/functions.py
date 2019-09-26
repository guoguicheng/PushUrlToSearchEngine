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


def log_success_fail_count(mydb, status, url_id, info=''):
    """更新url提交结果"""
    current_time = int(time.time())
    update_sql = """UPDATE urls SET success = success + %s,failed = failed + %s,updated_time=%s,info=%s WHERE id = %s"""
    success_step = 1 if status == 1 else 0
    failed_step = 1 if status == 0 else 0
    param = (success_step, failed_step, current_time, info, url_id)
    mydb.execute(update_sql, param)
