from web3 import Web3
from plasma.child_chain.transaction import Transaction


NULL_ADDRESS = b'\x00' * 20


def test_deposit(test_lang):
    owner_1 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)

    tx = Transaction(0, 0, 0, 0, 0, 0, owner_1['address'], 100, NULL_ADDRESS, 0, 0)
    deposit_hash = bytes.fromhex(Web3.soliditySha3(['address', 'uint256'], [owner_1['address'], 100])[2:])

    assert test_lang.transactions[deposit_id]['tx'].hash == tx.hash

    deposit_blknum = 1
    deposit_block = test_lang.child_chain.blocks[deposit_blknum]
    assert deposit_block.transaction_set[0].hash == tx.hash
    assert test_lang.root_chain.call().getChildChain(deposit_blknum)[0].encode('latin-1') == deposit_hash


def test_transfer(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    transfer_id = test_lang.transfer(deposit_id, 0, owner_2, 100, owner_1)

    tx = Transaction(1, 0, 0,
                     0, 0, 0,
                     owner_2['address'], 100,
                     NULL_ADDRESS, 0,
                     0)

    assert test_lang.transactions[transfer_id]['tx'].hash == tx.hash
    assert test_lang.child_chain.current_block.transaction_set[0].hash == tx.hash


def test_submit_block(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    test_lang.transfer(deposit_id, 0, owner_2, 100, owner_1)
    test_lang.submit_block()

    blknum = 1000
    assert test_lang.root_chain.call().getChildChain(blknum)[0].encode('latin-1') == test_lang.child_chain.blocks[blknum].merklize_transaction_set()


def test_confirm(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    transfer_id = test_lang.transfer(deposit_id, 0, owner_2, 100, owner_1)
    test_lang.submit_block()
    test_lang.confirm(transfer_id, owner_1)

    assert test_lang.transactions[transfer_id]['confirm_sigs'] != ''


def test_withdraw_transfer(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    transfer_id = test_lang.transfer(deposit_id, 0, owner_2, 100, owner_1)
    test_lang.submit_block()
    test_lang.confirm(transfer_id, owner_1)
    test_lang.withdraw(transfer_id, 0, owner_2)

    exit_data = test_lang.root_chain.call().getExit(1000000000000)
    assert exit_data[0].lower() == owner_2['address']
    assert exit_data[1] == 100


def test_withdraw_deposit(test_lang):
    owner_1 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    test_lang.withdraw(deposit_id, 0, owner_1)

    exit_data = test_lang.root_chain.call().getExit(1000000001)
    assert exit_data[0].lower() == owner_1['address']
    assert exit_data[1] == 100
