pragma solidity 0.4.18;

import "./RLP.sol";


library PlasmaRLP {

    struct exitingTx {
        uint256 amount;
        address exitor;
        uint256 inputCount;
    }

    /* Public Functions */

    function getUtxoPos(bytes memory challengingTxBytes, uint256 oIndex)
        internal
        constant
        returns (uint256)
    {
        var txList = RLP.toList(RLP.toRlpItem(challengingTxBytes));
        uint256 oIndexShift = oIndex * 3;
        return
            RLP.toUint(txList[0 + oIndexShift]) +
            RLP.toUint(txList[1 + oIndexShift]) +
            RLP.toUint(txList[2 + oIndexShift]);
    }

    function createExitingTx(bytes memory exitingTxBytes, uint256 oindex)
        internal
        constant
        returns (exitingTx)
    {
        var txList = RLP.toList(RLP.toRlpItem(exitingTxBytes));
        return exitingTx({
            amount: RLP.toUint(txList[7 + 2 * oindex]),
            exitor: RLP.toAddress(txList[6 + 2 * oindex]),
            inputCount: RLP.toUint(txList[0]) * RLP.toUint(txList[3])
        });
    }
}
