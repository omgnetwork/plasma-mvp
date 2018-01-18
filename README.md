### PLASMA MVP WIP

We're implementing the [Minimum Viable Plasma](https://ethresear.ch/t/minimal-viable-plasma/426.)


Current repo includes:

1. Root chain smart contracts
2. Building blocks for child chain

The rest of the child chain and client will pushed up after an internal audit.

To deploy root chain smart contracts start testrpc on port 8454 and run:
    ``make root-chain``

To run tests:
    ``make test``

