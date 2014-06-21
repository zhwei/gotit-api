#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web

class BaseRequestHandler(tornado.web.RequestHandler):
    pass

class RequestHandler(BaseRequestHandler):
    pass

class APIHandler(BaseRequestHandler):
    pass


application = tornado.web.Application([
    (r"/", MainHandler),
])


if __name__ == "__main__":
    application.listen(8888)
    print("listening http://0.0.0.0:8888")
    tornado.ioloop.IOLoop.instance().start()
