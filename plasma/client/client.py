import json
import rlp
from web3.contract import ConciseContract
from web3 import HTTPProvider
from plasma.config import plasma_config
from plasma.root_chain.deployer import Deployer
from plasma.child_chain.transaction import Transaction, UnsignedTransaction
from .child_chain_service import ChildChainService


class Client(object):

    def __init__(self, root_chain_provider=HTTPProvider('http://localhost:8545'), child_chain_url="http://localhost:8546/jsonrpc"):
        deployer = Deployer(root_chain_provider)
        abi = json.load(open("contract_data/RootChain.json"))
        self.root_chain = deployer.w3.eth.contract(abi, plasma_config['ROOT_CHAIN_CONTRACT_ADDRESS'], ContractFactoryClass=ConciseContract)
        self.child_chain = ChildChainService(child_chain_url)

    def create_transaction(self, blknum1=0, txindex1=0, oindex1=0,
                           blknum2=0, txindex2=0, oindex2=0,
                           newowner1=b'\x00' * 20, amount1=0,
                           newowner2=b'\x00' * 20, amount2=0,
                           fee=0):
        return Transaction(blknum1, txindex1, oindex1,
                           blknum2, txindex2, oindex2,
                           newowner1, amount1,
                           newowner2, amount2,
                           fee)

    def sign_transaction(self, transaction, key1=b'', key2=b''):
        if key1:
            transaction.sign1(key1)
        if key2:
            transaction.sign1(key2)
        return transaction

    def deposit(self, amount, owner):
        self.root_chain.deposit(transact={'from': owner, 'value': amount})

    def apply_transaction(self, transaction):
        self.child_chain.apply_transaction(transaction)

    def submit_block(self, block):
        self.child_chain.submit_block(block)

    def withdraw(self, blknum, txindex, oindex, tx, proof, sigs):
        utxo_pos = blknum * 1000000000 + txindex * 10000 + oindex * 1
        self.root_chain.startExit(utxo_pos, rlp.encode(tx, UnsignedTransaction), proof, sigs, transact={'from': '0x' + tx.newowner1.hex()})

    def withdraw_deposit(self, owner, deposit_pos, amount):
        self.root_chain.startDepositExit(deposit_pos, amount, transact={'from': owner})

    def get_transaction(self, blknum, txindex):
        return self.child_chain.get_transaction(blknum, txindex)

    def get_current_block(self):
        return self.child_chain.get_current_block()

    def get_block(self, blknum):
        return self.child_chain.get_block(blknum)

    def get_current_block_num(self):
        return self.child_chain.get_current_block_num()
