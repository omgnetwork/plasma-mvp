import time
import json
import threading
from web3 import Web3, HTTPProvider
from hashlib import sha256

class RootEventListener(object):

    def __init__(self, root_chain, w3=Web3(HTTPProvider('http://localhost:8545')), finality=6):
        self.root_chain = root_chain
        self.w3 = w3
        self.finality = finality
    
        self.seen_events = {}
        self.active_events = {}
        self.subscribers = {}
        self.listen_for_event('Deposit')

    def on(self, event_name, event_handler):
        self.subscribers[event_name] = event_handler
        
    def listen_for_event(self, event_name):
        self.subscribers[event_name] = []
        self.active_events[event_name] = True
        threading.Thread(target=self.filter_loop, args=(event_name,)).start()

    def stop_listening_for_event(self, event_name):
        del self.active_events[event_name]

    def stop_all(self):
        for event in list(self.active_events):
            self.stop_listening_for_event(event)

    def filter_loop(self, event_name):
        while event_name in self.active_events:
            current_block = self.w3.eth.getBlock('latest')
            event_filter = self.root_chain.eventFilter(event_name, {
                'fromBlock': current_block['number'] - (self.finality * 2),
                'toBlock': current_block['number'] - self.finality
            })
            for event in event_filter.get_all_events():
                event_hash = self.hash_event(event)
                if event_hash not in self.seen_events:
                    self.seen_events[event_hash] = True
                    self.broadcast_event(event_name, event)
            time.sleep(5)

    def broadcast_event(self, event_name, event):
        for subscriber in self.subscribers[event_name]:
            subscriber(event)

    def hash_event(self, event):
        stringified_event = json.dumps(event, sort_keys=True)
        return sha256(stringified_event.encode()).hexdigest()
