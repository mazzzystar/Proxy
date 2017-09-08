import pymysql as mdb
import config as cfg
import requests

conn = mdb.connect(cfg.host, cfg.user, cfg.passwd, cfg.DB_NAME)
cursor = conn.cursor()

ip_list = []
try:
    cursor.execute('SELECT content FROM %s' % cfg.TABLE_NAME)
    result = cursor.fetchall()
    for i in result:
        ip_list.append(i[0])
except Exception as e:
    print e
finally:
    cursor.close()
    conn.close()

for i in ip_list:
    proxy = {'http': 'http://'+i}
    url = "https://www.github.com/"
    r = requests.get(url, proxies=proxy, timeout=4)
    print r.headers