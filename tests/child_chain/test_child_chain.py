import pytest
from plasma_core.exceptions import (InvalidBlockSignatureException,
                                    InvalidTxSignatureException,
                                    TxAlreadySpentException)


def test_apply_deposit(test_lang):
    owner = test_lang.get_account()
    amount = 100

    test_lang.deposit(owner, amount)

    deposit_block_number = 1
    deposit_block = test_lang.child_chain.get_block(deposit_block_number)
    assert len(deposit_block.transaction_set) == 1


def test_send_tx_with_sig(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    amount = 100

    deposit_id = test_lang.deposit(owner_1, amount)
    test_lang.transfer(deposit_id, owner_2, amount, owner_1)


def test_send_tx_no_sig(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    amount = 100
    key = None

    deposit_id = test_lang.deposit(owner_1, amount)

    with pytest.raises(InvalidTxSignatureException):
        test_lang.transfer(deposit_id, owner_2, amount, key)


def test_send_tx_invalid_sig(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    owner_3 = test_lang.get_account()
    amount = 100

    deposit_id = test_lang.deposit(owner_1, amount)

    with pytest.raises(InvalidTxSignatureException):
        test_lang.transfer(deposit_id, owner_2, amount, owner_3)


def test_send_tx_double_spend(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    amount = 100

    deposit_id = test_lang.deposit(owner_1, amount)
    test_lang.transfer(deposit_id, owner_2, amount, owner_1)

    with pytest.raises(TxAlreadySpentException):
        test_lang.transfer(deposit_id, owner_2, amount, owner_1)


def test_submit_block(test_lang):
    old_block_number = test_lang.child_chain.get_current_block().number
    test_lang.submit_block()
    new_block_number = test_lang.child_chain.get_current_block().number
    assert new_block_number == old_block_number + test_lang.child_chain.chain.child_block_interval


def test_submit_block_no_sig(test_lang):
    with pytest.raises(InvalidBlockSignatureException):
        test_lang.submit_block(None)


def test_submit_block_invalid_sig(test_lang):
    owner_1 = test_lang.get_account()

    with pytest.raises(InvalidBlockSignatureException):
        test_lang.submit_block(owner_1)
