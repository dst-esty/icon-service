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
from ..base.exception import IconServiceBaseException


class IconScoreStepCounterFactory(object):
    """Creates a step counter for the transaction
    """

    def __init__(
            self,
            default_step: int = 0,
            sset_step_unit: int = 0,
            sreplace_step_unit: int = 0,
            sdelete_step_unit: int = 0,
            transfer_step_unit: int = 0,
            msgcall_step_unit: int = 0,
            eventlog_step_unit: int = 0) -> None:
        """Constructor

        :param default_step: default steps for every single transaction
        :param sset_step_unit: a base step unit for newly storing to DB
        :param sreplace_step_unit: a base step unit for modifying DB
        :param sdelete_step_unit: a base step unit for deleting key/value from DB
        :param transfer_step_unit: a base step unit for transferring ICX
        :param msgcall_step_unit: a base step unit for calling to another SCORE
        :param eventlog_step_unit: a base step unit for logging.
        """
        self.default_step = default_step
        self.sset_step_unit = sset_step_unit
        self.sreplace_step_unit = sreplace_step_unit
        self.sdelete_step_unit = sdelete_step_unit
        self.transfer_step_unit = transfer_step_unit
        self.msgcall_step_unit = msgcall_step_unit
        self.eventlog_step_unit = eventlog_step_unit

    def create(self, step_limit: int) -> 'IconScoreStepCounter':
        """Creates a step counter for the transaction

        :param step_limit: step limit of the transaction
        :return: step counter
        """
        return IconScoreStepCounter(
            self.default_step,
            self.sset_step_unit,
            self.sreplace_step_unit,
            self.sdelete_step_unit,
            self.transfer_step_unit,
            self.msgcall_step_unit,
            self.eventlog_step_unit,
            step_limit)


class OutOfStepException(IconServiceBaseException):
    """ An Exception which is thrown when steps are exhausted.
    """

    def __init__(self, step_limit: int, step_used: int,
                 requested_step: int) -> None:
        """Constructor

        :param step_limit: step limit of the transaction
        :param step_used: used steps in the transaction
        :param requested_step: consuming steps before the exception is thrown
        """
        self.__step_limit: int = step_limit
        self.__step_used = step_used
        self.__requested_step = requested_step

    @property
    def message(self) -> str:
        """
        Returns the exception message
        :return: the exception message
        """
        return f'\'Requested steps\': {self.requested_step}, ' \
               f'\'Remaining steps\': {self.step_limit - self.step_used} '

    @property
    def step_limit(self) -> int:
        """
        Returns step limit of the transaction
        :return: step limit of the transaction
        """
        return self.__step_limit

    @property
    def step_used(self) -> int:
        """
        Returns used steps before the exception is thrown in the transaction
        :return: used steps in the transaction
        """
        return self.__step_used

    @property
    def requested_step(self) -> int:
        """
        Returns consuming steps before the exception is thrown.
        :return: Consuming steps before the exception is thrown.
        """
        return self.__requested_step


class IconScoreStepCounter(object):
    """ Counts steps in a transaction
    """

    def __init__(self,
                 default_step: int,
                 sset_step_unit: int,
                 sreplace_step_unit: int,
                 sdelete_step_unit: int,
                 transfer_step_unit: int,
                 msgcall_step_unit: int,
                 eventlog_step_unit: int,
                 step_limit: int) -> None:
        """Constructor

        :param default_step: default steps for every single transaction
        :param sset_step_unit: a base step unit for newly storing to DB
        :param sreplace_step_unit: a base step unit for modifying DB
        :param sdelete_step_unit: a base step unit for deleting key/value from DB
        :param transfer_step_unit: a base step unit for transferring ICX
        :param msgcall_step_unit: a base step unit for calling to another SCORE
        :param eventlog_step_unit: a base step unit for logging.
        :param step_limit: step limit of the transaction
        """
        self.__step_used: int = default_step
        self.__sset_step_unit = sset_step_unit
        self.__sreplace_step_unit = sreplace_step_unit
        self.__sdelete_step_unit = sdelete_step_unit
        self.__transfer_step_unit = transfer_step_unit
        self.__msgcall_step_unit = msgcall_step_unit
        self.__eventlog_step_unit = eventlog_step_unit
        self.__step_limit: int = step_limit

    @property
    def step_used(self) -> int:
        """
        Returns used steps in the transaction
        :return: used steps in the transaction
        """

        if self.__step_used < 0:
            return 0
        return self.__step_used

    @property
    def step_limit(self) -> int:
        """
        Returns step limit of the transaction
        :return: step limit of the transaction
        """
        return self.__step_limit

    def increase_sset_step(self, data_size: int) -> int:
        """ Increases steps for newly storing to DB
        """
        return self.__increase_step(data_size * self.__sset_step_unit)

    def increase_sreplace_step(self, data_size: int) -> int:
        """ Increases steps for modifying DB
        """
        return self.__increase_step(data_size * self.__sreplace_step_unit)

    def increase_sdelete_step(self, data_size: int) -> int:
        """ Increases steps for deleting key/value from DB
        """
        return self.__increase_step(data_size * self.__sdelete_step_unit)

    def increase_transfer_step(self, count: int) -> int:
        """ Increases transfer step when transferring icx
        """
        return self.__increase_step(count * self.__transfer_step_unit)

    def increase_msgcall_step(self, count: int) -> int:
        """ Increases message call step when internal calling in a transaction.
        """
        return self.__increase_step(count * self.__msgcall_step_unit)

    def increase_eventlog_step(self, data_size: int) -> int:
        """ Increases log step when logging.
        """
        return self.__increase_step(data_size * self.__eventlog_step_unit)

    def __increase_step(self, step_to_increase) -> int:
        """ Increases step
        """

        if step_to_increase + self.step_used > self.__step_limit:
            raise OutOfStepException(self.__step_limit, self.step_used,
                                     step_to_increase)
        self.__step_used += step_to_increase
        return self.__step_used