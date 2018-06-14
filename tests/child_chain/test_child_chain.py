<<<<<<< HEAD
from unittest.mock import MagicMock

import pytest
import rlp
from ethereum import utils as u
from plasma.utils.utils import pack_utxo_pos
from plasma.child_chain.block import Block
from plasma.child_chain.child_chain import ChildChain
from plasma.child_chain.exceptions import (InvalidBlockMerkleException,
                                           InvalidBlockSignatureException,
=======
import pytest
from plasma.child_chain.exceptions import (InvalidBlockSignatureException,
>>>>>>> eb9a1ba4b82b5aa9179c68fcf6f1b75eb1798977
                                           InvalidTxSignatureException,
                                           TxAlreadySpentException)


<<<<<<< HEAD
@pytest.fixture(scope='function')
def child_chain():
    child_chain = ChildChain(AUTHORITY, MagicMock())
=======
def test_apply_deposit(test_lang):
    owner = test_lang.get_account()
>>>>>>> eb9a1ba4b82b5aa9179c68fcf6f1b75eb1798977

    test_lang.deposit(owner, 100)

<<<<<<< HEAD
    # Create a block with those transactions
    child_chain.blocks[1] = Block([tx1, tx2])

    yield child_chain

    child_chain.event_listener.stop_all()
=======
    deposit_block_number = 1
    deposit_block = test_lang.child_chain.blocks[deposit_block_number]
    assert len(deposit_block.transaction_set) == 1
>>>>>>> eb9a1ba4b82b5aa9179c68fcf6f1b75eb1798977


def test_send_tx_with_sig(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    test_lang.transfer(deposit_id, 0, owner_2, 100, owner_1)


def test_send_tx_no_sig(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    key = None

    deposit_id = test_lang.deposit(owner_1, 100)

    with pytest.raises(InvalidTxSignatureException):
        test_lang.transfer(deposit_id, 0, owner_2, 100, key)


def test_send_tx_invalid_sig(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()
    owner_3 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)

    with pytest.raises(InvalidTxSignatureException):
        test_lang.transfer(deposit_id, 0, owner_2, 100, owner_3)


def test_send_tx_double_spend(test_lang):
    owner_1 = test_lang.get_account()
    owner_2 = test_lang.get_account()

    deposit_id = test_lang.deposit(owner_1, 100)
    test_lang.transfer(deposit_id, 0, owner_2, 100, owner_1)

    with pytest.raises(TxAlreadySpentException):
        test_lang.transfer(deposit_id, 0, owner_2, 100, owner_1)


def test_submit_block(test_lang):
    old_block_number = test_lang.child_chain.current_block_number
    test_lang.submit_block()
    assert test_lang.child_chain.current_block_number == old_block_number + test_lang.child_chain.child_block_interval


def test_submit_block_no_sig(test_lang):
    with pytest.raises(InvalidBlockSignatureException):
        test_lang.submit_block(None)


def test_submit_block_invalid_sig(test_lang):
    owner_1 = test_lang.get_account()

    with pytest.raises(InvalidBlockSignatureException):
<<<<<<< HEAD
        child_chain.submit_block(block)


def test_submit_block_invalid_tx_set(child_chain):
    block = Block()
    block.transaction_set = child_chain.current_block.transaction_set[:]
    unsubmitted_tx = Transaction(0, 0, 0, 0, 0, 0, newowner1, 1234, b'\x00' * 20, 0)
    # Add an arbitrary transaction that hasn't been correctly submitted
    block.transaction_set.append(unsubmitted_tx)

    block.make_mutable()
    block.sign(block_key)
    block = rlp.encode(block).hex()

    with pytest.raises(InvalidBlockMerkleException):
        child_chain.submit_block(block)


def test_apply_deposit(child_chain):
    deposit_block_number = 1
    sample_event = {
        'args': {
            'depositor': '0xfd02EcEE62797e75D86BCff1642EB0844afB28c7',
            'amount': 100,
            'depositBlock': deposit_block_number,
        },
        'event': 'Deposit',
        'logIndex': 0,
        'transactionIndex': 0,
        'transactionHash': '0x35e6446818b53b2c4537ebba32b9453b274286ffbb25e5b521a6b0a33e2cb953',
        'address': '0xA3B2a1804203b75b494028966C0f62e677447A39',
        'blockHash': '0x2550290dd333ea2876539b7ba474a804a9143b0d4ecb57b9d824f07ffd016747',
        'blockNumber': 1
    }
    child_chain.apply_deposit(sample_event)

    # Deposit block only contains one transaction
    assert len(child_chain.blocks[deposit_block_number].transaction_set) == 1


def test_apply_exit(child_chain):
    (blknum, txindex, oindex) = (1, 0, 0)
    sample_event = {
        'args': {
            'exitor': '0xfd02EcEE62797e75D86BCff1642EB0844afB28c7',
            'utxoPos': pack_utxo_pos(blknum, txindex, oindex),
            'amount': 100,
        },
        'event': 'ExitStarted',
        'logIndex': 0,
        'transactionIndex': 0,
        'transactionHash': '0x35e6446818b53b2c4537ebba32b9453b274286ffbb25e5b521a6b0a33e2cb953',
        'address': '0xA3B2a1804203b75b494028966C0f62e677447A39',
        'blockHash': '0x2550290dd333ea2876539b7ba474a804a9143b0d4ecb57b9d824f07ffd016747',
        'blockNumber': 1
    }

    # Transaction not marked spent
    assert not child_chain.blocks[blknum].transaction_set[txindex].spent1

    child_chain.apply_exit(sample_event)

    # Transaction is marked spent
    assert child_chain.blocks[blknum].transaction_set[txindex].spent1
=======
        test_lang.submit_block(owner_1)
>>>>>>> eb9a1ba4b82b5aa9179c68fcf6f1b75eb1798977
