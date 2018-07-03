from ethereum.utils import sha3
from plasma_core.constants import NULL_HASH
from .exceptions import MemberNotExistException
from .node import Node


class FixedMerkle(object):

    def __init__(self, depth, leaves=[], hashed=False):
        if depth < 1:
            raise ValueError('depth should be at least 1')

        self.depth = depth
        self.leaf_count = 2 ** depth
        self.hashed = hashed

        if len(leaves) > self.leaf_count:
            raise ValueError('num of leaves exceed max avaiable num with the depth')

        if not hashed:
            leaves = [sha3(leaf) for leaf in leaves]
        self.leaves = leaves + [NULL_HASH] * (self.leaf_count - len(leaves))
        self.tree = [self.create_nodes(self.leaves)]
        self.create_tree(self.tree[0])

    def create_nodes(self, leaves):
        return [Node(leaf) for leaf in leaves]

    def create_tree(self, leaves):
        if len(leaves) == 1:
            self.root = leaves[0].data
            return self.root
        next_level = len(leaves)
        tree_level = []
        for i in range(0, next_level, 2):
            combined = sha3(leaves[i].data + leaves[i + 1].data)
            next_node = Node(combined, leaves[i], leaves[i + 1])
            tree_level.append(next_node)
        self.tree.append(tree_level)
        self.create_tree(tree_level)

    def check_membership(self, leaf, index, proof):
        if not self.hashed:
            leaf = sha3(leaf)
        computed_hash = leaf
        for i in range(0, self.depth * 32, 32):
            segment = proof[i:i + 32]
            if index % 2 == 0:
                computed_hash = sha3(computed_hash + segment)
            else:
                computed_hash = sha3(segment + computed_hash)
            index = index // 2
        return computed_hash == self.root

    def create_membership_proof(self, leaf):
        if not self.hashed:
            leaf = sha3(leaf)
        if not self.is_member(leaf):
            raise MemberNotExistException('leaf is not in the merkle tree')

        index = self.leaves.index(leaf)
        proof = b''
        for i in range(0, self.depth, 1):
            if index % 2 == 0:
                sibling_index = index + 1
            else:
                sibling_index = index - 1
            index = index // 2
            proof += self.tree[i][sibling_index].data
        return proof

    def is_member(self, leaf):
        return leaf in self.leaves

    def not_member(self, leaf):
        return leaf not in self.leaves
