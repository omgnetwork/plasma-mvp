import rlp
from rlp.sedes import big_endian_int, CountableList
from ethereum import utils
from plasma.config import plasma_config
from plasma.utils.utils import get_sender
from .utxo import Utxo


class Transaction(rlp.Serializable):

    fields = [
        ('blknum1', big_endian_int),
        ('txindex1', big_endian_int),
        ('oindex1', big_endian_int),
        ('blknum2', big_endian_int),
        ('txindex2', big_endian_int),
        ('oindex2', big_endian_int),
        ('utxos', CountableList(Utxo)),
        ('fee', big_endian_int),
        ('sig1', CountableList(big_endian_int)),
        ('sig2', CountableList(big_endian_int)),
    ]

    # fields 
    def __init__(self, blknum1, txindex1, oindex1,
                    blknum2, txindex2, oindex2,
                    newowner1, amount1, 
                    newowner2, amount2,
                    fee):
        # Input 1
        self.blknum1 = blknum1
        self.txindex1 = txindex1
        self.oindex1 = oindex1
        self.sig1 = [0, 0, 0]

        # Input 2
        self.blknum2 = blknum2
        self.txindex2 = txindex2
        self.oindex2 = oindex2
        self.sig2 = [0, 0, 0]

        # Outputs
        self.utxos = [Utxo(newowner1, amount1), Utxo(newowner2, amount2)]

        # Fee
        self.fee = fee

    @property
    def hash(self):
        return utils.sha3(rlp.encode(self, UnsignedTransaction))

    def sign1(self, key):
        self.sig1 = utils.ecsign(self.hash, key)

    def sign2(self, key):
        self.sig2 = utils.ecsign(self.hash, key)

    @property
    def sender1(self):
        return get_sender(self.hash, self.sig1)

    @property
    def sender2(self):
        return get_sender(self.hash, self.sig2)

UnsignedTransaction = Transaction.exclude(['sig1', 'sig2'])