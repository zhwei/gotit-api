#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import time
import base64
import pickle
import logging
import requests

import tornado.gen

from gotit_api.libs import images
from gotit_api.utils import exceptions
from gotit_api.utils.redis2s import Redis
from gotit_api.utils.utils import get_unique_key
from gotit_api.utils.config_parser import get_config

class BaseRequest:

    headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': ('Mozilla/5.0 (X11; Ubuntu; Linux i686;'
                            'rv:18.0) Gecko/20100101 Firefox/18.0'),
        }

    site_name = None
    cookies = None


    def __init__(self, site_name=None):

        self.site_name = site_name

    def check_page(self, req_text):
        """ 检查页面是否合理
        如果不合理则抛出异常
        :param req_text: utf-8 html content
        :return: None
        """
        pass

    def get(self, url, cookies=None, *args, **kwargs):

        try:
            _req = requests.get(url, cookies=cookies, *args, **kwargs)
            self.cookies = cookies if cookies else _req.cookies
        except requests.ConnectionError:
            msg = 'Can Not Connect to {}'.format(self.site_name)
            logging.error(msg)
            raise exceptions.RequestError(msg)

        self.check_page(_req.text)
        return _req

    def post(self, url, data, *args, **kwargs):

        try:
            _req = requests.post(url, data, cookies=self.cookies,
                                 headers=self.headers, *args, **kwargs)
        except requests.ConnectionError:
            msg = 'Can Not Connect to {}'.format(self.site_name)
            logging.error(msg)
            raise exceptions.RequestError(msg)

        self.check_page(_req.text)
        return _req


USER_RDS_PREFIX = "User:ZF:"


class ZfSoft(BaseRequest):

    """ 正方教务系统相关
    """

    def __init__(self, *args, **kwargs):

        super(ZfSoft, self).__init__(*args, **kwargs)

        config = get_config()["DEFAULT"]
        if config.get("zf_hash"):
            url_with_hash = self.get(config.get("zf_url")).url
            _hash_str = url_with_hash.split('/')[-2]
            self.base_url = config.get("zf_url") + _hash_str + '/'
        else:
            self.base_url = config.get("zf_url")

        self.login_url = self.base_url + "Default2.aspx"
        self.code_url = self.base_url + 'CheckCode.aspx'
        self.headers["Host"] = self.base_url

        self.rds = Redis.get_conn()

    def __get_token(self, page):
        """ 获取网页中VIEWSTATE参数， 提交时实用
        :param page: 网页内容
        :return:
        """
        try:
            com = re.compile(r'name="__VIEWSTATE" value="(.*?)"')
            vs = com.findall(page)[0]
        except IndexError:
            self.rds.hset('Error:Hash:zfr:GetVsIndexError', time.time(), page)
            raise exceptions.PageError("请求错误, 请重新查询")
        return vs

    def pre_login(self):
        """ 存在验证码时登录前的准备
        """
        uid = get_unique_key(prefix=USER_RDS_PREFIX)
        self.token = self.__get_token(self.get(self.base_url).text)
        # base64_image = images.get_base64_image(self.get(self.code_url).text)
        _image = self.get(self.code_url).text
        self.rds.hmset(uid, {       # cache in redis
                "checkcode" : base64.b64encode(pickle.dumps(_image)),
                "base_url"  : self.base_url,
                "viewstate" : self.token,
                'cookies'   : base64.b64encode(pickle.dumps(self.cookies)),
            })
        self.rds.pexpire(uid, 600000) # set expire time(milliseconds)
        return uid
