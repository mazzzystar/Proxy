# -*- coding:utf-8 -*-
import sys
import requests
import time
import datetime
import random
import logging
from bs4 import BeautifulSoup
from lxml import etree
import pymysql as mdb
# import MySQLdb as mdb
reload(sys)
sys.setdefaultencoding('utf-8')

log_file = 'acquire_logger.log'
logging.basicConfig(filename=log_file, level=logging.WARNING)

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
# conn = mdb.connect(**config)
# cursor = conn.cursor()

flag = 0
proxy_list = []
# ip_file = "ip.txt"


def query_insert(ip_list, full_ip, conn):
    # Only when full_ip not in Database, insert it into ip_list.
    try:
        cursor = conn.cursor()
        ipExist = cursor.execute('SELECT * FROM %s WHERE content= "%s"' % (TABLE_NAME, full_ip))
        if not ipExist:
            # ip not in database
            ip_list.append(full_ip)
            print full_ip + " is new!"
            logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + full_ip + \
                            " has been accepted as new ip.")
        else:
            print full_ip + " is old!"
            logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + full_ip + \
                            " already exists!")
    except Exception as e:
        logging.error(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + str(e))


# Get all <66ip> ip in a specified page
def get_66ip(page, conn):
    ip_list = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
    url = 'http://www.66ip.cn/areaindex_1/'+str(page)+'.html'  # The ip resources url
    url_xpath = '/html/body/div[last()]//table//tr[position()>1]/td[1]/text()'
    port_xpath = '/html/body/div[last()]//table//tr[position()>1]/td[2]/text()'
    try:
        if flag == 0:  # if the first time
            results = requests.get(url, headers=headers, timeout=4)
        else:
            rd = random.randint(0, len(proxy_list) - 1)
            proxy_ip = proxy_list[rd]
            proxy = {'http': 'http://'+proxy_ip}
            results = requests.get(url, headers=headers, proxies=proxy, timeout=4)
        tree = etree.HTML(results.text)
        url_results = tree.xpath(url_xpath)  # Get ip
        # print url_results
        port_results = tree.xpath(port_xpath)  # Get port
        urls = [line.strip() for line in url_results]
        ports = [line.strip() for line in port_results]
        if len(urls) != len(ports):
            print "No! It's crazy!"
        else:
            for i in range(len(urls)):
                # Match each ip with it's port
                full_ip = urls[i]+":"+ports[i]
                # judge if already in database
                if flag == 1:
                    query_insert(ip_list, full_ip, conn)
                else:
                    print full_ip
                    ip_list.append(full_ip)
        return ip_list
    except Exception, e:
            print 'get proxies error: ', e
            return ip_list


# Get all #cn-proxy# ip in a specified page
def get_cnip(conn):
    ip_list = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
        url = 'http://cn-proxy.com/'  # The ip resources url
        url_xpath = '/html/body//table[@class="sortable"]//tr[position()>2]/td[1]/text()'
        port_xpath = '/html/body//table[@class="sortable"]//tr[position()>2]/td[2]/text()'
        if flag == 0:  # if the first time
            results = requests.get(url, headers=headers, timeout=4)
        else:
            rd = random.randint(0, len(proxy_list) - 1)
            proxy_ip = proxy_list[rd]
            proxy = {'http': 'http://'+proxy_ip}
            results = requests.get(url, headers=headers, proxies=proxy, timeout=4)
        tree = etree.HTML(results.text)
        url_results = tree.xpath(url_xpath)  # Get ip
        # print url_results
        port_results = tree.xpath(port_xpath)  # Get port
        urls = [line.strip() for line in url_results]
        ports = [line.strip() for line in port_results]
        ip_list = []
        if len(urls) != len(ports):
            print "No! It's crazy!"
        else:
            for i in range(len(urls)):
                # Match each ip with it's port
                full_ip = urls[i]+":"+ports[i]
                if flag == 1:
                    # if not the first
                    query_insert(ip_list, full_ip, conn)
                else:
                    print full_ip
                    ip_list.append(full_ip)
        return ip_list
    except Exception, e:
            print 'get proxies error: ', e
            return ip_list


