from ethereum.utils import sha3
from plasma.utils.merkle.fixed_merkle import FixedMerkle
from plasma.utils.utils import get_empty_merkle_tree_hash
import rlp


def test_initial_state():
    assert FixedMerkle(2).leaves == [b'\x00' * 32] * 4
    assert FixedMerkle(3).leaves == [b'\x00' * 32] * 8
    assert FixedMerkle(12).leaves == [b'\x00' * 32] * (2**12)


def test_initialize_with_leaves(assert_tx_failed):
    leaves_1 = [b'a', b'c', b'c']
    leaves_2 = [b'a', b'c', b'c', b'd', b'e']
    assert FixedMerkle(2, leaves_1, True).leaves == leaves_1 + [b'\x00' * 32]
    # Fails if more leaves are submitted then tree depth permits can handle
    assert_tx_failed(lambda: FixedMerkle(1, leaves_1, True), AssertionError)
    assert_tx_failed(lambda: FixedMerkle(2, leaves_2, True), AssertionError)
    assert FixedMerkle(3, leaves_2, True).leaves == leaves_2 + [b'\x00' * 32] * 3


def test_hash_empty_tree():
    root_1 = sha3(b'\x00' * 32 + b'\x00' * 32)
    root_2 = sha3(root_1 + root_1)
    assert FixedMerkle(1, [], True).root == root_1
    assert FixedMerkle(2, [], True).root == root_2
    assert FixedMerkle(16, [], True).root == get_empty_merkle_tree_hash(16)


def test_check_membership(u):
    leaf_1 = b'\xff' * 31 + b'\x01'
    leaf_2 = b'\xff' * 31 + b'\x02'
    leaf_3 = b'\xff' * 31 + b'\x03'
    leaf_4 = b'\xff' * 31 + b'\x04'
    root = u.sha3(u.sha3(leaf_1 + leaf_2) + u.sha3(leaf_3 + leaf_4))
    zero_bytes = b'\x00' * 32
    zeros_hashes = get_empty_merkle_tree_hash(2)
    for i in range(13):
        root = u.sha3(root + zeros_hashes[-32:])
        zeros_hashes += u.sha3(zeros_hashes[-32:] + zeros_hashes[-32:])
    left_proof = leaf_2 + u.sha3(leaf_3 + leaf_4)  + zeros_hashes
    left_middle_proof = leaf_1 + u.sha3(leaf_3 + leaf_4) + zeros_hashes
    right_middle_proof = leaf_4 + u.sha3(leaf_1 + leaf_2) + zeros_hashes
    right_proof = leaf_3 + u.sha3(leaf_1 + leaf_2) + zeros_hashes
    fixed_merkle = FixedMerkle(16, [leaf_1, leaf_2, leaf_3, leaf_4], True)
    assert  fixed_merkle.check_membership(leaf_1, 0, left_proof) == True
    assert  fixed_merkle.check_membership(leaf_2, 1, left_middle_proof) == True
    assert  fixed_merkle.check_membership(leaf_3, 2, right_middle_proof) == True
    assert  fixed_merkle.check_membership(leaf_4, 3, right_proof) == True

def test_create_membership_proof():
    leaves = [b'a', b'b', b'c']
    merkle = FixedMerkle(2, leaves)
    proof_1 = merkle.create_membership_proof(b'a')
    proof_2 = merkle.create_membership_proof(b'c')
    assert merkle.check_membership(b'a', 0, proof_1) == True
    assert merkle.check_membership(b'c', 2, proof_2) == True

def test_is_member():
    leaves = [b'a', b'b', b'c']
    merkle = FixedMerkle(2, leaves, True)
    assert merkle.is_member(b'b') == True
    assert merkle.is_member(b'd') == False


def test_non_member():
    leaves = [b'a', b'b', b'c']
    merkle = FixedMerkle(2, leaves, True)
    assert merkle.not_member(b'b') == False
    assert merkle.not_member(b'd') == True
