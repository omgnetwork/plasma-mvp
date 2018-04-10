import re
import time
import rlp
from ethereum import utils as u
from web3 import Web3, HTTPProvider
from plasma.root_chain.deployer import Deployer
from plasma.child_chain.child_chain import ChildChain
from plasma.child_chain.transaction import Transaction, UnsignedTransaction
from plasma.utils.merkle.fixed_merkle import FixedMerkle
from plasma.utils.utils import confirm_tx

AUTHORITY = b'\xfd\x02\xec\xeeby~u\xd8k\xcf\xf1d.\xb0\x84J\xfb(\xc7'
AUTHORITY_KEY = u.normalize_key(b'3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304')

ACCOUNTS = [
    {
        'address': '0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26',
        'key': u.normalize_key(b'b937b2c6a606edf1a4d671485f0fa61dcc5102e1ebca392f5a8140b23a8ac04f')
    },
    {
        'address': '0xda20a48913f9031337a5e32325f743e8536860e2',
        'key': u.normalize_key(b'999ba3f77899ba4802af5109221c64a9238a6772718f287a8bd3ca3d1b68187f')
    },
    {
        'address': '0xf6d8982698dcc46b8e96e34bc2bf3c97302b9923',
        'key': u.normalize_key(b'ef4134d11aa32bcbd314d3cd94b7a5f93bea2b809007d4307a4393cce0285652')
    },
    {
        'address': '0x2d75468c0cafa9d41fc5bf3cca6c292a3cc03d94',
        'key': u.normalize_key(b'25c8620e5bd51caed1d2ff5e79b43dfbef17d0b4eb38d0db8d834da9de5a6120')
    },
    {
        'address': '0xf05b4b746aad830062505ad0cfd3619917484e46',
        'key': u.normalize_key(b'e3d66a68573a85734e80d3de47b82e13374c2a026f219cb766978510a8b8697e')
    },  
    {
        'address': '0x81a9bfa79598f1536b4918a6556e9855c5e141d5',
        'key': u.normalize_key(b'81e244b79cef097c187d9299a2fc3a680cf1d2637fb7463ca7aa70445a0a0410')
    },
    {
        'address': '0xa669513ad878cc0891d8c305cc21903068a9afe9',
        'key': u.normalize_key(b'ebcaa9c519c2aaa27e7c1656451b9c72167cadf0fd30bc4bcc3bda6d6fcbd507')
    },
    {
        'address': '0xc3aae3a9be258bd485105ef81eb0d5b677ee26fd',
        'key': u.normalize_key(b'b991543d47829ea4f296d182dfa7088303fb3f04dd0c95a5cb7132397e4a008d')
    },
    {
        'address': '0xb9db71c2d02a1b30dfe29c90738b3228dd9d2ec2',
        'key': u.normalize_key(b'484eb2f0465e7357575f05bf5af5e77cb4b678fb774dd127d9d99e3d31c5f80e')
    }
]
NULL_ADDRESS = b'\x00' * 20

class TestingLanguage(object):
    
    TOKEN_PATTERN = r'([A-Za-z]*)([0-9]*)\[(.*?)\]'

    def __init__(self):
        self.w3 = Web3(HTTPProvider('http://localhost:8545'))
        self.root_chain = Deployer().create_contract('RootChain/RootChain.sol', concise=False)
        self.child_chain = ChildChain(AUTHORITY, self.root_chain)

        self.transactions = dict()
        self.accounts = dict()

        self.handlers = dict()

        self.register_handler('Deposit', self.deposit)
        self.register_handler('Transfer', self.transfer)
        self.register_handler('SubmitBlock', self.submit_block)
        self.register_handler('Confirm', self.confirm)
        self.register_handler('Withdraw', self.withdraw)

    def register_handler(self, token, function):
        self.handlers[token] = function

    def get_account(self, account_name):
        account = self.accounts.get(account_name, None)
        if account is None:
            account = ACCOUNTS[len(self.accounts)]
            self.accounts[account_name] = account
        return account

    def deposit(self, deposit_name, account_name, amount):
        account = self.get_account(account_name)
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
                         NULL_ADDRESS, 0,
                         0)

        self.transactions[deposit_name] = {
            'tx': tx,
            'confirm_sigs': b''
        }

    def transfer(self, transfer_name,
                 input1, newowner1, amount1, signatory1,
                 input2, newowner2, amount2, signatory2):
        newowner_address1 = self.get_account(newowner1)['address']
        amount1 = int(amount1)

        newowner_address2 = NULL_ADDRESS
        if newowner2 is not None:
            newowner_address2 = self.get_account(newowner2)['address']
        amount2 = int(amount2) if amount2 is not None else 0

        encoded_input_tx1 = rlp.encode(self.transactions[input1]['tx']).hex()
        blknum1, txindex1 = self.child_chain.get_tx_pos(encoded_input_tx1)
        oindex1 = 1 if input1.endswith('.1') else 0

        blknum2, txindex2, oindex2 = 0, 0, 0
        if input2 is not None:
            encoded_input_tx2 = rlp.encode(self.transactions[input2]['tx']).hex()
            blknum2, txindex2 = self.child_chain.get_tx_pos(encoded_input_tx2)
            oindex2 = 1 if input2.endswith('.1') else 0
            
        tx = Transaction(blknum1, txindex1, oindex1,
                         blknum2, txindex2, oindex2,
                         newowner_address1, amount1,
                         newowner_address2, amount2,
                         0)

        key1 = self.get_account(signatory1)['key']
        tx.sign1(key1)

        if input2 is not None:
            key2 = self.get_account(signatory1)['key']
            tx.sign2(key2)

        encoded_tx = rlp.encode(tx).hex()

        self.child_chain.apply_transaction(encoded_tx)

        self.transactions[transfer_name] = {
            'tx': tx,
            'confirm_sigs': b''
        }

    def submit_block(self, signatory=AUTHORITY):
        signing_key = None
        if signatory == AUTHORITY:
            signing_key = AUTHORITY_KEY
        elif signatory != None:
            signing_key = self.get_account(signatory)['key']

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
            self.handlers[handler](*arguments)

    def parse_token(self, token):
        handler, method_id, arguments = re.match(self.TOKEN_PATTERN, token.strip()).groups()

        parsed_arguments = arguments.split(',') if len(arguments) > 0 else []

        method_name = handler + method_id if method_id else None
        if method_name is not None:
            parsed_arguments.insert(0, method_name)

        parsed_arguments = [None if arg == 'null' else arg for arg in parsed_arguments]

        return handler, parsed_arguments
