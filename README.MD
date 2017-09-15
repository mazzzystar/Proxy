Proxy
===============
A tiny tool for crawling, assessing, storing some useful proxies.[中文版](https://github.com/fancoo/Proxy/blob/master/README.zh-cn.md)

### Construct your ip pool
First make sure `mysql` has been installed in your machine, and modify db connection information in `config.py`.
```python
# crawl, assess and store proxies
python ip_pool.py

# assess proxies quality in db periodically.
python assess_quality.py
```

### Demo on how to use these proxies.
**Please first construct your ip pool.**

Crawl [github](https://www.github.com/) homepage data:
```python
# visit database to get all proxies
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

# use this proxies to crawl website
for i in ip_list:
    proxy = {'http': 'http://'+i}
    url = "https://www.github.com/"
    r = requests.get(url, proxies=proxy, timeout=4)
    print r.text
```
More detail in [crawl_demo.py](https://github.com/fancoo/Proxy/blob/master/crawl_demo.py)。

### Contact
myfancoo@qq.com
