pragma solidity 0.4.18;
import './ByteUtils.sol';
import './ECRecovery.sol';


library Validate {
    function checkSigs(bytes32 txHash, bytes32 rootHash, uint256 inputCount, bytes sigs)
        internal
        view
        returns (bool)
    {
        require(sigs.length % 65 == 0 && sigs.length <= 260);
        bytes memory sig1 = ByteUtils.slice(sigs, 0, 65);
        bytes memory sig2 = ByteUtils.slice(sigs, 65, 65);
        bytes memory confSig1 = ByteUtils.slice(sigs, 130, 65);
        bytes32 confirmationHash = keccak256(txHash, sig1, sig2, rootHash);
        if (inputCount == 0) {
            return msg.sender == ECRecovery.recover(confirmationHash, confSig1);
        }
        if (inputCount < 1000000) {
            return ECRecovery.recover(txHash, sig1) == ECRecovery.recover(confirmationHash, confSig1);
        } else {
            bytes memory confSig2 = ByteUtils.slice(sigs, 195, 65);
            bool check1 = ECRecovery.recover(txHash, sig1) == ECRecovery.recover(confirmationHash, confSig1);
            bool check2 = ECRecovery.recover(txHash, sig2) == ECRecovery.recover(confirmationHash, confSig2);
            return check1 && check2;
        }
    }
}
