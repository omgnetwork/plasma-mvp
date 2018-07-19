from plasma_core.transaction import Transaction
from plasma_core.constants import NULL_ADDRESS


BLKNUM_OFFSET = 1000000000
TXINDEX_OFFSET = 10000


def decode_utxo_id(utxo_id):
    blknum = utxo_id // BLKNUM_OFFSET
    txindex = (utxo_id % BLKNUM_OFFSET) // BLKNUM_OFFSET
    oindex = utxo_id - blknum * BLKNUM_OFFSET - txindex * TXINDEX_OFFSET
    return (blknum, txindex, oindex)


def encode_utxo_id(blknum, txindex, oindex):
    return (blknum * BLKNUM_OFFSET) + (txindex * TXINDEX_OFFSET) + (oindex * 1)


def decode_tx_id(utxo_id):
    (blknum, txindex, _) = decode_utxo_id(utxo_id)
    return encode_utxo_id(blknum, txindex, 0)


def get_deposit_tx(owner, amount):
    return Transaction(0, 0, 0,
                       0, 0, 0,
                       NULL_ADDRESS,
                       owner, amount,
                       NULL_ADDRESS, 0)
