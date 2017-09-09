# coding:utf-8
import time
import config as cfg
import requests
from lxml import etree
import pymysql as mdb
import datetime
from multiprocessing import Process, Manager
import random


class IPFactory:
    """
    * crawl
    * evaluation
    * storage
    """

    def __init__(self):
        self.page_num = cfg.page_num
        self.timeout = cfg.timeout
        self.all_ip = set()

        # init database
        self.create_db()

    def create_db(self):
        """
        create database if not exists.
        """

        '''sql statement'''
        drop_db_str = 'drop database if exists ' + cfg.DB_NAME + ' ;'
        create_db_str = 'create database ' + cfg.DB_NAME + ' ;'
        use_db_str = 'use ' + cfg.DB_NAME + ' ;'
        create_table_str = "CREATE TABLE " + cfg.TABLE_NAME + """(
          `content` varchar(30) NOT NULL,
          `test_times` int(5) NOT NULL DEFAULT '0',
          `failure_times` int(5) NOT NULL DEFAULT '0',
          `success_rate` float(5,2) NOT NULL DEFAULT '0.00',
          `avg_response_time` float NOT NULL DEFAULT '0',
          `score` float(5,2) NOT NULL DEFAULT '0.00'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;"""

        # database connection
        conn = mdb.connect(cfg.host, cfg.user, cfg.passwd)
        cursor = conn.cursor()
        try:
            cursor.execute(drop_db_str)
            cursor.execute(create_db_str)
            cursor.execute(use_db_str)
            cursor.execute(create_table_str)
            conn.commit()
        except OSError:
            print "cannot create database! please check your username & password."
        finally:
            cursor.close()
            conn.close()

    def get_content(self, url, url_xpath, port_xpath):
        """
        parse web html using xpath
        return ip list.
        """
        ip_list = []

        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko'}

            results = requests.get(url, headers=headers, timeout=4)
            tree = etree.HTML(results.text)

            # parse [ip:port] pairs.
            url_results = tree.xpath(url_xpath)
            port_results = tree.xpath(port_xpath)
            urls = [line.strip() for line in url_results]
            ports = [line.strip() for line in port_results]

            if len(urls) == len(ports):
                for i in range(len(urls)):
                    # match each ip with it's port to the format like "127.0.0.1:80"
                    full_ip = urls[i]+":"+ports[i]

                    # if current ip has been crawled
                    if full_ip in self.all_ip:
                        continue

                    ip_list.append(full_ip)
        except Exception as e:
            print 'get proxies error: ', e

        return ip_list

    def get_all_ip(self):
        """
        merge the ip crawled from several websites.
        """
        current_all_ip = set()

        ##################################
        # 66ip (http://www.66ip.cn/)
        ###################################
        url_xpath_66 = '/html/body/div[last()]//table//tr[position()>1]/td[1]/text()'
        port_xpath_66 = '/html/body/div[last()]//table//tr[position()>1]/td[2]/text()'
        for i in xrange(self.page_num):
            url_66 = 'http://www.66ip.cn/' + str(i+1) + '.html'
            results = self.get_content(url_66, url_xpath_66, port_xpath_66)

            if len(results):
                self.all_ip.update(results)
                current_all_ip.update(results)
                # wait 0.5 secs.
                time.sleep(0.5)

        ##################################
        # xicidaili (http://www.xicidaili.com/nn/)
        ###################################
        url_xpath_xici = '//table[@id="ip_list"]//tr[position()>1]/td[position()=2]/text()'
        port_xpath_xici = '//table[@id="ip_list"]//tr[position()>1]/td[position()=3]/text()'
        for i in xrange(self.page_num):
            url_xici = 'http://www.xicidaili.com/nn/' + str(i+1)
            results = self.get_content(url_xici, url_xpath_xici, port_xpath_xici)
            self.all_ip.update(results)
            current_all_ip.update(results)
            time.sleep(0.5)

        ##################################
        # mimiip (http://www.mimiip.com/gngao/)
        ###################################
        url_xpath_mimi = '//table[@class="list"]//tr[position()>1]/td[1]/text()'
        port_xpath_mimi = '//table[@class="list"]//tr[position()>1]/td[2]/text()'
        for i in xrange(self.page_num):
            url_mimi = 'http://www.mimiip.com/gngao/' + str(i+1)
            results = self.get_content(url_mimi, url_xpath_mimi, port_xpath_mimi)
            self.all_ip.update(results)
            current_all_ip.update(results)
            time.sleep(0.5)

        ##################################
        # kuaidaili (http://www.kuaidaili.com/)
        ###################################
        url_xpath_kuaidaili = '//td[@data-title="IP"]/text()'
        port_xpath_kuaidaili = '//td[@data-title="PORT"]/text()'
        for i in xrange(self.page_num):
            url_kuaidaili = 'http://www.kuaidaili.com/free/inha/' + str(i+1) + '/'
            results = self.get_content(url_kuaidaili, url_xpath_kuaidaili, port_xpath_kuaidaili)
            self.all_ip.update(results)
            current_all_ip.update(results)
            time.sleep(0.5)

        print current_all_ip
        print ">>>>>>>>>>>>>> All proxies has been crawled <<<<<<<<<<<"
        return current_all_ip

    def get_valid_ip(self, ip_set, manager_list, timeout):
        """
        test if ip is valid.
        """
        # request url.
        # url = 'http://httpbin.org/get?show_env=1'
        url = 'http://github.com'

        # check proxy one by one
        for p in ip_set:
            proxy = {'http': 'http://'+p}
            try:
                start = time.time()
                r = requests.get(url, proxies=proxy, timeout=timeout)
                end = time.time()

                # judge if proxy valid
                if r.status_code == 200:
                    print 'succeed: ' + p + '\t' + " succeed in " + format(end-start, '0.4f') + 's!'
                    # add to result
                    manager_list.append(p)
            except Exception:
                print p + "\t timeout."

    def multi_thread_validation(self, ip_set, manager_list, timeout, thread=50):
        """
        use multiple process to accelerate the judgement of valid proxies.
        """
        if len(ip_set) < thread:
            thread = len(ip_set)

        # divide ip_set to blocks for later multiprocess.
        slice_len = len(ip_set) / thread

        jobs = []
        for i in xrange(thread-1):
            part = set(random.sample(ip_set, slice_len))
            ip_set -= part
            p = Process(target=self.get_valid_ip, args=(part, manager_list, timeout))
            jobs.append(p)
            p.start()

        # the last slice of ip_set.
        p = Process(target=self.get_valid_ip, args=(ip_set, manager_list, timeout))
        p.start()
        jobs.append(p)

        # join threads
        for job in jobs:
            if job.is_alive():
                job.join()

    def save_to_db(self, valid_ips):
        """
        save all valid proxies into db
        """
        if len(valid_ips) == 0:
            print "not proxy available for this time."
            return

        # store valid proxies into db.
        print "\n>>>>>>>>>>>>>>>>>>>> Insert to database Start  <<<<<<<<<<<<<<<<<<<<<<"
        conn = mdb.connect(cfg.host, cfg.user, cfg.passwd, cfg.DB_NAME)
        cursor = conn.cursor()
        try:
            for item in valid_ips:
                # check if current ip exists.
                item_exist = cursor.execute('SELECT * FROM %s WHERE content="%s"' %(cfg.TABLE_NAME, item))

                # it's new ip
                if item_exist == 0:
                    n = cursor.execute('INSERT INTO %s VALUES("%s", 1, 0, 0, 1.0, 2.5)' %(cfg.TABLE_NAME, item))
                    conn.commit()

                    if n:
                        print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" "+item+" insert successfully."
                    else:
                        print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" "+item+" insert failed."

                else:
                    print datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" "+ item + " exists."
        except Exception as e:
            print "store to db failed：" + str(e)
        finally:
            cursor.close()
            conn.close()
        print ">>>>>>>>>>>>>>>>>>>> Insert to database Ended  <<<<<<<<<<<<<<<<<<<<<<"
        print "Finished."

    def get_proxies(self, manager_list):
        ip_list = []

        # db connection
        conn = mdb.connect(cfg.host, cfg.user, cfg.passwd, cfg.DB_NAME)
        cursor = conn.cursor()

        try:
            ip_exist = cursor.execute('SELECT * FROM %s ' % cfg.TABLE_NAME)
            result = cursor.fetchall()

            # if exists proxies in db, fetch and return.
            if len(result):
                for item in result:
                    ip_list.append(item[0])
            else:
                # crawl more proxies.
                current_ips = self.get_all_ip()
                self.multi_thread_validation(current_ips, manager_list, cfg.timeout)
                valid_ips = manager_list
                self.save_to_db(valid_ips)
                ip_list.extend(valid_ips)
        except Exception as e:
            print "get ip from database failed." + str(e)
        finally:
            cursor.close()
            conn.close()

        return ip_list


def main():
    ip_pool = IPFactory()
    while True:
        manager = Manager()
        manager_list = manager.list()
        current_ips = ip_pool.get_all_ip()
        ip_pool.multi_thread_validation(current_ips, manager_list, cfg.timeout)
        print "\n>>>>>>>>>>>>> Valid proxies <<<<<<<<<<"
        print manager_list + '\n'
        ip_pool.save_to_db(manager_list)
        time.sleep(cfg.CHECK_TIME_INTERVAL)

if __name__ == '__main__':
    main()
