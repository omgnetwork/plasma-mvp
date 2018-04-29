from web3 import Web3
from plasma.child_chain.transaction import Transaction


NULL_ADDRESS = b'\x00' * 20


def test_deposit(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
    '''

    test_lang.parse(test_lang_string)

    owner1 = test_lang.accounts['Owner1']
    tx = Transaction(0, 0, 0, 0, 0, 0, owner1['address'], 100, NULL_ADDRESS, 0, 0)
    deposit_hash = bytes.fromhex(Web3.soliditySha3(['address', 'uint256'], [owner1['address'], 100])[2:])

    assert test_lang.transactions['Deposit1']['tx'].hash == tx.hash

    deposit_blknum = 1
    deposit_block = test_lang.child_chain.blocks[deposit_blknum]
    assert deposit_block.transaction_set[0].hash == tx.hash
    assert test_lang.root_chain.call().getChildChain(deposit_blknum)[0].encode('latin-1') == deposit_hash


def test_transfer(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1]
    '''

    test_lang.parse(test_lang_string)

    owner2 = test_lang.accounts['Owner2']
    tx = Transaction(1, 0, 0,
                     0, 0, 0,
                     owner2['address'], 100,
                     NULL_ADDRESS, 0,
                     0)

    assert test_lang.transactions['Transfer1']['tx'].hash == tx.hash
    assert test_lang.child_chain.current_block.transaction_set[0].hash == tx.hash


def test_submit_block(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1]
        SubmitBlock[OPERATOR]
    '''

    test_lang.parse(test_lang_string)

    blknum = 1000
    assert test_lang.root_chain.call().getChildChain(blknum)[0].encode('latin-1') == test_lang.child_chain.blocks[blknum].merklize_transaction_set()


def test_confirm(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1]
        SubmitBlock[OPERATOR]
        Confirm[Transfer1,Owner1]
    '''

    test_lang.parse(test_lang_string)

    assert test_lang.transactions['Transfer1']['confirm_sigs'] != ''


def test_withdraw_transfer(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1]
        SubmitBlock[OPERATOR]
        Confirm[Transfer1,Owner1]
        Withdraw[Transfer1.0,Owner2]
    '''

    test_lang.parse(test_lang_string)

    owner2 = test_lang.accounts['Owner2']
    exit_data = test_lang.root_chain.call().getExit(1000000000000)
    assert exit_data[0].lower() == owner2['address']
    assert exit_data[1] == 100


def test_withdraw_deposit(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Withdraw[Deposit1,Owner1]
    '''

    test_lang.parse(test_lang_string)

    owner1 = test_lang.accounts['Owner1']
    exit_data = test_lang.root_chain.call().getExit(1000000001)
    assert exit_data[0].lower() == owner1['address']
    assert exit_data[1] == 100
