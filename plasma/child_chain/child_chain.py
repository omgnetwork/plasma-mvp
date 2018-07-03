import rlp
from ethereum import utils

from plasma.utils.utils import unpack_utxo_pos
from .block import Block
from .exceptions import (InvalidBlockMerkleException,
                         InvalidBlockSignatureException,
                         InvalidTxSignatureException, TxAlreadySpentException,
                         TxAmountMismatchException)
from .transaction import Transaction
from .root_event_listener import RootEventListener

ZERO_ADDRESS = b'\x00' * 20


class ChildChain(object):

    def __init__(self, authority, root_chain):
        self.root_chain = root_chain
        self.authority = authority
        self.blocks = {}
        self.child_block_interval = 1000
        self.current_block_number = self.child_block_interval
        self.current_block = Block()
        self.pending_transactions = []

        self.event_listener = RootEventListener(root_chain, confirmations=0)

        # Register event listeners
        self.event_listener.on('Deposit', self.apply_deposit)
        self.event_listener.on('ExitStarted', self.apply_exit)

    def apply_exit(self, event):
        event_args = event['args']
        utxo_pos = event_args['utxoPos']
        self.mark_utxo_spent(*unpack_utxo_pos(utxo_pos))

    def apply_deposit(self, event):
        event_args = event['args']

        depositor = event_args['depositor']
        amount = event_args['amount']
        blknum = event_args['depositBlock']

        deposit_tx = Transaction(0, 0, 0,
                                 0, 0, 0,
                                 ZERO_ADDRESS,
                                 depositor, amount,
                                 ZERO_ADDRESS, 0)
        deposit_block = Block([deposit_tx])

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

        output_amount = tx.amount1 + tx.amount2
        input_amount = 0

        for (blknum, txindex, oindex) in inputs:
            # Assume empty inputs and are valid
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

        if input_amount < output_amount:
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
        if block.merklize_transaction_set() != self.current_block.merklize_transaction_set():
            raise InvalidBlockMerkleException('input block merkle mismatch with the current block')

        valid_signature = block.sig != b'\x00' * 65 and block.sender == bytes.fromhex(self.authority[2:])
        if not valid_signature:
            raise InvalidBlockSignatureException('failed to submit block')

        self.root_chain.transact({'from': self.authority}).submitBlock(block.merkle.root)
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
