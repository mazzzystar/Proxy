# coding:utf-8

"""
Page number that you crawl from those websites.
* if your crawl task is not heavy, set page_num=2~5
* if you'd like to keep a proxies pool, page_num=10 can meet your need.
"""
page_num = 1

# ip test timeout.
timeout = 4

# database host
host = '127.0.0.1'

# database host
port = 3306

# db user
user = 'root'

# db password
passwd = '123456'

# db name
DB_NAME = 'proxies'

# table name
TABLE_NAME = 'valid_ip'

# encode
charset = 'utf8'

# max failure times of an ip, if exceed, delete it from db.
USELESS_TIME = 4

# lowest success rate of an ip, if exceed, delete it from db.
SUCCESS_RATE = 0.8

# timeout punishment
TIME_OUT_PENALTY = 10

# ip quality assessment time interval. (currently once per day.)
CHECK_TIME_INTERVAL = 24*3600
