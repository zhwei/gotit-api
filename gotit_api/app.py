#!/usr/bin/env python3
import time

import requests
import tornado.gen
import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.httpclient
from tornado.options import define, options

from gotit_api.libs import zfsoft
from gotit_api.utils.redis2s import Redis

define("port", default=1234, help="--port")
define("mode", default="DEFAULT", help="--mode")

rds = Redis.get_conn()

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

        self.write("hello")
        t = zfsoft.ZfSoft()
        t.login_without_verify({"xh":"1111051046","pw":"zhejiushimima"})
        content = yield tornado.gen.Task(t.get_default)


class TestHandler(BaseRequestHandler):

    def test(self, callback):

        time.sleep(2)
        callback("ok")

    @tornado.gen.coroutine
    def get(self):

        s = yield tornado.gen.Task(self.test)
        self.write(s)


settings = dict(
    debug=True,
    autoreload=True,
)

from gotit_api.handlers.basehandler import APIBaseHandler

application = tornado.web.Application([
                                          (r"/", MainHandler),
                                          (r"/base", APIBaseHandler),
                                          (r"/test", TestHandler),
                                      ], **settings)

def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    print("listening http://0.0.0.0:{}".format(options.port))
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()