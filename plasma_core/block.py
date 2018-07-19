import rlp
from rlp.sedes import binary, CountableList
from ethereum import utils
from plasma_core.utils.merkle.fixed_merkle import FixedMerkle
from plasma_core.utils.signatures import sign, get_signer
from plasma_core.transaction import Transaction
from plasma_core.constants import NULL_SIGNATURE


class Block(rlp.Serializable):

    fields = [
        ('transaction_set', CountableList(Transaction)),
        ('sig', binary),
    ]

    def __init__(self, transaction_set=[], sig=NULL_SIGNATURE):
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
        return get_signer(self.hash, self.sig)

    def merklize_transaction_set(self):
        hashed_transaction_set = [transaction.merkle_hash for transaction in self.transaction_set]
        self.merkle = FixedMerkle(16, hashed_transaction_set, hashed=True)
        return self.merkle.root


UnsignedBlock = Block.exclude(['sig'])
