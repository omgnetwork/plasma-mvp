import rlp
from rlp.sedes import big_endian_int
from ethereum.utils import address

class Utxo(rlp.Serializable):

    fields = [
        ('owner', address),
        ('amount', big_endian_int),

    ]

    def __init__(self, owner, amount):
        self.owner = owner
        self.amount = amount
