def test_parse_token_without_method_id(test_lang):
    test_lang_string = '''
        Withdraw[Deposit1,Owner1]
    '''

    handler, arguments = test_lang.parse_token(test_lang_string)

    assert handler == 'Withdraw'
    assert arguments == ['Deposit1', 'Owner1']


def test_parse_token_with_method_id(test_lang):
    test_lang_string = '''
        Deposit1[Owner1,Amount1]
    '''

    handler, arguments = test_lang.parse_token(test_lang_string)

    assert handler == 'Deposit'
    assert arguments == ['Deposit1', 'Owner1', 'Amount1']


def test_parse_token_with_null_args(test_lang):
    test_lang_string = '''
        Transfer1[Deposit1,Owner2,100,Owner1,null,null,null,null]
    '''

    handler, arguments = test_lang.parse_token(test_lang_string)

    assert handler == 'Transfer'
    assert arguments == ['Transfer1', 'Deposit1', 'Owner2', '100', 'Owner1', None, None, None, None]


def test_get_account(test_lang):
    account1 = test_lang.get_account('NonexistentAccount1')
    assert account1['address'] == '0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26'

    account2 = test_lang.get_account('NonexistentAccount2')
    assert account2['address'] == '0xda20a48913f9031337a5e32325f743e8536860e2'
