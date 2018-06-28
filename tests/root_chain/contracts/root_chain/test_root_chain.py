import pytest
import rlp
from plasma.child_chain.transaction import Transaction, UnsignedTransaction
from plasma.utils.merkle.fixed_merkle import FixedMerkle
from plasma.utils.utils import confirm_tx, get_deposit_hash


@pytest.fixture
def root_chain(t, get_contract):
    contract = get_contract('RootChain')
    t.chain.mine()
    return contract


def test_deposit(t, u, root_chain):
    owner, value_1 = t.a0, 100
    blknum = root_chain.getDepositBlock()
    root_chain.deposit(value=value_1)
    assert root_chain.getChildChain(blknum)[0] == u.sha3(owner + b'\x00' * 31 + b'\x00' * 20 + u.int_to_bytes(value_1))
    assert root_chain.getChildChain(blknum)[1] == t.chain.head_state.timestamp
    assert root_chain.getDepositBlock() == blknum + 1


def test_start_deposit_exit(t, u, root_chain, assert_tx_failed):
    two_weeks = 60 * 60 * 24 * 7 * 2
    value_1 = 100
    # Deposit once to make sure everything works for deposit block
    root_chain.deposit(value=value_1)
    blknum = root_chain.getDepositBlock()
    root_chain.deposit(value=value_1)
    expected_utxo_pos = blknum * 1000000000
    expected_exitable_at = t.chain.head_state.timestamp + two_weeks
    null_address = b'\x00' * 20
    root_chain.startDepositExit(expected_utxo_pos, null_address, value_1)
    utxo_pos, exitable_at = root_chain.getNextExit(null_address)
    assert utxo_pos == expected_utxo_pos
    assert exitable_at == expected_exitable_at
    enc_null_address = "0x" + "00" * 20
    assert root_chain.exits(utxo_pos) == ['0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1', enc_null_address, 100]
    # Same deposit cannot be exited twice
    assert_tx_failed(lambda: root_chain.startDepositExit(utxo_pos, null_address, value_1))
    # Fails if transaction sender is not the depositor
    assert_tx_failed(lambda: root_chain.startDepositExit(utxo_pos, null_address, value_1, sender=t.k1))
    # Fails if utxo_pos is wrong
    assert_tx_failed(lambda: root_chain.startDepositExit(utxo_pos * 2, null_address, value_1))
    # Fails if value given is not equal to deposited value
    assert_tx_failed(lambda: root_chain.startDepositExit(utxo_pos, null_address, value_1 + 1))


def test_start_fee_exit(t, u, root_chain, assert_tx_failed):
    two_weeks = 60 * 60 * 24 * 7 * 2
    value_1 = 100
    blknum = root_chain.getDepositBlock()
    root_chain.deposit(value=value_1)
    expected_utxo_pos = root_chain.currentFeeExit()
    expected_exitable_at = t.chain.head_state.timestamp + two_weeks + 1
    assert root_chain.currentFeeExit() == 1
    null_address = b'\x00' * 20
    root_chain.startFeeExit(null_address, 1)
    assert root_chain.currentFeeExit() == 2
    utxo_pos, exitable_at = root_chain.getNextExit(null_address)
    fee_priority = exitable_at << 128 | utxo_pos
    assert utxo_pos == expected_utxo_pos
    assert exitable_at == expected_exitable_at

    expected_utxo_pos = blknum * 1000000000 + 1
    root_chain.startDepositExit(expected_utxo_pos, null_address, value_1)
    utxo_pos, created_at = root_chain.getNextExit(null_address)
    deposit_priority = created_at << 128 | utxo_pos
    assert fee_priority > deposit_priority
    # Fails if transaction sender isn't the authority
    assert_tx_failed(lambda: root_chain.startFeeExit(null_address, 1, sender=t.k1))


