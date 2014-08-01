#!/usr/bin/python3
import os
import configparser

from gotit_api.utils.helper import singleton_func

@singleton_func
def get_config():
    """ 获取解析的配置文件
    :return:
    """
    config_path = os.path.abspath(os.path.dirname(__file__))
    config_path = os.path.join(config_path, "../configs/website.ini")
    config = configparser.ConfigParser()
    config.read(config_path)
    return config["DEFAULT"]