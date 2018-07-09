import os
import pytest
from ethereum.tools import tester, _solidity
from ethereum.abi import ContractTranslator
from ethereum import utils
from plasma_core.utils import utils as plasma_utils
from plasma.root_chain.deployer import Deployer
from testlang.testing_language import TestingLanguage


OWN_DIR = os.path.dirname(os.path.realpath(__file__))

# Compile contracts once before tests start
deployer = Deployer()
deployer.compile_all()


@pytest.fixture
def t():
    tester.chain = tester.Chain()
    return tester


def get_dirs(path):
    abs_contract_path = os.path.realpath(os.path.join(OWN_DIR, '..', 'plasma', 'root_chain', 'contracts'))
    sub_dirs = [x[0] for x in os.walk(abs_contract_path)]
    extra_args = ' '.join(['{}={}'.format(d.split('/')[-1], d) for d in sub_dirs])
    path = '{}/{}'.format(abs_contract_path, path)
    return path, extra_args


def create_abi(path):
    path, extra_args = get_dirs(path)
    abi = _solidity.compile_last_contract(path, combined='abi', extra_args=extra_args)['abi']
    return ContractTranslator(abi)


@pytest.fixture
def assert_tx_failed(t):
    def assert_tx_failed(function_to_test, exception=tester.TransactionFailed):
        initial_state = t.chain.snapshot()
        with pytest.raises(exception):
            function_to_test()
        t.chain.revert(initial_state)
    return assert_tx_failed


@pytest.fixture
def u():
    utils.plasma = plasma_utils
    return utils


@pytest.fixture
def get_contract(t, u):
    def create_contract(path, args=(), sender=t.k0):
        abi, hexcode = deployer.get_contract_data(path)
        bytecode = u.decode_hex(hexcode)
        ct = ContractTranslator(abi)
        code = bytecode + (ct.encode_constructor_arguments(args) if args else b'')
        address = t.chain.tx(sender=sender, to=b'', startgas=(4 * 10 ** 6 + 5 * 10 ** 5), value=0, data=code)
        return t.ABIContract(t.chain, abi, address)
    return create_contract


@pytest.fixture
def bytes_helper():
    def bytes_helper(inp, length):
        return bytes(length - len(inp)) + inp
    return bytes_helper


@pytest.fixture()
def test_lang():
    t = TestingLanguage()
    yield t
    t.child_chain.event_listener.stop_all()
