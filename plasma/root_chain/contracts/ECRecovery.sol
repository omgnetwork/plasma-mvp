pragma solidity ^0.4.0;


/**
 * @title Eliptic curve signature operations
 * @dev Based on https://gist.github.com/axic/5b33912c6f61ae6fd96d6c4a47afde6d.
 */
library ECRecovery {
    /*
     * Internal functions
     */

    /**
     * @dev Recover signer address from a message by using their signature.
     * @param _hash Hash of the signed message 
     * @param _sig Signature over the signed message.
     * @return Address that signed the hash.
     */
    function recover(bytes32 _hash, bytes _sig) internal pure returns (address) {
        bytes32 r;
        bytes32 s;
        uint8 v;

        // Check the signature length.
        if (_sig.length != 65) {
            revert("Invalid signature length.");
        }

        // Divide the signature in v, r, and s variables.
        assembly {
            r := mload(add(_sig, 32))
            s := mload(add(_sig, 64))
            v := byte(0, mload(add(_sig, 96)))
        }

        // Version of signature should be 27 or 28, but 0 and 1 are also possible versions.
        if (v < 27) {
            v += 27;
        }

        // If the version is correct return the signer address.
        if (v != 27 && v != 28) {
            revert("Invalid signature version.");
        } else {
            return ecrecover(_hash, v, r, s);
        }
    }
}