# Get all #xici# ip in a specified page
def get_xici(page, conn):
    ip_list = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
        url = 'http://www.xicidaili.com/nn/'+str(page)  # The ip resources url
        # url_xpath = '/html/body//table[@class="sortable"]//tr[position()>2]/td[1]/text()'
        # port_xpath = '/html/body//table[@class="sortable"]//tr[position()>2]/td[2]/text()'
        if flag == 0:  # if the first time
            results = requests.get(url, headers=headers, timeout=4)
        else:
            rd = random.randint(0, len(proxy_list) - 1)
            proxy_ip = proxy_list[rd]
            proxy = {'http': 'http://'+proxy_ip}
            results = requests.get(url, headers=headers, proxies=proxy, timeout=4)
        soup = BeautifulSoup(results.text)
        ip = []
        port = []
        for s in soup.find("table").find_all("tr")[1:]:
            try:
                d = s.find_all("td")
                ip.append(str(d[1].string))
                port.append(str(d[2].string))
            except Exception as e:
                    print ('XiCiDaiLi parse error: %s', e)
        ip_list = []
        if len(ip) != len(port):
            print "No! It's crazy!"
        else:
            for i in range(len(ip)):
                # Match each ip with it's port
                full_ip = ip[i]+":"+port[i]
                if flag == 1:
                    query_insert(ip_list, full_ip, conn)
                else:
                    print full_ip
                    ip_list.append(full_ip)
        return ip_list
    except Exception, e:
            print 'get proxies error: ', e
            return ip_list


# Get all #kuaidaili# ip in a specified page
def get_kuaidaili(page, conn):
    ip_list = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
        url = 'http://www.kuaidaili.com/free/inha/'+str(page)+'/'  # The ip resources url
        url_xpath = '//td[@data-title="IP"]/text()'
        port_xpath = '//td[@data-title="PORT"]/text()'
        if flag == 0:  # if the first time
            results = requests.get(url, headers=headers, timeout=4)
        else:
            rd = random.randint(0, len(proxy_list) - 1)
            proxy_ip = proxy_list[rd]
            proxy = {'http': 'http://'+proxy_ip}
            results = requests.get(url, headers=headers, proxies=proxy, timeout=4)
        tree = etree.HTML(results.text)
        url_results = tree.xpath(url_xpath)  # Get ip
        # print url_results
        port_results = tree.xpath(port_xpath)  # Get port
        urls = [line.strip() for line in url_results]
        ports = [line.strip() for line in port_results]
        ip_list = []
        if len(urls) != len(ports):
            print "No! It's crazy!"
        else:
            for i in range(len(urls)):
                # Match each ip with it's port
                full_ip = urls[i]+":"+ports[i]
                if flag == 1:
                    query_insert(ip_list, full_ip, conn)
                else:
                    print full_ip
                    ip_list.append(full_ip)
        return ip_list
    except Exception, e:
            print 'get proxies error: ', e
            return ip_list


# Get all #mimi# ip in a specified page
def get_mimi(page, conn):
    ip_list = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}
        url = 'http://www.mimiip.com/gngao/'+str(page)  # The ip resources url
        url_xpath = '//table[@class="list"]//tr[position()>1]/td[1]/text()'
        port_xpath = '//table[@class="list"]//tr[position()>1]/td[2]/text()'
        if flag == 0:  # if the first time
            results = requests.get(url, headers=headers, timeout=4)
        else:
            rd = random.randint(0, len(proxy_list) - 1)
            proxy_ip = proxy_list[rd]
            proxy = {'http': 'http://'+proxy_ip}
            results = requests.get(url, headers=headers, proxies=proxy, timeout=4)
        tree = etree.HTML(results.text)
        url_results = tree.xpath(url_xpath)  # Get ip
        # print url_results
        port_results = tree.xpath(port_xpath)  # Get port
        urls = [line.strip() for line in url_results]
        ports = [line.strip() for line in port_results]
        ip_list = []
        if len(urls) != len(ports):
            print "No! It's crazy!"
        else:
            for i in range(len(urls)):
                # Match each ip with it's port
                full_ip = urls[i]+":"+ports[i]
                if flag == 1:
                    query_insert(ip_list, full_ip, conn)
                else:
                    print full_ip
                    ip_list.append(full_ip)
        return ip_list
    except Exception, e:
            print 'get proxies error: ', e
            return ip_list


#  Get all ip in 0~page pages website
def get_all_ip(page, conn):
    ip_list = []
    # mimi
    print ">>>>>mimi<<<<"
    for i in range(page):
        cur_ip_list = get_mimi(i+1, conn)
        for item in cur_ip_list:
            ip_list.append(item)

    # 66ip
    print ">>>>>66ip<<<<"
    for i in range(page):
        cur_ip_list = get_66ip(i+1, conn)
        for item in cur_ip_list:
            ip_list.append(item)

    # xici
    print ">>>>>xici<<<<"
    for i in range(page):
        cur_ip_list = get_xici(i+1, conn)
        for item in cur_ip_list:
            ip_list.append(item)

    # cn-proxy
    print ">>>>>cnproxy<<<<"
    cnproxy_ip = get_cnip(conn)
    if len(cnproxy_ip) != 0:
        for j in cnproxy_ip:
            ip_list.append(j)

    # kuaidaili
    print ">>>>>kuaidaili<<<<"
    for i in range(page):
        cur_ip_list = get_kuaidaili(i+1, conn)
        for item in cur_ip_list:
            ip_list.append(item)

    # for item in ip_list:
    #     print item
    return ip_list


