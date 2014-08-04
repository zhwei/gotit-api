#!/usr/bin/env python3
""" API 请求的基类， 添加新的接口需要 APIBaseHandler
推荐在本文件夹中创建同名python文件
"""
import tornado.web
import tornado.escape as tor_escape


class APIBaseHandler(tornado.web.RequestHandler):
    """ API处理基类
    """
    message = "success"

    def get(self):

        pass

    def process(self, data):
        """重写此方法处理请求
        """

        return []

    def post(self):
        """ POST请求
        """
        # 设置http头信息
        self.set_header('Content-Type', 'application/json;charset=UTF-8')
        self.set_status(200)

        req_body_raw = self.request.body.decode()
        req_body = tor_escape.json_decode(req_body_raw)

        # 构造返回json
        result = dict(status=self.get_status(), message=self.message,)
        result.update(dict(data=self.process(req_body)))    # 调用process方法处理数据
        json_ret = tor_escape.json_encode(result)
        self.write(json_ret)