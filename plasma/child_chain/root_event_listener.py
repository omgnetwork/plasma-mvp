import time
import random
import json
import threading
from web3 import Web3, HTTPProvider
from hashlib import sha256
from hexbytes import HexBytes
from web3.utils.datastructures import AttributeDict


class RootEventListener(object):
    """Listens to events on the root chain.

    We abstract the logic for listening to events because
    we only want events to be acted upon once they're considered
    finalized. Events are known to be missed accidentally sometimes,
    so we try to make event listening more robust.

    Args:
        root_chain (ConciseContract): A Web3 ConciseContract representing the root chain.
        w3 (Web3): A Web3 object.
        finality (int): Number of blocks before events should be considered final.
    """

    def __init__(self, root_chain, w3=Web3(HTTPProvider('http://localhost:8545')), confirmations=6):
        self.root_chain = root_chain
        self.w3 = w3
        self.confirmations = confirmations

        self.seen_events = {}
        self.active_events = {}
        self.subscribers = {}

        self.__listen_for_event('Deposit')
        self.__listen_for_event('ExitStarted')

    def on(self, event_name, event_handler):
        """Registers an event handler to an event by name.

        Event handlers are passed the Web3 Event dict.

        Args:
            event_name (str): Name of the event to listen to.
            event_handler (function): A function to call when the event is caught.
        """

        self.subscribers[event_name].append(event_handler)

    def __listen_for_event(self, event_name):
        """Registers an event as being watched for and starts a filter loop.

        Args:
            event_name (str): Name of the event to watch for.
        """

        self.subscribers[event_name] = []
        self.active_events[event_name] = True
        threading.Thread(target=self.filter_loop, args=(event_name,)).start()

    def stop_listening_for_event(self, event_name):
        """Stops watching for a certain event.

        Args:
            event_name (str): Name of event to deregister.
        """

        del self.active_events[event_name]

    def stop_all(self):
        """Stops watching for all events
        """

        for event in list(self.active_events):
            self.stop_listening_for_event(event)

    def filter_loop(self, event_name):
        """Starts a filter loop to broadcast events.

        Note that we only watch for events that occur between
        `confirmations` and `confirmations * 2`. This is important because
        we never want a client to act on an event that isn't
        finalized. We might catch the same event twice, so we hash
        each event and make sure we haven't seen that event yet before
        broadcasting

        Args:
            event_name (str): Name of event to watch.
        """

        while event_name in self.active_events:
            current_block = self.w3.eth.getBlock('latest')

            event_filter = self.root_chain.eventFilter(event_name, {
                'fromBlock': current_block['number'] - (self.confirmations * 2 + 1),
                'toBlock': current_block['number'] + 1 - self.confirmations
            })

            for event in event_filter.get_all_entries():
                event_hash = self.__hash_event(event)
                if event_hash not in self.seen_events:
                    self.seen_events[event_hash] = True
                    self.broadcast_event(event_name, event)

            time.sleep(random.random())

    def broadcast_event(self, event_name, event):
        """Broadcasts an event to all subscribers.

        Args:
            event_name (str): Name of event to broadcast.
            event (dict): Event data to broadcast.
        """

        for subscriber in self.subscribers[event_name]:
            subscriber(event)

    def __hash_event(self, event):
        """Returns the sha256 hash of an event dict.

        Args:
            event (dict): Event dict to hash.

        Returns:
            str: Hexadecimal hash string.
        """

        # HACK: Be able to JSON serialize the AttributeDict/HexBytes objects https://github.com/ethereum/web3.py/issues/782

        class CustomJsonEncoder(json.JSONEncoder):
            def default(self, obj):   # pylint: disable=E0202
                if isinstance(obj, AttributeDict):
                    return obj.__dict__
                if isinstance(obj, HexBytes):
                    return obj.hex()
                return super().default(obj)

        stringified_event = json.dumps(dict(event), sort_keys=True, cls=CustomJsonEncoder)
        return sha256(stringified_event.encode()).hexdigest()
