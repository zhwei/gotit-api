#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = 'zhwei'

import os
import io
import json
import configparser

DIR = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(DIR, "../configs/website.ini")

def get_config():

    config = configparser.ConfigParser()
    config.read(config_path)
    return config