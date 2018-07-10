import time
from plasma.root_chain.deployer import Deployer
from plasma.child_chain.child_chain import ChildChain
from plasma_core.transaction import Transaction
from plasma_core.utils.utils import confirm_tx
from plasma_core.utils.transactions import encode_utxo_id, decode_utxo_id
from plasma_core.constants import AUTHORITY, ACCOUNTS, NULL_ADDRESS, NULL_ADDRESS_HEX


class TestingLanguage(object):

    def __init__(self):
        self.root_chain = Deployer().deploy_contract('RootChain', concise=False)
        self.child_chain = ChildChain(AUTHORITY['address'], self.root_chain)
        self.confirmations = {}
        self.accounts = []

    def get_account(self):
        account = ACCOUNTS[len(self.accounts)]
        self.accounts.append(account)
        return account

    def deposit(self, account, amount):
        deposit_blknum = self.child_chain.chain.next_deposit_block

        self.root_chain.transact({
            'from': account['address'],
            'value': amount
        }).deposit()

        # Wait for the Deposit event to be detected
        time.sleep(1)

        return encode_utxo_id(deposit_blknum, 0, 0)

    def transfer(self,
                 input1, newowner1, amount1, signatory1,
                 input2=0, newowner2=None, amount2=0, signatory2=None, cur12=NULL_ADDRESS):
        newowner_address1 = newowner1['address']
        newowner_address2 = NULL_ADDRESS
        if newowner2 is not None:
            newowner_address2 = newowner2['address']

        tx = Transaction(*decode_utxo_id(input1),
                         *decode_utxo_id(input2),
                         cur12,
                         newowner_address1, amount1,
                         newowner_address2, amount2)

        if signatory1 is not None:
            key1 = signatory1['key']
            tx.sign1(key1)

        if signatory2 is not None:
            key2 = signatory2['key']
            tx.sign2(key2)

        spend_id = self.child_chain.apply_transaction(tx)
        self.submit_block()
        return spend_id

    def submit_block(self, signatory=AUTHORITY):
        signing_key = None
        if signatory is not None:
            signing_key = signatory['key']

        block = self.child_chain.current_block
        if signing_key:
            block.sign(signing_key)

        self.child_chain.submit_block(block)

    def confirm(self, tx_id, signatory1, signatory2=None):
        tx = self.child_chain.get_transaction(tx_id)
        (blknum, _, _) = decode_utxo_id(tx_id)
        block_root = self.child_chain.get_block(blknum).root

        confirm_sigs = b''
        for signatory in [x for x in [signatory1, signatory2] if x is not None]:
            confirm_sigs += confirm_tx(tx, block_root, signatory['key'])

        self.confirmations[tx_id] = confirm_sigs

    def start_deposit_exit(self, utxo_id, exitor):
        tx = self.child_chain.get_transaction(utxo_id)

        self.root_chain.transact({
            'from': exitor['address']
        }).startDepositExit(utxo_id, NULL_ADDRESS_HEX, tx.amount1)

    def start_exit(self, utxo_id, exitor):
        tx = self.child_chain.get_transaction(utxo_id)

        sigs = tx.sig1 + tx.sig2 + self.confirmations[utxo_id]
        (blknum, _, _) = decode_utxo_id(utxo_id)
        block = self.child_chain.get_block(blknum)
        proof = block.merkle.create_membership_proof(tx.merkle_hash)

        self.root_chain.transact({
            'from': exitor['address']
        }).startExit(utxo_id, tx.encoded, proof, sigs)
