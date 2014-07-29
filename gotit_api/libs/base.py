#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import time
import base64
import pickle
import logging
import functools

import requests

from gotit_api.libs import images
from gotit_api.utils import exceptions
from gotit_api.utils.redis2s import Redis
from gotit_api.utils.utils import get_unique_key
from gotit_api.utils.config_parser import get_config

class BaseRequest:

    site_name = "DEFAULT_SITE_NAME"     # 用于持久化等操作中的标志
    headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': ('Mozilla/5.0 (X11; Ubuntu; Linux i686;'
                            'rv:18.0) Gecko/20100101 Firefox/18.0'),
        }

    def __init__(self, site_name=None):
        """ 初始化必要变量
        :param site_name: 站点名称， 英文
        :return: None
        """
        if site_name: self.site_name = site_name

        self.req = requests.Session()
        self.req.headers.update(self.headers)

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
                                self.req.headers,
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
        key = self.build_redis_key()
        rds.setex(key, pickle.dumps(self.req))
        return key

    def load_session(self, key):
        """ 加载持久化的Session
        推荐重写此方法和dump_session()
        :param key: Redis中的键值 [string]
        :return: None
        """
        rds = Redis.get_conn()
        _data = rds.get(key)
        if _data:
            self.req = pickle.loads(_data)
        else:
            raise Exception("Can not load from redis")
