#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

import os
import base64
import pickle
import zipfile
import logging
import functools
from io import StringIO
from os.path import join

from gotit_api.utils import exceptions
from gotit_api.utils.redis2s import Redis


def pickle_and_b64(s):
    """ 序列化后base64编码
    :param s:
    :return:
    """
    return base64.b64encode(pickle.dumps(s))

def unb64_and_unpickle(s):
    """ base64解码后反序列化
    :param s:
    :return:
    """

    return pickle.loads(base64.b64decode(s))


def singleton_func(func):
    """实现函数返回值的单例"""
    single = None

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        nonlocal single

        if single is None:
            single = func(*args, **kwargs)

        return single

    return _wrapper

class PageAlert(object):
    """ 处理页面警告
    从redis中获取页面警告
    """

    def __getattr__(self, item):
        """从redis中获取警告内容"""
        rds = Redis.get_conn()
        alert = rds.get('Single:{}'.format(item))
        return alert

def get_unique_key(prefix=None):

    import uuid
    key = uuid.uuid4().hex
    if prefix: key = "{}{}".format(prefix, key)
    return key

def not_error_page(page):
    """检查页面
    检查页面是否有弹窗警告
    """
    import re
    res = ">alert\(\'(.+)\'\)\;"
    _m = re.search(res, page)
    if _m:
        raise exceptions.PageError(_m.group(1))
        #return _m.group(1)
    if page.find('ERROR - 出错啦！') != -1:
        raise exceptions.RequestError('正方教务系统不可用')
    return True


def zipf2strio(foldername, includeEmptyDIr=True):
    """ 压缩目录, 压缩包写入StringIO 并返回
    """
    empty_dirs = []
    fi = StringIO()
    zip = zipfile.ZipFile(fi, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(foldername):
        empty_dirs.extend([dir for dir in dirs if os.listdir(join(root, dir)) == []])
        for name in files:
            zip.write(join(root ,name))
        if includeEmptyDIr:
            for dir in empty_dirs:
                zif = zipfile.ZipInfo(join(root, dir) + "/")
                zip.writestr(zif, "")
        empty_dirs = []
    zip.close()
    return fi



def send_mail(to_list, subject, content):
    import smtplib
    from email.mime.text import MIMEText
    from gotit_api.utils.config_parser import get_config
    config = get_config()
    msg = MIMEText(content,_subtype='html',_charset='gb2312')    #创建一个实例，这里设置为html格式邮件
    msg['Subject'] = subject    #设置主题
    msg['From'] = config.DEFAULT_FROM_EMAIL
    msg['To'] = ";".join(to_list)
    try:
        s = smtplib.SMTP()
        s.connect(config.EMAIL_HOST)  #连接smtp服务器
        s.login(config.EMAIL_HOST_USER,config.EMAIL_HOST_PASSWORD)  #登陆服务器
        s.sendmail(config.DEFAULT_FROM_EMAIL, to_list, msg.as_string())  #发送邮件
        s.close()
        return True
    except Exception as e:
        logging.error(e)
        return False
