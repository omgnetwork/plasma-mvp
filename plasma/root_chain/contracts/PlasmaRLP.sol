pragma solidity ^0.5.0;

import "./RLPDecode.sol";


library PlasmaRLP {

    struct exitingTx {
        address payable exitor;
        address token;
        uint256 amount;
        uint256 inputCount;
    }

    /* Public Functions */

    function getUtxoPos(bytes memory challengingTxBytes, uint256 oIndex)
        internal
        returns (uint256)
    {
        RLPDecode.RLPItem[] memory txList = RLPDecode.toList(RLPDecode.toRlpItem(challengingTxBytes));
        uint256 oIndexShift = oIndex * 3;
        return
            RLPDecode.toUint(txList[0 + oIndexShift]) * 1000000000 +
            RLPDecode.toUint(txList[1 + oIndexShift]) * 10000 +
            RLPDecode.toUint(txList[2 + oIndexShift]);
    }

    function createExitingTx(bytes memory exitingTxBytes, uint256 oindex)
        internal
        returns (exitingTx memory)
    {
        RLPDecode.RLPItem[] memory txList = RLPDecode.toList(RLPDecode.toRlpItem(exitingTxBytes));
//    address payable exitor = RLPDecode.toAddress(txList[7 + 2 * oindex]);
        return exitingTx({
            exitor: RLPDecode.toAddress(txList[7 + 2 * oindex]),
            token: RLPDecode.toAddress(txList[6]),
            amount: RLPDecode.toUint(txList[8 + 2 * oindex]),
            inputCount: RLPDecode.toUint(txList[0]) * RLPDecode.toUint(txList[3])
        });
    }
}
