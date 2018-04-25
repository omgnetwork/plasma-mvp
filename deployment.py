from plasma.root_chain.deployer import Deployer

deployer = Deployer()
deployer.compile_all()
deployer.deploy_contract("RootChain")
