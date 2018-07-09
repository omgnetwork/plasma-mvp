from web3 import Web3
from plasma_core.constants import NULL_ADDRESS, NULL_ADDRESS_HEX
from plasma_core.transaction import Transaction


def test_deposit(test_lang):
    owner_1 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)

    tx = Transaction(0, 0, 0, 0, 0, 0, NULL_ADDRESS, owner_1['address'], 100, NULL_ADDRESS, 0, 0)
    deposit_hash = Web3.soliditySha3(['address', 'address', 'uint256'], [owner_1['address'], NULL_ADDRESS_HEX, 100])

    assert test_lang.transactions[deposit_id]['tx'].hash == tx.hash

    deposit_blknum = 1
    deposit_block = test_lang.child_chain.blocks[deposit_blknum]
    assert deposit_block.transaction_set[0].hash == tx.hash
    assert test_lang.root_chain.call().getChildChain(deposit_blknum)[0] == deposit_hash


def test_transfer(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    transfer_id = test_lang.transfer(deposit_id, 0, owner_2, 100, owner_1)

    tx = Transaction(1, 0, 0,
                     0, 0, 0,
                     NULL_ADDRESS,
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
    assert test_lang.root_chain.call().getChildChain(blknum)[0] == test_lang.child_chain.blocks[blknum].merklize_transaction_set()


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
    assert exit_data[0] == owner_2['address']
    assert exit_data[1] == NULL_ADDRESS_HEX
    assert exit_data[2] == 100


def test_withdraw_deposit(test_lang):
    owner_1 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    test_lang.withdraw(deposit_id, 0, owner_1)

    exit_data = test_lang.root_chain.call().getExit(1000000001)
    assert exit_data[0] == owner_1['address']
    assert exit_data[1] == NULL_ADDRESS_HEX
    assert exit_data[2] == 100
