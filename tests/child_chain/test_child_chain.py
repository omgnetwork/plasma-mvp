from unittest.mock import Mock

import pytest
import rlp
from ethereum import utils as u
from plasma.child_chain.block import Block
from plasma.child_chain.child_chain import ChildChain
from plasma.child_chain.exceptions import (InvalidBlockMerkleException,
                                           InvalidBlockSignatureException,
                                           InvalidTxSignatureException,
                                           TxAlreadySpentException)
from plasma.child_chain.transaction import Transaction

AUTHORITY = b'\xfd\x02\xec\xeeby~u\xd8k\xcf\xf1d.\xb0\x84J\xfb(\xc7'
tx_key = u.normalize_key(b'8b76243a95f959bf101248474e6bdacdedc8ad995d287c24616a41bd51642965')
invalid_tx_key = u.normalize_key(b'8a76243a95f959bf101248474e6bdacdedc8ad995d287c24616a41bd51642965')
block_key = u.normalize_key(b'3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304')
invalid_block_key = u.normalize_key(b'3ab369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304')
newowner1 = b'\x8cT\xa4\xa0\x17\x9f$\x80\x1fI\xf92-\xab<\x87\xeb\x19L\x9b'
amount1 = 200
amount2 = 400


@pytest.fixture
def child_chain():
    child_chain = ChildChain(AUTHORITY, Mock())

    # Create some valid transations
    tx1 = Transaction(0, 0, 0, 0, 0, 0, newowner1, amount1, b'\x00' * 20, 0)
    tx2 = Transaction(0, 0, 0, 0, 0, 0, newowner1, amount1, b'\x00' * 20, 0)

    # Create a block with those transactions
    child_chain.blocks[1] = Block([tx1, tx2])

    return child_chain


def test_send_tx_with_sig(child_chain):
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner1, amount2, b'\x00' * 20, 0)

    # Sign the transaction
    tx3.sign1(tx_key)
    tx3.sign2(tx_key)

    child_chain.apply_transaction(rlp.encode(tx3).hex())


def test_send_tx_no_sig(child_chain):
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner1, amount2, b'\x00' * 20, 0)

    with pytest.raises(InvalidTxSignatureException):
        child_chain.apply_transaction(rlp.encode(tx3).hex())


def test_send_tx_invalid_sig(child_chain):
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner1, amount2, b'\x00' * 20, 0)

    # Sign with an invalid key
    tx3.sign1(invalid_tx_key)
    tx3.sign2(invalid_tx_key)

    with pytest.raises(InvalidTxSignatureException):
        child_chain.apply_transaction(rlp.encode(tx3).hex())


def test_send_tx_double_spend(child_chain):
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner1, amount2, b'\x00' * 20, 0)

    tx3.sign1(tx_key)
    tx3.sign2(tx_key)

    # Submit once
    child_chain.apply_transaction(rlp.encode(tx3).hex())

    # Try to submit again
    with pytest.raises(TxAlreadySpentException):
        child_chain.apply_transaction(rlp.encode(tx3).hex())


def test_submit_block(child_chain):
    block = child_chain.current_block
    block.make_mutable()
    block.sign(block_key)
    block = rlp.encode(block).hex()

    old_block_number = child_chain.current_block_number
    child_chain.submit_block(block)
    assert child_chain.current_block_number == old_block_number + child_chain.child_block_interval


def test_submit_block_no_sig(child_chain):
    block = child_chain.current_block
    block = rlp.encode(block).hex()

    with pytest.raises(InvalidBlockSignatureException):
        child_chain.submit_block(block)


def test_submit_block_invalid_sig(child_chain):
    block = child_chain.current_block
    block.make_mutable()
    block.sign(invalid_block_key)
    block = rlp.encode(block).hex()

    with pytest.raises(InvalidBlockSignatureException):
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
