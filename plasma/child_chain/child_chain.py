import rlp
from rlp.sedes import CountableList
from plasma.config import plasma_config
from ethereum import utils
from .block import Block
from .transaction import Transaction
import inspect

class ChildChain(object):

    def __init__(self, authority):
        self.authority = authority
        self.blocks = {}
        self.current_block_number = 1
        self.current_block = Block()
        self.pending_transactions = []

    def submit_block(self, block, deposit=False):
        block = rlp.decode(utils.decode_hex(block), Block)
        assert block.sender == self.authority
        # iterate through block and validate transactions
        for tx in block.transaction_set:
            self.apply_transaction(tx)
        self.blocks[self.current_block_number] =  self.current_block
        self.current_block_number += 1
        if not deposit:
            self.current_block =  Block()

    def apply_transaction(self, transaction):
        self.validate_transaction(transaction)
        self.spend_transaction(transaction)
        self.current_block.transaction_set.append(transaction)

    def add_pending_transaction(self, transaction):
        transaction = rlp.decode(utils.decode_hex(transaction), Transaction)
        self.validate_transaction(transaction)
        self.pending_transactions.append(transaction)
        return True

    def check_tx_confirmation(self, tx, block_number, confirmationSigs):
        # Add verification that the tx i in the root
        confirmation_hash = utils.sha3(tx.hash + tx.sig1 + tx.sig2, self.blocks[block_number].merkle.root)
        input_count =tx.blknum2 * 1000000 + tx.blknum1
        if input_count < 1000000:
            assert tx.sender1 ==  get_sender(confirmationHash, confirmationsigs[0:65])
        else:
            assert tx.sender1 ==  get_sender(confirmationHash, confirmationsigs[0:65])
            assert tx.sender2 ==  get_sender(confirmationHash, confirmationsigs[65:130])

    def validate_transaction(self, transaction):
        in_utxo1 = self.blocks[transaction.blknum1].transaction_set[transaction.txindex1]
        if in_utxo1.spent:
            raise Exception("Input1 already spent")
        total_output_value = transaction.utxos[0].amount + transaction.utxos[1].amount + fee
        total_input_value = in_utxo1.amount
        if not transaction.is_single_utxo:
            in_utxo2 = self.blocks[transaction.blknum2].transaction_set[transaction.txindex2]
            if in_utxo2.spent:
                raise Exception("Input2 already spent")
            total_input_value += in_utxo2.amount
            assert in_utxo2.owner == transaction.sender2
        assert total_input_value == total_output_value
        assert in_utxo1.owner == transaction.sender1

    def spend_transaction(self, transaction):
        self.blocks[transaction.blknum1].transaction_set[transaction.txindex1].spent[transaction.oindex1] = True
        self.blocks[transaction.blknum2].transaction_set[transaction.txindex2].spent[transaction.oindex2] = True

    # def get_transactions_for_account(self, address):
    #     return rlp.encode(balance[address], CountableList(Transaction))

    def get_block(self, blknum):
        return rlp.encode(self.blocks[blknum]).hex()

    def get_current_block_num(self):
        return self.current_block_number

    def get_pending_transactions(self):
        return rlp.encode(self.pending_transactions, CountableList(Transaction)).hex()
