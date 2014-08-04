#!/usr/bin/env python3
import os
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
from gotit_api.handlers.baseapihandler import APIBaseHandler

define("port", default=1234, help="--port")
define("mode", default="DEFAULT", help="--mode")

rds = Redis.get_conn()
HOME_PATH = os.path.dirname(__file__)


class BaseRequestHandler(tornado.web.RequestHandler):
    pass


class MainHandler(BaseRequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write("hello")
        t = zfsoft.ZfSoft()
        t.login_without_verify({"xh": "1111051046", "pw": "zhejiushimima"})
        content = yield tornado.gen.Task(t.get_default)


class UBoxHandler(tornado.web.RequestHandler):
    """ 友宝
    """

    def get(self):

        self.render("ubox-login.html")


class TestHandler(BaseRequestHandler):
    def test(self, callback):
        time.sleep(2)
        callback("ok")

    @tornado.gen.coroutine
    def get(self):
        s = yield tornado.gen.Task(self.test)
        self.write(s)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/ubox", UBoxHandler),
            (r"/base", APIBaseHandler),
            (r"/test", TestHandler),
        ]
        settings = dict(
            xsrf_cookies=True,
            cookie_secret="hello-world-listen",
            static_path=os.path.join(HOME_PATH, "static"),
            template_path=os.path.join(HOME_PATH, "templates"),
            debug=True,
            autoreload=True,
        )
        super(Application, self).__init__(handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(int(options.port))
    print("listening http://0.0.0.0:{}".format(options.port))
    tornado.ioloop.IOLoop.instance().start()