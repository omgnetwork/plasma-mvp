import json
import web3
import os
from ethereum.tools import tester as t
from ethereum.tools import _solidity
from solc import compile_standard
from web3.contract import ConciseContract
from web3 import Web3, HTTPProvider


OWN_DIR = os.path.dirname(os.path.realpath(__file__))


class Deployer(object):

    def __init__(self, provider=HTTPProvider('http://localhost:8545')):
        self.w3 = Web3(provider)

    def get_dirs(self, path):
        abs_contract_path = os.path.realpath(os.path.join(OWN_DIR, 'contracts'))
        extra_args = [[file, [os.path.realpath(os.path.join(r, file))]] for r, d, f in os.walk(abs_contract_path) for file in f]
        contracts = {}
        for contract in extra_args:
            contracts[contract[0]] = {'urls': contract[1]}
        path = '{}/{}'.format(abs_contract_path, path)
        return path, contracts

    def compile_contract(self, path, args=()):
        file_name = path.split('/')[1]
        contract_name = file_name.split('.')[0]
        path, contracts = self.get_dirs(path)
        compiled_sol = compile_standard({'language': 'Solidity',
                                         'sources': {**{path.split('/')[-1]: {'urls': [path]}}, **contracts}},  # Noqa E999
                                        allow_paths=OWN_DIR + "/contracts")
        abi = compiled_sol['contracts'][file_name][contract_name]['abi']
        bytecode = compiled_sol['contracts'][file_name][contract_name]['evm']['bytecode']['object']
        contract_file = open("contract_data/%s.json" % (file_name.split('.')[0]), "w+")
        json.dump(abi, contract_file)
        contract_file.close()
        return abi, bytecode

    def create_contract(self, path, args=(), gas=4410000, sender=t.k0):
        abi, bytecode = self.compile_contract(path, args)
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        # Get transaction hash from deployed contract
        tx_hash = contract.deploy(transaction={'from': self.w3.eth.accounts[0], 'gas': gas}, args=args)

        # Get tx receipt to get contract address
        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
        contract_address = tx_receipt['contractAddress']

        # Contract instance in concise mode
        contract_instance = self.w3.eth.contract(abi, contract_address, ContractFactoryClass=ConciseContract)
        return contract_instance
