import pytest
from plasma.child_chain.exceptions import (InvalidBlockSignatureException,
                                           InvalidTxSignatureException,
                                           TxAlreadySpentException)


def test_apply_deposit(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
    '''

    test_lang.parse(test_lang_string)
    deposit_block_number = 1
    deposit_block = test_lang.child_chain.blocks[deposit_block_number]
    assert len(deposit_block.transaction_set) == 1


def test_send_tx_with_sig(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1]
    '''

    test_lang.parse(test_lang_string)


def test_send_tx_no_sig(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100]
    '''

    with pytest.raises(InvalidTxSignatureException):
        test_lang.parse(test_lang_string)


def test_send_tx_invalid_sig(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner3]
    '''

    with pytest.raises(InvalidTxSignatureException):
        test_lang.parse(test_lang_string)


def test_send_tx_double_spend(test_lang):
    test_lang_string1 = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1]
    '''

    test_lang_string2 = '''
        Transfer2[Deposit1,Owner2,100,Owner1]
    '''

    test_lang.parse(test_lang_string1)

    # Try to submit again
    with pytest.raises(TxAlreadySpentException):
        test_lang.parse(test_lang_string2)


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
