import rlp
from rlp.sedes import binary, CountableList, big_endian_int
from ethereum import utils
from plasma_core.utils.merkle.fixed_merkle import FixedMerkle
from plasma_core.utils.signatures import sign, get_signer
from plasma_core.utils.transactions import encode_utxo_id
from plasma_core.transaction import Transaction
from plasma_core.constants import NULL_SIGNATURE


class Block(rlp.Serializable):

    fields = [
        ('transaction_set', CountableList(Transaction)),
        ('number', big_endian_int),
        ('sig', binary),
    ]

    def __init__(self, transaction_set=None, number=0, sig=NULL_SIGNATURE):
        self.transaction_set = transaction_set or []
        self.number = number
        self.sig = sig
        self.spent_utxos = {}

    @property
    def hash(self):
        return utils.sha3(self.encoded)

    @property
    def signer(self):
        return get_signer(self.hash, self.sig)

    @property
    def merkle(self):
        hashed_transaction_set = [transaction.merkle_hash for transaction in self.transaction_set]
        return FixedMerkle(16, hashed_transaction_set, hashed=True)

    @property
    def root(self):
        return self.merkle.root

    @property
    def is_deposit_block(self):
        return len(self.transaction_set) == 1 and self.transaction_set[0].is_deposit_transaction

    @property
    def encoded(self):
        return rlp.encode(self, UnsignedBlock)

    def sign(self, key):
        self.sig = sign(self.hash, key)

    def add_transaction(self, tx):
        self.transaction_set.append(tx)
        inputs = [(tx.blknum1, tx.txindex1, tx.oindex1), (tx.blknum2, tx.txindex2, tx.oindex2)]
        for i in inputs:
            input_id = encode_utxo_id(*i)
            self.spent_utxos[input_id] = True


UnsignedBlock = Block.exclude(['sig'])
