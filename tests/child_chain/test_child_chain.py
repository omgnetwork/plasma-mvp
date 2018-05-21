import pytest
from plasma.child_chain.exceptions import (InvalidBlockSignatureException,
                                           InvalidTxSignatureException,
                                           TxAlreadySpentException)


def test_apply_deposit(test_lang):
    # given
    owner = test_lang.get_account()

    # when
    test_lang.deposit(owner, 100)

    # then
    deposit_block_number = 1
    deposit_block = test_lang.child_chain.blocks[deposit_block_number]
    assert len(deposit_block.transaction_set) == 1


def test_send_tx_with_sig(test_lang):
    # given
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    # when
    deposit_id = test_lang.deposit(owner_1, 100)
    test_lang.transfer(deposit_id, owner_2, 100, owner_1)

    # then
    # XXX - assert something?


# XXX - redundant test – tests the same behavior as `test_send_tx_invalid_sig`
# def test_send_tx_no_sig(test_lang):
#     # test_lang_string = '''
#     #     Deposit1[Owner1,100]
#     #     Transfer1[Deposit1,Owner2,100,null,null,null,null,null]
#     # '''
#
#     owner_1 = test_lang.get_account()
#     owner_2 = test_lang.get_account()
#     key = None
#
#     deposit_id = test_lang.deposit(owner_1, 100)
#
#     with pytest.raises(InvalidTxSignatureException):
#         test_lang.transfer(deposit_id, owner_2, 100, key)


def test_send_tx_invalid_sig(test_lang):
    # given
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    owner_3 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)

    # when/then
    with pytest.raises(InvalidTxSignatureException):
        test_lang.transfer(deposit_id, owner_2, 100, owner_3)


def test_send_tx_double_spend(test_lang):
    # given
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    test_lang.transfer(deposit_id, owner_2, 100, owner_1)

    # when/then
    with pytest.raises(TxAlreadySpentException):
        # Try to submit again
        test_lang.transfer(deposit_id, owner_2, 100, owner_1)


def test_submit_block(test_lang):
    test_lang_string = '''
        SubmitBlock[OPERATOR]
    '''

    old_block_number = test_lang.child_chain.current_block_number
    test_lang.parse(test_lang_string)
    assert test_lang.child_chain.current_block_number == old_block_number + test_lang.child_chain.child_block_interval


def test_submit_block_no_sig(test_lang):
    test_lang_string = '''
        SubmitBlock[null]
    '''

    with pytest.raises(InvalidBlockSignatureException):
        test_lang.parse(test_lang_string)


def test_submit_block_invalid_sig(test_lang):
    test_lang_string = '''
        SubmitBlock[Owner1]
    '''

    with pytest.raises(InvalidBlockSignatureException):
        test_lang.parse(test_lang_string)
