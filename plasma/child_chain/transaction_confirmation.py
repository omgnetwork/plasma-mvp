import rlp
from etheruem import utils
from rlp.sedes import big_endian_int, binary
from plasma.utils.utils import sign, get_sender


class TransactionConfirmation(rlp.Serializable):

    fields = [
        ('blknum', binary),
        ('txindex', big_endian_int),
        ('txHash', binary),
        ('sig1', binary),
        ('sig2', binary),
    ]

    def __init__(self, blknum, txindex, tx_hash, proof,
                 sig=b'\x00' * 65):
        self.blknum = blknum
        self.txindex = txindex
        self.tx_hash = tx_hash
        self.proof = proof
        self.sig = sig

    @property
    def hash(self):
        return utils.sha3(rlp.encode(self, TransactionConfirmation))

    @property
    def sign(self, key):
        self.sig1 = sign(self.hash, key)

    @property
    def sender(self):
        return get_sender(self.hash, self.sig)


UnsignTransactionConfirmation = TransactionConfirmation.exclude(['sig'])
