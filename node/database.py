import json
import os


PORT = os.getenv("NODE_PORT", "8000")
DATABASE = f"database_{PORT}.json"


def initialize_database():

    if not os.path.exists(DATABASE):

        data = {
            "blockchain": [],
            "transactions": [],
            "nodes": []
        }

        save_database(data)



def load_database():

    with open(DATABASE, "r") as file:
        return json.load(file)



def save_database(data):

    with open(DATABASE, "w") as file:

        json.dump(
            data,
            file,
            indent=4
        )



def save_block(block):

    data = load_database()


    data["blockchain"].append(
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "nonce": block.nonce,

            "transactions": [

                {
                    "sender": tx.sender,
                    "receiver": tx.receiver,
                    "amount": tx.amount,
                    "signature": tx.signature,
                    "tx_id": tx.tx_id
                }

                for tx in block.transactions
            ]
        }
    )


    save_database(data)