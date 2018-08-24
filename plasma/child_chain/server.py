import rlp
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from jsonrpc import JSONRPCResponseManager, dispatcher
from ethereum import utils
from plasma.child_chain.child_chain import ChildChain
from plasma.root_chain.deployer import Deployer
from plasma_core.constants import CONTRACT_ADDRESS, AUTHORITY
from plasma_core.block import Block
from plasma_core.transaction import Transaction

root_chain = Deployer().get_contract_at_address("RootChain", CONTRACT_ADDRESS, concise=False)
child_chain = ChildChain(AUTHORITY['address'], root_chain)


@Request.application
def application(request):
    # Dispatcher is dictionary {<method_name>: callable}
    dispatcher["submit_block"] = lambda block: child_chain.submit_block(rlp.decode(utils.decode_hex(block), Block))
    dispatcher["apply_transaction"] = lambda transaction: child_chain.apply_transaction(rlp.decode(utils.decode_hex(transaction), Transaction))
    dispatcher["get_transaction"] = lambda blknum, txindex: rlp.encode(child_chain.get_transaction(blknum, txindex), Transaction).hex()
    dispatcher["get_current_block"] = lambda: rlp.encode(child_chain.get_current_block(), Block).hex()
    dispatcher["get_current_block_num"] = lambda: child_chain.get_current_block_num()
    dispatcher["get_block"] = lambda blknum: rlp.encode(child_chain.get_block(blknum), Block).hex()
    response = JSONRPCResponseManager.handle(
        request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


if __name__ == '__main__':
    run_simple('localhost', 8546, application)
