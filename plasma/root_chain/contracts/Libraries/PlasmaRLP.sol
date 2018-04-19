pragma solidity 0.4.18;

/**
 * @title RLPReader
 * @dev RLPReader is used to read and parse RLP encoded data in memory.
 * @author Andreas Olofsson (androlo1980@gmail.com)
 */

library PlasmaRLP {
    uint constant DATA_SHORT_START = 0x80;
    uint constant DATA_LONG_START = 0xB8;
    uint constant LIST_SHORT_START = 0xC0;
    uint constant LIST_LONG_START = 0xF8;

    uint constant DATA_LONG_OFFSET = 0xB7;


    struct RLPItem {
        uint _unsafe_memPtr;    // Pointer to the RLP-encoded bytes.
        uint _unsafe_length;    // Number of bytes. This is the full length of the string.
    }

    struct exitingTx {
        uint256 amount;
        address exitor;
        uint256 inputCount;
    }

    struct Iterator {
        RLPItem _unsafe_item;   // Item that's being iterated over.
        uint _unsafe_nextPtr;   // Position of the next item in the list.
    }

    /* Public Functions */

    function getUtxoPos(bytes memory challengingTxBytes, uint256 numItems, uint256 oIndex)
        internal
        constant
        returns (uint256)
    {
        var txList = toList(toRLPItem(challengingTxBytes), numItems);
        uint256 oIndexShift = oIndex * 3;
        return toUint(txList[0 + oIndexShift]) + toUint(txList[1 + oIndexShift]) + toUint(txList[2 + oIndexShift]);
    }

    function createExitingTx(bytes memory exitingTxBytes, uint256 numItems, uint256 oindex)
        internal
        constant
        returns (exitingTx)
    {
        var txList = toList(toRLPItem(exitingTxBytes), numItems);
        return exitingTx({
            amount: toUint(txList[7 + 2 * oindex]),
            exitor: toAddress(txList[6 + 2 * oindex]),
            inputCount: toUint(txList[0]) * toUint(txList[3]) 
        });
    }

    /* Iterator */

    function next(Iterator memory self) private constant returns (RLPItem memory subItem) {
        var ptr = self._unsafe_nextPtr;
        var itemLength = _itemLength(ptr);
        subItem._unsafe_memPtr = ptr;
        subItem._unsafe_length = itemLength;
        self._unsafe_nextPtr = ptr + itemLength;
    }

    function hasNext(Iterator memory self) private constant returns (bool) {
        var item = self._unsafe_item;
        return self._unsafe_nextPtr < item._unsafe_memPtr + item._unsafe_length;
    }

    /* RLPItem */

    /// @dev Creates an RLPItem from an array of RLP encoded bytes.
    /// @param self The RLP encoded bytes.
    /// @return An RLPItem
    function toRLPItem(bytes memory self) private constant returns (RLPItem memory) {
        uint len = self.length;
        uint memPtr;
        assembly {
            memPtr := add(self, 0x20)
        }
        return RLPItem(memPtr, len);
    }

    /// @dev Create an iterator.
    /// @param self The RLP item.
    /// @return An 'Iterator' over the item.
    function iterator(RLPItem memory self) private constant returns (Iterator memory it) {
        uint ptr = self._unsafe_memPtr + _payloadOffset(self);
        it._unsafe_item = self;
        it._unsafe_nextPtr = ptr;
    }

    /// @dev Get the list of sub-items from an RLP encoded list.
    /// Warning: This requires passing in the number of items.
    /// @param self The RLP item.
    /// @return Array of RLPItems.
    function toList(RLPItem memory self, uint256 numItems) private constant returns (RLPItem[] memory list) {
        list = new RLPItem[](numItems);
        var it = iterator(self);
        uint idx;
        while(idx < numItems) {
            list[idx] = next(it);
            idx++;
        }
    }

    /// @dev Decode an RLPItem into a uint. This will not work if the
    /// RLPItem is a list.
    /// @param self The RLPItem.
    /// @return The decoded string.
    function toUint(RLPItem memory self) private constant returns (uint data) {
        var (rStartPos, len) = _decode(self);
        assembly {
            data := div(mload(rStartPos), exp(256, sub(32, len)))
        }
    }

    /// @dev Decode an RLPItem into an address. This will not work if the
    /// RLPItem is a list.
    /// @param self The RLPItem.
    /// @return The decoded string.
    function toAddress(RLPItem memory self)
        private
        view
        returns (address data)
    {
        var (rStartPos, len) = _decode(self);
        assembly {
            data := div(mload(rStartPos), exp(256, 12))
        }
    }

    // Get the payload offset.
    function _payloadOffset(RLPItem memory self)
        private
        view
        returns (uint)
    {
        uint b0;
        uint memPtr = self._unsafe_memPtr;
        assembly {
            b0 := byte(0, mload(memPtr))
        }
        if(b0 < DATA_SHORT_START)
            return 0;
        if(b0 < DATA_LONG_START || (b0 >= LIST_SHORT_START && b0 < LIST_LONG_START))
            return 1;
    }

    // Get the full length of an RLP item.
    function _itemLength(uint memPtr)
        private
        view
        returns (uint len)
    {
        uint b0;
        assembly {
            b0 := byte(0, mload(memPtr))
        }
        if (b0 < DATA_SHORT_START)
            len = 1;
        else if (b0 < DATA_LONG_START)
            len = b0 - DATA_SHORT_START + 1;
    }

    // Get start position and length of the data.
    function _decode(RLPItem memory self)
        private
        view
        returns (uint memPtr, uint len)
    {
        uint b0;
        uint start = self._unsafe_memPtr;
        assembly {
            b0 := byte(0, mload(start))
        }
        if (b0 < DATA_SHORT_START) {
            memPtr = start;
            len = 1;
            return;
        }
        if (b0 < DATA_LONG_START) {
            len = self._unsafe_length - 1;
            memPtr = start + 1;
        } else {
            uint bLen;
            assembly {
                bLen := sub(b0, 0xB7) // DATA_LONG_OFFSET
            }
            len = self._unsafe_length - 1 - bLen;
            memPtr = start + bLen + 1;
        }
        return;
    }
}
