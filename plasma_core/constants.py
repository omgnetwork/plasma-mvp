from ethereum import utils as u

CONTRACT_ADDRESS = '0xA3B2a1804203b75b494028966C0f62e677447A39'

AUTHORITY = {
    'address': '0xfd02EcEE62797e75D86BCff1642EB0844afB28c7',
    'key': u.normalize_key(b'3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304')
}

ACCOUNTS = [
    {
        'address': '0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26',
        'key': u.normalize_key(b'b937b2c6a606edf1a4d671485f0fa61dcc5102e1ebca392f5a8140b23a8ac04f')
    },
    {
        'address': '0xda20A48913f9031337a5e32325F743e8536860e2',
        'key': u.normalize_key(b'999ba3f77899ba4802af5109221c64a9238a6772718f287a8bd3ca3d1b68187f')
    },
    {
        'address': '0xF6d8982698dCC46b8E96e34bC2BF3c97302b9923',
        'key': u.normalize_key(b'ef4134d11aa32bcbd314d3cd94b7a5f93bea2b809007d4307a4393cce0285652')
    },
    {
        'address': '0x2d75468C0cafA9D41FC5BF3ccA6C292a3cC03d94',
        'key': u.normalize_key(b'25c8620e5bd51caed1d2ff5e79b43dfbef17d0b4eb38d0db8d834da9de5a6120')
    },
    {
        'address': '0xF05B4B746AAd830062505AD0cFd3619917484E46',
        'key': u.normalize_key(b'e3d66a68573a85734e80d3de47b82e13374c2a026f219cb766978510a8b8697e')
    },
    {
        'address': '0x81A9bfA79598f1536B4918A6556e9855c5E141d5',
        'key': u.normalize_key(b'81e244b79cef097c187d9299a2fc3a680cf1d2637fb7463ca7aa70445a0a0410')
    },
    {
        'address': '0xa669513ad878cC0891d8C305CC21903068a9AFe9',
        'key': u.normalize_key(b'ebcaa9c519c2aaa27e7c1656451b9c72167cadf0fd30bc4bcc3bda6d6fcbd507')
    },
    {
        'address': '0xC3AaE3a9be258BD485105ef81EB0D5b677EE26fd',
        'key': u.normalize_key(b'b991543d47829ea4f296d182dfa7088303fb3f04dd0c95a5cb7132397e4a008d')
    },
    {
        'address': '0xB9DB71c2D02a1B30dfE29C90738b3228Dd9d2ec2',
        'key': u.normalize_key(b'484eb2f0465e7357575f05bf5af5e77cb4b678fb774dd127d9d99e3d31c5f80e')
    }
]

NULL_BYTE = b'\x00'
NULL_HASH = NULL_BYTE * 32
NULL_SIGNATURE = NULL_BYTE * 65
NULL_ADDRESS = NULL_BYTE * 20
NULL_ADDRESS_HEX = '0x' + NULL_ADDRESS.hex()
