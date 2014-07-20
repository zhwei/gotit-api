#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web

from libs import zfsoft

class BaseRequestHandler(tornado.web.RequestHandler):

    pass


class APIBaseHandler(BaseRequestHandler):
    """API 基类
    其他API必须集成本类
    """

    def process(self, data):

        raise NotImplementedError


    def call(self):

        pass


class MainHandler(BaseRequestHandler):

    def get(self):

        t = zfsoft.BaseRequest()
        ret = t.get("www.baidu.com")
        self.write(ret.text)

settings = dict(
    debug = True,
    autoreload = True,
)

application = tornado.web.Application([
    (r"/", MainHandler),
])


if __name__ == "__main__":
    application.listen(8888)
    print("listening http://0.0.0.0:8888")
    tornado.ioloop.IOLoop.instance().start()
