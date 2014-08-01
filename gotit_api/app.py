#!/usr/bin/env python3

import tornado.gen
import tornado.web
import tornado.ioloop
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

    def get(self):

        t = zfsoft.ZfSoft()
        uid = t.login_without_verify({"xh":"1111051046","pw":"zhejiushimima"})
        self.write(uid)


settings = dict(
    debug=True,
    autoreload=True,
)

application = tornado.web.Application([
                                          (r"/", MainHandler),
                                      ], **settings)

if __name__ == "__main__":
    application.listen(options.port)
    print("listening http://0.0.0.0:{}".format(options.port))
    tornado.ioloop.IOLoop.instance().start()
