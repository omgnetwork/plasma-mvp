import pytest
import rlp
from plasma.child_chain.transaction import Transaction, UnsignedTransaction
from plasma.utils.merkle.fixed_merkle import FixedMerkle
from plasma.utils.utils import get_merkle_of_leaves, confirm_tx, get_deposit_hash


@pytest.fixture
def root_chain(t, get_contract):
    contract = get_contract('RootChain/RootChain.sol')
    t.chain.mine()
    return contract


def testNextBlockNumber(t, root_chain):
    assert 1000 == root_chain.childBlockInterval()
    assert 1000 == root_chain.nextWeekOldChildBlock(0)
    assert 1000 == root_chain.nextWeekOldChildBlock(55)
    assert 2000 == root_chain.nextWeekOldChildBlock(1000)
    assert 2000 == root_chain.nextWeekOldChildBlock(1001)


def test_deposit(t, u, root_chain):
    owner, value_1 = t.a0, 100
    blknum = root_chain.getDepositBlock()
    root_chain.deposit(value=value_1)
    assert root_chain.getChildChain(blknum)[0] == get_merkle_of_leaves(16, [owner + b'\x00' * 31 + u.int_to_bytes(value_1)]).root
    assert root_chain.getChildChain(blknum)[1] == t.chain.head_state.timestamp


def test_start_exit(t, root_chain, assert_tx_failed):
    week_and_a_half = 60 * 60 * 24 * 13
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                      owner, value_1, null_address, 0, 0)
    deposit_tx_hash = get_deposit_hash(owner, value_1)
    dep_blknum = root_chain.getDepositBlock()
    assert dep_blknum == 1
    root_chain.deposit(value=value_1, sender=key)
    merkle = FixedMerkle(16, [deposit_tx_hash], True)
    proof = merkle.create_membership_proof(deposit_tx_hash)
    confirmSig1 = confirm_tx(tx1, root_chain.getChildChain(dep_blknum)[0], key)
    priority1 = dep_blknum * 1000000000 + 10000 * 0 + 0
    snapshot = t.chain.snapshot()
    sigs = tx1.sig1 + tx1.sig2 + confirmSig1
    utxoId = dep_blknum * 1000000000 + 10000 * 0 + 0
    # Deposit exit
    root_chain.startDepositExit(utxoId, tx1.amount1, proof, sender=key)

    t.chain.head_state.timestamp += week_and_a_half
    # Cannot exit twice off of the same utxo
    utxoPos1 = dep_blknum * 1000000000 + 10000 * 0 + 0
    assert_tx_failed(lambda: root_chain.startExit(utxoPos1, deposit_tx_hash, proof, sigs, sender=key))
    assert root_chain.getExit(priority1) == ['0x' + owner.hex(), 100]
    t.chain.revert(snapshot)

    tx2 = Transaction(dep_blknum, 0, 0, 0, 0, 0,
                      owner, value_1, null_address, 0, 0)
    tx2.sign1(key)
    tx_bytes2 = rlp.encode(tx2, UnsignedTransaction)
    merkle = FixedMerkle(16, [tx2.merkle_hash], True)
    proof = merkle.create_membership_proof(tx2.merkle_hash)
    child_blknum = root_chain.currentChildBlock()
    assert child_blknum == 1000
    root_chain.submitBlock(merkle.root)
    confirmSig1 = confirm_tx(tx2, root_chain.getChildChain(child_blknum)[0], key)
    priority2 = child_blknum * 1000000000 + 10000 * 0 + 0
    sigs = tx2.sig1 + tx2.sig2 + confirmSig1
    snapshot = t.chain.snapshot()
    # # Single input exit
    utxoPos2 = child_blknum * 1000000000 + 10000 * 0 + 0
    root_chain.startExit(utxoPos2, tx_bytes2, proof, sigs, sender=key)
    assert root_chain.getExit(priority2) == ['0x' + owner.hex(), 100]
    t.chain.revert(snapshot)
    dep2_blknum = root_chain.getDepositBlock()
    assert dep2_blknum == 1001
    root_chain.deposit(value=value_1, sender=key)
    tx3 = Transaction(child_blknum, 0, 0, dep2_blknum, 0, 0,
                      owner, value_1, null_address, 0, 0)
    tx3.sign1(key)
    tx3.sign2(key)
    tx_bytes3 = rlp.encode(tx3, UnsignedTransaction)
    merkle = FixedMerkle(16, [tx3.merkle_hash], True)
    proof = merkle.create_membership_proof(tx3.merkle_hash)
    child2_blknum = root_chain.currentChildBlock()
    assert child2_blknum == 2000
    root_chain.submitBlock(merkle.root)
    confirmSig1 = confirm_tx(tx3, root_chain.getChildChain(child2_blknum)[0], key)
    confirmSig2 = confirm_tx(tx3, root_chain.getChildChain(child2_blknum)[0], key)
    priority3 = child2_blknum * 1000000000 + 10000 * 0 + 0
    sigs = tx3.sig1 + tx3.sig2 + confirmSig1 + confirmSig2
    # Double input exit
    utxoPos3 = child2_blknum * 1000000000 + 10000 * 0 + 0
    root_chain.startExit(utxoPos3, tx_bytes3, proof, sigs, sender=key)
    assert root_chain.getExit(priority3) == ['0x' + owner.hex(), 100]


