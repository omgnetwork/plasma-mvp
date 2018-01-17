### PLASMA MVP WIP

We're implementing the [Minium Viable Plasma](https://ethresear.ch/t/minimal-viable-plasma/426.)


Current repo includes:

1. Root chain smart contracts
2. Building blocks for chail chain

The rest of the child chain and client will pushed up after an internal audit.

To deploy root chain smart contracts start testrpc on port 8454 and run:
    ``make root-chain``

To run tests:
    ``make tests``

Use this to close testrpc: 
    kill -9 $ \`lsof -i:8545 -t\`
