import rlp
from rlp.sedes import binary, CountableList
from ethereum import utils
from plasma.utils.merkle.fixed_merkle import FixedMerkle
from plasma.utils.utils import sign, get_sender
from .transaction import Transaction


class Block(rlp.Serializable):

    fields = [
        ('transaction_set', CountableList(Transaction)),
        ('sig', binary),
    ]

    def __init__(self, transaction_set=[], sig=b'\x00' * 65):
        self.transaction_set = transaction_set
        self.sig = sig
        self.merkle = None

    @property
    def hash(self):
        return utils.sha3(rlp.encode(self, UnsignedBlock))

    def sign(self, key):
        self.sig = sign(self.hash, key)

    @property
    def sender(self):
        return get_sender(self.hash, self.sig)

    @property
    def merkilize_transaction_set(self):
        hashed_transaction_set = [transaction.hash for transaction in self.transaction_set]
        self.merkle = FixedMerkle(16, hashed_transaction_set).root
        return self.merkle


UnsignedBlock = Block.exclude(['sig'])
