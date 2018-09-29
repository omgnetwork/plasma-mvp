import rlp
from ethereum import utils
from web3 import HTTPProvider
from plasma_core.block import Block
from plasma_core.transaction import Transaction, UnsignedTransaction
from plasma_core.constants import NULL_ADDRESS, CONTRACT_ADDRESS
from plasma_core.utils.transactions import encode_utxo_id
from plasma.root_chain.deployer import Deployer
from .child_chain_service import ChildChainService
from plasma_core.utils.merkle.fixed_merkle import FixedMerkle
from eth_utils import address


class Client(object):

    def __init__(self, root_chain_provider=HTTPProvider('http://localhost:8545'), child_chain_url="http://localhost:8546/jsonrpc"):
        deployer = Deployer(root_chain_provider)
        self.root_chain = deployer.get_contract_at_address("RootChain", CONTRACT_ADDRESS, concise=True)
        self.child_chain = ChildChainService(child_chain_url)

    def create_transaction(self, blknum1=0, txindex1=0, oindex1=0,
                           blknum2=0, txindex2=0, oindex2=0,
                           newowner1=NULL_ADDRESS, amount1=0,
                           newowner2=NULL_ADDRESS, amount2=0,
                           cur12=NULL_ADDRESS,
                           fee=0):
        return Transaction(blknum1, txindex1, oindex1,
                           blknum2, txindex2, oindex2,
                           cur12,
                           newowner1, amount1,
                           newowner2, amount2,
                           fee)

    def sign_transaction(self, transaction, key1=b'', key2=b''):
        if key1:
            transaction.sign1(key1)
        if key2:
            transaction.sign2(key2)
        return transaction

    def deposit(self, amount, owner):
        self.root_chain.deposit(transact={'from': owner, 'value': amount})

    def apply_transaction(self, transaction):
        self.child_chain.apply_transaction(transaction)

    def submit_block(self, block):
        self.child_chain.submit_block(block)

    def withdraw(self, blknum, txindex, oindex, tx, proof, sigs):
        utxo_pos = encode_utxo_id(blknum, txindex, oindex)
        encoded_transaction = rlp.encode(tx, UnsignedTransaction)

        _from = ''
        if oindex == 0:
            _from = address.to_checksum_address('0x' + tx.newowner1.hex())
        else:
            _from = address.to_checksum_address('0x' + tx.newowner2.hex())

        self.root_chain.startExit(utxo_pos, encoded_transaction, proof, sigs, transact={'from': _from})

    def withdraw_deposit(self, owner, deposit_pos, amount):
        self.root_chain.startDepositExit(deposit_pos, NULL_ADDRESS, amount, transact={'from': owner})

    def get_transaction(self, blknum, txindex):
        encoded_transaction = self.child_chain.get_transaction(blknum, txindex)
        return rlp.decode(utils.decode_hex(encoded_transaction), Transaction)

    def get_current_block(self):
        encoded_block = self.child_chain.get_current_block()
        return rlp.decode(utils.decode_hex(encoded_block), Block)

    def get_block(self, blknum):
        encoded_block = self.child_chain.get_block(blknum)
        return rlp.decode(utils.decode_hex(encoded_block), Block)

    def get_current_block_num(self):
        return self.child_chain.get_current_block_num()

    def finalize_exits(self, account):
        self.root_chain.finalizeExits(NULL_ADDRESS, transact={'from': account})

    def challenge_exit(self, blknum, confirmSig, account):
        oindex = 0
        utxo_pos = encode_utxo_id(blknum, 0, oindex)

        tx = self.get_transaction(blknum, 0)
        tx_bytes = rlp.encode(tx, UnsignedTransaction)

        merkle = FixedMerkle(16, [tx.merkle_hash], True)
        proof = merkle.create_membership_proof(tx.merkle_hash)

        sigs = tx.sig1 + tx.sig2

        return self.root_chain.challengeExit(utxo_pos, oindex, tx_bytes, proof, sigs, confirmSig, transact={'from': account})
