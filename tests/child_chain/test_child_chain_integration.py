from plasma.child_chain.transaction import Transaction

NULL_ADDRESS = b'\x00' * 20

def test_deposit_string(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
    '''

    test_lang.parse(test_lang_string)

    owner = test_lang.accounts['Owner1']
    tx = Transaction(0, 0, 0, 0, 0, 0, owner['address'], 100, NULL_ADDRESS, 0, 0)

    assert test_lang.transactions['Deposit1']['tx'].hash == tx.hash

    deposit_blknum = 1
    deposit_block = test_lang.child_chain.blocks[deposit_blknum]
    assert deposit_block.transaction_set[0].hash == tx.hash
    assert test_lang.root_chain.call().getChildChain(deposit_blknum)[0].encode('latin-1') == deposit_block.merkilize_transaction_set

def test_transfer_string(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1,null,null,null,null]
    '''

    test_lang.parse(test_lang_string)

    owner2 = test_lang.accounts['Owner2']
    tx = Transaction(1, 0, 0,
                     0, 0, 0,
                     owner2['address'], 100,
                     NULL_ADDRESS, 0,
                     0)

    assert test_lang.transactions['Transfer1']['tx'].hash == tx.hash
    assert test_lang.child_chain.current_block.transaction_set[0].hash == tx.hash

def test_submit_block_string(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1,null,null,null,null]
        SubmitBlock[]
    '''

    test_lang.parse(test_lang_string)

    blknum = 1000
    assert test_lang.root_chain.call().getChildChain(blknum)[0].encode('latin-1') == test_lang.child_chain.blocks[blknum].merkilize_transaction_set

def test_confirm_string(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1,null,null,null,null]
        SubmitBlock[]
        Confirm[Transfer1,Owner1,null]
    '''

    test_lang.parse(test_lang_string)

    assert test_lang.transactions['Transfer1']['confirm_sigs'] != ''

def test_withdraw_string(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,100]
        Transfer1[Deposit1,Owner2,100,Owner1,null,null,null,null]
        SubmitBlock[]
        Confirm[Transfer1,Owner1,null]
        Withdraw[Transfer1.0,Owner2]
    '''

    test_lang.parse(test_lang_string)

    owner2 = test_lang.accounts['Owner2']
    exit_data = test_lang.root_chain.call().getExit(1000000000000)
    assert exit_data[0].lower() == owner2['address']
    assert exit_data[1] == 100
