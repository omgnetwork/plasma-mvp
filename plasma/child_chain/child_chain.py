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

        # Validate the transaction
        self.validate_tx(tx)

        # Mark the inputs as spent
        self.mark_utxo_spent(tx.blknum1, tx.txindex1, tx.oindex1)
        self.mark_utxo_spent(tx.blknum2, tx.txindex2, tx.oindex2)

        self.current_block.transaction_set.append(tx)

    def validate_tx(self, tx):
        inputs = [(tx.blknum1, tx.txindex1, tx.oindex1), (tx.blknum2, tx.txindex2, tx.oindex2)]

        output_amount = tx.amount1 + tx.amount2 + tx.fee
        input_amount = 0

        for (blknum, txindex, oindex) in inputs:
            if blknum == 0:
                continue

            transaction = self.blocks[blknum].transaction_set[txindex]

            if oindex == 0:
                valid_signature = tx.sig1 != b'\x00' * 65 and transaction.newowner1 == tx.sender1
                spent = transaction.spent1
                input_amount += transaction.amount1
            else:
                valid_signature = tx.sig2 != b'\x00' * 65 and transaction.newowner2 == tx.sender2
                spent = transaction.spent2
                input_amount += transaction.amount2
            assert not spent
            assert valid_signature

        assert input_amount == output_amount

    def mark_utxo_spent(self, blknum, txindex, oindex):
        if blknum == 0:
            return

        if oindex == 0:
            self.blocks[blknum].transaction_set[txindex].spent1 = True
        else:
            self.blocks[blknum].transaction_set[txindex].spent2 = True

    def submit_block(self, block):
        block = rlp.decode(utils.decode_hex(block), Block)
        assert block.sender == self.authority
        # TODO: iterate through block and validate transactions
        self.blocks[self.current_block_number] = self.current_block
        self.current_block_number += 1
        self.current_block = Block()

    def get_transaction(self, blknum, txindex):
        return rlp.encode(self.blocks[blknum].transaction_set[txindex]).hex()

    def get_block(self, blknum):
        return rlp.encode(self.blocks[blknum]).hex()

    def get_current_block(self):
        return rlp.encode(self.current_block).hex()

    def get_current_block_num(self):
        return self.current_block_number
