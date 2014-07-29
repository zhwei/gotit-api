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
from gotit_api.libs.base import BaseRequest
from gotit_api.utils.utils import get_unique_key
from gotit_api.utils.config_parser import get_config


class ZfSoft(BaseRequest):

    """ 正方教务系统相关
    """
    site_name = "ZfSoft"

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
        self.token = self.__get_token(self.get(self.base_url).text)
        self._image = self.get(self.code_url).text
        return self.dump_session(pre=True)


    def dump_session(self, second=600, pre_login=False):

        if pre_login:
            uid = self.build_redis_key()
            self.rds.hmset(uid, {       # cache in redis
                    "token" : self.token,
                    "base_url"  : self.base_url,
                    "session" : pickle.dumps(self.req),
                    "code" : base64.b64encode(pickle.dumps(self._image)),
                })
        else:
            super(ZfSoft, self).dump_session()