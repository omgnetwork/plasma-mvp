### MVP PLASMA

This repo implements https://ethresear.ch/t/minimal-viable-plasma/426.

Use this to close testrpc: 
    kill -9 $ \`lsof -i:8545 -t\`

Notes:
    Right now confirmation signatures are:
    confirmationHash = keccak256(txHash, sig1, sig2, rootHash)
    confirmationSig = ecsign(confirmationHash, key)
    
    For those receiving a confirmation they should be able to prove that there transaction is included on the root chain but does that information need to be included in the confirmation signature itself or can the information simply be passed along?
