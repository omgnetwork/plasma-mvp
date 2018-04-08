import rlp
from ethereum import utils

from .block import Block
from .exceptions import (InvalidBlockMerkleException,
                         InvalidBlockSignatureException,
                         InvalidTxSignatureException, TxAlreadySpentException,
                         TxAmountMismatchException)
from .transaction import Transaction


class ChildChain(object):

    def __init__(self, authority, root_chain):
        self.root_chain = root_chain
        self.authority = authority
        self.blocks = {}
        self.child_block_interval = 1000
        self.current_block_number = self.child_block_interval
        self.current_block = Block()
        self.pending_transactions = []

        # Register for deposit event listener
        deposit_filter = self.root_chain.on('Deposit')
        deposit_filter.watch(self.apply_deposit)

    def apply_deposit(self, event):
        event_args = event['args']
        depositor = event_args['depositor']
        amount = event_args['amount']
        blknum = event_args['blknum']

        deposit_tx = Transaction(0, 0, 0,
                                 0, 0, 0,
                                 depositor, amount,
                                 b'\x00' * 20, 0,
                                 0)

        deposit_block = Block([deposit_tx])
        # Add block validation
        self.blocks[blknum] = deposit_block

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
            if spent:
                raise TxAlreadySpentException('failed to validate tx')
            if not valid_signature:
                raise InvalidTxSignatureException('failed to validate tx')

        if input_amount != output_amount:
            raise TxAmountMismatchException('failed to validate tx')

    def mark_utxo_spent(self, blknum, txindex, oindex):
        if blknum == 0:
            return

        if oindex == 0:
            self.blocks[blknum].transaction_set[txindex].spent1 = True
        else:
            self.blocks[blknum].transaction_set[txindex].spent2 = True

    def submit_block(self, block):
        block = rlp.decode(utils.decode_hex(block), Block)
        if block.merkilize_transaction_set != self.current_block.merkilize_transaction_set:
            raise InvalidBlockMerkleException('input block merkle mismatch with the current block')

        valid_signature = block.sig != b'\x00' * 65 and block.sender == self.authority
        if not valid_signature:
            raise InvalidBlockSignatureException('failed to submit block')

        self.root_chain.transact({'from': '0x' + self.authority.hex()}).submitBlock(block.merkle.root, self.current_block_number)
        # TODO: iterate through block and validate transactions
        self.blocks[self.current_block_number] = self.current_block
        self.current_block_number += self.child_block_interval
        self.current_block = Block()

    def get_transaction(self, blknum, txindex):
        return rlp.encode(self.blocks[blknum].transaction_set[txindex]).hex()

    def get_tx_pos(self, transaction):
        decoded_tx = rlp.decode(utils.decode_hex(transaction), Transaction)

        for blknum in self.blocks:
            block = self.blocks[blknum]
            for txindex in range(0, len(block.transaction_set)):
                tx = block.transaction_set[txindex]
                if (decoded_tx.hash == tx.hash):
                    return blknum, txindex

        return None, None

    def get_block(self, blknum):
        return rlp.encode(self.blocks[blknum]).hex()

    def get_current_block(self):
        return rlp.encode(self.current_block).hex()

    def get_current_block_num(self):
        return self.current_block_number
