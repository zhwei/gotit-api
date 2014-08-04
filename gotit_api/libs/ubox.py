#!/usr/bin/env python3

from gotit_api.libs.base import BaseRequest

class UBoxRequest(BaseRequest):
    """ 友宝
    """


    login_url = "www.ubox.cn/account/login.html"


    def pre_login(self):
        """
        :return:
        """
        code_url = "http://www.ubox.cn/account/validit_picture"
        ver_code = self.get_b64_image(code_url)
        return

    def login(self, post_content):

        _phone = post_content.get("phone")
        _password = post_content.get("password")
        _validit_code = None
        data = dict(phone=_phone, password=_password,
                    validit_code=_validit_code)
        self.post(self.login_url, data)

    def dump_session(self, second=600, ver_code=None):

        # super(UBoxRequest, self).dump_session(second)
        if ver_code:
            uid = self.build_redis_key()
