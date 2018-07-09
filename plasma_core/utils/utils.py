from ethereum import utils as u
from plasma_core.constants import NULL_HASH
from plasma_core.utils.merkle.fixed_merkle import FixedMerkle


def get_empty_merkle_tree_hash(depth):
    zeroes_hash = NULL_HASH
    for i in range(depth):
        zeroes_hash = u.sha3(zeroes_hash + zeroes_hash)
    return zeroes_hash


def get_merkle_of_leaves(depth, leaves):
    return FixedMerkle(depth, leaves)


def bytes_fill_left(inp, length):
    return bytes(length - len(inp)) + inp


def confirm_tx(tx, root, key):
    return sign(u.sha3(tx.hash + root), key)


def get_deposit_hash(owner, token, value):
    return u.sha3(owner + token + b'\x00' * 31 + u.int_to_bytes(value))


def sign(hash, key):
    vrs = u.ecsign(hash, key)
    rsv = vrs[1:] + vrs[:1]
    vrs_bytes = [u.encode_int32(i) for i in rsv[:2]] + [u.int_to_bytes(rsv[2])]
    return b''.join(vrs_bytes)


def get_sender(hash, sig):
    v = sig[64]
    if v < 27:
        v += 27
    r = u.bytes_to_int(sig[:32])
    s = u.bytes_to_int(sig[32:64])
    pub = u.ecrecover_to_pub(hash, v, r, s)
    return u.sha3(pub)[-20:]


def unpack_utxo_pos(utxo_pos):
    blknum = utxo_pos // 1000000000
    txindex = (utxo_pos % 1000000000) // 10000
    oindex = utxo_pos - blknum * 1000000000 - txindex * 10000
    return (blknum, txindex, oindex)


def pack_utxo_pos(blknum, txindex, oindex):
    return (blknum * 1000000000) + (txindex * 10000) + (oindex * 1)
