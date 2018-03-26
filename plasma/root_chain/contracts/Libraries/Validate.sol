pragma solidity 0.4.18;

import "./ByteUtils.sol";
import "./ECRecovery.sol";

/**
 * @title Validate
 * @dev Checks that the signatures on a transaction are valid
 */

library Validate {
    function checkSigs(bytes32 txHash, bytes32 rootHash, uint256 blknum1, uint256 blknum2, bytes sigs)
        internal
        view
        returns (bool)
    {
        require(sigs.length % 65 == 0 && sigs.length <= 260);
        bytes memory sig1 = ByteUtils.slice(sigs, 0, 65);
        bytes memory sig2 = ByteUtils.slice(sigs, 65, 65);
        bytes memory confSig1 = ByteUtils.slice(sigs, 130, 65);
        bytes32 confirmationHash = keccak256(txHash, rootHash);

        if (blknum1 == 0 && blknum2 == 0) {
            return msg.sender == ECRecovery.recover(confirmationHash, confSig1);
        }
        bool check1 = true;
        bool check2 = true;
        if (blknum1 > 0) {
            check1 = ECRecovery.recover(txHash, sig1) == ECRecovery.recover(confirmationHash, confSig1);
        } 
        if (blknum2 > 0) {
            bytes memory confSig2 = ByteUtils.slice(sigs, 195, 65);
            check2 = ECRecovery.recover(txHash, sig2) == ECRecovery.recover(confirmationHash, confSig2);
        }
        return check1 && check2;
    }
}
