import os


def log_fail_items(domain, date, data):
    with open(os.path.join(os.getcwd(), 'log/%s_%s_urls.txt' % (domain, date)), 'w+') as f:
        f.writelines([item+'\n' for item in data])


def log_success(domain, date, data):
    with open(os.path.join(os.getcwd(), 'log/%s_%s_push.log' % (domain, date)), 'w+') as f:
        f.writelines([item+'\n' for item in data])
