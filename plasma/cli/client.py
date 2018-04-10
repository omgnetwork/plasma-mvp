import click
import plyvel
import rlp
from ethereum import utils
from .main import main
from plasma.utils.utils import confirm_tx
from plasma.client.client import Client
from plasma.child_chain.child_chain import Block
from plasma.child_chain.transaction import Transaction


@main.command('start')
@click.pass_context
def start_client_cmd(ctx):
    client_parser = ClientParser()
    while True:
        inp = input(">").split(' ')
        client_parser.process_input(inp)


class ClientParser():

    def __init__(self):
        self.client = Client()
        self.db = plyvel.DB('/tmp/plasma_mvp_db/', create_if_missing=True)
        self.current_block = self.client.get_current_block_num()
        self.synced_block = 1
        self.client_cmds = dict(
            sync=self.sync_child_chain,
            deposit=self.deposit,
            send_tx=self.send_tx,
            submit_block=self.submit_block,
            withdraw=self.withdraw,
            help=self.help,
        )

    def process_input(self, inp):
        self.inp = inp
        command = self.inp[0]
        if command not in self.client_cmds:
            print("Please enter a valid command ('or enter help')")
        else:
            return self.client_cmds[command]()

    def sync_child_chain(self):
        self.current_block = self.client.get_current_block_num()
        while self.synced_block < self.current_block:
            block_number = self.synced_block
            block = self.client.get_block(self.synced_block)
            self.db.put(bytes(block_number), utils.str_to_bytes(block))
            print("Synced %s" % self.synced_block)
            self.synced_block += 1
        print("Syncing complete!")

    def deposit(self):
        if len(self.inp) != 3:
            raise Exception("Wrong number of inputs for deposit")
        amount1 = int(self.inp[1])
        key = utils.normalize_key(self.inp[2])
        newOwner1 = utils.privtoaddr(key)
        newOwner2, amount2 = utils.normalize_address(b'\x00' * 20), 0
        tx = Transaction(0, 0, 0, 0, 0, 0,
                         newOwner1, amount1,
                         newOwner2, amount2,
                         0)
        self.client.deposit(tx)
        print("Succesfully deposited %s to %s" % (amount1, newOwner1))

    def send_tx(self):
        if len(self.inp) != 14 and len(self.inp) != 13:
            raise Exception("Wrong number of inputs for sending a transaction!")
        blknum1, tx_pos1, utxo_pos1 = int(self.inp[1]), int(self.inp[2]), int(self.inp[3])
        blknum2, tx_pos2, utxo_pos2 = int(self.inp[4]), int(self.inp[5]), int(self.inp[6])
        newowner1 = utils.normalize_address(self.inp[7])
        amount1 = int(self.inp[8])
        newowner2 = utils.normalize_address(self.inp[9])
        amount2 = int(self.inp[10])
        fee = int(self.inp[11])
        key1 = utils.normalize_key(self.inp[12])
        key2 = utils.normalize_key(self.inp[13]) if len(self.inp) == 14 else b''
        tx = Transaction(blknum1, tx_pos1, utxo_pos1,
                         blknum2, tx_pos2, utxo_pos2,
                         newowner1, amount1,
                         newowner2, amount2,
                         fee)
        tx.sign1(key1)
        if key2:
            tx.sign2(key2)
        self.client.apply_transaction(tx)
        print("Succesfully added transaction!")

    def submit_block(self):
        if len(self.inp) != 2:
            raise("Wrong number of inputs to submit block")
        key = utils.normalize_key(self.inp[1])
        block = self.client.get_current_block()
        block = rlp.decode(utils.decode_hex(block), Block)
        block.make_mutable()
        block.sign(key)
        self.client.submit_block(block)
        print("Successfully submitted a block!")

    def withdraw(self):
        blknum, txindex, oindex = int(self.inp[1]), int(self.inp[2]), int(self.inp[3])
        txPos = [blknum, txindex, oindex]
        key1 = utils.normalize_key(self.inp[4])
        key2 = utils.normalize_key(self.inp[5]) if len(self.inp) == 6 else b''
        block = self.client.get_block(blknum)
        block = rlp.decode(utils.decode_hex(block), Block)
        tx = block.transaction_set[txindex]
        block.merkilize_transaction_set
        proof = block.merkle.create_membership_proof(tx.merkle_hash)
        confirmSig1 = confirm_tx(tx, block.merkle.root, key1)
        confirmSig2 = b''
        if key2:
            confirmSig2 = confirm_tx(tx, block.merkle.root, key2)
        sigs = tx.sig1 + tx.sig2 + confirmSig1 + confirmSig2
        self.client.withdraw(txPos, tx, proof, sigs)
        print("Successfully submitted a withdrawal")

    def help(self):
        print("Please enter one of the following commands:")
        for cmd in self.client_cmds:
            print(cmd)
