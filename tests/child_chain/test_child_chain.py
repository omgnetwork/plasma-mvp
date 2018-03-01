import rlp
import pytest
from plasma.child_chain.transaction import Transaction
from plasma.child_chain.block import Block
from plasma.child_chain.child_chain import ChildChain

@pytest.fixture
def root_chain(get_contract):
    return get_contract('RootChain/RootChain.sol')

@pytest.fixture
def child_chain(root_chain):
    child_chain = ChildChain(None, None, None)

    # Create some valid transations
    key = b'8b76243a95f959bf101248474e6bdacdedc8ad995d287c24616a41bd51642965'
    owner, amount1 = '0x8f2ecdd6103c0423f4c3e906666238936e81e538', 200
    tx1 = Transaction(0, 0, 0, 0, 0, 0, owner, amount1, b'\x00' * 20, 0, 0)
    tx2 = Transaction(0, 0, 0, 0, 0, 0, owner, amount1, b'\x00' * 20, 0, 0)

    # Create a block with those transactions
    child_chain.blocks[1] = Block([tx1, tx2])

    return child_chain

def test_send_tx_with_sig(child_chain):
    # Valid key
    key = b'8b76243a95f959bf101248474e6bdacdedc8ad995d287c24616a41bd51642965'

    newowner, amount2 = '0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26', 400
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner, amount2, b'\x00' * 20, 0, 0)

    # Sign the transaction
    tx3.sign1(key)
    tx3.sign2(key)

    child_chain.apply_transaction(rlp.encode(tx3).hex())

def test_send_tx_no_sig(child_chain):
    newowner, amount2 = '0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26', 400
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner, amount2, b'\x00' * 20, 0, 0)

    with pytest.raises(ValueError):
        child_chain.apply_transaction(rlp.encode(tx3).hex())

def test_send_tx_invalid_sig(child_chain):
    # Invalid key
    key = b'8a76243a95f959bf101248474e6bdacdedc8ad995d287c24616a41bd51642965'

    newowner, amount2 = '0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26', 400
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner, amount2, b'\x00' * 20, 0, 0)

    # Sign with an invalid key
    tx3.sign1(key)
    tx3.sign2(key)

    with pytest.raises(AssertionError):
        child_chain.apply_transaction(rlp.encode(tx3).hex())

def test_send_tx_double_spend(child_chain):
    key = b'8b76243a95f959bf101248474e6bdacdedc8ad995d287c24616a41bd51642965'

    newowner, amount2 = '0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26', 400
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner, amount2, b'\x00' * 20, 0, 0)

    tx3.sign1(key)
    tx3.sign2(key)

    # Submit once
    child_chain.apply_transaction(rlp.encode(tx3).hex())

    # Try to submit again
    with pytest.raises(AssertionError):
        child_chain.apply_transaction(rlp.encode(tx3).hex())
