from web3 import Web3
from plasma_core.constants import NULL_ADDRESS, NULL_ADDRESS_HEX
from plasma_core.transaction import Transaction
from plasma_core.utils.transactions import decode_utxo_id


def test_deposit(test_lang):
    owner_1 = test_lang.get_account()
    amount = 100

    deposit_id = test_lang.deposit(owner_1, amount)

    tx = Transaction(0, 0, 0, 0, 0, 0, NULL_ADDRESS, owner_1['address'], amount, NULL_ADDRESS, 0)
    deposit_hash = Web3.soliditySha3(['address', 'address', 'uint256'], [owner_1['address'], NULL_ADDRESS_HEX, amount])  # pylint: disable=E1120

    (deposit_blknum, _, _) = decode_utxo_id(deposit_id)
    deposit_block = test_lang.child_chain.get_block(deposit_blknum)
    assert deposit_block.transaction_set[0].hash == tx.hash
    assert test_lang.root_chain.call().getPlasmaBlock(deposit_blknum)[0] == deposit_hash


def test_transfer(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    amount = 100

    deposit_id = test_lang.deposit(owner_1, amount)
    transfer_id = test_lang.transfer(deposit_id, owner_2, amount, owner_1)

    tx = Transaction(1, 0, 0,
                     0, 0, 0,
                     NULL_ADDRESS,
                     owner_2['address'], amount,
                     NULL_ADDRESS, 0)

    assert test_lang.child_chain.get_transaction(transfer_id).hash == tx.hash


def test_submit_block(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    amount = 100

    deposit_id = test_lang.deposit(owner_1, amount)
    test_lang.transfer(deposit_id, owner_2, amount, owner_1)

    blknum = 1000
    assert test_lang.root_chain.call().getPlasmaBlock(blknum)[0] == test_lang.child_chain.get_block(blknum).root


def test_withdraw_transfer(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    amount = 100

    deposit_id = test_lang.deposit(owner_1, amount)
    transfer_id = test_lang.transfer(deposit_id, owner_2, amount, owner_1)
    test_lang.confirm(transfer_id, owner_1)
    test_lang.start_exit(transfer_id, owner_2)

    exit_data = test_lang.root_chain.call().getExit(1000000000000)
    assert exit_data[0] == owner_2['address']
    assert exit_data[1] == NULL_ADDRESS_HEX
    assert exit_data[2] == amount


def test_withdraw_deposit(test_lang):
    owner_1 = test_lang.get_account()
    amount = 100

    deposit_id = test_lang.deposit(owner_1, amount)
    test_lang.start_deposit_exit(deposit_id, owner_1)

    exit_data = test_lang.root_chain.call().getExit(1000000000)
    assert exit_data[0] == owner_1['address']
    assert exit_data[1] == NULL_ADDRESS_HEX
    assert exit_data[2] == amount
