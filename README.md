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

- [LevelDB](https://github.com/google/leveldb)

Mac:
```
$ brew install leveldb
```

Linux:

LevelDB should be installed along with `plyvel` once you make the project later on.

Windows:

First, install [vcpkg](https://github.com/Microsoft/vcpkg). Then,

```
> vcpkg install leveldb
```

- [Solidity 0.4.18](https://github.com/ethereum/solidity/releases/tag/v0.4.18)

Mac:
```
$ brew unlink solidity
$ brew install https://raw.githubusercontent.com/ethereum/homebrew-ethereum/2aea171d7d6901b97d5f1f71bd07dd88ed5dfb42/solidity.rb
```

Linux:
```
$ wget https://github.com/ethereum/solidity/releases/download/v0.4.18/solc-static-linux
$ chmod +x ./solc-static-linux
$ sudo mv solc-static-linux /usr/bin/solc
```

Windows:

Follow [this guide](https://solidity.readthedocs.io/en/v0.4.21/installing-solidity.html#prerequisites-windows).

- [Python 3.2+](https://www.python.org/downloads/)

It's also recommended to run [`ganache-cli`](https://github.com/trufflesuite/ganache-cli) when developing, testing, or playing around. This will allow you to receive near instant feedback.

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

Before you run tests, make sure you have an Ethereum client running and an JSON RPC API exposed on port `8545`. We recommend using `ganache-cli` to accomplish this when running tests.

Project tests can be found in the `tests/` folder. Run tests with:

```
$ make test
```

If you're contributing to this project, make sure you also lint your work:

```
$ make lint
```

### Starting Plasma

The fastest way to start playing with our Plasma MVP is by starting up `ganache-cli`, deploying everything locally, and running our CLI. Full documentation for the CLI is available [here](#cli-documentation).

```bash
$ ganache-cli -m=plasma_mvp # Start ganache-cli
$ make root-chain           # Deploy the root chain contract
$ make child-chain          # Run our child chain and server
$ omg start                 # Start the Plasma CLI
```

## CLI Documentation

`omg` is a simple Plasma CLI that enables interactions with the child chain. Full documentation is provided below.

### `help`

#### Description

Shows a list of available commands.

#### Usage

```
help
```

### `deposit`

#### Description

Creates a deposit transaction and submits it to the child chain.

#### Usage

```
deposit <amount> <key>
```

#### Example

```
deposit 100 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

### `send_tx`

#### Description

Creates a transaction and submits it to the child chain.

#### Usage

```
send_tx <blknum1> <tx_pos1> <utxo_pos1> <blknum2> <tx_pos2> <utxo_pos2> <newowner1> <amount1> <newowner2> <amount2> <fee> <key1> [<key2>]
```

#### Example

```
send_tx 1 0 0 0 0 0 0xfd02ecee62797e75d86bcff1642eb0844afb28c7 50 0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26 45 5 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

### `submit_block`

#### Description

Signs and submits the current block to the root contract.

#### Usage

```
submit_block <key>
```

#### Example

```
submit_block 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

### `withdraw`

#### Description

Creates an exit transaction for the given UTXO.

#### Usage

```
withdraw <blknum> <tx_pos> <utxo_pos> <key1> [<key2>]
```

#### Example

```
withdraw 1 0 0 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

### `send_tx`

#### Description

Writes any unsynced blocks to a local database.

#### Usage

```
sync
```

## CLI Example

Let's play around a bit:

1. Start the server and CLI up as per [Starting Plasma](#starting-plasma).

2. We'll start by depositing:
```
deposit 100 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

3. Then we'll send a tx:
```
send_tx 1 0 0 0 0 0 0xfd02ecee62797e75d86bcff1642eb0844afb28c7 50 0x4b3ec6c9dc67079e82152d6d55d8dd96a8e6aa26 45 5 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

4.  Next we'll submit the block:
```
submit_block 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

5. Now we'll withdraw our original deposit (this is a double spend!):

```
withdraw 1 0 0 3bb369fecdc16b93b99514d8ed9c2e87c5824cf4a6a98d2e8e91b7dd0c063304
```

Note: The functionality to challenge double spends from the cli is still being worked on.

6. Now we'll sync with the child chain (the deposit and the block we just submitted) locally: 
```
sync
```

7. And finally we'll close the client with `Ctrl+C`.
