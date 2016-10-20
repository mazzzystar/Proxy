#!/user/bin/env python
# -*- coding:utf-8 -*-
#
# @author   Ringo
# @email    myfancoo@qq.com
# @date     2016/10/12
#

import requests
import time
import datetime
import logging
import pymysql as mdb
# import MySQLdb as mdb

# database config
config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'passwd': '*****',
    'db': 'proxy',
    'charset': 'utf8'
}
TABLE_NAME = 'valid_ip'

log_file = 'assess_logger.log'
logging.basicConfig(filename=log_file, level=logging.WARNING)

USELESS_TIME = 4   # maximum number of failures
SUCCESS_RATE = 0.8
TEST_ROUND_COUNT = 0
TIME_OUT_PENALTY = 10  # when timeout, set a penalty
CHECK_TIME_INTERVAL = 12*3600  # check per half day.


def modify_score(ip, type, time, conn):
    # type = 0 means ip hasn't pass the test
    cursor = conn.cursor()
    if type == 0:
        logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + ip + \
                        " out of time")
        try:
            cursor.execute('SELECT * FROM %s WHERE content= "%s"' % (TABLE_NAME, ip))
            q_result = cursor.fetchall()
            for r in q_result:
                test_times = r[1] + 1
                failure_times = r[2]
                success_rate = r[3]
                avg_response_time = r[4]
                score = r[5]
                if failure_times > 4 and success_rate < SUCCESS_RATE:
                    cursor.execute('DELETE FROM %s WHERE content= "%s"' % (TABLE_NAME, ip))
                    conn.commit()
                    logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + ip + \
                                    " was deleted.")
                else:
                    # not too bad
                    failure_times += 1
                    success_rate = 1 - float(failure_times) / test_times
                    avg_response_time = (avg_response_time * (test_times - 1) + TIME_OUT_PENALTY) / test_times
                    score = (success_rate + float(test_times) / 500) / avg_response_time
                    n = cursor.execute('UPDATE %s SET test_times = %d, failure_times = %d, success_rate = %.2f, avg_response_time = %.2f, score = %.2f WHERE content = "%s"' % (TABLE_NAME, test_times, failure_times, success_rate, avg_response_time, score, ip))
                    conn.commit()
                    if n:
                        logging.error(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + \
                                      ip + ' has been modify successfully!')
                break
        except Exception as e:
            logging.error(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + \
                                      'Error when try to delete ' + ip + str(e))
    elif type == 1:
        # pass the test
        try:
            cursor.execute('SELECT * FROM %s WHERE content= "%s"' % (TABLE_NAME, ip))
            q_result = cursor.fetchall()
            for r in q_result:
                test_times = r[1] + 1
                failure_times = r[2]
                avg_response_time = r[4]
                success_rate = 1 - float(failure_times) / test_times
                avg_response_time = (avg_response_time * (test_times - 1) + time) / test_times
                score = (success_rate + float(test_times) / 500) / avg_response_time
                n = cursor.execute('UPDATE %s SET test_times = %d, success_rate = %.2f, avg_response_time = %.2f, score = %.2f WHERE content = "%s"' %(TABLE_NAME, test_times, success_rate, avg_response_time, score, ip))
                conn.commit()
                if n:
                    logging.error(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + \
                                  ip + 'has been modify successfully!')
                break
        except Exception as e:
            logging.error(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + \
                                      'Error when try to modify ' + ip + str(e))


# Use http://lwons.com/wx to test if the server is available.
def ip_test(proxies, timeout, conn):
    # You may change the url by yourself if it didn't work.
    url = 'http://lwons.com/wx'
    for p in proxies:
        proxy = {'http': 'http://'+p}
        try:
            start = time.time()
            r = requests.get(url, proxies=proxy, timeout=timeout)
            end = time.time()
            if r.text == 'default':
                logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + p + \
                                " out of time")
                resp_time = end -start
                modify_score(p, 1, resp_time, conn)
                print 'Database test succeed: '+p+'\t'+str(resp_time)
        except:
            modify_score(p, 0, 0, conn)


def assess():
    global TEST_ROUND_COUNT
    TEST_ROUND_COUNT += 1
    logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + ">>>>\t" + str(TEST_ROUND_COUNT) + " round!\t<<<<")
    conn = mdb.connect(**config)
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM %s' % TABLE_NAME)
    result = cursor.fetchall()
    ip_list = []
    for i in result:
        ip_list.append(i[0])
    ip_test(ip_list, USELESS_TIME, conn)
    conn.close()


def main():
    while True:
        assess()
        time.sleep(CHECK_TIME_INTERVAL)

if __name__ == '__main__':
    main()