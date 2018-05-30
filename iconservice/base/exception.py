# -*- coding: utf-8 -*-

# Copyright 2017-2018 theloop Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import IntEnum, unique
from functools import wraps
from ..logger import Logger

from ..icon_config import *


@unique
class ExceptionCode(IntEnum):
    """Result code enumeration

    Refer to http://www.simple-is-better.org/json-rpc/jsonrpc20.html#examples
    """
    OK = 0

    # -32000 ~ -32099: Server error
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    PARSE_ERROR = -32700

    LOCKED_ACCOUNT = -40000
    NOT_ENOUGH_BALANCE = -40001
    INVALID_FEE = -40002

    def __str__(self) -> str:
        if self.value == self.INVALID_REQUEST:
            return "Invalid Request"
        else:
            return str(self.name).capitalize().replace('_', ' ')


# 아이콘 서비스에서 사용하는 모든 예외는 다음을 상속받는다.
class IconServiceBaseException(BaseException):

    def __init__(self, message: str):
        self.__message = message

    @property
    def message(self):
        return self.__message

    def __str__(self):
        return f'{self.message}'


class DatabaseException(IconServiceBaseException):
    pass


class IconException(IconServiceBaseException):
    """Defines Icx Errors
    """
    def __init__(self, code: ExceptionCode, message: str = None) -> None:
        if message is None or message == '':
            message = str(code)

        super().__init__(message)
        self._code = code

    @property
    def code(self):
        return self._code

    def __str__(self):
        return f'{self.message} ({self.code})'


class IconScoreException(IconServiceBaseException):
    def __init__(self, message: str) -> None:
        super().__init__(message)


class APIIconScoreBaseException(IconScoreException):
    def __init__(self, message: str, func_name: str, cls_name: str) -> None:
        super().__init__(message)
        self.__func_name = func_name
        self.__cls_name = cls_name

    @property
    def func_name(self):
        return self.__func_name

    @property
    def cls_name(self):
        return self.__cls_name

    def __str__(self):
        return f'msg: {self.message} func: {self.func_name} cls: {self.cls_name}'


def check_exception(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IconServiceBaseException as e:
                Logger.exception(e, ICON_EXCEPTION_LOG_TAG)
        except Exception as e:
            Logger.exception(e, ICON_EXCEPTION_LOG_TAG)
            raise e
        finally:
            pass
    return _wrapper


class ExternalException(APIIconScoreBaseException):
    pass


class PayableException(APIIconScoreBaseException):
    pass


class ScoreInstallException(IconScoreException):
    pass


class ScoreInstallExtractException(IconScoreException):
    pass


class ContainerDBException(IconScoreException):
    pass
