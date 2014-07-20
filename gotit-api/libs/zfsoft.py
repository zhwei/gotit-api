#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

import requests

from ..utils import exceptions
from ..utils.redis2s import Redis

class BaseRequest:

    headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': ('Mozilla/5.0 (X11; Ubuntu; Linux i686;'
                            'rv:18.0) Gecko/20100101 Firefox/18.0'),
        }

    site_name = None
    def __init__(self, site_name=None):

        if site_name: self.site_name = site_name

    def set_referer(self, referer):
        """ Set Header Referer
        :param referer: Header referer
        :return: None
        """
        self.headers["Referer"] = referer


    def check_page(self, req_text):
        """ 检查页面是否合理
        如果不合理则抛出异常
        :param req_text: utf-8 html content
        :return: None
        """
        pass

    def pre_request(self, func):

        def do_request(*args, **kwargs):
            try:
                _req = func(*args, **kwargs)
            except requests.ConnectionError:
                msg = 'Can Not Connect to {}'.format(self.site_name)
                logging.error(msg)
                raise exceptions.RequestError(msg)
            self.check_page(_req.text)
            return _req

        return do_request()

    @pre_request
    def get(self, *args, **kwargs):

        try:
            _req = requests.get(*args, **kwargs)
        except requests.ConnectionError:
            msg = 'Can Not Connect to {}'.format(self.site_name)
            logging.error(msg)
            raise exceptions.RequestError(msg)

        self.check_page(_req.text)
        return _req

    def post(self, data):

        pass


# if __name__ == '__main__':
