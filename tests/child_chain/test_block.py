import pytest
from plasma_core.block import Block
from plasma_core.constants import NULL_SIGNATURE
from plasma_core.utils.signatures import sign, get_signer


@pytest.fixture
def block():
    return Block()


def test_initial_state(block):
    assert block.transaction_set == []
    assert block.sig == NULL_SIGNATURE


def test_signature(t, block):
    block.sign(t.k0)
    assert block.sig == sign(block.hash, t.k0)
    assert block.signer == get_signer(block.hash, sign(block.hash, t.k0))
