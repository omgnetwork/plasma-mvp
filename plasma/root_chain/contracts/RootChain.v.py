Deposit: __log__({depositor: indexed(address), amount: num(wei)})


authority: public(address)
genesis_block_hash: public(bytes32)

current_child_block: public(num)
last_parent_block: public(num)
child_chain: public({root: bytes32,
                    eth_deposited: num(wei),
                    submitted_at: num}[num])

current_deposit_id: public(num)

deposits: public({
    owner: address
    amount: num(wei),
    created_at: num,
}[num])


@public
def __init__(_authority: address):
    self.authority = _authority
    self.genesis_block_hash = extract32("'3\xe5\x0fRn\xc2\xfa\x19\xa2+1\xe8\xedP\xf2<\xd1\xfd\xf9L\x91T\xed:v\t\xa2\xf1\xff\x98\x1f", 0)
    self.current_child_block = 1
    self.current_deposit_id = 1
    self.last_parent_block = block.number
    self.child_chain[self.current_child_block] = self.genesis_block_hash

@public
def verify_membership(leaf: bytes32, index: num, root: bytes32, proof: bytes <= 512) -> bool:
    computed_hash = leaf
    _ind = index
    for i in range(15):
        proof_element = extract32(proof, i * 32)
        if _ind % 2 == 0:
            computed_hash = keccak256(concat(computed_hash, proof_element))
        else:
            computed_hash = keccak256(concat(proof_element, computed_hash))
        _ind = floor(decimal(_ind) / 2)
    if computed_hash == root:
        return True
    return False

@public
def submit_block(root: bytes32, eth_deposited: num(wei):
    assert msg.sender == self.authority
    assert block.number > self.last_parent_block + 6
    self.last_parent_block = block.number
    self.child_chain[self.current_child_block] = {
        root: root,
        eth_deposited: eth_deposited,
        submitted_at: block.timestamp
    self.current_child_block += 1

@public
@payable
def deposit(utxo_bytes: bytes <= 512):
    utxo = RLPList(utxo_bytes, [num, num, num, bytes32, num256, num256, num256,
                                num, num, num, bytes32, num256, num256, num256,
                                address, num,
                                address, num])
    for i in range(13):
        assert utxo[i] == null
    assert utxo[16] == 0
    assert utxo[17] == 0
    depositor = utxo[14]
    amount = utxo[15]
    assert amount > 0
    assert amount == msg.value
    assert depositor == msg.sender
    zero_bytes: bytes32
    utxo_hash = keccak256(utxo_bytes)
    root = utxo_hash
    for i in range(15):
        root = keccak256(concat(root, zero_bytes))
        zero_bytes = keccak256(zero_bytes, zero_bytes)
    self.deposits[self.current_deposit_id] = {
        owner: msg.sender
        amount: msg.value,
        created_at: block.timestamp,
    }
    self.child_chainp[self.current_block_number + self.current_deposit_id] = {
        root: root,
        eth_deposited: amount,
        submitted_at: block.timestamp
    }
    self.current_deposit_id += 1
    log.Deposit(depositor, amount)
