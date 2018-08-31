# Plasma MVP

We're implementing [Minimum Viable Plasma](https://ethresear.ch/t/minimal-viable-plasma/426). This repository represents a work in progress and will undergo large-scale modifications as requirements change.

## Overview

Plasma MVP is split into four main parts: `root_chain`, `child_chain`, `client`, and `cli`. Below is an overview of each sub-project.

### root_chain

`root_chain` represents the Plasma contract to be deployed to the root blockchain. In our case, this contract is written in Solidity and is designed to be deployed to Ethereum. `root_chain` also includes a compilation/deployment script.

`RootChain.sol` is based off of the Plasma design specified in [Minimum Viable Plasma](https://ethresear.ch/t/minimal-viable-plasma/426). Currently, this contract allows a single authority to publish child chain blocks to the root chain. This is *not* a permanent design and is intended to simplify development of more critical components in the short term.

### child_chain

`child_chain` is a Python implementation of a Plasma MVP child chain client. It's useful to think of `child_chain` as analogous to [Parity](https://www.parity.io) or [Geth](https://geth.ethereum.org). This component manages a store of `Blocks` and `Transactions` that are updated when events are fired in the root contract.

`child_chain` also contains an RPC server that enables client interactions. By default, this server runs on port `8546`.

### client

`client` is a simple Python wrapper of the RPC API exposed by `child_chain`, similar to `Web3.py` for Ethereum. You can use this client to write Python applications that interact with this Plasma chain.

### cli

`cli` is a simple Python application that uses `client` to interact with `child_chain`, via the command line. A detailed documentation of `cli` is available [here](#cli-documentation).

## Getting Started

### Dependencies

This project has a few pre-installation dependencies.

#### [Solidity](https://solidity.readthedocs.io/en/latest/installing-solidity.html)

Mac:
```sh
brew update
brew upgrade
brew tap ethereum/ethereum
brew install solidity
```

Linux:
```sh
sudo add-apt-repository ppa:ethereum/ethereum
sudo apt-get update
sudo apt-get install solc
```

Windows:

Follow [this guide](https://solidity.readthedocs.io/en/latest/installing-solidity.html#prerequisites-windows)


#### [Python 3.2+](https://www.python.org/downloads/)

Mac:
```sh
brew install python
```

Linux:
```sh
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3
```

Windows:
```sh
choco install python
```

#### [Ganache CLI 6.1.8+](https://github.com/trufflesuite/ganache-cli)

### Installation

Note: we optionally recommend using something like [`virtualenv`](https://pypi.python.org/pypi/virtualenv) in order to create an isolated Python environment:

```
$ virtualenv env -p python3
```

Fetch and install the project's dependencies with:

```
$ make
```

### Testing

Before you run tests, make sure you have an Ethereum client running and an JSON RPC API exposed on port `8545`. We recommend using `ganache-cli` to accomplish this when running tests. Start it with the command-line argument `-m="plasma_mvp"`.

Project tests can be found in the `tests/` folder. Run tests with:

```
$ make test
```

If you're contributing to this project, make sure you also install [`flake8`](https://pypi.org/project/flake8/) and lint your work:

```
$ make lint
```

### Starting Plasma

The fastest way to start playing with our Plasma MVP is by starting up `ganache-cli`, deploying everything locally, and running our CLI. Full documentation for the CLI is available [here](#cli-documentation).

```bash
$ ganache-cli -m=plasma_mvp # Start ganache-cli
$ make root-chain           # Deploy the root chain contract
$ make child-chain          # Run our child chain and server
```

## CLI Documentation

`omg` is a simple Plasma CLI that enables interactions with the child chain. Full documentation is provided below.

### `help`

#### Description

Shows a list of available commands.

#### Usage

```
--help
```

### `deposit`

#### Description

Creates a deposit transaction and submits it to the child chain.

#### Usage

```
deposit <amount> <address>
```

#### Example

```
deposit 100 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7
```

### `sendtx`

#### Description

Creates a transaction and submits it to the child chain.

#### Usage

```
sendtx <blknum1> <txindex1> <oindex1> <blknum2> <txindex2> <oindex2> <cur12> <newowner1> <amount1> <newowner2> <amount2> <key1> [<key2>]
```

#### Example

```
sendtx 1 0 0 0 0 0 0x0 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 50 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 45 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

### `submitblock`

#### Description

Signs and submits the current block to the root contract.

#### Usage

```
submitblock <key>
```

#### Example

```
submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

### `withdraw`

#### Description

Creates an exit transaction for the given UTXO.

#### Usage

```
withdraw <blknum> <txindex> <oindex> <key1> [<key2>]
```

#### Example

```
withdraw 1000 0 0 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

### `withdrawdeposit`

#### Description

Withdraws from a deposit.

#### Usage

```
withdrawdeposit <owner> <blknum> <amount>
```

#### Example

```
withdrawdeposit 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 1 100
```


## CLI Example

Let's play around a bit:

1. Deploy the root chain contract and start the child chain as per [Starting Plasma](#starting-plasma).

2. Start by depositing:
```
omg deposit 100 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7
```

3. Send a transaction:
```
omg sendtx 1 0 0 0 0 0 0x0 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 50 0x4B3eC6c9dC67079E82152d6D55d8dd96a8e6AA26 45 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

4.  Submit the block:
```
omg submitblock 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

5. Withdraw the original deposit (this is a double spend!):

```
omg withdrawdeposit 0xfd02EcEE62797e75D86BCff1642EB0844afB28c7 1 100
```

Note: The functionality to challenge double spends from the cli is still being worked on.
