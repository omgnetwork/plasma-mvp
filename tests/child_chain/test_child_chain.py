import rlp
import pytest
from plasma.child_chain.transaction import Transaction
from plasma.child_chain.block import Block
from plasma.child_chain.child_chain import ChildChain

def test_submit_double_spend():
    child_chain = ChildChain(None, None, None)

    # Create some valid inputs
    owner, amount1 = '0xfd02ecee62797e75d86bcff1642eb0844afb28c7', 200
    tx1 = Transaction(0, 0, 0, 0, 0, 0, owner, amount1, b'\x00' * 20, 0, 0)
    tx2 = Transaction(0, 0, 0, 0, 0, 0, owner, amount1, b'\x00' * 20, 0, 0)

    # Create a block with those transactions
    child_chain.blocks[1] = Block([tx1, tx2])

    # Create a tx that spends the above UTXOs
    newowner, amount2 = '0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26', 400
    tx3 = Transaction(1, 0, 0, 1, 1, 0, newowner, amount2, b'\x00' * 20, 0, 0)

    # Submit the tx once
    child_chain.apply_transaction(rlp.encode(tx3).hex())

    # Try to submit the tx again
    with pytest.raises(AssertionError):
        child_chain.apply_transaction(rlp.encode(tx3).hex())
