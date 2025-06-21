import time
import json
import hashlib
import random
import threading
from peer_discovery import known_peers
from outbox import gossip_message
from utils import generate_message_id

class TransactionMessage:
    #initialize
    def __init__(self, sender, receiver, amount, timestamp=None):
        self.type = "TX"    #transaction type   
        self.from_peer = sender   #sender's ID
        self.to_peer = receiver   #receiver's ID
        self.amount = amount     #amount of money to transfer
        self.timestamp = timestamp if timestamp else time.time()    #current timestamp
        self.id = self.compute_hash()   #compute hash of the transaction
        self.message_id = generate_message_id()  # 添加message_id字段

    def compute_hash(self):
        tx_data = {
            "type": self.type,
            "from": self.from_peer,
            "to": self.to_peer,
            "amount": self.amount,
            "timestamp": self.timestamp
        }
        return hashlib.sha256(json.dumps(tx_data, sort_keys=True).encode()).hexdigest()

    #change the transaction to a dictionary
    def to_dict(self):
        return {
            "type": self.type,
            "id": self.id,
            "from": self.from_peer,
            "to": self.to_peer,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "message_id": self.message_id  # 添加message_id到字典
        }

    @staticmethod
    def from_dict(data):
        tx = TransactionMessage(
            sender=data["from"],
            receiver=data["to"],
            amount=data["amount"],
            timestamp=data["timestamp"]
        )
        # 保留原始message_id（如果存在）
        if "message_id" in data:
            tx.message_id = data["message_id"]
        return tx
    
tx_pool = [] # local transaction pool
tx_ids = set() # the set of IDs of transactions in the local pool
    

#known_peers = {}        # { peer_id: (ip, port) }
def transaction_generation(self_id, interval=15):
    def loop():
        while True:
            if known_peers:
                peer_ids=known_peers.keys()
                peer_id_list=list(peer_ids)     #[peer1,peer2,peer3...]
                if self_id in peer_id_list:
                    peer_id_list.remove(self_id)
                if peer_id_list:    
                    peer_num=peer_id_list.__len__()
                    # TODO: Randomly choose a peer from `known_peers` and generate a transaction to transfer arbitrary amount of money to the peer.
                    random_num=random.randint(0,peer_num-1)
                    peer_select=peer_id_list[random_num]
                    amount=random.randint(0,100)
                    tx=TransactionMessage(sender=self_id,receiver=peer_select,amount=amount)
                    # TODO:  Add the transaction to local `tx_pool` using the function `add_transaction`.
                    add_transaction(tx)
                    # TODO:  Broadcast the transaction to `known_peers` using the function `gossip_message` in `outbox.py`.
                    gossip_message(self_id, tx.to_dict())
            time.sleep(interval)
    threading.Thread(target=loop, daemon=True).start()

def add_transaction(tx):
    # TODO: Add a transaction to the local `tx_pool` if it is in the pool.
    if tx.id not in tx_ids:
        tx_pool.append(tx)
        # TODO: Add the transaction ID to `tx_ids`.
        tx_ids.add(tx.id)
        # Optionally, you can print or log the transaction addition
        print(f"Transaction added: {tx.to_dict()}")
    else:
        print(f"Transaction {tx.id} already exists in the pool.")


def get_recent_transactions():
    # TODO: Return all transactions in the local `tx_pool`
    transaction_ids = []
    for tx in tx_pool:
        transaction_ids.append(tx.to_dict())
    return transaction_ids

def clear_pool():
    # Remove all transactions in `tx_pool` and transaction IDs in `tx_ids`.
    tx_ids.clear()
    tx_pool.clear()