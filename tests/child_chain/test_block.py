import pytest
from plasma.child_chain.block import Block
from plasma.utils.utils import sign, get_sender


@pytest.fixture
def block():
    return Block()


def test_initial_state(block):
    block.transaction_set = []
    block.sig = b'\x00' * 65
    block.merkle = None


def test_signature(t, block):
    block.sign(t.k0)
    assert block.sig == sign(block.hash, t.k0)
    assert block.sender == get_sender(block.hash, sign(block.hash, t.k0))
