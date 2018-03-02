import rlp
import pytest
from ethereum import utils as u
from plasma.child_chain.transaction import Transaction
from plasma.child_chain.block import Block
from plasma.child_chain.child_chain import ChildChain


key1 = u.normalize_key(b'8b76243a95f959bf101248474e6bdacdedc8ad995d287c24616a41bd51642965')
invalid_key = u.normalize_key(b'8a76243a95f959bf101248474e6bdacdedc8ad995d287c24616a41bd51642965')
newowner1 = b'\x8cT\xa4\xa0\x17\x9f$\x80\x1fI\xf92-\xab<\x87\xeb\x19L\x9b'
amount1 = 200
amount2 = 400


@pytest.fixture
def root_chain(get_contract):
    return get_contract('RootChain/RootChain.sol')


@pytest.fixture
def child_chain(root_chain):
    child_chain = ChildChain(None, None, None)

    # Create some valid transations
    tx1 = Transaction(0, 0, 0, 0, 0, 0, newowner1, amount1, b'\x00' * 20, 0, 0)
    tx2 = Transaction(0, 0, 0, 0, 0, 0, newowner1, amount1, b'\x00' * 20, 0, 0)

    # Create a block with those transactions
    child_chain.blocks[1] = Block([tx1, tx2])

    return child_chain


def test_send_tx_with_sig(child_chain):
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner1, amount2, b'\x00' * 20, 0, 0)

    # Sign the transaction
    tx3.sign1(key1)
    tx3.sign2(key1)

    child_chain.apply_transaction(rlp.encode(tx3).hex())


def test_send_tx_no_sig(child_chain):
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner1, amount2, b'\x00' * 20, 0, 0)

    with pytest.raises(AssertionError):
        child_chain.apply_transaction(rlp.encode(tx3).hex())


def test_send_tx_invalid_sig(child_chain):
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner1, amount2, b'\x00' * 20, 0, 0)

    # Sign with an invalid key
    tx3.sign1(invalid_key)
    tx3.sign2(invalid_key)

    with pytest.raises(AssertionError):
        child_chain.apply_transaction(rlp.encode(tx3).hex())


def test_send_tx_double_spend(child_chain, u):
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner1, amount2, b'\x00' * 20, 0, 0)

    tx3.sign1(key1)
    tx3.sign2(key1)

    # Submit once
    child_chain.apply_transaction(rlp.encode(tx3).hex())

    # Try to submit again
    with pytest.raises(AssertionError):
        child_chain.apply_transaction(rlp.encode(tx3).hex())
