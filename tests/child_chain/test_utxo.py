import rlp
from plasma.child_chain.utxo import Utxo


def test_utxo(t, u):
    owner, amount = t.a0, 100
    utxo = Utxo(owner, amount)
    assert utxo.owner == owner
    assert utxo.amount == amount
    assert rlp.decode(rlp.encode(utxo), Utxo) == utxo
