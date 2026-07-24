from node.blockchain import Blockchain
from wallet.wallet import Wallet
from node.transaction import Transaction


def demo():

    alice = Wallet()
    bob = Wallet()
    miner = Wallet()

    coin = Blockchain()

    print("Alice address:", alice.address)
    print("Bob address:", bob.address)
    print("Miner address:", miner.address)

    print("\nMining Alice's funding block...")

    coin.mine_pending_transactions(alice.address)

    transaction = Transaction(
        alice.address,
        bob.address,
        10,
        alice.public_key
    )

    transaction.sign(
        alice.private_key
    )

    coin.add_transaction(
        transaction
    )

    coin.mine_pending_transactions(
        miner.address
    )

    print("\nBalances:")
    print("Alice:", coin.get_balance(alice.address))
    print("Bob:", coin.get_balance(bob.address))
    print("Miner:", coin.get_balance(miner.address))


if __name__ == "__main__":

    demo()