def test_challenge_exit(t, u, root_chain):
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                      owner, value_1, null_address, 0, 0)
    deposit_tx_hash = get_deposit_hash(owner, value_1)
    dep1_blknum = root_chain.getDepositBlock()
    root_chain.deposit(value=value_1, sender=key)
    merkle = FixedMerkle(16, [deposit_tx_hash], True)
    proof = merkle.create_membership_proof(deposit_tx_hash)
    confirmSig1 = confirm_tx(tx1, root_chain.getChildChain(dep1_blknum)[0], key)
    sigs = tx1.sig1 + tx1.sig2 + confirmSig1
    utxoPos1 = dep1_blknum * 1000000000 + 10000 * 0 + 0
    root_chain.startDepositExit(utxoPos1, tx1.amount1, proof, sender=key)
    tx2 = Transaction(dep1_blknum, 0, 0, 0, 0, 0,
                      owner, value_1, null_address, 0, 0)
    tx2.sign1(key)
    tx_bytes2 = rlp.encode(tx2, UnsignedTransaction)
    merkle = FixedMerkle(16, [tx2.merkle_hash], True)
    proof = merkle.create_membership_proof(tx2.merkle_hash)
    child_blknum = root_chain.currentChildBlock()
    root_chain.submitBlock(merkle.root)
    confirmSig = confirm_tx(tx2, root_chain.getChildChain(child_blknum)[0], key)
    sigs = tx2.sig1 + tx2.sig2
    utxoPos2 = child_blknum * 1000000000 + 10000 * 0 + 0
    assert root_chain.exits(utxoPos1) == ['0x' + owner.hex(), 100]
    root_chain.challengeExit(utxoPos2, utxoPos1, tx_bytes2, proof, sigs, confirmSig)
    assert root_chain.exits(utxoPos1) == ['0x0000000000000000000000000000000000000000', value_1]


def test_finalize_exits(t, u, root_chain):
    two_weeks = 60 * 60 * 24 * 14
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                      owner, value_1, null_address, 0, 0)
    deposit_tx_hash = get_deposit_hash(owner, value_1)
    dep1_blknum = root_chain.getDepositBlock()
    root_chain.deposit(value=value_1, sender=key)
    merkle = FixedMerkle(16, [deposit_tx_hash], True)
    proof = merkle.create_membership_proof(deposit_tx_hash)
    utxoPos1 = dep1_blknum * 1000000000 + 10000 * 0 + 0 * 10000000
    root_chain.startDepositExit(utxoPos1, tx1.amount1, proof, sender=key)
    t.chain.head_state.timestamp += two_weeks * 2
    assert root_chain.exits(utxoPos1) == ['0x' + owner.hex(), 100]
    pre_balance = t.chain.head_state.get_balance(owner)
    root_chain.finalizeExits(sender=t.k2)
    post_balance = t.chain.head_state.get_balance(owner)
    assert post_balance == pre_balance + value_1
    assert root_chain.exits(utxoPos1) == ['0x0000000000000000000000000000000000000000', value_1]
