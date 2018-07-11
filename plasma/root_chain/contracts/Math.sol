pragma solidity ^0.4.0;


/**
 * @title Math
 * @dev Basic math operations
 */
library Math {

    /**
     * @dev Returns the maximum of two numbers
     * @param a uint256 number
     * @param b uint256 number
     */
    function max(uint256 a, uint256 b)
        internal
        pure
        returns (uint256) 
    {
        return a >= b ? a : b;
    }
}