# Use http://lwons.com/wx to test if the server is available.
def get_valid_proxies(proxies, timeout):
    # You may change the url by yourself if it didn't work.
    url = 'http://httpbin.org/get?show_env=1'
    results = []
    for p in proxies:
        proxy = {'http': 'http://'+p}
        succeed = False
        try:
            start = time.time()
            r = requests.get(url, proxies=proxy, timeout=timeout)
            end = time.time()
            if r.text is not None:
                succeed = True
        except Exception, e:
            print 'error:', p
            succeed = False
        if succeed:
            print 'succeed: '+p+'\t'+str(end-start)
            results.append(p)
        time.sleep(0.5)  # Avoid frequently crawling
    results = list(set(results))
    return results


def get_the_best(round, proxies, timeout, sleeptime):
    """
    ========================================================
    With the strategy of N round test to find those secure
    and stable ip. During each round it will sleep a while to
    avoid a 'famous 15 minutes"
    ========================================================"""
    for i in range(round):
        print '\n'
        print ">>>>>>>Round\t"+str(i+1)+"<<<<<<<<<<"
        proxies = get_valid_proxies(proxies, timeout)
        if i != round - 1:
            time.sleep(sleeptime)
    return proxies


# def get_mimi_proxy(page, mimi_proxies, round, timeout, sleeptime):
#     mimi_ip_list = []
#     for i in range(page):
#         cur_ip_list = get_mimi(i+1, mimi_proxies)
#         time.sleep(1)
#         for item in cur_ip_list:
#             mimi_ip_list.append(item)
#     for i in range(round):
#         print '\n'
#         print ">>>>>>>MiMi Round\t"+str(i+1)+"<<<<<<<<<<"
#         mimi_ip_list = get_valid_proxies(mimi_ip_list, timeout)
#         if i != round - 1:
#             time.sleep(sleeptime)
#     return mimi_ip_list


def get_proxies(page, round, timeout, sleep, conn):
    ip_list = get_all_ip(page, conn)
    proxies = get_the_best(round, ip_list, timeout, sleep)  # The suggested parameters
    return proxies


def store(page):
    global flag
    global proxy_list
    proxy_list = []
    conn = mdb.connect(**config)
    cursor = conn.cursor()
    if flag == 1:
        # Use proxy to crawl web
        try:
            cursor.execute('select count(*) from  %s ' % TABLE_NAME)
            length = 0
            for r in cursor:
                length = r[0]
            cursor.execute('SELECT * FROM %s LIMIT %d, %d' % (TABLE_NAME, length-20, length-5))
            result = cursor.fetchall()
            for i in result:
                proxy_list.append(i[0])
        except Exception as e:
            logging.error(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + \
                          " Use proxy to crawl web error! " + str(e))
    proxies = get_proxies(page, 3, 2.5, 1200, conn)  # 6, 5, 2.5, 1200
    print "\n\n\n"
    print ">>>>>>>>>>>>>>>>>>>The Final Ip<<<<<<<<<<<<<<<<<<<<<<"
    for item in proxies:
        print item
        try:
            ipExist = cursor.execute('SELECT * FROM %s WHERE content= "%s"' % (TABLE_NAME, item))
            if not ipExist:
                n = cursor.execute('INSERT INTO %s VALUES ("%s", 1, 0, 0, 1.0, 2.5, 0.0)' % (TABLE_NAME, item))
                conn.commit()
                if n:
                    logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + item + \
                                    " has been accepted as new ip in the " + str(n) + " row.")
                else:
                    logging.error(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + item + \
                                  " insert failure!")
            else:
                logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + item + \
                                " is not been inserted as it already exists.")
        except Exception as e:
            logging.critical(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+": " + str(e))
    conn.close()
    flag = 1
    if len(proxies) < 40:
        time.sleep(24*3600)


def main():
    while True:
        store(3)
        time.sleep(24*3600)

if __name__ == '__main__':
    main()

# TODO:
# 1. 把经过一次循环的存进数据库，对于新的ip，在round之前就判断其
# 是不是已经被收纳了，(或者曾经收纳后被淘汰过，此处放弃），如果不是再进入round
# 2. 对于一次过后就放入数据库proxy下的表valid_ip，之后每天对
# 3. 那个抓新ip并检测的程序永久运行，每次运行完都sleep3小时接着运行。
# 在database中新加一个字段，avg_response_time
# 再增加一个字段，score，score = success_rate / avg_response_time
# 每天crawl一遍新的ip，如果抓到的有用ip小于100，则养一天，后天再抓
# 每半天对存进数据库里的ip检测一次，对ping不通的判断其是否累积超过4&&20%, 超过
# 则从数据库删除。
# 4. 加一个新字段， test_times，统计该ip被检测次数， 因为不能让所有的ip共用一个test_times。
# 现在score = (success_rate + float(test_times) / 500) / avg_response_time, 即评价标准中引入test_times
