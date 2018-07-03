import re
import time
import rlp
from inspect import signature
from web3 import Web3, HTTPProvider
from plasma.root_chain.deployer import Deployer
from plasma.child_chain.child_chain import ChildChain
from plasma.child_chain.transaction import Transaction, UnsignedTransaction
from plasma.utils.merkle.fixed_merkle import FixedMerkle
from plasma.utils.utils import confirm_tx
from .constants import AUTHORITY, ACCOUNTS, NULL_ADDRESS, NULL_ADDRESS_HEX

class TestingLanguage(object):

    TOKEN_PATTERN = r'([A-Za-z]*)([0-9]*)\[(.*?)\]'

    def __init__(self):
        self.w3 = Web3(HTTPProvider('http://localhost:8545'))
        self.root_chain = Deployer().deploy_contract('RootChain', concise=False)
        self.child_chain = ChildChain(AUTHORITY['address'], self.root_chain)

        self.transactions = []
        self.accounts = []

    def get_account(self):
        account = ACCOUNTS[len(self.accounts)]
        self.accounts.append(account)
        return account

    def deposit(self, account, amount):
        amount = int(amount)

        self.root_chain.transact({
            'from': account['address'],
            'value': amount
        }).deposit()

        # Wait for the Deposit event to be detected
        time.sleep(1)

        tx = Transaction(0, 0, 0,
                         0, 0, 0,
                         NULL_ADDRESS,
                         account['address'], amount,
                         NULL_ADDRESS, 0)

        self.transactions.append({
            'tx': tx,
            'confirm_sigs': b'',
            'is_deposit': True
        })
        return len(self.transactions) - 1

    def transfer(self,
                 input1, oindex1, newowner1, amount1, signatory1,
                 input2=None, oindex2=0, newowner2=None, amount2=None, signatory2=None, cur12=NULL_ADDRESS):
        newowner_address1 = newowner1['address']
        amount1 = int(amount1)

        newowner_address2 = NULL_ADDRESS
        if newowner2 is not None:
            newowner_address2 = newowner2['address']
        amount2 = int(amount2) if amount2 is not None else 0

        encoded_input_tx1 = rlp.encode(self.transactions[input1]['tx']).hex()
        blknum1, txindex1 = self.child_chain.get_tx_pos(encoded_input_tx1)

        blknum2, txindex2 = 0, 0
        if input2 is not None:
            encoded_input_tx2 = rlp.encode(self.transactions[input2]['tx']).hex()
            blknum2, txindex2 = self.child_chain.get_tx_pos(encoded_input_tx2)

        tx = Transaction(blknum1, txindex1, oindex1,
                         blknum2, txindex2, oindex2,
                         cur12,
                         newowner_address1, amount1,
                         newowner_address2, amount2)

        if signatory1 is not None:
            key1 = signatory1['key']
            tx.sign1(key1)

        if signatory2 is not None:
            key2 = signatory2['key']
            tx.sign2(key2)

        encoded_tx = rlp.encode(tx).hex()

        self.child_chain.apply_transaction(encoded_tx)

        self.transactions.append({
            'tx': tx,
            'confirm_sigs': b'',
            'is_deposit': False
        })
        return len(self.transactions) - 1


    def submit_block(self, signatory=AUTHORITY):
        signing_key = None
        if signatory is not None:
            signing_key = signatory['key']

        block = self.child_chain.current_block
        block.make_mutable()
        if signing_key:
            block.sign(signing_key)

        self.child_chain.submit_block(rlp.encode(block).hex())

    def confirm(self, tx_id, signatory1, signatory2=None):
        transaction = self.transactions[tx_id]

        tx = transaction['tx']
        encoded_tx = rlp.encode(tx).hex()

        blknum, _ = self.child_chain.get_tx_pos(encoded_tx)
        block_root = self.child_chain.blocks[blknum].merkle.root

        confirm_sigs = b''
        for signatory in [x for x in [signatory1, signatory2] if x is not None]:
            confirm_sigs += confirm_tx(tx, block_root, signatory['key'])

        self.transactions[tx_id]['confirm_sigs'] = confirm_sigs

    def withdraw(self, tx_id, oindex, exitor):
        transaction = self.transactions[tx_id]

        tx = transaction['tx']
        encoded_tx = rlp.encode(tx).hex()
        tx_bytes = rlp.encode(tx, UnsignedTransaction)
        sigs = tx.sig1 + tx.sig2 + transaction['confirm_sigs']

        blknum, txindex = self.child_chain.get_tx_pos(encoded_tx)
        utxo_pos = blknum * 1000000000 + txindex * 10000 + oindex * 1

        if transaction['is_deposit']:
            deposit_amount = tx.amount1

            self.root_chain.transact({
                'from': exitor['address']
            }).startDepositExit(utxo_pos + 1, NULL_ADDRESS_HEX, deposit_amount)
        else:
            output_block = self.child_chain.blocks[blknum]
            hashed_transaction_set = [transaction.merkle_hash for transaction in output_block.transaction_set]
            merkle = FixedMerkle(16, hashed_transaction_set, hashed=True)
            proof = merkle.create_membership_proof(tx.merkle_hash)

            self.root_chain.transact({
                'from': exitor['address']
            }).startExit(utxo_pos, tx_bytes, proof, sigs)