def test_start_exit(t, root_chain, assert_tx_failed):
    week_and_a_half = 60 * 60 * 24 * 13
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                      null_address,
                      owner, value_1, null_address, 0)
    deposit_tx_hash = get_deposit_hash(owner, null_address, value_1)
    dep_blknum = root_chain.getDepositBlock()
    assert dep_blknum == 1
    root_chain.deposit(value=value_1, sender=key)
    merkle = FixedMerkle(16, [deposit_tx_hash], True)
    proof = merkle.create_membership_proof(deposit_tx_hash)
    confirmSig1 = confirm_tx(tx1, root_chain.getChildChain(dep_blknum)[0], key)
    priority1 = dep_blknum * 1000000000 + 10000 * 0 + 1
    snapshot = t.chain.snapshot()
    sigs = tx1.sig1 + tx1.sig2 + confirmSig1
    utxoId = dep_blknum * 1000000000 + 10000 * 0 + 1
    # Deposit exit
    root_chain.startDepositExit(utxoId, null_address, tx1.amount1, sender=key)

    t.chain.head_state.timestamp += week_and_a_half
    # Cannot exit twice off of the same utxo
    utxo_pos1 = dep_blknum * 1000000000 + 10000 * 0 + 1
    assert_tx_failed(lambda: root_chain.startExit(utxo_pos1, deposit_tx_hash, proof, sigs, sender=key))
    enc_null_address = "0x" + "00" * 20
    assert root_chain.getExit(priority1) == ['0x' + owner.hex(), enc_null_address, 100]
    t.chain.revert(snapshot)

    tx2 = Transaction(dep_blknum, 0, 0, 0, 0, 0,
                      null_address,
                      owner, value_1, null_address, 0)
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
    utxo_pos2 = child_blknum * 1000000000 + 10000 * 0 + 0
    root_chain.startExit(utxo_pos2, tx_bytes2, proof, sigs, sender=key)
    assert root_chain.getExit(priority2) == ['0x' + owner.hex(), enc_null_address, 100]
    t.chain.revert(snapshot)
    dep2_blknum = root_chain.getDepositBlock()
    assert dep2_blknum == 1001
    root_chain.deposit(value=value_1, sender=key)
    tx3 = Transaction(child_blknum, 0, 0, dep2_blknum, 0, 0,
                      null_address,
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
    assert root_chain.getExit(priority3) == ['0x' + owner.hex(), enc_null_address, 100]


def test_challenge_exit(t, u, root_chain, assert_tx_failed):
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                      null_address,
                      owner, value_1, null_address, 0)
    deposit_tx_hash = get_deposit_hash(owner, null_address, value_1)
    utxo_pos1 = root_chain.getDepositBlock() * 1000000000 + 1
    root_chain.deposit(value=value_1, sender=key)
    utxo_pos2 = root_chain.getDepositBlock() * 1000000000
    root_chain.deposit(value=value_1, sender=key)
    merkle = FixedMerkle(16, [deposit_tx_hash], True)
    proof = merkle.create_membership_proof(deposit_tx_hash)
    confirmSig1 = confirm_tx(tx1, root_chain.getChildChain(utxo_pos1)[0], key)
    sigs = tx1.sig1 + tx1.sig2 + confirmSig1
    root_chain.startDepositExit(utxo_pos1, null_address, tx1.amount1, sender=key)
    tx3 = Transaction(utxo_pos2, 0, 0, 0, 0, 0,
                      null_address,
                      owner, value_1, null_address, 0)
    tx3.sign1(key)
    tx_bytes3 = rlp.encode(tx3, UnsignedTransaction)
    merkle = FixedMerkle(16, [tx3.merkle_hash], True)
    proof = merkle.create_membership_proof(tx3.merkle_hash)
    child_blknum = root_chain.currentChildBlock()
    root_chain.submitBlock(merkle.root)
    confirmSig = confirm_tx(tx3, root_chain.getChildChain(child_blknum)[0], key)
    sigs = tx3.sig1 + tx3.sig2
    utxo_pos3 = child_blknum * 1000000000 + 10000 * 0 + 0
    tx4 = Transaction(utxo_pos1, 0, 0, 0, 0, 0,
                      null_address,
                      owner, value_1, null_address, 0)
    tx4.sign1(key)
    tx_bytes4 = rlp.encode(tx4, UnsignedTransaction)
    merkle = FixedMerkle(16, [tx4.merkle_hash], True)
    proof = merkle.create_membership_proof(tx4.merkle_hash)
    child_blknum = root_chain.currentChildBlock()
    root_chain.submitBlock(merkle.root)
    confirmSig = confirm_tx(tx4, root_chain.getChildChain(child_blknum)[0], key)
    sigs = tx4.sig1 + tx4.sig2
    utxo_pos4 = child_blknum * 1000000000 + 10000 * 0 + 0
    oindex1 = 0
    enc_null_address = "0x" + "00" * 20
    assert root_chain.exits(utxo_pos1) == ['0x' + owner.hex(), enc_null_address, 100]
    # Fails if transaction after exit doesn't reference the utxo being exited
    assert_tx_failed(lambda: root_chain.challengeExit(utxo_pos3, utxo_pos1, tx_bytes3, proof, sigs, confirmSig))
    # Fails if transaction proof is incorrect
    assert_tx_failed(lambda: root_chain.challengeExit(utxo_pos4, utxo_pos1, tx_bytes4, proof[::-1], sigs, confirmSig))
    # Fails if transaction confirmation is incorrect
    assert_tx_failed(lambda: root_chain.challengeExit(utxo_pos4, utxo_pos1, tx_bytes4, proof, sigs, confirmSig[::-1]))
    root_chain.challengeExit(utxo_pos4, oindex1, tx_bytes4, proof, sigs, confirmSig)
    assert root_chain.exits(utxo_pos1) == ['0x0000000000000000000000000000000000000000', enc_null_address, value_1]


def test_finalize_exits(t, u, root_chain):
    two_weeks = 60 * 60 * 24 * 14
    owner, value_1, key = t.a1, 100, t.k1
    null_address = b'\x00' * 20
    tx1 = Transaction(0, 0, 0, 0, 0, 0,
                      null_address,
                      owner, value_1, null_address, 0)
    dep1_blknum = root_chain.getDepositBlock()
    root_chain.deposit(value=value_1, sender=key)
    utxo_pos1 = dep1_blknum * 1000000000 + 10000 * 0 + 1
    root_chain.startDepositExit(utxo_pos1, null_address, tx1.amount1, sender=key)
    t.chain.head_state.timestamp += two_weeks * 2
    enc_null_address = "0x" + "00" * 20
    assert root_chain.exits(utxo_pos1) == ['0x' + owner.hex(), enc_null_address, 100]
    pre_balance = t.chain.head_state.get_balance(owner)
    root_chain.finalizeExits(sender=t.k2)
    post_balance = t.chain.head_state.get_balance(owner)
    assert post_balance == pre_balance + value_1
    assert root_chain.exits(utxo_pos1) == ['0x0000000000000000000000000000000000000000', enc_null_address, value_1]
