import unittest

from iconservice.base.exception import ExceptionCode, IconException
from iconservice.base.exception import ExternalException, PayableException
from iconservice.base.exception import check_exception


class TestCheckException(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @check_exception
    def check_built_in_exception_func1(self):
        raise Exception('built_in_func1 raise exception')

    @check_exception
    def check_external_exception_func1(self):
        raise ExternalException('external_exception_func1 raise exception', 'func_name', 'cls_name')

    @check_exception
    def check_payable_exception_func1(self):
        raise PayableException('external_exception_func1 raise exception', 'func_name', 'cls_name')

    def call_check_external_exception_func1(self):
        return self.check_external_exception_func1()

    @check_exception
    def check_call_check_external_exception_func1(self):
        return self.check_external_exception_func1()

    def test_external_exception_call(self):
        self.assertRaises(Exception, self.check_built_in_exception_func1)

        #handling exception
        #self.check_external_exception_func1()
        #self.call_check_external_exception_func1()
        #self.check_call_check_external_exception_func1()

    @check_exception
    def check_icx_error_func1(self, code: ExceptionCode):
            raise IconException(code)

    def loop_icx_error_func1(self):
        for code in ExceptionCode:
            self.check_icx_error_func1(code)

    @check_exception
    def check_loop_icx_error_func1(self):
        return self.loop_icx_error_func1()

    def test_icx_error_call(self):

        # handling exception
        #  self.check_icx_error_func1(ErrorCode.OK)
        # self.loop_icx_error_func1()
        # self.check_loop_icx_error_func1()
        pass

    def raise_icx_exception(self):
        raise IconException(ExceptionCode.OK)

    def call_raise_icx_exception1(self):
        return self.raise_icx_exception()

    def call_raise_icx_exception2(self):
        return self.call_raise_icx_exception1()

    def call_raise_icx_exception3(self):
        return self.call_raise_icx_exception2()

    @check_exception
    def check_call_raise_icx_exception3(self):
        return self.call_raise_icx_exception2()

    def test_non_check_icx_error(self):
        self.assertRaises(IconException, self.call_raise_icx_exception3)

        # handling exception
        #self.check_call_raise_icx_error3()


if __name__ == '__main__':
    unittest.main()
