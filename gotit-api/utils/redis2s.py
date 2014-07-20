#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Redis Tools

import redis

class Redis:

    def get_conn(self):

        rdb = redis.StrictRedis(host='localhost', port=6379, db=0)
        return rdb
