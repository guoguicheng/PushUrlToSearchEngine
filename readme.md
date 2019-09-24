
### 环境

    python3.6

    apt-get install python3.6-dev libmysqlclient-dev

    pip install -U requests[socks]

### 部署

    pip install -r requirements.txt

### 运行

    # url文件导入mysql
    python push_url.py -i filename.txt

    # 开始提交
    python push_url.py

