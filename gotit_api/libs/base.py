#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import base64
import pickle
import logging

import requests

from gotit_api.utils import exceptions
from gotit_api.utils.redis2s import Redis
from gotit_api.utils.helper import get_unique_key

class BaseRequest:
    """ 爬虫基类
    一个可扩展请求的基类，要满足的条件：
        + 满足需要登录的情形
        + 对Session持久化
        + 可扩展的异常处理
    """
    site_name = "DEFAULT_SITE_NAME"     # 用于持久化等操作中的标志
    logged = False
    data = dict()

    def __init__(self, uid=None, site_name=None):
        """ 初始化必要变量
        :param site_name: 站点名称， 英文
        :return: None
        """
        if uid:
            self.load_session(uid)
        else:
            self.req = requests.Session()
            __headers = {
                'Connection': 'Keep-Alive',
                'User-Agent': ('Mozilla/5.0 (X11; Ubuntu; Linux i686;'
                                'rv:18.0) Gecko/20100101 Firefox/18.0'),
            }
            self.req.headers.update(__headers)
            if site_name:
                self.site_name = site_name
            uid = self.build_redis_key()
        self.uid = uid

    def check_page(self, req_text):
        """ 检查页面是否合理
        如果不合理则抛出异常
        :param req_text: utf-8 html content
        :return: None
        """
        pass

    def get(self, url):
        """ GET
        :param url:
        :return:
        """
        _req = requests.Request("GET", url,
                                headers=self.req.headers)
        prepped = _req.prepare()
        return self.do_request(prepped)

    def post(self, url, data):
        """ POST
        :param url:
        :param data:
        :return:
        """
        _req = requests.Request("POST", url,
                                headers=self.req.headers,
                                data=data)
        prepped = _req.prepare()
        return self.do_request(prepped)

    def do_request(self, prepped):
        """ 实际请求操作
        :param prepped: req.prepare
        :return:
        """
        try:
            _req = self.req.send(prepped)
            self.check_page(_req.text)
            return _req
        except requests.ConnectionError:
            msg = 'Can Not Connect to {}'.format(self.site_name)
            logging.error(msg)
            raise exceptions.RequestError(msg)

    def build_redis_key(self):
        """ 创建唯一持久化key
        :return:
        """
        key = get_unique_key("Request:{0}:".format(self.site_name))
        return key

    def dump_session(self, second=600):
        """ 持久化Session
        默认序列化后放入Redis， 推荐重写本方法和load_session()
        :param second: 缓存时间，单位为秒 [int]
        :return: Redis中的key [string]
        """
        rds = Redis.get_conn()
        self.data["session"] = pickle.dumps(self.req)
        rds.hmset(self.uid, self.data)
        return self.uid

    def load_session(self, uid):
        """ 加载持久化的Session
        推荐重写此方法和dump_session()
        :param uid: Redis中的键值 [string]
        :return: None
        """
        rds = Redis.get_conn()
        _data = rds.get(uid)
        if _data:
            self.req = pickle.loads(_data)
        else:
            raise Exception("Can not load from redis")

    def get_b64_image(self, code_url):
        """ 获取经过Base64转码后的图片
        返回结果可以直接在浏览器地址栏中打开
        :return:
        """
        ver_code = self.get(code_url).content      # 获取图片
        ver_code = base64.b64encode(ver_code).decode().replace('\n', '')
        ver_code = "data:image/gif\;base64,{}".format(ver_code)
        return ver_code