Proxy
============
一个小巧的代理ip抓取+评估+存储一体化的工具,使用requests+mysql完成。

### 使用
有`ip_pool.py`和`assess_quality.py`两个程序，前者负责每天抓ip/评估/存进数据库，后者负责数据库中ip的清理和打分。

#### 运行程序
首先确保你的电脑安装了`mysql`，此外你需要在`config.py`里将配置修改为自己数据库配置。
```python
# 定期抓取+评估+存储代理ip
python ip_pool.py

# 定期对数据库里的ip质量进行评估
python assess_quality.py
```
之后按默认配置，这两个程序每天分别执行抓取和评估工作。

#### 代理使用Demo
以抓取[github](https://www.github.com/)主页为例：
```python
# 访问数据库拿到代理
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

# 利用代理抓取github页面
for i in ip_list:
    proxy = {'http': 'http://'+i}
    url = "https://www.github.com/"
    r = requests.get(url, proxies=proxy, timeout=4)
    print r.text
```
详见[crawl_demo.py](https://github.com/fancoo/Proxy/blob/master/crawl_demo.py)。

### 简介

程序有如下几个功能：

* 每天从多个代理ip网站上抓下最新高匿ip数据。
* 经过筛选后的ip将存入数据库。
* 存入数据库的ip每天也要经过测试，存在剔除、评分机制，多次不合格的ip将被删除，每个ip都被评分，我们最终可以按得分排名获得稳定、低响应时间的优质ip。

存储如下图所示：
![ip在数据库中的存储结构](https://github.com/fancoo/Proxy/blob/master/images/data.png)


### 参数
```python
USELESS_TIME = 4   # 最大失效次数
SUCCESS_RATE = 0.8
TIME_OUT_PENALTY = 10  # 超时惩罚时间
CHECK_TIME_INTERVAL = 24*3600  # 每天更新一次
```
除数据库配置参数外，主要用到的几个参数说明如下：

* ```USELESS_TIME```和```SUCCESS_RATE```是配合使用的，当某个```ip```的```USELESS_TIME < 4 && SUCCESS_RATE < 0.8```时（同时兼顾到ip短期和长期的检测表现），则剔除该ip。
* ```TIME_OUT_PENALTY```， 当某个ip在某次检测时失效，而又没有达到上一条的条件时（比如检测了100次后第一次出现超时），设置一个```response_time```的惩罚项，此处为10秒。
* ```CHECK_TIME_INTERVAL```， 检测周期。此处设置为每隔12小时检测一次数据库里每一个ip的可用性。


### 策略

* 每天如下5个代理ip网站上抓下最新高匿ip数据：
  * ```mimi```
  * ```66ip```
  * ```xici```
  * ```cn-proxy```
  * ```kuaidaili```
* N轮筛选
  * 收集到的ip集合将经过N轮，间隔为t的连接测试，对于每一个ip，必须全部通过这N轮测试才能最终进入数据库。如果当天进入数据库的ip较少，则暂停一段时间（一天）再抓。

* 数据库中ip评价准则
  * 检测过程中累计超时次数>```USELESS_TIME```&&成功率<```SUCCESS_RATE```就被剔除。
  ```score = (success_rate + test_times / 500) / avg_response_time```
  原来的考虑是```score = success_rate / avg_response_time```, 即：评分=成功率/平均响应时间， 考虑到检测合格过100次的老ip比新ip更有价值，检测次数也被引入评分。

### 问题反馈
联系邮箱：myfancoo@qq.com 欢迎指正。
