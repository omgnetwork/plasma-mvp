import pytest
import rlp
from plasma.child_chain.utxo import Utxo
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
    assert tx.utxos[0].owner == newowner1
    assert tx.utxos[0].amount == amount1
    assert tx.utxos[1].owner == newowner2
    assert tx.utxos[1].amount == amount2
    assert tx.sig1 == [0, 0, 0]
    assert tx.sig2 == [0, 0, 0]
    tx_vars = [blknum1, txindex1, oindex1,
                blknum2, txindex2, oindex2,
                newowner1, amount1,
                newowner2, amount2,
                fee]
    assert_failed(lambda: tx.sender1, ValueError)
    assert_failed(lambda: tx.sender2, ValueError)
    tx.sign1(key1)
    assert tx.sender1 ==  oldowner1
    assert_failed(lambda: tx.sender2, ValueError)
    tx.sign2(key2)
    assert tx.sender2 ==  oldowner2
