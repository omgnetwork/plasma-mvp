pragma solidity ^0.4.0;

import "./SafeMath.sol";
import "./Math.sol";
import "./PlasmaRLP.sol";
import "./Merkle.sol";
import "./Validate.sol";
import "./PriorityQueue.sol";


/**
 * @title RootChain
 * @dev This contract secures a utxo payments plasma child chain to ethereum.
 */
contract RootChain {
    using SafeMath for uint256;
    using Merkle for bytes32;
    using PlasmaRLP for bytes;


    /*
     * Events
     */

    event Deposit(
        address indexed depositor,
        uint256 indexed depositBlock,
        uint256 amount
    );

    event ExitStarted(
        address indexed exitor,
        uint256 indexed utxoPos,
        uint256 amount
    );

    event BlockSubmitted(
        bytes32 root,
        uint256 timestamp
    );


    /*
     * Storage
     */

    uint256 public constant CHILD_BLOCK_INTERVAL = 1000;

    address public operator;

    uint256 public currentChildBlock;
    uint256 public currentDepositBlock;
    uint256 public currentFeeExit;

    mapping (uint256 => ChildBlock) public childChain;
    mapping (uint256 => Exit) public exits;

    PriorityQueue exitsQueue;

    struct Exit {
        address owner;
        uint256 amount;
    }

    struct ChildBlock {
        bytes32 root;
        uint256 timestamp;
    }


    /*
     * Modifiers
     */

    modifier onlyOperator() {
        require(msg.sender == operator);
        _;
    }


    /*
     * Constructor
     */

    constructor()
        public
    {
        operator = msg.sender;
        currentChildBlock = CHILD_BLOCK_INTERVAL;
        currentDepositBlock = 1;
        currentFeeExit = 1;
        exitsQueue = new PriorityQueue();
    }


    /*
     * Public Functions
     */

    /**
     * @dev Allows Plasma chain operator to submit block root.
     * @param _root The root of a child chain block.
     */
    function submitBlock(bytes32 _root)
        public
        onlyOperator
    {   
        childChain[currentChildBlock] = ChildBlock({
            root: _root,
            timestamp: block.timestamp
        });

        // Update block numbers.
        currentChildBlock = currentChildBlock.add(CHILD_BLOCK_INTERVAL);
        currentDepositBlock = 1;

        emit BlockSubmitted(_root, block.timestamp);
    }

    /**
     * @dev Allows anyone to deposit funds into the Plasma chain.
     */
    function deposit()
        public
        payable
    {
        // Only allow up to CHILD_BLOCK_INTERVAL deposits per child block.
        require(currentDepositBlock < CHILD_BLOCK_INTERVAL);

        bytes32 root = keccak256(msg.sender, msg.value);
        uint256 depositBlock = getDepositBlock();
        childChain[depositBlock] = ChildBlock({
            root: root,
            timestamp: block.timestamp
        });
        currentDepositBlock = currentDepositBlock.add(1);

        emit Deposit(msg.sender, depositBlock, msg.value);
    }

    /**
     * @dev Starts an exit from a deposit.
     * @param _depositPos UTXO position of the deposit.
     * @param _amount Deposit amount.
     */
    function startDepositExit(uint256 _depositPos, uint256 _amount)
        public
    {
        uint256 blknum = _depositPos / 1000000000;

        // Check that the given UTXO is a deposit.
        require(blknum % CHILD_BLOCK_INTERVAL != 0);

        // Validate the given owner and amount.
        bytes32 root = childChain[blknum].root;
        bytes32 depositHash = keccak256(msg.sender, _amount);
        require(root == depositHash);

        addExitToQueue(_depositPos, msg.sender, _amount, childChain[blknum].timestamp);
    }

    /**
     * @dev Allows the operator withdraw any allotted fees. Starts an exit to avoid theft.
     * @param _amount Amount in fees to withdraw.
     */
    function startFeeExit(uint256 _amount)
        public
        onlyOperator
    {
        addExitToQueue(currentFeeExit, msg.sender, _amount, block.timestamp + 1);
        currentFeeExit = currentFeeExit.add(1);
    }

    /**
     * @dev Starts to exit a specified utxo.
     * @param _utxoPos The position of the exiting utxo in the format of blknum * 1000000000 + index * 10000 + oindex.
     * @param _txBytes The transaction being exited in RLP bytes format.
     * @param _proof Proof of the exiting transactions inclusion for the block specified by utxoPos.
     * @param _sigs Both transaction signatures and confirmations signatures used to verify that the exiting transaction has been confirmed.
     */
    function startExit(
        uint256 _utxoPos,
        bytes _txBytes,
        bytes _proof,
        bytes _sigs
    )
        public
    {
        uint256 blknum = _utxoPos / 1000000000;
        uint256 txindex = (_utxoPos % 1000000000) / 10000;
        uint256 oindex = _utxoPos - blknum * 1000000000 - txindex * 10000; 

        // Check the sender owns this UTXO.
        var exitingTx = _txBytes.createExitingTx(oindex);
        require(msg.sender == exitingTx.exitor);

        // Check the transaction was included in the chain and is correctly signed.
        bytes32 root = childChain[blknum].root; 
        bytes32 merkleHash = keccak256(keccak256(_txBytes), ByteUtils.slice(_sigs, 0, 130));
        require(Validate.checkSigs(keccak256(_txBytes), root, exitingTx.inputCount, _sigs));
        require(merkleHash.checkMembership(txindex, root, _proof));

        addExitToQueue(_utxoPos, exitingTx.exitor, exitingTx.amount, childChain[blknum].timestamp);
    }

    /**
     * @dev Allows anyone to challenge an exiting transaction by submitting proof of a double spend on the child chain.
     * @param _cUtxoPos The position of the challenging utxo.
     * @param _eUtxoIndex The output position of the exiting utxo.
     * @param _txBytes The challenging transaction in bytes RLP form.
     * @param _proof Proof of inclusion for the transaction used to challenge.
     * @param _sigs Signatures for the transaction used to challenge.
     * @param _confirmationSig The confirmation signature for the transaction used to challenge.
     */
    function challengeExit(
        uint256 _cUtxoPos,
        uint256 _eUtxoIndex,
        bytes _txBytes,
        bytes _proof,
        bytes _sigs,
        bytes _confirmationSig
    )
        public
    {
        uint256 eUtxoPos = _txBytes.getUtxoPos(_eUtxoIndex);
        uint256 txindex = (_cUtxoPos % 1000000000) / 10000;
        bytes32 root = childChain[_cUtxoPos / 1000000000].root;
        var txHash = keccak256(_txBytes);
        var confirmationHash = keccak256(txHash, root);
        var merkleHash = keccak256(txHash, _sigs);
        address owner = exits[eUtxoPos].owner;

        // Validate the spending transaction.
        require(owner == ECRecovery.recover(confirmationHash, _confirmationSig));
        require(merkleHash.checkMembership(txindex, root, _proof));

        // Delete the owner but keep the amount to prevent another exit.
        delete exits[eUtxoPos].owner;
    }

    /**
     * @dev Processes any exits that have completed the challenge period. 
     */
    function finalizeExits()
        public
    {
        uint256 utxoPos;
        uint256 exitable_at;
        (utxoPos, exitable_at) = getNextExit();
        Exit memory currentExit = exits[utxoPos];
        while (exitable_at < block.timestamp) {
            currentExit = exits[utxoPos];
            currentExit.owner.transfer(currentExit.amount);
            exitsQueue.delMin();
            delete exits[utxoPos].owner;

            if (exitsQueue.currentSize() > 0) {
                (utxoPos, exitable_at) = getNextExit();
            } else {
                return;
            }
        }
    }


    /* 
     * Public view functions
     */

    /**
     * @dev Queries the child chain.
     * @param _blockNumber Number of the block to return.
     * @return Child chain block at the specified block number.
     */
    function getChildChain(uint256 _blockNumber)
        public
        view
        returns (bytes32, uint256)
    {
        return (childChain[_blockNumber].root, childChain[_blockNumber].timestamp);
    }

    /**
     * @dev Determines the next deposit block number.
     * @return Block number to be given to the next deposit block.
     */
    function getDepositBlock()
        public
        view
        returns (uint256)
    {
        return currentChildBlock.sub(CHILD_BLOCK_INTERVAL).add(currentDepositBlock);
    }

    /**
     * @dev Returns information about an exit.
     * @param _utxoPos Position of the UTXO in the chain.
     * @return A tuple representing the active exit for the given UTXO.
     */
    function getExit(uint256 _utxoPos)
        public
        view
        returns (address, uint256)
    {
        return (exits[_utxoPos].owner, exits[_utxoPos].amount);
    }

    /**
     * @dev Determines the next exit to be processed.
     * @return A tuple of the position and time when this exit can be processed.
     */
    function getNextExit()
        public
        view
        returns (uint256, uint256)
    {
        uint256 priority = exitsQueue.getMin();
        uint256 utxoPos = uint256(uint128(priority));
        uint256 exitable_at = priority >> 128;
        return (utxoPos, exitable_at);
    }


    /*
     * Private functions
     */

    /**
     * @dev Adds an exit to the exit queue.
     * @param utxoPos Position of the UTXO in the child chain.
     * @param exitor Owner of the UTXO.
     * @param amount Amount to be exited.
     * @param created_at Time when the UTXO was created.
     */
    function addExitToQueue(
        uint256 utxoPos,
        address exitor,
        uint256 amount,
        uint256 created_at
    )
        private
    {
        // Calculate priority.
        uint256 exitable_at = Math.max(created_at + 2 weeks, block.timestamp + 1 weeks);
        uint256 priority = exitable_at << 128 | utxoPos;
        
        // Check exit is valid and doesn't already exist.
        require(amount > 0);
        require(exits[utxoPos].amount == 0);

        exitsQueue.insert(priority);
        exits[utxoPos] = Exit({
            owner: exitor,
            amount: amount
        });

        emit ExitStarted(msg.sender, utxoPos, amount);
    }
}
