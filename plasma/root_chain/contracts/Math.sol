pragma solidity ^0.4.0;


/**
 * @title Math
 * @dev Basic math operations.
 */
library Math {
    /*
     * Internal functions.
     */

    /**
     * @dev Returns the maximum of two numbers.
     * @param _a uint256 number.
     * @param _b uint256 number.
     * @return The greater of _a or _b.
     */
    function max(uint256 _a, uint256 _b) internal pure returns (uint256) {
        return _a >= _b ? _a : _b;
    }
}
