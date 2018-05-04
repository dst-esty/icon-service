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


import json
import os
import hashlib



from .base.address import Address, AddressPrefix, ICX_ENGINE_ADDRESS, create_address
from .base.exception import ExceptionCode, IconException
from .base.block import Block
from .base.message import Message
from .base.transaction import Transaction
from .database.factory import DatabaseFactory
from .database.batch import BlockBatch, TransactionBatch
from .icx.icx_engine import IcxEngine
from .icx.icx_storage import IcxStorage
from .iconscore.icon_score_info_mapper import IconScoreInfoMapper
from .iconscore.icon_score_context import IconScoreContext
from .iconscore.icon_score_context import IconScoreContextType
from .iconscore.icon_score_context import IconScoreContextFactory
from .iconscore.icon_score_engine import IconScoreEngine
from .iconscore.icon_score_loader import IconScoreLoader
from .iconscore.icon_score_result import IconBlockResult, TransactionResult, \
    JsonSerializer

TEST_SCORE_ADDRESS = create_address(AddressPrefix.CONTRACT, b'test')


class IconServiceEngine(object):
    """The entry of all icon service related components

    It MUST NOT have any loopchain dependencies.
    It is contained in IconOuterService.
    """

    def __init__(self) -> None:
        """Constructor

        :param icon_score_root_path:
        :param state_db_root_path:
        """
        # jsonrpc handlers
        self._handlers = {
            'icx_getBalance': self._handle_icx_getBalance,
            'icx_getTotalSupply': self._handle_icx_getTotalSupply,
            'icx_call': self._handle_icx_call,
            'icx_sendTransaction': self._handle_icx_sendTransaction
        }

    def open(self,
             icon_score_root_path: str,
             state_db_root_path: str) -> None:
        """Get necessary paramters and initialize

        :param icon_score_root_path:
        :param state_db_root_path:
        """
        if not os.path.isdir(icon_score_root_path):
            os.mkdir(icon_score_root_path)
        if not os.path.isdir(state_db_root_path):
            os.mkdir(state_db_root_path)

        self._db_factory = DatabaseFactory(state_db_root_path)
        self._context_factory = IconScoreContextFactory(max_size=5)
        self._icon_score_loader = IconScoreLoader('score')

        # TODO have to get IcxStorage!
        self._icx_storage = IcxStorage(None)

        self._icon_score_mapper = IconScoreInfoMapper(self._icx_storage, self._db_factory, self._icon_score_loader)
        self._icon_score_engine = IconScoreEngine(self._icx_storage, self._icon_score_mapper)

        self._init_icx_engine(self._db_factory)

        IconScoreContext.icx = self._icx_engine
        IconScoreContext.icon_score_mapper = self._icon_score_mapper

    def _init_icx_engine(self, db_factory: DatabaseFactory) -> None:
        """Initialize icx_engine

        :param db_factory:
        """
        db = db_factory.create_by_name('icon_dex')
        db.address = ICX_ENGINE_ADDRESS

        self._icx_engine = IcxEngine()
        self._icx_engine.open(db)

    def close(self) -> None:
        self._icx_engine.close()

    def genesis_invoke(self, accounts: list) -> None:
        """Process the list of account info in the genesis block

        :param accounts: account infos in the genesis block
        """

        context = self._context_factory.create(IconScoreContextType.GENESIS)

        genesis_account = accounts[0]
        self._icx_engine.init_genesis_account(
            context=context,                
            address=genesis_account['address'],
            amount=genesis_account['balance'])

        fee_treasury_account = accounts[1]
        self._icx_engine.init_fee_treasury_account(
            context=context,                
            address=fee_treasury_account['address'],
            amount=fee_treasury_account['balance'])

        self._context_factory.destroy(context)

    def invoke(self,
               block_height: int,
               block_hash: str,
               transactions) -> list:
        """Process transactions in a block sent by loopchain

        :param block_height:
        :param block_hash:
        :param transactions: transactions in a block
        :return: The results of transactions
        """
        # Remaining part of a IconScoreContext will be set in each handler.
        context = self._context_factory.create(IconScoreContextType.INVOKE)
        context.block = Block(block_height, block_hash)
        context.block_batch = BlockBatch(block_height, block_hash)
        context.tx_batch = TransactionBatch()
        context.block_result = IconBlockResult(JsonSerializer())

        for tx in transactions:
            method = tx['method']
            params = tx['params']
            self.call(context, method, params)

            context.tx_batch.clear()

        self._context_factory.destroy(context)

    def query(self, method: str, params: dict) -> object:
        """Process a query message call from outside

        State change is not allowed in a query message call

        * icx_getBalance
        * icx_getTotalSupply
        * icx_call

        :param method:
        :param params:
        :return: the result of query
        """
        context = self._context_factory.create(IconScoreContextType.QUERY)

        ret = self.call(context, method, params)

        self._context_factory.destroy(context)

        return ret

    def call(self,
             context: IconScoreContext,
             method: str,
             params: dict) -> object:
        """Call invoke and query requests in jsonrpc format

        This method is designed to be called in icon_outer_service.py.
        We assume that all param values have been already converted to the proper types.
        (types: Address, int, str, bool, bytes and array)

        invoke: Changes states of icon scores or icx
        query: query states of icon scores or icx without state changing

        :param context:
        :param method: 'icx_sendTransaction' only
        :param params: params in jsonrpc message
        :return:
            icx_sendTransaction: (bool) True(success) or False(failure)
            icx_getBalance, icx_getTotalSupply, icx_call:
                (dict) result or error object in jsonrpc response
        """
        try:
            handler = self._handlers[method]
            return handler(context, params)
        except KeyError as ke:
            print(ke)
        except Exception as e:
            print(e)

    def _handle_icx_getBalance(self,
                               context: IconScoreContext,
                               params: dict) -> int:
        """Returns the icx balance of the given address

        :param context:
        :param params:
        :return: icx balance in loop
        """
        address = params['address']
        return self._icx_engine.get_balance(context, address)

    def _handle_icx_getTotalSupply(self, context: IconScoreContext) -> int:
        """Returns the amount of icx total supply

        :param context:
        :return: icx amount in loop (1 icx == 1e18 loop)
        """
        return self._icx_engine.get_total_supply(context)

    def _handle_icx_call(self,
                         context: IconScoreContext,
                         params: dict) -> object:
        """Handles an icx_call jsonrpc request
        :param params:
        :return:
        """
        _from: Address = params['from']
        _to: Address = params['to']
        _data_type = params.get('data_type', None)
        _data = params.get('data', None)

        context.tx = Transaction(origin=_from)
        context.msg = Message(sender=_from)

        return self._icon_score_engine.query(_to, context, _data_type, _data)

    def _handle_icx_sendTransaction(self,
                                    context: IconScoreContext,
                                    params: dict) -> object:
        """icx_sendTransaction message handler

        * EOA to EOA
        * EOA to Score

        :param params: jsonrpc params
        :return: return value of an IconScoreBase method
            None is allowed
        """
        _tx_hash = params['tx_hash']
        _from: Address = params['from']
        _to: Address = params['to']
        _value: int = params.get('value', 0)
        _fee: int = params['fee']

        self._icx_engine.transfer(context, _from, _to, _value)

        if _to is None or _to.is_contract:
            # EOA to Score
            _data_type: str = params['data_type']
            _data: dict = params['data']
            _tx_result = self.__handle_score_invoke(
                _tx_hash, _to, context, _data_type, _data)
        else:
            # EOA to EOA
            _tx_result = TransactionResult(
                _tx_hash, context.block, _to, TransactionResult.SUCCESS)

        context.block_result.append(_tx_result)

    def __handle_score_invoke(self,
                              tx_hash: str,
                              to: Address,
                              context: IconScoreContext,
                              data_type: str,
                              data: dict) -> TransactionResult:
        """Handle score invocation

        :param tx_hash: transaction hash
        :param to: a recipient address
        :param context:
        :param data_type:
        :param data: calldata
        :return: A result of the score transaction
        """
        tx_result = TransactionResult(tx_hash, context.block, to)
        try:
            if data_type == 'install':
                to = TEST_SCORE_ADDRESS
                tx_result.contract_address = self.__generate_contract_address(
                    context.tx.origin, context.tx.timestamp, context.tx.nonce)

            self._icon_score_engine.invoke(to, context, data_type, data)

            context.block_batch.put_tx_batch(context.tx_batch)
            context.tx_batch.clear()

            tx_result.status = TransactionResult.SUCCESS
        except:
            tx_result.status = TransactionResult.FAILURE

        return tx_result

    def __generate_contract_address(self,
                                    from_: Address,
                                    timestamp: int,
                                    nonce: int = None) -> Address:
        """Generates a contract address from the transaction information.

        :param from_:
        :param timestamp:
        :param nonce:
        :return:
        """
        data = from_.body + timestamp.to_bytes(32, 'big')
        if nonce is not None:
            data += nonce.to_bytes(32, 'big')

        hash_value = hashlib.sha3_256(data).hexdigest()
        return Address(AddressPrefix.CONTRACT, hash_value[-20:])

    def _set_tx_info_to_context(self,
                                context: IconScoreContext,
                                params: dict) -> None:
        """Set transaction and message info to IconScoreContext

        :param context:
        :param params: jsonrpc params
        """
        _from = params['from']
        _tx_hash = params.get('tx_hash', None)
        _value = params.get('value', 0)
        _timestamp = None
        _nonce = None
        if 'timestamp' in params:
            _timestamp = int(params.get('timestamp', None))
        if 'nonce' in params:
            _nonce = int(params.get('nonce', None), 16)

        context.tx = Transaction(tx_hash=_tx_hash,
                                 origin=_from,
                                 timestamp=_timestamp,
                                 nonce=_nonce)
        context.msg = Message(sender=_from, value=_value)

    def commit(self):
        """Write updated states in a context.block_batch to StateDB
        when the candidate block has been confirmed
        """
        pass

    def rollback(self):
        """Delete updated states in a context.block_batch and 
        """
        pass
