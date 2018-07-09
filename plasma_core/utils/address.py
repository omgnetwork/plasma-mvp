def address_to_hex(address):
    return '0x' + address.hex()


def address_to_bytes(address):
    return bytes.fromhex(address[2:])
