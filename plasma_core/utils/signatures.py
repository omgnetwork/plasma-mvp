from ethereum import utils as u


def sign(hash, key):
    vrs = u.ecsign(hash, key)
    rsv = vrs[1:] + vrs[:1]
    vrs_bytes = [u.encode_int32(i) for i in rsv[:2]] + [u.int_to_bytes(rsv[2])]
    return b''.join(vrs_bytes)


def get_signer(hash, sig):
    v = sig[64]
    if v < 27:
        v += 27
    r = u.bytes_to_int(sig[:32])
    s = u.bytes_to_int(sig[32:64])
    pub = u.ecrecover_to_pub(hash, v, r, s)
    return u.sha3(pub)[-20:]
