pragma solidity ^0.4.0;


/**
 * @title Merkle
 * @dev Operations on Merkle trees.
 */
library Merkle {
    /*
     * Internal function
     */
    
    /**
     * @dev Checks that a leaf is actually in a Merkle tree.
     * @param _leaf Leaf to verify.
     * @param _index Index of the leaf in the tree.
     * @param _rootHash Root of the tree.
     * @param _proof Merkle proof showing the leaf is in the tree.
     * @return True if the leaf is in the tree, false otherwise.
     */
    function checkMembership(
        bytes32 _leaf,
        uint256 _index,
        bytes32 _rootHash,
        bytes _proof
    ) internal pure returns (bool) {
        // Check that the proof length is valid.
        require(_proof.length % 32 == 0, "Invalid proof length.");

        // Compute the merkle root.
        bytes32 proofElement;
        bytes32 computedHash = _leaf;
        uint256 index = _index;
        for (uint256 i = 32; i <= _proof.length; i += 32) {
            assembly {
                proofElement := mload(add(_proof, i))
            }
            if (_index % 2 == 0) {
                computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
            } else {
                computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
            }
            index = index / 2;
        }

        // Check that the computer root and specified root match.
        return computedHash == _rootHash;
    }
}
