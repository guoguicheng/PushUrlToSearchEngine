import os


def log_fail_items(date, k, data):
    with open(os.path.join(os.getcwd(), 'log/%s_%s_urls.txt' % (date, k)), 'w+') as f:
        f.writelines([item+'\n' for item in data])


def log_success(date, remain, success):
    with open(os.path.join(os.getcwd(), 'log/push.log'), 'w+') as f:
        f.write("[%s] remain:%d,success:%d" % (date, remain, success))
