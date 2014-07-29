#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tornado.gen
import tornado.web
import tornado.ioloop
from tornado.options import define, options

from libs import zfsoft

define("port", default=1234, help="--port")

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


    @tornado.gen.coroutine
    def get(self):

        t = zfsoft.ZfSoft()
        self.write(t.pre_login())
        # uid = yield t.pre_login()
        # self.write("hello world")
        # self.finish()
        # return

settings = dict(
    debug = True,
    autoreload = True,
)

application = tornado.web.Application([
        (r"/", MainHandler),
    ], **settings)


if __name__ == "__main__":
    application.listen(options.port)
    print("listening http://0.0.0.0:{}".format(options.port))
    tornado.ioloop.IOLoop.instance().start()
