import pytest
import rlp
from plasma.child_chain.transaction import Transaction, UnsignedTransaction
from plasma.config import plasma_config


def test_transaction(t, u, assert_failed):
    blknum1, txindex1, oindex1 = 1, 1, 0
    blknum2, txindex2, oindex2 = 2, 2, 1
    newowner1, amount1 = t.a1, 100
    newowner2, amount2 = t.a2, 150
    fee = 5
    oldowner1, oldowner2 = t.a1, t.a2
    key1, key2 = t.k1, t.k2
    tx = Transaction(blknum1, txindex1, oindex1,
                blknum2, txindex2, oindex2,
                newowner1, amount1,
                newowner2, amount2,
                fee)
    assert tx.blknum1 == blknum1
    assert tx.txindex1 == txindex1
    assert tx.oindex1 == oindex1
    assert tx.blknum2 == blknum2
    assert txindex2 == txindex2
    assert tx.oindex2 == oindex2
    assert tx.newowner1 == newowner1
    assert tx.amount1 == amount1
    assert tx.newowner2 == newowner2
    assert tx.amount2 == amount2
    assert tx.sig1 == b'\x00' * 65
    assert tx.sig2 == b'\x00' * 65
    tx.sign1(key1)
    assert tx.sender1 ==  oldowner1
    tx.sign2(key2)
    assert tx.sender2 ==  oldowner2