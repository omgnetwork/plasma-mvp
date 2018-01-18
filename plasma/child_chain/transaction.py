import rlp
from rlp.sedes import big_endian_int, binary
from ethereum import utils
from plasma.utils.utils import get_sender, sign


class Transaction(rlp.Serializable):

    fields = [
        ('blknum1', big_endian_int),
        ('txindex1', big_endian_int),
        ('oindex1', big_endian_int),
        ('blknum2', big_endian_int),
        ('txindex2', big_endian_int),
        ('oindex2', big_endian_int),
        ('newowner1', utils.address),
        ('amount1', big_endian_int),
        ('newowner2', utils.address),
        ('amount2', big_endian_int),
        ('fee', big_endian_int),
        ('sig1', binary),
        ('sig2', binary),
    ]

    def __init__(self, blknum1, txindex1, oindex1,
                 blknum2, txindex2, oindex2,
                 newowner1, amount1,
                 newowner2, amount2,
                 fee,
                 sig1=b'\x00' * 65,
                 sig2=b'\x00' * 65):
        # Input 1
        self.blknum1 = blknum1
        self.txindex1 = txindex1
        self.oindex1 = oindex1
        self.sig1 = sig1

        # Input 2
        self.blknum2 = blknum2
        self.txindex2 = txindex2
        self.oindex2 = oindex2
        self.sig2 = sig2

        # Outputs
        self.newowner1 = newowner1
        self.amount1 = amount1

        self.newowner2 = newowner2
        self.amount2 = amount2

        # Fee
        self.fee = fee

    @property
    def hash(self):
        return utils.sha3(rlp.encode(self, UnsignedTransaction))

    @property
    def merkle_hash(self):
        return utils.sha3(self.hash + self.sig1 + self.sig2)

    def sign1(self, key):
        self.sig1 = sign(self.hash, key)

    def sign2(self, key):
        self.sig2 = sign(self.hash, key)

    @property
    def is_single_utxo(self):
        if self.blknum2 == 0:
            return True
        return False

    @property
    def sender1(self):
        return get_sender(self.hash, self.sig1)

    @property
    def sender2(self):
        return get_sender(self.hash, self.sig2)


UnsignedTransaction = Transaction.exclude(['sig1', 'sig2'])
