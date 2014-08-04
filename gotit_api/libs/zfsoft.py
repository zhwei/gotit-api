#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import base64
import pickle
from urllib.parse import urlparse

import tornado.gen
from tornado.ioloop import IOLoop
from tornado.concurrent import return_future
import lxml.etree as lxml_etree

from gotit_api.utils import exceptions
from gotit_api.utils.redis2s import Redis
from gotit_api.libs.base import BaseRequest
from gotit_api.utils.config_parser import get_config
# from gotit_api.utils.factory import (TimeTableJsonFactory,
#                                      ScoreJsonFactory)

VIEW_STATE_PAR = re.compile(r'name="__VIEWSTATE" value="(.*?)"')


class ZfSoft(BaseRequest):
    """ 正方教务系统相关
    """
    xh = None
    token = None
    _image = None
    base_url = None
    site_name = "ZfSoft"
    rds = Redis.get_conn()

    # def __init__(self, io_loop=None, **kwargs):
    #     super(ZfSoft, self).__init__(**kwargs)
    #     self.io_loop = io_loop or IOLoop.current()

    def __process_url(self, init=False, login_postfix=None):
        """ 处理相关url
        调用此函数需要设置init为True或者self.base_url已经存在
        :return:
        """
        if init:
            config = get_config()
            if config.get("zf_hash"):
                url_with_hash = self.get(config.get("zf_url")).url
                _hash_str = url_with_hash.split('/')[-2]
                self.base_url = config.get("zf_url") + _hash_str + '/'
            else:
                self.base_url = config.get("zf_url")
        login_postfix = login_postfix if login_postfix else "Default2.aspx"
        self.login_url = self.base_url + login_postfix
        self.code_url = self.base_url + 'CheckCode.aspx'
        self.req.headers.update(dict(
            Host=urlparse(self.base_url).netloc,
            Referer=self.login_url,
        ))

    def __get_token(self, page):
        """ 获取网页中VIEWSTATE参数， 提交时实用
        :param page: 网页内容
        :return:
        """
        try:
            token = VIEW_STATE_PAR.findall(page)[0]
        except IndexError:
            raise exceptions.PageError("请求错误, 请重新查询")
        return token

    def pre_login(self):
        """ 存在验证码时登录前的准备
        """
        self.__process_url(True)  # 获取base_url, 处理获取其他相关url
        self.token = self.__get_token(self.get(self.base_url).text)
        ver_code = self.get_b64_image(self.code_url)
        return self.dump_session(checkcode=ver_code)

    def do_login(self, post_content):
        """ 登录用户
        :param post_content:
        :return:
        """
        self.xh = post_content.get("xh")
        __pw = post_content.get("pw")
        __verify = post_content.get("verify")
        data = {
            'Button1': '',
            'RadioButtonList1': "学生",
            "txtUserName": self.xh,
            'TextBox2': __pw,
            'txtSecretCode': __verify,
            '__VIEWSTATE': self.token,
            'lbLanguage': '',
        }
        self.post(url=self.login_url, data=data)  # 登录操作
        self.rds.hset(self.uid, "xh", self.xh)
        self.rds.pexpire(self.uid, 600)  # 延时
        self.logged = True
        # self.dump_session()     # 持久化
        return self.uid

    def check_page(self, req_text):

        res = ">alert\(\'(.+)\'\)\;"
        _m = re.search(res, req_text)
        if _m:
            raise exceptions.PageError(_m.group(1))
        if req_text.find('ERROR - 出错啦！') != -1:
            raise exceptions.RequestError('无法连接到正方教务系统')
        return True

    def dump_session(self, second=600, checkcode=None):
        """ 重写持久化
        :param second:
        :return:
        """
        if not self.logged:
            uid = self.build_redis_key()
            self.rds.hmset(uid, dict(token=self.token,
                                     base_url=self.base_url,
                                     session=pickle.dumps(self.req),
                                     checkcode=checkcode, ), )
        else:
            uid = super(ZfSoft, self).dump_session()
        return uid

    def load_session(self, uid):
        """ 读取持久化信息
        :param uid:
        :return:
        """
        if not self.logged:
            _data = self.rds.hgetall(uid)
            self.token = _data.get(b"token").decode()
            self.base_url = _data.get(b"base_url").decode()
            self.req = pickle.loads(_data.get(b"session"))
        else:
            super(ZfSoft, self).load_session(uid)
        self.__process_url()  # 根据上面获取到的base_url获取其他url

    def login_without_verify(self, post_content):
        """ 无验证码登录接口
        :return:
        """
        self.xh = post_content.get('xh')
        __pw = post_content.get('pw')
        self.__process_url(init=True, login_postfix="default6.aspx")
        _token = self.__get_token(self.get(self.login_url).text)
        data = dict(tname='', tbtns='', tnameXw='yhdl',
                    tbtnsXw='yhdl|xwxsdl', tbtnsXm='', rblJs="学生",
                    txtYhm=self.xh, txtMm=__pw,
                    __VIEWSTATE=_token, btnDl='登 录')
        self.post(url=self.login_url, data=data)    # 登录请求
        self.dump_session()
        return self.uid

    def another_request(self,url ,data=None):
        """ 用于登录后的请求操作
        :param url: 请求url
        :param data: 发送的数据，如果为空则使用get，不为空使用post
                    不需要传送 `__VIEWSTATE`参数
        :return: 页面内容 string
        """
        if data:
            token = self.__get_token(self.get(url).text)
            data["__VIEWSTATE"] = token
            ret = self.post(url, data)
        else:
            ret = self.get(url)
        return ret.text

    def get_timetable_by_year(self, fy=None, ty=None, term="1", default=False):
        """ 按照给定学年，学期抓取信息
        :param fy: 开始学年
        :param ty: 结束学年
        :param term: 第几学期
        :return:
        """
        url = self.base_url + 'xskbcx' + ".aspx?xh=" + self.xh
        if default:     # 返回默认内容
            html = self.another_request(url)
        else:
            data = dict(__EVENTTARGET="xqd", __EVENTARGUMENT="",
                        xnd='{0}-{1}'.format(fy, ty),
                        xqd="{0}".format(term))
            html = self.another_request(url, data)
        tree = lxml_etree.HTML(html)
        normal_table = tree.xpath("//table[@id='Table1']")[0]
        other_1 = tree.xpath("//table[@id='DBGrid']")[0]
        other_2 = tree.xpath("//table[@id='Table3']")[0]
        for i in (normal_table, other_1, other_2):
            yield lxml_etree.tostring(i)

    def get_score_by_year(self, fy=None, ty=None, term="1", default=False):
        """ 按学年获取成绩内容
        :param fy:
        :param ty:
        :param term:
        :return:
        """
        url = self.base_url + 'xscjcx_dq' + ".aspx?xh=" + self.xh
        if default:     # 返回默认内容
            html = self.another_request(url)
        else:
            data = dict(__EVENTTARGET="", __EVENTARGUMENT="",
                        ddlxn='{0}-{1}'.format(fy, ty),
                        ddlxq="{0}".format(term), btnCx=" 查  询 ")
            html = self.another_request(url, data)
        tree = lxml_etree.HTML(html)
        normal_table = tree.xpath("//table[@id='DataGrid1']")[0]
        # for i in (normal_table,):
        #     yield lxml_etree.tostring(i)
        return lxml_etree.tostring(normal_table)

    def gen_timetable_json(self, html_body):
        """ 生成课表json
        :param html_body:
        :return:
        """
        # k = TimeTableJsonFactory(html_body)
        # return k.get_json()

    def gen_score_json(self, html_body):
        """ 生成成绩json
        :param html_body:
        :return:
        """
        # return ScoreJsonFactory.get_list(html_body)

    # @return_future
    # @tornado.gen.coroutine
    def get_default(self, callback=None):

        # response = self.get_score_by_year(default=True)
        response = self.get("http://baidu.com").text

        return callback(response)
