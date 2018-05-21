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
from .constants import AUTHORITY, ACCOUNTS, NULL_ADDRESS

class TestingLanguage(object):

    TOKEN_PATTERN = r'([A-Za-z]*)([0-9]*)\[(.*?)\]'

    def __init__(self):
        self.w3 = Web3(HTTPProvider('http://localhost:8545'))
        self.root_chain = Deployer().deploy_contract('RootChain', concise=False)
        self.child_chain = ChildChain(bytes.fromhex(AUTHORITY['address'][2:]), self.root_chain)

        self.transactions = []
        self.accounts = []

        self.handlers = dict()

        self.register_handler('Deposit', self.deposit)
        self.register_handler('Transfer', self.transfer)
        self.register_handler('SubmitBlock', self.submit_block)
        self.register_handler('Confirm', self.confirm)
        self.register_handler('Withdraw', self.withdraw)

    def register_handler(self, token, function):
        self.handlers[token] = function

    def get_account(self, operator=False):
        if operator:
            account = AUTHORITY
        else:
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
                         account['address'], amount,
                         NULL_ADDRESS, 0)

        self.transactions.append({
            'tx': tx,
            'confirm_sigs': b''
        })
        return len(self.transactions) - 1

    def transfer(self,
                 input1, newowner1, amount1, key1,
                 input2=None, newowner2=None, amount2=None, key2=None):
        newowner_address1 = newowner1['address']
        amount1 = int(amount1)

        newowner_address2 = NULL_ADDRESS
        if newowner2 is not None:
            newowner_address2 = newowner2['address']
        amount2 = int(amount2) if amount2 is not None else 0

        encoded_input_tx1 = rlp.encode(self.transactions[input1]['tx']).hex()
        blknum1, txindex1 = self.child_chain.get_tx_pos(encoded_input_tx1)
        # KTXXX - support oindex
        oindex1 = 0
        # oindex1 = 1 if input1.endswith('.1') else 0

        blknum2, txindex2, oindex2 = 0, 0, 0
        if input2 is not None:
            encoded_input_tx2 = rlp.encode(self.transactions[input2]['tx']).hex()
            blknum2, txindex2 = self.child_chain.get_tx_pos(encoded_input_tx2)
            # KTXXX - support oindex
            oindex2 = 0
            # oindex2 = 1 if input2.endswith('.1') else 0

        tx = Transaction(blknum1, txindex1, oindex1,
                         blknum2, txindex2, oindex2,
                         newowner_address1, amount1,
                         newowner_address2, amount2)

        tx.sign1(key1)

        if input2 is not None:
            tx.sign2(key2)

        encoded_tx = rlp.encode(tx).hex()

        self.child_chain.apply_transaction(encoded_tx)

        self.transactions.append({
            'tx': tx,
            'confirm_sigs': b''
        })
        return len(self.transactions) - 1


    def submit_block(self, signatory):
        signing_key = self.get_account(signatory)['key']
        print(signing_key)

        block = self.child_chain.current_block
        block.make_mutable()
        if signing_key:
            block.sign(signing_key)

        self.child_chain.submit_block(rlp.encode(block).hex())

    def confirm(self, tx_name, signatory1, signatory2):
        transaction = self.transactions[tx_name]

        tx = transaction['tx']
        encoded_tx = rlp.encode(tx).hex()

        blknum, _ = self.child_chain.get_tx_pos(encoded_tx)
        block_root = self.child_chain.blocks[blknum].merkle.root

        confirm_sigs = b''
        for signatory_name in [x for x in [signatory1, signatory2] if x is not None]:
            account = self.accounts[signatory_name]
            confirm_sigs += confirm_tx(tx, block_root, account['key'])

        self.transactions[tx_name]['confirm_sigs'] = confirm_sigs

    def withdraw(self, tx_name, exitor_name):
        is_deposit = 'Deposit' in tx_name
        transaction = self.transactions[tx_name.split('.')[0]]
        account = self.get_account(exitor_name)

        tx = transaction['tx']
        encoded_tx = rlp.encode(tx).hex()
        tx_bytes = rlp.encode(tx, UnsignedTransaction)
        sigs = tx.sig1 + tx.sig2 + transaction['confirm_sigs']

        blknum, txindex = self.child_chain.get_tx_pos(encoded_tx)
        oindex = 1 if tx_name.endswith('.1') else 0
        utxo_pos = blknum * 1000000000 + txindex * 10000 + oindex * 1

        if is_deposit:
            deposit_amount = tx.amount1

            self.root_chain.transact({
                'from': account['address']
            }).startDepositExit(utxo_pos + 1, deposit_amount)
        else:
            output_block = self.child_chain.blocks[blknum]
            hashed_transaction_set = [transaction.merkle_hash for transaction in output_block.transaction_set]
            merkle = FixedMerkle(16, hashed_transaction_set, hashed=True)
            proof = merkle.create_membership_proof(tx.merkle_hash)

            self.root_chain.transact({
                'from': account['address']
            }).startExit(utxo_pos, tx_bytes, proof, sigs)



    def parse(self, test_lang_string):
        for token in test_lang_string.split():
            handler, arguments = self.parse_token(token)
            fn = self.handlers[handler]

            # Determine how many arguments are required and pad with None
            required_args = len(signature(fn).parameters)
            arguments += [None] * (required_args - len(arguments))

            fn(*arguments)

    def parse_token(self, token):
        handler, method_id, arguments = re.match(self.TOKEN_PATTERN, token.strip()).groups()

        parsed_arguments = arguments.split(',') if len(arguments) > 0 else []

        method_name = handler + method_id if method_id else None
        if method_name is not None:
            parsed_arguments.insert(0, method_name)

        # Anything explicitly marked as "null" converted to None
        parsed_arguments = [None if arg == 'null' else arg for arg in parsed_arguments]

        return handler, parsed_arguments
