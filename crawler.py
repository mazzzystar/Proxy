#!/user/bin/env python
# -*- coding:utf-8 -*-
#
# @author   Ringo
# @email    myfancoo@qq.com
# @date     2016/7/28
#

# ===========
# Test ip
# ===========
import os
import Queue
import threading
import requests
import logging
import time
import datetime
import random
from bs4 import BeautifulSoup, Comment
import ip_pool

log_file = 'proxy_logger.log'
logging.basicConfig(filename=log_file, level=logging.WARNING)


proportion = 0.35
Thread_Num = 30
base_page = 551300
USELESS_TIMES = 4  # proxy最大失效次数
base_time = time.time()
useful_proxies_dict = {}
useful_proxies_list = ip_pool.get_proxies(25, 5, 5, 2.5, 100)
for item in useful_proxies_list:
    useful_proxies_dict[item] = 0
origin_proxiesNum = len(useful_proxies_dict)


mutex = threading.RLock()

current_page = base_page


class UrlThread(threading.Thread):
    """get url response"""

    def __init__(self, saved_set):
        threading.Thread.__init__(self)
        self.saved_set = saved_set

    def run(self):
        global current_page
        global useful_proxies_dict
        global origin_proxiesNum
        global base_time

        while 1:
            rd = random.randint(0, len(useful_proxies_dict) - 1)
            proxy_ip = useful_proxies_dict.keys()[rd]
            status, content = html_save(current_page, proxy_ip, self.saved_set)
            # logging.info("Request Time:%s " % (time.time()-start))
            if status == 1:
                mutex.acquire()
                current_page += 1
                if (current_page - base_page) % 512 == 0:
                    vac = 512/float(time.time()-base_time)
                    logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\t" + \
                                    ">>>>>>Now is in<<<<<<<< " + str(current_page) + " Page! "+str(vac)+' p/s ')
                    base_time = time.time()
                mutex.release()
            elif status == -1:
                useless_proxy = content
                # logging.warning(useless_proxy+" is useless!")
                mutex.acquire()
                if useless_proxy in useful_proxies_dict:
                    useful_proxies_dict[useless_proxy] += 1
                    logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"\t"+useless_proxy+" has " + \
                                    str(useful_proxies_dict[useless_proxy]) + " times ERROR!")
                    if useful_proxies_dict[useless_proxy] == USELESS_TIMES:
                        del useful_proxies_dict[useless_proxy]
                        if len(useful_proxies_dict) == int(origin_proxiesNum*(1-proportion)):
                            expand_ip_pool()
                        logging.error(useless_proxy+" has been removed!")
                    # TODO: Call a function to change the proxies pool, just with a start(), when the function is over..
                else:
                    logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"Useless proxy "+ \
                                    useless_proxy+" has not been removed!")
                mutex.release()


class GetMoreIpThread(threading.Thread):
    """Get more ip"""
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global origin_proxiesNum
        global useful_proxies_dict
        addition_proxies_list = ip_pool.get_proxies(5, 2, 5, 2.5, 100)
        mutex.acquire()
        for proxy in addition_proxies_list:
            useful_proxies_dict[proxy] = 0
        origin_proxiesNum = len(useful_proxies_dict)
        logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"Currently there are" + \
                        str(origin_proxiesNum) + "proxies")
        mutex.release()


def html_save(com_id, proxy_ip, saved_set):
    if com_id in saved_set:
        return 100, ''
    proxy = {'http': 'http://'+proxy_ip}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko', 'Accept-Encoding': 'gzip,deflate'}
    try:
        web_content = requests.get("http://jobs.51job.com/all/co"+str(com_id)+".html", headers=headers, proxies=proxy, timeout=2.5)
        web_content.encoding = 'gbk'
        soup = BeautifulSoup(web_content.text)
        result = soup.find_all('a', 'icon_b i_house')
        if len(result) != 0:
            # remove JS
            [s.extract() for s in soup('script')]
            # remove CSS
            [s.extract() for s in soup('style')]
            # remove redundant HTML
            [s.extract() for s in soup(text=lambda text: isinstance(text, Comment))]
            [s.extract() for s in soup.find_all("div", {"id":"top"})]
            [s.extract() for s in soup.find_all("div", {"class":"navbtbg"})]
            [s.extract() for s in soup.find_all("div", {"class":"topbannerList"})]
            [s.extract() for s in soup.find_all("div", {"class":"tSeach_list_bot"})]
            [s.extract() for s in soup.find_all("div", {"id":"navbt"})]
            [s.extract() for s in soup.find_all("div", {"class":"wytj"})]
            [s.extract() for s in soup.find_all("div", {"id":"bott"})]
            # remove all links
            [s.extract() for s in soup.find_all("link")]

            with open('multi_data/' + str(com_id) + '.dict', 'w') as hf:
                hf.write(soup.prettify().rstrip()+'\n')
                logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+">>>>>编号为："+str(com_id)+ \
                                "的公司获取成功<<<<<")
            hf.close()
        else:
            logging.warning(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"编号为："+str(com_id)+"的公司不存在！")
        return 1, str(com_id)+'\t' + web_content.text
    except Exception, e:
            # print 'download error: ', e
            logging.error(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"Proxy useless:" + proxy_ip)
            return -1, proxy_ip


def expand_ip_pool():
    gmp = GetMoreIpThread()
    gmp.start()


def save_set(dir):
    # TODO
    num_list = []
    try:
        file_list = os.listdir(dir)
        it = iter(file_list)
        for i in it:
            item = int(i[:-5])
            num_list.append(item)
        file_set = set(file_list)
        return file_set
    except Exception:
        return set(num_list)


def main():
    dir = u'\\data\\ringo\\WORK\\51JOB_CRAWLER\\mutil_data'
    saved_set = save_set(dir)

    for i in range(Thread_Num):
        ut = UrlThread(saved_set)
        # ut.setDaemon(True)
        ut.start()

main()