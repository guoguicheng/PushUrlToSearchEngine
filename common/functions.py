import os


def log_fail_items(domain, date, k, data):
    with open(os.path.join(os.getcwd(), 'log/%s_%s_%s_urls.txt' % (domain, date, k)), 'w+') as f:
        f.writelines([item+'\n' for item in data])


def log_success(domain, date, remain, success):
    with open(os.path.join(os.getcwd(), 'log/%s_%s_push.log' % (domain, date)), 'w+') as f:
        f.write("[%s] remain:%d,success:%d" % (date, remain, success))
