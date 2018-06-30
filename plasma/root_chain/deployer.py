import json
import os
from solc import compile_standard
from web3.contract import ConciseContract
from web3 import Web3, HTTPProvider

OWN_DIR = os.path.dirname(os.path.realpath(__file__))
CONTRACTS_DIR = OWN_DIR + '/contracts'
OUTPUT_DIR = 'contract_data'


class Deployer(object):

    def __init__(self, provider=HTTPProvider('http://localhost:8545')):
        self.w3 = Web3(provider)

    @staticmethod
    def get_solc_input():
        """Walks the contract directory and returns a Solidity input dict

        Learn more about Solidity input JSON here: https://goo.gl/7zKBvj

        Returns:
            dict: A Solidity input JSON object as a dict
        """

        solc_input = {
            'language': 'Solidity',
            'sources': {
                file_name: {
                    'urls': [os.path.realpath(os.path.join(r, file_name))]
                } for r, d, f in os.walk(CONTRACTS_DIR) for file_name in f
            },
            'settings': {
                'outputSelection': {
                    "*": {
                        "": [
                            "legacyAST",
                            "ast"
                        ],
                        "*": [
                            "abi",
                            "evm.bytecode.object",
                            "evm.bytecode.sourceMap",
                            "evm.deployedBytecode.object",
                            "evm.deployedBytecode.sourceMap"
                        ]
                    }
                }
            }
        }

        return solc_input

    def compile_all(self):
        """Compiles all of the contracts in the /contracts directory

        Creates {contract name}.json files in /build that contain
        the build output for each contract.
        """

        # Solidity input JSON
        solc_input = self.get_solc_input()

        # Compile the contracts
        compilation_result = compile_standard(solc_input, allow_paths=CONTRACTS_DIR)

        # Create the output folder if it doesn't already exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Write the contract ABI to output files
        compiled_contracts = compilation_result['contracts']
        for contract_file in compiled_contracts:
            for contract in compiled_contracts[contract_file]:
                contract_name = contract.split('.')[0]
                contract_data = compiled_contracts[contract_file][contract_name]

                contract_data_path = OUTPUT_DIR + '/{0}.json'.format(contract_name)
                with open(contract_data_path, "w+") as contract_data_file:
                    json.dump(contract_data, contract_data_file)

    @staticmethod
    def get_contract_data(contract_name):
        """Returns the contract data for a given contract

        Args:
            contract_name (str): Name of the contract to return.

        Returns:
            str, str: ABI and bytecode of the contract
        """

        contract_data_path = OUTPUT_DIR + '/{0}.json'.format(contract_name)
        with open(contract_data_path, 'r') as contract_data_file:
            contract_data = json.load(contract_data_file)

        abi = contract_data['abi']
        bytecode = contract_data['evm']['bytecode']['object']

        return abi, bytecode

    def deploy_contract(self, contract_name, gas=5000000, args=(), concise=True):
        """Deploys a contract to the given Ethereum network using Web3

        Args:
            contract_name (str): Name of the contract to deploy. Must already be compiled.
            provider (HTTPProvider): The Web3 provider to deploy with.
            gas (int): Amount of gas to use when creating the contract.
            args (obj): Any additional arguments to include with the contract creation.
            concise (bool): Whether to return a Contract or ConciseContract instance.

        Returns:
            Contract: A Web3 contract instance.
        """

        abi, bytecode = self.get_contract_data(contract_name)

        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)

        # Get transaction hash from deployed contract
        tx_hash = contract.deploy(transaction={
            'from': self.w3.eth.accounts[0],
            'gas': gas
        }, args=args)

        # Get tx receipt to get contract address
        tx_receipt = self.w3.eth.getTransactionReceipt(tx_hash)
        contract_address = tx_receipt['contractAddress']

        contract_instance = self.w3.eth.contract(address=contract_address, abi=abi)

        print("Successfully deployed {0} contract!".format(contract_name))

        return ConciseContract(contract_instance) if concise else contract_instance

    def get_contract_at_address(self, contract_name, address, concise=True):
        """Returns a Web3 instance of the given contract at the given address

        Args:
            contract_name (str): Name of the contract. Must already be compiled.
            address (str): Address of the contract.
            concise (bool): Whether to return a Contract or ConciseContract instance.

        Returns:
            Contract: A Web3 contract instance.
        """

        abi, _ = self.get_contract_data(contract_name)

        contract_instance = self.w3.eth.contract(abi=abi, address=address)

        return ConciseContract(contract_instance) if concise else contract_instance
