import rlp
import json
from plasma.config import plasma_config
from ethereum import utils
from .block import Block
from .transaction import Transaction
from web3.contract import ConciseContract
from plasma.root_chain.deployer import Deployer
from web3 import HTTPProvider


class ChildChain(object):

    def __init__(self, authority, root_chain_provider=HTTPProvider('http://localhost:8545'), child_chain_url="http://localhost:8546/jsonrpc"):
        deployer = Deployer(root_chain_provider)
        abi = json.load(open("contract_data/RootChain.json"))
        self.w3 = deployer.w3
        self.root_chain = self.w3.eth.contract(abi, plasma_config['ROOT_CHAIN_CONTRACT_ADDRESS'], ContractFactoryClass=ConciseContract)
        self.authority = authority
        self.blocks = {}
        self.current_block_number = 1
        self.current_block = Block()
        self.pending_transactions = []

    def submit_deposit(self, tx_hash):
        tx = self.w3.eth.getTransaction(tx_hash)
        newowner1 = tx['from']
        amount1 = tx['value']
        deposit_tx = Transaction(0, 0, 0, 0, 0, 0,
                                 newowner1, amount1, b'\x00' * 20, 0, 0)
        deposit_block = Block([deposit_tx])
        # Add block validation
        self.blocks[self.current_block_number] = deposit_block
        self.current_block_number += 1

    def apply_transaction(self, transaction):
        tx = rlp.decode(utils.decode_hex(transaction), Transaction)
        # Check for valid inputs and get input amounts
        amount1 = self.valid_input_tx(tx.blknum1, tx.txindex1, tx.oindex1)
        amount2 = self.valid_input_tx(tx.blknum2, tx.txindex2, tx.oindex2)

        # Check that input and output values are equal
        assert amount1 + amount2 == tx.amount1 + tx.amount2 + tx.fee

        self.current_block.transaction_set.append(tx)

    def valid_input_tx(self, blknum, txindex, oindex):
        if blknum == 0:
            return 0
        if oindex == 0:
            spent = self.blocks[blknum].transaction_set[txindex].spent1
            amount = self.blocks[blknum].transaction_set[txindex].amount1
        else:
            spent = self.blocks[blknum].transaction_set[txindex].spent2
            amount = self.blocks[blknum].transaction_set[txindex].amount2
        assert spent is False
        spent = True
        return amount

    def submit_block(self, block):
        block = rlp.decode(utils.decode_hex(block), Block)
        assert block.sender == self.authority
        # TODO: iterate through block and validate transactions
        self.blocks[self.current_block_number] = self.current_block
        self.current_block_number += 1
        self.current_block = Block()

    def get_transaction(self, blknum, txindex):
        return rlp.encode(self.block[blknum].transaction_set[txindex]).hex()

    def get_block(self, blknum):
        return rlp.encode(self.blocks[blknum]).hex()

    def get_current_block(self):
        return rlp.encode(self.current_block).hex()

    def get_current_block_num(self):
        return self.current_block_number
