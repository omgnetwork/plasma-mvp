pragma solidity 0.4.18;


/**
 * @title Bytes operations
 *
 * @dev Based on https://github.com/GNSPS/solidity-bytes-utils/blob/master/contracts/BytesLib.sol
 */

library ByteUtils {
    function slice(bytes _bytes, uint _start, uint _length)
        internal
        pure
        returns (bytes)
    {
        
        bytes memory tempBytes;
        
        assembly {
            tempBytes := mload(0x40)
            
            let lengthmod := and(_length, 31)
            
            let mc := add(tempBytes, lengthmod)
            let end := add(mc, _length)
            
            for {
                let cc := add(add(_bytes, lengthmod), _start)
            } lt(mc, end) {
                mc := add(mc, 0x20)
                cc := add(cc, 0x20)
            } {
                mstore(mc, mload(cc))
            }
            
            mstore(tempBytes, _length)
            
            //update free-memory pointer
            //allocating the array padded to 32 bytes like the compiler does now
            mstore(0x40, and(add(mc, 31), not(31)))
        }
        
        return tempBytes;
    }
}
