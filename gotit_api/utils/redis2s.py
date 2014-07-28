#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Redis Tools

import redis

class Redis:

    @staticmethod
    def get_conn():

        rdb = redis.StrictRedis(host='localhost', port=6379, db=0)
        return rdb
