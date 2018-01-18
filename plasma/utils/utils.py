from ethereum import utils as u
from plasma.utils.merkle.fixed_merkle import FixedMerkle


def get_empty_merkle_tree_hash(depth):
    zeroes_hash = b'\x00' * 32
    for i in range(depth):
        zeroes_hash = u.sha3(zeroes_hash + zeroes_hash)
    return zeroes_hash


def get_merkle_of_leaves(depth, leaves):
    return FixedMerkle(depth, leaves)


def bytes_fill_left(inp, length):
    return bytes(length - len(inp)) + inp


ZEROS_BYTES = [b'\x00' * 32]


def confirm_tx(tx, root, key):
    return sign(u.sha3(tx.hash + tx.sig1 + tx.sig2 + root), key)


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
