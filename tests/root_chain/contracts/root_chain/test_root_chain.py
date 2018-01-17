import pytest
import rlp
from plasma.child_chain.transaction import Transaction, UnsignedTransaction
from plasma.utils.merkle.fixed_merkle import FixedMerkle
from plasma.utils.utils import get_merkle_of_leaves, confirm_tx


@pytest.fixture
def root_chain(t, get_contract):
    contract = get_contract('RootChain/RootChain.sol')
    t.chain.mine()
    return contract


def test_deposit(t, root_chain):
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx = Transaction(0, 0, 0, 0, 0, 0,
                owner, value_1, null_address, 0, 0)
    tx_bytes = rlp.encode(tx, UnsignedTransaction)
    root_chain.deposit(tx_bytes, value=value_1)
    assert root_chain.getChildChain(1)[0] == get_merkle_of_leaves(16, [tx.hash + tx.sig1 + tx.sig2]).root
    assert root_chain.getChildChain(1)[1] == t.chain.head_state.timestamp
    assert root_chain.currentChildBlock() == 2


def test_start_exit(t, root_chain, assert_tx_failed):
    week_and_a_half = 60 * 60 * 24 * 13
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                owner, value_1, null_address, 0, 0)
    tx_bytes1 = rlp.encode(tx1, UnsignedTransaction)
    root_chain.deposit(tx_bytes1, value=value_1)
    merkle = FixedMerkle(16, [tx1.merkle_hash], True)
    proof = merkle.create_membership_proof(tx1.merkle_hash)
    confirmSig1 = confirm_tx(tx1, root_chain.getChildChain(1)[0], key)
    priority1 = 1 * 1000000000 + 10000 * 0 + 0
    snapshot = t.chain.snapshot()
    sigs = tx1.sig1 + tx1.sig2 + confirmSig1
    # Deposit exit
    root_chain.startExit([1, 0, 0], tx_bytes1, proof, sigs, sender=key)
    t.chain.head_state.timestamp += week_and_a_half
    # Cannot exit twice off of the same utxo
    assert_tx_failed(lambda:root_chain.startExit([1, 0, 0], tx_bytes1, proof, sigs, sender=key));
    assert root_chain.getExit(priority1) == ['0x' + owner.hex(), 100, [1, 0, 0]]
    t.chain.revert(snapshot)

    tx2 = Transaction(1, 0, 0, 0, 0, 0,
                owner, value_1, null_address, 0, 0)
    tx2.sign1(key)
    tx_bytes2 = rlp.encode(tx2, UnsignedTransaction)
    merkle = FixedMerkle(16, [tx2.merkle_hash], True)
    proof = merkle.create_membership_proof(tx2.merkle_hash)
    t.chain.head_state.block_number += 7
    root_chain.submitBlock(merkle.root)
    confirmSig1 = confirm_tx(tx2, root_chain.getChildChain(2)[0], key)
    priority2 = 2 * 1000000000 + 10000 * 0 + 0
    sigs = tx2.sig1 + tx2.sig2 + confirmSig1
    snapshot = t.chain.snapshot()
    # Single input exit
    root_chain.startExit([2, 0, 0], tx_bytes2, proof, sigs, sender=key)
    assert root_chain.getExit(priority2) == ['0x' + owner.hex(), 100, [2, 0, 0]]
    t.chain.revert(snapshot)

    root_chain.deposit(tx_bytes1, value=value_1)
    tx3 = Transaction(2, 0, 0, 3, 0, 0,
                owner, value_1, null_address, 0, 0)
    tx3.sign1(key)
    tx3.sign2(key)
    tx_bytes3 = rlp.encode(tx3, UnsignedTransaction)
    merkle = FixedMerkle(16, [tx3.merkle_hash], True)
    proof = merkle.create_membership_proof(tx3.merkle_hash)
    t.chain.head_state.block_number += 7
    root_chain.submitBlock(merkle.root)
    confirmSig1 = confirm_tx(tx3, root_chain.getChildChain(4)[0], key)
    confirmSig2 = confirm_tx(tx3, root_chain.getChildChain(4)[0], key)
    priority3 = 4 * 1000000000 + 10000 * 0 + 0
    sigs = tx3.sig1 + tx3.sig2 + confirmSig1 + confirmSig2
    # Double input exit
    root_chain.startExit([4, 0, 0], tx_bytes3, proof, sigs, sender=key)
    assert root_chain.getExit(priority3) == ['0x' + owner.hex(), 100, [4, 0, 0]]


def test_challenge_exit(t, u, root_chain):
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                owner, value_1, null_address, 0, 0)
    tx_bytes1 = rlp.encode(tx1, UnsignedTransaction)
    root_chain.deposit(tx_bytes1, value=value_1)
    merkle = FixedMerkle(16, [tx1.merkle_hash], True)
    proof = merkle.create_membership_proof(tx1.merkle_hash)
    confirmSig1 = confirm_tx(tx1, root_chain.getChildChain(1)[0], key)
    sigs = tx1.sig1 + tx1.sig2 + confirmSig1
    root_chain.startExit([1, 0, 0], tx_bytes1, proof, sigs, sender=key)
    tx2 = Transaction(1, 0, 0, 0, 0, 0,
                owner, value_1, null_address, 0, 0)
    tx2.sign1(key)
    tx_bytes2 = rlp.encode(tx2, UnsignedTransaction)
    merkle = FixedMerkle(16, [tx2.merkle_hash], True)
    proof = merkle.create_membership_proof(tx2.merkle_hash)
    t.chain.head_state.block_number += 7
    root_chain.submitBlock(merkle.root)
    confirmSig = confirm_tx(tx2, root_chain.getChildChain(2)[0], key)
    sigs = tx2.sig1 + tx2.sig2
    exit_id = 1 * 1000000000 + 10000 * 0 + 0
    assert root_chain.exits(exit_id) == ['0x' + owner.hex(), 100]
    assert root_chain.exitIds(exit_id) == exit_id
    root_chain.challengeExit(exit_id, [2, 0, 0], tx_bytes2, proof, sigs, confirmSig)
    assert root_chain.exits(exit_id) == ['0x0000000000000000000000000000000000000000', 0]
    assert root_chain.exitIds(exit_id) == 0


def test_finalize_exits(t, u, root_chain):
    two_weeks = 60 * 60 * 24 * 14
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                owner, value_1, null_address, 0, 0)
    tx_bytes1 = rlp.encode(tx1, UnsignedTransaction)
    root_chain.deposit(tx_bytes1, value=value_1)
    merkle = FixedMerkle(16, [tx1.merkle_hash], True)
    proof = merkle.create_membership_proof(tx1.merkle_hash)
    confirmSig1 = confirm_tx(tx1, root_chain.getChildChain(1)[0], key)
    sigs = tx1.sig1 + tx1.sig2 + confirmSig1
    root_chain.startExit([1, 0, 0], tx_bytes1, proof, sigs, sender=key)
    exit_id = 1 * 1000000000 + 10000 * 0 + 0
    t.chain.head_state.timestamp += two_weeks * 2
    assert root_chain.exits(exit_id) == ['0x' + owner.hex(), 100]
    assert root_chain.exitIds(exit_id) == exit_id
    pre_balance = t.chain.head_state.get_balance(owner)
    root_chain.finalizeExits(sender=t.k2)
    post_balance = t.chain.head_state.get_balance(owner)
    assert post_balance == pre_balance + value_1
    assert root_chain.exits(exit_id) == ['0x0000000000000000000000000000000000000000', 0]
    assert root_chain.exitIds(exit_id) == 0
